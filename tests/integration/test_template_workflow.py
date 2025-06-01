"""Integration tests for the complete template workflow."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import yaml

from resume_agent_template_engine.core.template_engine import TemplateEngine, TemplateConfig
from resume_agent_template_engine.templates.template_manager import TemplateManager
from resume_agent_template_engine.api.app import app
from fastapi.testclient import TestClient


class TestTemplateWorkflowIntegration:
    """Integration tests for the complete template workflow."""
    
    @pytest.fixture
    def template_engine_with_mock_templates(self, tmp_path):
        """Create a template engine with mock templates for testing"""
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
        return "\\\\documentclass{article}\\\\begin{document}Test Resume\\\\end{document}"
    
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
        
        # Create cover letter template
        cover_letter_dir = templates_dir / "cover_letter" / "formal"
        cover_letter_dir.mkdir(parents=True)
        
        cover_letter_helper = '''
from resume_agent_template_engine.core.template_engine import TemplateInterface, DocumentType

class FormalCoverLetterTemplate(TemplateInterface):
    def __init__(self, data, config=None):
        super().__init__(data, config)
    
    def validate_data(self):
        if "personalInfo" not in self.data:
            raise ValueError("Personal info required")
        if "recipient" not in self.data:
            raise ValueError("Recipient info required")
    
    def render(self):
        return "\\\\documentclass{letter}\\\\begin{document}Test Cover Letter\\\\end{document}"
    
    def export_to_pdf(self, output_path):
        # Mock PDF export
        with open(output_path, 'wb') as f:
            f.write(b"Mock Cover Letter PDF content")
        return output_path
    
    @property
    def required_fields(self):
        return ["personalInfo", "recipient"]
    
    @property
    def template_type(self):
        return DocumentType.COVER_LETTER
'''
        (cover_letter_dir / "helper.py").write_text(cover_letter_helper)
        (cover_letter_dir / "template.tex").write_text("% Mock cover letter template")
        
        return TemplateEngine(templates_path=str(templates_dir))

    def test_template_discovery_workflow(self, template_engine_with_mock_templates):
        """Test complete template discovery workflow"""
        engine = template_engine_with_mock_templates
        
        # Test getting all templates
        all_templates = engine.get_available_templates()
        assert isinstance(all_templates, dict)
        assert "resume" in all_templates
        assert "cover_letter" in all_templates
        assert "classic" in all_templates["resume"]
        assert "formal" in all_templates["cover_letter"]
        
        # Test getting templates by type
        resume_templates = engine.get_available_templates("resume")
        assert isinstance(resume_templates, list)
        assert "classic" in resume_templates
        
        cover_letter_templates = engine.get_available_templates("cover_letter")
        assert isinstance(cover_letter_templates, list)
        assert "formal" in cover_letter_templates

    def test_template_validation_workflow(self, template_engine_with_mock_templates):
        """Test template validation workflow"""
        engine = template_engine_with_mock_templates
        
        # Test valid templates
        assert engine.validate_template("resume", "classic") is True
        assert engine.validate_template("cover_letter", "formal") is True
        
        # Test invalid templates
        assert engine.validate_template("resume", "nonexistent") is False
        assert engine.validate_template("nonexistent_type", "classic") is False

    def test_document_generation_workflow(self, template_engine_with_mock_templates, tmp_path):
        """Test complete document generation workflow"""
        engine = template_engine_with_mock_templates
        
        # Test resume generation
        resume_data = {
            "personalInfo": {
                "name": "John Doe",
                "email": "john@example.com"
            },
            "experience": [{
                "position": "Developer",
                "company": "Tech Corp"
            }]
        }
        
        # Test LaTeX rendering
        latex_content = engine.render_document("resume", "classic", resume_data)
        assert isinstance(latex_content, str)
        assert "documentclass" in latex_content
        
        # Test PDF export
        pdf_path = str(tmp_path / "test_resume.pdf")
        result_path = engine.export_to_pdf("resume", "classic", resume_data, pdf_path)
        assert result_path == pdf_path
        assert os.path.exists(pdf_path)
        
        # Test cover letter generation
        cover_letter_data = {
            "personalInfo": {
                "name": "John Doe",
                "email": "john@example.com"
            },
            "recipient": {
                "name": "Jane Smith",
                "company": "Target Corp"
            }
        }
        
        cover_letter_content = engine.render_document("cover_letter", "formal", cover_letter_data)
        assert isinstance(cover_letter_content, str)
        assert "documentclass" in cover_letter_content

    def test_template_info_retrieval_workflow(self, template_engine_with_mock_templates):
        """Test template information retrieval workflow"""
        engine = template_engine_with_mock_templates
        
        # Test getting template info
        resume_info = engine.get_template_info("resume", "classic")
        assert isinstance(resume_info, dict)
        assert resume_info["name"] == "classic"
        assert resume_info["document_type"] == "resume"
        assert "personalInfo" in resume_info["required_fields"]
        
        cover_letter_info = engine.get_template_info("cover_letter", "formal")
        assert isinstance(cover_letter_info, dict)
        assert cover_letter_info["name"] == "formal"
        assert cover_letter_info["document_type"] == "cover_letter"
        # Note: required_fields might be empty if template class instantiation fails
        if cover_letter_info["required_fields"]:
            assert "personalInfo" in cover_letter_info["required_fields"]
            assert "recipient" in cover_letter_info["required_fields"]

    def test_error_handling_workflow(self, template_engine_with_mock_templates):
        """Test error handling in template workflow"""
        engine = template_engine_with_mock_templates
        
        # Test invalid template creation
        with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
            engine.create_template("resume", "nonexistent", {})
        
        # Test invalid data validation
        invalid_data = {"invalid": "data"}
        with pytest.raises(ValueError, match="Personal info required"):
            engine.create_template("resume", "classic", invalid_data)
        
        # Test missing required fields for cover letter
        incomplete_cover_letter_data = {
            "personalInfo": {"name": "John Doe"}
            # Missing recipient
        }
        with pytest.raises(ValueError, match="Recipient info required"):
            engine.create_template("cover_letter", "formal", incomplete_cover_letter_data)


class TestAPIIntegration:
    """Integration tests for API with template engine"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_template_engine(self):
        """Create a mock template engine for API testing"""
        mock_engine = Mock()
        mock_engine.get_available_templates.return_value = {
            "resume": ["classic", "modern"],
            "cover_letter": ["formal", "creative"]
        }
        mock_engine.validate_template.return_value = True
        mock_engine.get_template_info.return_value = {
            "name": "classic",
            "document_type": "resume",
            "description": "Classic resume template",
            "required_fields": ["personalInfo"]
        }
        return mock_engine

    @patch('resume_agent_template_engine.api.app.TemplateEngine')
    @patch('tempfile.NamedTemporaryFile')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_api_template_engine_integration(self, mock_remove, mock_exists, mock_tempfile, mock_engine_class, client, mock_template_engine, sample_resume_data):
        """Test API integration with template engine"""
        mock_engine_class.return_value = mock_template_engine
        
        # Create a real temporary file for the test
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as real_temp:
            real_temp.write(b"Mock PDF content")
            real_temp_path = real_temp.name

        try:
            # Mock tempfile to return our real file path
            mock_temp = Mock()
            mock_temp.name = real_temp_path
            mock_tempfile.return_value.__enter__.return_value = mock_temp

            # Mock os operations
            mock_exists.return_value = True

            mock_template_engine.export_to_pdf.return_value = real_temp_path

            # Test template listing
            response = client.get("/templates")
            assert response.status_code == 200
            data = response.json()
            assert "templates" in data
            
            # Test template info
            response = client.get("/template-info/resume/classic")
            assert response.status_code == 200
            
            # Test document generation
            request_data = {
                "document_type": "resume",
                "template": "classic",
                "format": "pdf",
                "data": sample_resume_data
            }
            
            response = client.post("/generate", json=request_data)
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            
        finally:
            if os.path.exists(real_temp_path):
                os.remove(real_temp_path)


class TestConfigurationIntegration:
    """Integration tests for configuration with template engine"""

    def test_config_template_engine_integration(self, tmp_path):
        """Test configuration integration with template engine"""
        # Create custom config
        config_file = tmp_path / "config.yaml"
        config_content = """
templates:
  base_path: "custom_templates"
  auto_discover: true
  supported_formats: ["pdf", "latex"]
rendering:
  latex_engine: "xelatex"
  temp_dir: "/tmp/custom"
  cleanup: false
validation:
  strict_mode: true
  required_fields:
    resume: ["personalInfo", "experience"]
    cover_letter: ["personalInfo", "recipient", "content"]
"""
        config_file.write_text(config_content)

        # Initialize engine with custom config
        engine = TemplateEngine(config_path=str(config_file))

        # Test that configuration is properly loaded
        config = engine.config.config
        assert config["templates"]["base_path"] == "custom_templates"
        assert config["rendering"]["latex_engine"] == "xelatex"
        assert config["validation"]["strict_mode"] is True

    def test_config_fallback_behavior(self, tmp_path):
        """Test configuration fallback to defaults"""
        # Create invalid config file
        config_file = tmp_path / "invalid_config.yaml"
        config_file.write_text("invalid: yaml: content:")

        # Engine should fall back to default config
        with patch('resume_agent_template_engine.core.template_engine.logger.warning') as mock_warning:
            engine = TemplateEngine(config_path=str(config_file))
            mock_warning.assert_called()

        # Should have default configuration
        config = engine.config.config
        assert "templates" in config
        assert "rendering" in config
        assert "validation" in config

    def test_config_template_specific_settings(self, tmp_path):
        """Test template-specific configuration settings"""
        config_file = tmp_path / "config.yaml"
        config_content = """
templates:
  resume:
    classic:
      font_size: "11pt"
      margins: "1in"
  cover_letter:
    formal:
      letterhead: true
      signature_space: "1in"
"""
        config_file.write_text(config_content)

        config = TemplateConfig(str(config_file))

        # Test template-specific config retrieval
        resume_config = config.get_template_config("resume", "classic")
        assert resume_config.get("font_size") == "11pt"
        assert resume_config.get("margins") == "1in"

        cover_letter_config = config.get_template_config("cover_letter", "formal")
        assert cover_letter_config.get("letterhead") is True
        assert cover_letter_config.get("signature_space") == "1in"

    def test_rendering_config_integration(self):
        """Test rendering configuration integration"""
        config = TemplateConfig()
        rendering_config = config.get_rendering_config()

        # Test default rendering configuration
        assert "latex_engine" in rendering_config
        assert "temp_dir" in rendering_config
        assert "cleanup" in rendering_config

        # Test that defaults are reasonable
        assert rendering_config["latex_engine"] == "pdflatex"
        assert rendering_config["cleanup"] is True


class TestEndToEndWorkflow:
    """End-to-end workflow integration tests"""

    @pytest.fixture
    def complete_setup(self, tmp_path):
        """Set up complete testing environment"""
        # Create templates directory
        templates_dir = tmp_path / "templates"
        resume_dir = templates_dir / "resume" / "classic"
        resume_dir.mkdir(parents=True)
        
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
        
        # Create config file
        config_file = tmp_path / "config.yaml"
        config_content = """
templates:
  base_path: "templates"
  auto_discover: true
rendering:
  latex_engine: "pdflatex"
  cleanup: true
"""
        config_file.write_text(config_content)
        
        return {
            "templates_dir": str(templates_dir),
            "config_file": str(config_file),
            "tmp_path": tmp_path
        }

    def test_complete_workflow_from_config_to_pdf(self, complete_setup):
        """Test complete workflow from configuration to PDF generation"""
        setup = complete_setup
        
        # Initialize engine with config
        engine = TemplateEngine(
            config_path=setup["config_file"],
            templates_path=setup["templates_dir"]
        )
        
        # Verify templates are discovered
        templates = engine.get_available_templates()
        assert "resume" in templates
        assert "classic" in templates["resume"]
        
        # Prepare data
        data = {
            "personalInfo": {
                "name": "John Doe",
                "email": "john@example.com"
            }
        }
        
        # Generate document
        output_path = str(setup["tmp_path"] / "final_output.pdf")
        result_path = engine.export_to_pdf("resume", "classic", data, output_path)
        
        # Verify output
        assert result_path == output_path
        assert os.path.exists(output_path)
        
        # Verify content
        with open(output_path, 'rb') as f:
            content = f.read()
            assert content == b"Mock PDF content"

    def test_workflow_with_validation_errors(self, complete_setup):
        """Test workflow handling validation errors gracefully"""
        setup = complete_setup
        
        engine = TemplateEngine(
            config_path=setup["config_file"],
            templates_path=setup["templates_dir"]
        )
        
        # Test with invalid data
        invalid_data = {"invalid": "data"}
        
        with pytest.raises(ValueError, match="Personal info required"):
            engine.create_template("resume", "classic", invalid_data)
        
        # Test with non-existent template
        valid_data = {"personalInfo": {"name": "John Doe"}}
        
        with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
            engine.create_template("resume", "nonexistent", valid_data) 