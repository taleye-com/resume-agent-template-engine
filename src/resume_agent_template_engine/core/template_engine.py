import os
import yaml
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
    InternalServerException,
)
from .base import TemplateInterface, DocumentType
from .template_registry import get_available_templates as registry_get_available_templates
from .universal_template import UniversalTemplate

logger = logging.getLogger(__name__)


# TemplateInterface and DocumentType moved to base.py to avoid circular imports


class OutputFormat(str, Enum):
    """Supported output formats"""

    PDF = "pdf"
    LATEX = "latex"
    HTML = "html"


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
    """
    Registry for discovering and managing templates

    Now uses central template registry instead of scanning for helper.py files
    """

    def __init__(self, templates_base_path: str = "templates"):
        """
        Initialize template registry

        Args:
            templates_base_path: Base path for templates directory
        """
        self.templates_base_path = Path(templates_base_path)
        self._template_cache = {}
        # Use central registry instead of discovery
        self._available_templates = registry_get_available_templates()

    def get_available_templates(
        self, document_type: Optional[str] = None
    ) -> Union[Dict[str, List[str]], List[str]]:
        """Get available templates from central registry"""
        if document_type:
            return self._available_templates.get(document_type, [])
        return self._available_templates

    def load_template_class(self, document_type: str, template_name: str) -> type:
        """
        Load template class - now returns UniversalTemplate instead of helper classes
        """
        cache_key = f"{document_type}_{template_name}"

        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        if document_type not in self._available_templates:
            raise TemplateNotFoundException(
                template_name="",
                document_type=document_type,
                available_templates=list(self._available_templates.keys()),
            )

        if template_name not in self._available_templates[document_type]:
            raise TemplateNotFoundException(
                template_name=template_name,
                document_type=document_type,
                available_templates=self._available_templates[document_type],
            )

        # Return a factory function that creates UniversalTemplate instances
        def template_factory(data: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
            return UniversalTemplate(document_type, template_name, data, config)

        # Cache the factory
        self._template_cache[cache_key] = template_factory
        return template_factory


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
                available_templates=available,
            )

        # Load template factory
        template_factory = self.registry.load_template_class(document_type, template_name)

        # Get template-specific configuration
        template_config = self.config.get_template_config(document_type, template_name)

        # Create instance using factory
        return template_factory(data, template_config)

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
                details=f"Unsupported output format: {output_format}",
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
                available_templates=available,
            )

        template_factory = self.registry.load_template_class(document_type, template_name)

        # Create a dummy instance to get metadata
        try:
            temp_data = {"personalInfo": {"name": "Test", "email": "test@example.com"}}
            if document_type == "cover_letter":
                temp_data["body"] = "Test body"
            template_instance = template_factory(temp_data)
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
            "class_name": "UniversalTemplate",
            "description": f"{template_name.capitalize()} template for {document_type.replace('_', ' ')}",
        }
