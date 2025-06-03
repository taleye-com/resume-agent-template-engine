import os
import yaml
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import importlib.util
import logging
from enum import Enum

# Import new validation and systems
from .base_validator import ValidationError, ValidationIssue, ValidationSeverity
from .schema_validator import SchemaValidator, DocumentSchema
from .template_validator import TemplateValidator
from .template_inheritance import TemplateInheritanceManager, BaseTemplate
from .macro_system import MacroRegistry, MacroProcessor, MacroLibrary
from .build_system import ParallelBuilder, CrossPlatformBuilder, BuildRequest
from .template_versioning import TemplateVersionManager
from .variable_system import TemplateVariableSystem
from .font_system import FontManager, FontConfigGenerator
from .image_handler import ImageProcessor, LaTeXImageHandler
from .memory_optimizer import MemoryOptimizer, memory_efficient_decorator

logger = logging.getLogger(__name__)


def _ensure_string(value) -> str:
    """Convert enum or any value to string, handling DocumentType enums properly"""
    if hasattr(value, "value"):
        return value.value
    return str(value)


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
            "memory": {
                "auto_monitor": True,
                "memory_threshold": 80.0,
                "template_cache_size": 50,
                "template_cache_memory": 100,
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
        # Ensure document_type is a string (handle enum values)
        document_type = _ensure_string(document_type)

        cache_key = f"{document_type}_{template_name}"

        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        if document_type not in self._available_templates:
            raise ValueError(f"Document type '{document_type}' not found")

        if template_name not in self._available_templates[document_type]:
            raise ValueError(
                f"Template '{template_name}' not found for {document_type}"
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

        raise ValueError(f"No template class found in {module.__name__}")


class TemplateEngine:
    """
    Central template engine for document generation - Fast compiler with advanced features
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

        # Initialize core systems with memory optimization
        memory_config = self.config.config.get("memory", {})
        self.memory_optimizer = MemoryOptimizer(memory_config)

        # Initialize validation systems
        self.schema_validator = SchemaValidator()
        self.template_validator = TemplateValidator()
        self.inheritance_manager = TemplateInheritanceManager(self.templates_path)

        # Initialize macro and variable systems
        self.macro_registry = MacroRegistry()
        self.macro_processor = MacroProcessor(self.macro_registry)
        self.macro_library = MacroLibrary()
        self.variable_system = TemplateVariableSystem()

        # Initialize build and processing systems
        self.parallel_builder = ParallelBuilder()
        self.cross_platform_builder = CrossPlatformBuilder()
        self.version_manager = TemplateVersionManager(self.templates_path)

        # Initialize font and image systems
        self.font_manager = FontManager()
        self.font_config_generator = FontConfigGenerator(self.font_manager)
        self.image_processor = ImageProcessor()
        self.latex_image_handler = LaTeXImageHandler(self.image_processor)

        # Load macro collections
        self._load_macro_collections()

        available_templates = self.get_available_templates()
        total_templates = (
            sum(len(templates) for templates in available_templates.values())
            if isinstance(available_templates, dict)
            else len(available_templates)
        )
        logger.info(
            f"TemplateEngine initialized with {total_templates} templates from {self.templates_path}"
        )

    @memory_efficient_decorator
    def get_available_templates(
        self, document_type: Optional[str] = None
    ) -> Union[Dict[str, List[str]], List[str]]:
        """Get available templates"""
        return self.registry.get_available_templates(document_type)

    def validate_template(self, document_type: str, template_name: str) -> bool:
        """Validate that a template exists and is usable"""
        try:
            # Ensure document_type is a string (handle enum values)
            document_type = _ensure_string(document_type)
            available = self.get_available_templates(document_type)
            return template_name in available
        except Exception:
            return False

    @memory_efficient_decorator
    def create_template(
        self, document_type: str, template_name: str, data: Dict[str, Any]
    ) -> TemplateInterface:
        """
        Create a template instance with optimized data processing

        Args:
            document_type: Type of document (resume, cover_letter)
            template_name: Name of the template
            data: Document data

        Returns:
            Template instance
        """
        # Ensure document_type is a string (handle enum values)
        document_type = _ensure_string(document_type)

        if not self.validate_template(document_type, template_name):
            raise ValueError(
                f"Template '{template_name}' not found for document type '{document_type}'"
            )

        # Process data through variable system
        template_id = f"{document_type}/{template_name}"
        processed_data = self.variable_system.process_template_data(template_id, data)

        # Load template class (with caching)
        template_class = self.registry.load_template_class(document_type, template_name)

        # Get template-specific configuration
        template_config = self.config.get_template_config(document_type, template_name)

        # Create instance
        return template_class(processed_data, template_config)

    @memory_efficient_decorator
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
        # Ensure document_type is a string (handle enum values)
        document_type = _ensure_string(document_type)

        template = self.create_template(document_type, template_name, data)

        if output_format == OutputFormat.LATEX:
            content = template.render()
            # Add font configuration
            font_config = self.font_config_generator.generate_template_fonts(
                template.config, self.cross_platform_builder.preferred_engine
            )
            if font_config:
                # Insert font config after documentclass
                doc_class_pos = content.find("\\begin{document}")
                if doc_class_pos != -1:
                    content = (
                        content[:doc_class_pos]
                        + font_config
                        + "\n\n"
                        + content[doc_class_pos:]
                    )
            return content
        elif output_format == OutputFormat.PDF:
            # For PDF, we still return the LaTeX content
            # The actual PDF generation happens in export_to_pdf
            return template.render()
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    @memory_efficient_decorator
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
        # Ensure document_type is a string (handle enum values)
        document_type = _ensure_string(document_type)

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
        # Ensure document_type is a string (handle enum values)
        document_type = _ensure_string(document_type)

        if not self.validate_template(document_type, template_name):
            raise ValueError(
                f"Template '{template_name}' not found for document type '{document_type}'"
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

        # Get version info
        template_id = f"{document_type}/{template_name}"
        version_info = self.version_manager.get_latest_version(template_id)

        return {
            "name": template_name,
            "document_type": document_type,
            "required_fields": required_fields,
            "preview_path": preview_path,
            "template_dir": str(template_dir),
            "class_name": template_class.__name__,
            "description": f"{template_name.capitalize()} template for {document_type.replace('_', ' ')}",
            "version": version_info.version if version_info else "1.0.0",
            "inheritance_info": self.get_template_inheritance_info(
                document_type, template_name
            ),
        }

    def _load_macro_collections(self) -> None:
        """Load macro collections into the registry"""
        try:
            # Install resume and cover letter collections
            self.macro_library.install_collection("resume", self.macro_registry)
            self.macro_library.install_collection("cover_letter", self.macro_registry)
            logger.info("Loaded macro collections successfully")
        except Exception as e:
            logger.warning(f"Failed to load macro collections: {e}")

    def validate_data(self, data: Dict[str, Any], document_type: str) -> List[str]:
        """
        Validate data against document schema

        Args:
            data: Data to validate
            document_type: Type of document

        Returns:
            List of validation errors (empty if valid)
        """
        try:
            schema_type = DocumentSchema(document_type)
            schema_errors = self.schema_validator.validate_partial(data, schema_type)
            variable_errors = self.variable_system.validate_template_data(data)
            return schema_errors + variable_errors
        except ValueError:
            return [f"Unknown document type: {document_type}"]

    def validate_template_structure(
        self,
        document_type: str,
        template_name: str,
        sample_data: Optional[Dict[str, Any]] = None,
    ) -> List[ValidationIssue]:
        """
        Validate template structure and functionality

        Args:
            document_type: Type of document
            template_name: Name of template
            sample_data: Sample data for testing

        Returns:
            List of validation issues
        """
        document_type = _ensure_string(document_type)
        template_path = Path(self.templates_path) / document_type / template_name

        return self.template_validator.validate_template(
            str(template_path), sample_data
        )

    def get_template_inheritance_info(
        self, document_type: str, template_name: str
    ) -> Dict[str, Any]:
        """Get template inheritance information"""
        document_type = _ensure_string(document_type)
        template_id = f"{document_type}/{template_name}"

        inheritance_chain = []
        try:
            inheritance_chain = self.inheritance_manager.get_inheritance_chain(
                template_id
            )
        except Exception as e:
            logger.warning(f"Failed to get inheritance chain for {template_id}: {e}")

        return {
            "template_id": template_id,
            "inheritance_chain": inheritance_chain,
            "has_parent": len(inheritance_chain) > 1,
            "children": self.inheritance_manager.dependency_graph.get(
                template_id, {}
            ).get("children", []),
        }

    @memory_efficient_decorator
    def export_to_pdf_async(
        self,
        document_type: str,
        template_name: str,
        data: Dict[str, Any],
        output_path: str,
    ) -> str:
        """
        Export document to PDF asynchronously using parallel builder

        Args:
            document_type: Type of document
            template_name: Name of template
            data: Document data
            output_path: Output file path

        Returns:
            Build request ID for tracking
        """
        document_type = _ensure_string(document_type)

        # Optimize memory for this build
        self.memory_optimizer.optimize_for_build(1)

        # Validate data first
        validation_errors = self.validate_data(data, document_type)
        if validation_errors:
            raise ValidationError("Data validation failed", validation_errors)

        # Render LaTeX content
        latex_content = self.render_document(
            document_type, template_name, data, OutputFormat.LATEX
        )

        # Add macro definitions
        macro_preamble = self.macro_processor.generate_macro_preamble(latex_content)
        if macro_preamble:
            # Insert macro definitions after documentclass
            doc_class_match = latex_content.find("\\begin{document}")
            if doc_class_match != -1:
                latex_content = (
                    latex_content[:doc_class_match]
                    + macro_preamble
                    + "\n\n"
                    + latex_content[doc_class_match:]
                )

        # Optimize for platform
        latex_content = self.cross_platform_builder.optimize_for_platform(latex_content)

        # Create build request
        build_request = BuildRequest(
            id="",  # Will be auto-generated
            template_path=str(
                Path(self.templates_path) / document_type / template_name
            ),
            output_path=output_path,
            latex_content=latex_content,
            engine=self.cross_platform_builder.preferred_engine,
            metadata={"document_type": document_type, "template_name": template_name},
        )

        return self.parallel_builder.submit_build(build_request)

    def get_build_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get build status for async PDF generation"""
        result = self.parallel_builder.get_build_status(request_id)
        if result:
            return {
                "request_id": result.request_id,
                "status": result.status.value,
                "output_path": result.output_path,
                "error_message": result.error_message,
                "build_time": result.build_time,
                "logs": result.logs,
            }
        return None

    def wait_for_build(
        self, request_id: str, timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Wait for async build to complete"""
        result = self.parallel_builder.wait_for_build(request_id, timeout)
        return {
            "request_id": result.request_id,
            "status": result.status.value,
            "output_path": result.output_path,
            "error_message": result.error_message,
            "build_time": result.build_time,
            "logs": result.logs,
        }

    def get_macro_info(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get information about available macros"""
        if category:
            macros = self.macro_registry.get_macros_by_category(category)
            return {
                "category": category,
                "macros": [
                    {
                        "name": macro.name,
                        "type": macro.macro_type.value,
                        "parameters": macro.parameters,
                        "description": macro.description,
                    }
                    for macro in macros
                ],
            }
        else:
            return {
                "categories": list(self.macro_registry.categories.keys()),
                "total_macros": len(self.macro_registry.macros),
                "available_collections": self.macro_library.list_collections(),
            }

    def validate_latex_installation(self) -> List[ValidationIssue]:
        """Validate LaTeX installation and dependencies"""
        return self.template_validator.validate_latex_installation()

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for debugging"""
        memory_stats = self.memory_optimizer.get_optimization_stats()

        return {
            "platform": self.cross_platform_builder.platform,
            "latex_installations": self.cross_platform_builder.latex_installations,
            "preferred_engine": self.cross_platform_builder.preferred_engine.value,
            "template_path": self.templates_path,
            "cache_info": {
                "cache_dir": str(self.parallel_builder.cache.cache_dir),
                "cached_builds": len(self.parallel_builder.cache.cache_index),
            },
            "memory_stats": memory_stats,
            "available_fonts": len(self.font_manager.get_available_fonts()),
            "template_versions": len(self.version_manager.version_index),
        }

    def cleanup_cache(self, max_age_days: int = 30) -> None:
        """Clean up old build cache entries"""
        self.parallel_builder.cache.cleanup_old_entries(max_age_days)
        self.image_processor.cache_dir  # Image cache cleanup would go here

    def shutdown(self) -> None:
        """Shutdown the template engine and cleanup resources"""
        self.parallel_builder.shutdown()
        self.memory_optimizer.shutdown()
        logger.info("Template engine shutdown complete")

    # Additional convenience methods for DRY approach

    def process_image(self, image_path: str, latex_engine: str = None) -> str:
        """Process image for LaTeX inclusion"""
        engine = latex_engine or self.cross_platform_builder.preferred_engine.value
        return self.latex_image_handler.prepare_image_for_latex(image_path, engine)

    def create_version(
        self,
        document_type: str,
        template_name: str,
        version: str,
        author: str,
        description: str = "",
    ) -> None:
        """Create a new version of a template"""
        document_type = _ensure_string(document_type)
        template_id = f"{document_type}/{template_name}"
        self.version_manager.create_version(template_id, version, author, description)

    def get_font_recommendations(self, document_type: str = "resume") -> Dict[str, str]:
        """Get font recommendations for document type"""
        return self.font_manager.get_font_recommendations(
            self.cross_platform_builder.preferred_engine, document_type
        )
