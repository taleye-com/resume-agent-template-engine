"""Unit tests for the template engine core functionality."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from resume_agent_template_engine.core.template_engine import (
    TemplateEngine,
    TemplateRegistry,
    TemplateConfig,
    DocumentType,
    OutputFormat,
    TemplateInterface
)


class TestTemplateConfig:
    """Test TemplateConfig class"""

    def test_config_initialization_no_file(self):
        """Test config initialization without config file"""
        config = TemplateConfig()
        assert config.config is not None
        assert "templates" in config.config
        assert "rendering" in config.config
        assert "validation" in config.config

    def test_config_initialization_with_file(self, tmp_path):
        """Test config initialization with config file"""
        config_file = tmp_path / "config.yaml"
        config_content = """
templates:
  base_path: "custom_templates"
  auto_discover: true
rendering:
  latex_engine: "xelatex"
validation:
  strict_mode: true
"""
        config_file.write_text(config_content)
        
        config = TemplateConfig(str(config_file))
        assert config.config["templates"]["base_path"] == "custom_templates"
        assert config.config["rendering"]["latex_engine"] == "xelatex"
        assert config.config["validation"]["strict_mode"] is True

    def test_config_initialization_invalid_file(self, tmp_path):
        """Test config initialization with invalid YAML file"""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content:")
        
        with patch('resume_agent_template_engine.core.template_engine.logger.warning') as mock_warning:
            config = TemplateConfig(str(config_file))
            mock_warning.assert_called_once()
            # Should fall back to default config
            assert "templates" in config.config

    def test_get_template_config(self):
        """Test getting template-specific configuration"""
        config = TemplateConfig()
        template_config = config.get_template_config("resume", "classic")
        assert isinstance(template_config, dict)

    def test_get_rendering_config(self):
        """Test getting rendering configuration"""
        config = TemplateConfig()
        rendering_config = config.get_rendering_config()
        assert isinstance(rendering_config, dict)
        assert "latex_engine" in rendering_config


class TestTemplateRegistry:
    """Test TemplateRegistry class"""

    def test_registry_initialization(self, tmp_path):
        """Test template registry initialization with mock templates"""
        # Create mock template structure
        templates_dir = tmp_path / "templates"
        resume_dir = templates_dir / "resume" / "classic"
        resume_dir.mkdir(parents=True)
        (resume_dir / "helper.py").write_text("# Mock helper")
        (resume_dir / "template.tex").write_text("% Mock template")
        
        registry = TemplateRegistry(str(templates_dir))
        assert hasattr(registry, '_available_templates')
        assert "resume" in registry._available_templates
        assert "classic" in registry._available_templates["resume"]

    def test_registry_initialization_no_templates_dir(self, tmp_path):
        """Test registry initialization with non-existent templates directory"""
        nonexistent_dir = tmp_path / "nonexistent"
        
        with patch('resume_agent_template_engine.core.template_engine.logger.warning') as mock_warning:
            registry = TemplateRegistry(str(nonexistent_dir))
            mock_warning.assert_called_once()
            assert registry._available_templates == {}

    def test_get_available_templates_all(self, tmp_path):
        """Test getting all available templates"""
        # Create mock template structure
        templates_dir = tmp_path / "templates"
        resume_dir = templates_dir / "resume" / "classic"
        resume_dir.mkdir(parents=True)
        (resume_dir / "helper.py").write_text("# Mock helper")
        (resume_dir / "template.tex").write_text("% Mock template")
        
        registry = TemplateRegistry(str(templates_dir))
        templates = registry.get_available_templates()
        assert isinstance(templates, dict)
        assert "resume" in templates

    def test_get_available_templates_by_type(self, tmp_path):
        """Test getting available templates filtered by document type"""
        # Create mock template structure
        templates_dir = tmp_path / "templates"
        resume_dir = templates_dir / "resume" / "classic"
        resume_dir.mkdir(parents=True)
        (resume_dir / "helper.py").write_text("# Mock helper")
        (resume_dir / "template.tex").write_text("% Mock template")
        
        registry = TemplateRegistry(str(templates_dir))
        templates = registry.get_available_templates("resume")
        assert isinstance(templates, list)
        assert "classic" in templates

    def test_load_template_class_success(self, tmp_path):
        """Test loading template class successfully"""
        # Create mock template structure
        templates_dir = tmp_path / "templates"
        resume_dir = templates_dir / "resume" / "classic"
        resume_dir.mkdir(parents=True)
        
        # Create a mock helper.py with a template class
        helper_content = '''
class ClassicResumeTemplate:
    def __init__(self, data, config=None):
        self.data = data
        self.config = config or {}
'''
        (resume_dir / "helper.py").write_text(helper_content)
        (resume_dir / "template.tex").write_text("% Mock template")
        
        registry = TemplateRegistry(str(templates_dir))
        template_class = registry.load_template_class("resume", "classic")
        assert template_class.__name__ == "ClassicResumeTemplate"

    def test_load_template_class_not_found(self, tmp_path):
        """Test loading non-existent template class"""
        templates_dir = tmp_path / "templates"
        registry = TemplateRegistry(str(templates_dir))
        
        with pytest.raises(ValueError, match="Document type 'nonexistent' not found"):
            registry.load_template_class("nonexistent", "classic")

    def test_load_template_class_template_not_found(self, tmp_path):
        """Test loading template class for non-existent template"""
        # Create mock template structure
        templates_dir = tmp_path / "templates"
        resume_dir = templates_dir / "resume" / "classic"
        resume_dir.mkdir(parents=True)
        (resume_dir / "helper.py").write_text("# Mock helper")
        (resume_dir / "template.tex").write_text("% Mock template")
        
        registry = TemplateRegistry(str(templates_dir))
        
        with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
            registry.load_template_class("resume", "nonexistent")

    def test_load_template_class_caching(self, tmp_path):
        """Test that template classes are cached after first load"""
        # Create mock template structure
        templates_dir = tmp_path / "templates"
        resume_dir = templates_dir / "resume" / "classic"
        resume_dir.mkdir(parents=True)
        
        helper_content = '''
class ClassicResumeTemplate:
    def __init__(self, data, config=None):
        self.data = data
        self.config = config or {}
'''
        (resume_dir / "helper.py").write_text(helper_content)
        (resume_dir / "template.tex").write_text("% Mock template")
        
        registry = TemplateRegistry(str(templates_dir))
        
        # Load template class twice
        template_class1 = registry.load_template_class("resume", "classic")
        template_class2 = registry.load_template_class("resume", "classic")
        
        # Should be the same object (cached)
        assert template_class1 is template_class2

    def test_find_template_class_fallback(self, tmp_path):
        """Test finding template class with fallback naming"""
        # Create mock template structure
        templates_dir = tmp_path / "templates"
        resume_dir = templates_dir / "resume" / "classic"
        resume_dir.mkdir(parents=True)
        
        # Create helper with non-standard class name
        helper_content = '''
class SomeCustomTemplate:
    def __init__(self, data, config=None):
        self.data = data
        self.config = config or {}
'''
        (resume_dir / "helper.py").write_text(helper_content)
        (resume_dir / "template.tex").write_text("% Mock template")
        
        registry = TemplateRegistry(str(templates_dir))
        template_class = registry.load_template_class("resume", "classic")
        assert template_class.__name__ == "SomeCustomTemplate"


class TestTemplateEngine:
    """Test TemplateEngine class"""

    @pytest.fixture
    def template_engine(self, tmp_path):
        """Create a template engine with mock templates"""
        templates_dir = tmp_path / "templates"
        resume_dir = templates_dir / "resume" / "classic"
        resume_dir.mkdir(parents=True)
        
        # Create a mock helper.py with a template class
        helper_content = '''
from resume_agent_template_engine.core.template_engine import TemplateInterface, DocumentType

class ClassicResumeTemplate(TemplateInterface):
    def __init__(self, data, config=None):
        super().__init__(data, config)
    
    def validate_data(self):
        if "personalInfo" not in self.data:
            raise ValueError("Personal info required")
    
    def render(self):
        return "\\\\documentclass{article}\\\\begin{document}Test\\\\end{document}"
    
    def export_to_pdf(self, output_path):
        # Mock PDF export
        with open(output_path, 'wb') as f:
            f.write(b"Mock PDF content")
        return output_path
    
    @property
    def required_fields(self):
        return ["personalInfo"]
    
    @property
    def template_type(self):
        return DocumentType.RESUME
'''
        (resume_dir / "helper.py").write_text(helper_content)
        (resume_dir / "template.tex").write_text("% Mock template")
        
        return TemplateEngine(templates_path=str(templates_dir))

    def test_engine_initialization(self, template_engine):
        """Test template engine initialization"""
        assert template_engine.config is not None
        assert template_engine.registry is not None
        assert hasattr(template_engine, 'templates_path')

    def test_get_available_templates(self, template_engine):
        """Test getting available templates"""
        templates = template_engine.get_available_templates()
        assert isinstance(templates, dict)
        assert "resume" in templates

    def test_get_available_templates_by_type(self, template_engine):
        """Test getting available templates by type"""
        templates = template_engine.get_available_templates("resume")
        assert isinstance(templates, list)
        assert "classic" in templates

    def test_validate_template_exists(self, template_engine):
        """Test template validation for existing template"""
        is_valid = template_engine.validate_template("resume", "classic")
        assert is_valid is True

    def test_validate_template_not_exists(self, template_engine):
        """Test template validation for non-existing template"""
        is_valid = template_engine.validate_template("resume", "nonexistent")
        assert is_valid is False

    def test_create_template_success(self, template_engine):
        """Test successful template creation"""
        sample_data = {"personalInfo": {"name": "John Doe"}}
        template = template_engine.create_template("resume", "classic", sample_data)
        assert template is not None
        assert hasattr(template, 'data')
        assert template.data == sample_data

    def test_create_template_invalid_template(self, template_engine):
        """Test template creation with invalid template"""
        sample_data = {"personalInfo": {"name": "John Doe"}}
        
        with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
            template_engine.create_template("resume", "nonexistent", sample_data)

    def test_create_template_validation_error(self, template_engine):
        """Test template creation with validation error"""
        invalid_data = {"invalid": "data"}  # Missing personalInfo
        
        with pytest.raises(ValueError, match="Personal info required"):
            template_engine.create_template("resume", "classic", invalid_data)

    def test_render_document_latex(self, template_engine):
        """Test document rendering to LaTeX"""
        sample_data = {"personalInfo": {"name": "John Doe"}}
        content = template_engine.render_document("resume", "classic", sample_data, OutputFormat.LATEX)
        assert isinstance(content, str)
        assert "documentclass" in content

    def test_render_document_pdf_format(self, template_engine):
        """Test document rendering with PDF format (returns LaTeX)"""
        sample_data = {"personalInfo": {"name": "John Doe"}}
        content = template_engine.render_document("resume", "classic", sample_data, OutputFormat.PDF)
        assert isinstance(content, str)
        assert "documentclass" in content

    def test_render_document_unsupported_format(self, template_engine):
        """Test document rendering with unsupported format"""
        sample_data = {"personalInfo": {"name": "John Doe"}}
        
        with pytest.raises(ValueError, match="Unsupported output format"):
            template_engine.render_document("resume", "classic", sample_data, OutputFormat.HTML)

    def test_export_to_pdf_success(self, template_engine, tmp_path):
        """Test successful PDF export"""
        sample_data = {"personalInfo": {"name": "John Doe"}}
        output_path = str(tmp_path / "test.pdf")
        
        result_path = template_engine.export_to_pdf("resume", "classic", sample_data, output_path)
        assert result_path == output_path
        assert os.path.exists(output_path)

    def test_get_template_info(self, template_engine):
        """Test getting template information"""
        info = template_engine.get_template_info("resume", "classic")
        assert isinstance(info, dict)
        assert info["name"] == "classic"
        assert info["document_type"] == "resume"
        assert "required_fields" in info
        assert "description" in info

    def test_get_template_info_invalid_template(self, template_engine):
        """Test getting template info for invalid template"""
        with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
            template_engine.get_template_info("resume", "nonexistent")


class TestDocumentTypeEnum:
    """Test DocumentType enum"""

    def test_document_type_values(self):
        """Test DocumentType enum values"""
        assert DocumentType.RESUME == "resume"
        assert DocumentType.COVER_LETTER == "cover_letter"

    def test_document_type_membership(self):
        """Test DocumentType membership"""
        assert DocumentType.RESUME.value == "resume"
        assert DocumentType.COVER_LETTER.value == "cover_letter"
        
        # Test that we can create enum from string values
        assert DocumentType("resume") == DocumentType.RESUME
        assert DocumentType("cover_letter") == DocumentType.COVER_LETTER
        
        # Test invalid values raise ValueError
        with pytest.raises(ValueError):
            DocumentType("invalid")


class TestOutputFormatEnum:
    """Test OutputFormat enum"""

    def test_output_format_values(self):
        """Test OutputFormat enum values"""
        assert OutputFormat.PDF == "pdf"
        assert OutputFormat.LATEX == "latex"
        assert OutputFormat.HTML == "html"

    def test_output_format_membership(self):
        """Test OutputFormat membership"""
        assert OutputFormat.PDF.value == "pdf"
        assert OutputFormat.LATEX.value == "latex"
        assert OutputFormat.HTML.value == "html"
        
        # Test that we can create enum from string values
        assert OutputFormat("pdf") == OutputFormat.PDF
        assert OutputFormat("latex") == OutputFormat.LATEX
        assert OutputFormat("html") == OutputFormat.HTML
        
        # Test invalid values raise ValueError
        with pytest.raises(ValueError):
            OutputFormat("invalid")


class TestTemplateInterface:
    """Test TemplateInterface abstract base class"""

    def test_template_interface_is_abstract(self):
        """Test that TemplateInterface cannot be instantiated directly"""
        with pytest.raises(TypeError):
            TemplateInterface({"test": "data"})

    def test_template_interface_subclass_requirements(self):
        """Test that TemplateInterface subclasses must implement required methods"""
        class IncompleteTemplate(TemplateInterface):
            pass
        
        with pytest.raises(TypeError):
            IncompleteTemplate({"test": "data"})

    def test_template_interface_complete_subclass(self):
        """Test a complete TemplateInterface subclass"""
        class CompleteTemplate(TemplateInterface):
            def validate_data(self):
                pass
            
            def render(self):
                return "rendered content"
            
            def export_to_pdf(self, output_path):
                return output_path
            
            @property
            def required_fields(self):
                return ["field1"]
            
            @property
            def template_type(self):
                return DocumentType.RESUME
        
        template = CompleteTemplate({"test": "data"})
        assert template.data == {"test": "data"}
        assert template.config == {}
        assert template.render() == "rendered content"
        assert template.required_fields == ["field1"]
        assert template.template_type == DocumentType.RESUME 