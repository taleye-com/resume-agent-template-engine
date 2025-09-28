import os
import yaml
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import importlib.util
import logging
from enum import Enum

from .errors import ErrorCode
from .exceptions import (
    TemplateNotFoundException,
    TemplateCompilationException,
    TemplateRenderingException,
    InternalServerException
)

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    """Supported document types"""

    RESUME = "resume"
    COVER_LETTER = "cover_letter"


class OutputFormat(str, Enum):
    """Supported output formats"""

    PDF = "pdf"
    LATEX = "latex"
    HTML = "html"


class TemplateInterface(ABC):
    """Abstract base class for all templates"""

    def __init__(self, data: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        """
        Initialize template with data and configuration

        Args:
            data: Document data
            config: Template-specific configuration
        """
        self.data = data
        self.config = config or {}
        self.validate_data()

    @abstractmethod
    def validate_data(self) -> None:
        """Validate that required data fields are present"""
        pass

    @abstractmethod
    def render(self) -> str:
        """Render the template to LaTeX/HTML content"""
        pass

    @abstractmethod
    def export_to_pdf(self, output_path: str) -> str:
        """Export the rendered content to PDF"""
        pass

    @property
    @abstractmethod
    def required_fields(self) -> List[str]:
        """List of required data fields for this template"""
        pass

    @property
    @abstractmethod
    def template_type(self) -> DocumentType:
        """The document type this template handles"""
        pass


class TemplateConfig:
    """Configuration manager for templates"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path or not os.path.exists(self.config_path):
            return self._get_default_config()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load config from {self.config_path}: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "templates": {
                "base_path": "templates",
                "auto_discover": True,
                "supported_formats": ["pdf", "latex"],
            },
            "rendering": {
                "latex_engine": "pdflatex",
                "temp_dir": None,
                "cleanup": True,
            },
            "validation": {
                "strict_mode": False,
                "required_fields": {
                    "resume": ["personalInfo"],
                    "cover_letter": ["personalInfo", "recipient"],
                },
            },
        }

    def get_template_config(
        self, document_type: str, template_name: str
    ) -> Dict[str, Any]:
        """Get configuration for a specific template"""
        return (
            self.config.get("templates", {})
            .get(document_type, {})
            .get(template_name, {})
        )

    def get_rendering_config(self) -> Dict[str, Any]:
        """Get rendering configuration"""
        return self.config.get("rendering", {})


class TemplateRegistry:
    """Registry for discovering and managing templates"""

    def __init__(self, templates_base_path: str = "templates"):
        """
        Initialize template registry

        Args:
            templates_base_path: Base path for templates directory
        """
        self.templates_base_path = Path(templates_base_path)
        self._template_cache = {}
        self._discover_templates()

    def _discover_templates(self) -> None:
        """Discover available templates by scanning directories"""
        self._available_templates = {}

        if not self.templates_base_path.exists():
            logger.warning(f"Templates directory not found: {self.templates_base_path}")
            return

        for doc_type_dir in self.templates_base_path.iterdir():
            if not doc_type_dir.is_dir() or doc_type_dir.name.startswith("__"):
                continue

            doc_type = doc_type_dir.name
            self._available_templates[doc_type] = []

            for template_dir in doc_type_dir.iterdir():
                if not template_dir.is_dir() or template_dir.name.startswith("__"):
                    continue

                # Check if template has required files
                helper_file = template_dir / "helper.py"
                tex_files = list(template_dir.glob("*.tex"))

                if helper_file.exists() and tex_files:
                    self._available_templates[doc_type].append(template_dir.name)

    def get_available_templates(
        self, document_type: Optional[str] = None
    ) -> Union[Dict[str, List[str]], List[str]]:
        """Get available templates, optionally filtered by document type"""
        if document_type:
            return self._available_templates.get(document_type, [])
        return self._available_templates

    def load_template_class(self, document_type: str, template_name: str) -> type:
        """Load template class dynamically"""
        cache_key = f"{document_type}_{template_name}"

        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        if document_type not in self._available_templates:
            raise TemplateNotFoundException(
                template_name="",
                document_type=document_type,
                available_templates=list(self._available_templates.keys())
            )

        if template_name not in self._available_templates[document_type]:
            raise TemplateNotFoundException(
                template_name=template_name,
                document_type=document_type,
                available_templates=self._available_templates[document_type]
            )

        # Load the template class
        helper_path = (
            self.templates_base_path / document_type / template_name / "helper.py"
        )

        spec = importlib.util.spec_from_file_location(
            f"{document_type}_{template_name}", helper_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find template class in module
        template_class = self._find_template_class(module, document_type, template_name)

        # Cache the class
        self._template_cache[cache_key] = template_class
        return template_class

    def _find_template_class(
        self, module, document_type: str, template_name: str
    ) -> type:
        """Find the template class in the loaded module"""
        # Generate possible class names
        doc_type_camel = "".join(x.capitalize() for x in document_type.split("_"))
        template_camel = template_name.capitalize()

        possible_names = [
            f"{template_camel}{doc_type_camel}Template",
            f"{doc_type_camel}{template_camel}Template",
            f"{template_camel}Template",
        ]

        for class_name in possible_names:
            if hasattr(module, class_name):
                return getattr(module, class_name)

        # Fallback: find any class ending with 'Template'
        template_classes = [
            name
            for name in dir(module)
            if name.endswith("Template") and not name.startswith("_")
        ]
        if template_classes:
            return getattr(module, template_classes[0])

        raise TemplateCompilationException(
            template_name=template_name,
            details=f"No template class found in {module.__name__}"
        )


class TemplateEngine:
    """
    Central template engine for document generation
    """

    def __init__(
        self, config_path: Optional[str] = None, templates_path: Optional[str] = None
    ):
        """
        Initialize the template engine

        Args:
            config_path: Path to YAML configuration file
            templates_path: Path to templates directory
        """
        self.config = TemplateConfig(config_path)

        # Determine templates path
        if templates_path:
            self.templates_path = templates_path
        else:
            # Default to templates directory relative to this module
            module_dir = Path(
                __file__
            ).parent.parent  # Go up to resume_agent_template_engine
            default_templates_path = module_dir / "templates"

            config_templates_path = self.config.config.get("templates", {}).get(
                "base_path", str(default_templates_path)
            )

            # If config path is relative, make it relative to module dir
            if not os.path.isabs(config_templates_path):
                self.templates_path = str(module_dir / config_templates_path)
            else:
                self.templates_path = config_templates_path

        self.registry = TemplateRegistry(self.templates_path)
        available_templates = self.get_available_templates()
        total_templates = (
            sum(len(templates) for templates in available_templates.values())
            if isinstance(available_templates, dict)
            else len(available_templates)
        )
        logger.info(
            f"TemplateEngine initialized with {total_templates} templates from {self.templates_path}"
        )

    def get_available_templates(
        self, document_type: Optional[str] = None
    ) -> Union[Dict[str, List[str]], List[str]]:
        """Get available templates"""
        return self.registry.get_available_templates(document_type)

    def validate_template(self, document_type: str, template_name: str) -> bool:
        """Validate that a template exists and is usable"""
        try:
            available = self.get_available_templates(document_type)
            return template_name in available
        except Exception:
            return False

    def create_template(
        self, document_type: str, template_name: str, data: Dict[str, Any]
    ) -> TemplateInterface:
        """
        Create a template instance

        Args:
            document_type: Type of document (resume, cover_letter)
            template_name: Name of the template
            data: Document data

        Returns:
            Template instance
        """
        if not self.validate_template(document_type, template_name):
            available = self.get_available_templates(document_type)
            raise TemplateNotFoundException(
                template_name=template_name,
                document_type=document_type,
                available_templates=available
            )

        # Load template class
        template_class = self.registry.load_template_class(document_type, template_name)

        # Get template-specific configuration
        template_config = self.config.get_template_config(document_type, template_name)

        # Create instance
        return template_class(data, template_config)

    def render_document(
        self,
        document_type: str,
        template_name: str,
        data: Dict[str, Any],
        output_format: OutputFormat = OutputFormat.LATEX,
    ) -> str:
        """
        Render a document to the specified format

        Args:
            document_type: Type of document
            template_name: Name of the template
            data: Document data
            output_format: Output format

        Returns:
            Rendered content
        """
        template = self.create_template(document_type, template_name, data)

        if output_format == OutputFormat.LATEX:
            return template.render()
        elif output_format == OutputFormat.PDF:
            # For PDF, we still return the LaTeX content
            # The actual PDF generation happens in export_to_pdf
            return template.render()
        else:
            raise TemplateRenderingException(
                template_name=template_name,
                details=f"Unsupported output format: {output_format}"
            )

    def export_to_pdf(
        self,
        document_type: str,
        template_name: str,
        data: Dict[str, Any],
        output_path: str,
    ) -> str:
        """
        Export document directly to PDF

        Args:
            document_type: Type of document
            template_name: Name of the template
            data: Document data
            output_path: Path for output PDF

        Returns:
            Path to generated PDF
        """
        template = self.create_template(document_type, template_name, data)
        return template.export_to_pdf(output_path)

    def get_template_info(
        self, document_type: str, template_name: str
    ) -> Dict[str, Any]:
        """
        Get information about a specific template

        Args:
            document_type: Type of document
            template_name: Name of the template

        Returns:
            Template information
        """
        if not self.validate_template(document_type, template_name):
            available = self.get_available_templates(document_type)
            raise TemplateNotFoundException(
                template_name=template_name,
                document_type=document_type,
                available_templates=available
            )

        template_class = self.registry.load_template_class(document_type, template_name)

        # Create a dummy instance to get metadata
        try:
            temp_data = {"personalInfo": {"name": "Test", "email": "test@example.com"}}
            template_instance = template_class(temp_data)
            required_fields = template_instance.required_fields
        except Exception:
            required_fields = []

        template_dir = Path(self.templates_path) / document_type / template_name

        # Look for preview image
        preview_path = None
        for ext in [".png", ".jpg", ".jpeg"]:
            preview_file = template_dir / f"preview{ext}"
            if preview_file.exists():
                preview_path = str(preview_file)
                break

        return {
            "name": template_name,
            "document_type": document_type,
            "required_fields": required_fields,
            "preview_path": preview_path,
            "template_dir": str(template_dir),
            "class_name": template_class.__name__,
            "description": f"{template_name.capitalize()} template for {document_type.replace('_', ' ')}",
        }
