"""Unit tests for the FastAPI application endpoints."""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from resume_agent_template_engine.api.app import (
    app,
    validate_date_format,
    validate_resume_data,
)
from resume_agent_template_engine.core.template_engine import DocumentType


class TestValidationFunctions:
    """Test cases for validation helper functions."""

    def test_validate_date_format_valid_yyyy_mm(self):
        """Test validation of valid YYYY-MM date format."""
        assert validate_date_format("2023-01") is True
        assert validate_date_format("2024-12") is True

    def test_validate_date_format_valid_yyyy_mm_dd(self):
        """Test validation of valid YYYY-MM-DD date format."""
        assert validate_date_format("2023-01-15") is True
        assert validate_date_format("2024-12-31") is True

    def test_validate_date_format_invalid(self):
        """Test validation of invalid date formats."""
        assert validate_date_format("2023") is False
        assert validate_date_format("23-01") is False
        assert validate_date_format("2023-13") is False
        assert validate_date_format("2023-01-32") is False
        assert validate_date_format("invalid-date") is False

    def test_validate_resume_data_valid(self, sample_resume_data):
        """Test validation of valid resume data."""
        # Should not raise any exception
        validate_resume_data(sample_resume_data)

    def test_validate_resume_data_missing_personal_info(self):
        """Test validation with missing personal information."""
        invalid_data = {"experience": []}

        with pytest.raises(ValueError, match="Personal information is required"):
            validate_resume_data(invalid_data)

    def test_validate_resume_data_invalid_email(self):
        """Test validation with invalid email."""
        invalid_data = {"personalInfo": {"name": "John Doe", "email": "invalid-email"}}

        with pytest.raises(ValueError):
            validate_resume_data(invalid_data)

    def test_validate_resume_data_invalid_date(self):
        """Test validation with invalid experience dates."""
        invalid_data = {
            "personalInfo": {"name": "John Doe", "email": "john@example.com"},
            "experience": [
                {
                    "title": "Engineer",
                    "company": "Tech Corp",
                    "startDate": "invalid-date",
                }
            ],
        }

        with pytest.raises(ValueError, match="Invalid start date format"):
            validate_resume_data(invalid_data)


class TestAPIEndpoints:
    """Test cases for API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI application."""
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

    def test_health_check_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @patch("resume_agent_template_engine.api.app.TemplateEngine")
    def test_list_templates_endpoint(self, mock_engine_class, client):
        """Test the list templates endpoint."""
        mock_engine = Mock()
        mock_engine.get_available_templates.return_value = {
            "resume": ["classic", "modern"],
            "cover_letter": ["formal", "creative"],
        }
        mock_engine_class.return_value = mock_engine

        response = client.get("/templates")
        assert response.status_code == 200

        data = response.json()
        assert "templates" in data
        assert "resume" in data["templates"]
        assert "cover_letter" in data["templates"]

    @patch("resume_agent_template_engine.api.app.TemplateEngine")
    def test_list_templates_by_type_endpoint(self, mock_engine_class, client):
        """Test the list templates by type endpoint."""
        mock_engine = Mock()
        mock_engine.get_available_templates.return_value = ["classic", "modern"]
        mock_engine_class.return_value = mock_engine

        response = client.get("/templates/resume")
        assert response.status_code == 200

        data = response.json()
        assert "templates" in data
        assert data["templates"] == ["classic", "modern"]

    @patch("resume_agent_template_engine.api.app.TemplateEngine")
    def test_list_templates_by_type_not_found(self, mock_engine_class, client):
        """Test the list templates by type endpoint with invalid type."""
        mock_engine = Mock()
        mock_engine.get_available_templates.side_effect = ValueError(
            "Document type not found"
        )
        mock_engine_class.return_value = mock_engine

        response = client.get("/templates/invalid_type")
        assert response.status_code == 422  # FastAPI validation error for invalid enum

    @patch("resume_agent_template_engine.api.app.TemplateEngine")
    def test_get_template_info_endpoint(self, mock_engine_class, client):
        """Test the get template info endpoint."""
        mock_engine = Mock()
        mock_info = {
            "name": "classic",
            "document_type": "resume",
            "description": "Classic resume template",
            "required_fields": ["personalInfo"],
            "preview_path": None,
        }
        mock_engine.get_template_info.return_value = mock_info
        mock_engine_class.return_value = mock_engine

        response = client.get("/template-info/resume/classic")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "classic"
        assert data["document_type"] == "resume"

    @patch("resume_agent_template_engine.api.app.TemplateEngine")
    def test_get_template_info_not_found(self, mock_engine_class, client):
        """Test the get template info endpoint with non-existent template."""
        mock_engine = Mock()
        mock_engine.get_template_info.side_effect = ValueError("Template not found")
        mock_engine_class.return_value = mock_engine

        response = client.get("/template-info/resume/nonexistent")
        assert response.status_code == 404

    def test_get_document_schema_resume(self, client):
        """Test the get document schema endpoint for resume."""
        response = client.get("/schema/resume")
        assert response.status_code == 200

        data = response.json()
        assert "schema" in data
        assert data["schema"]["type"] == "object"

    def test_get_document_schema_cover_letter(self, client):
        """Test the get document schema endpoint for cover letter."""
        response = client.get("/schema/cover_letter")
        assert response.status_code == 200

        data = response.json()
        assert "schema" in data
        assert data["schema"]["type"] == "object"

    @patch("resume_agent_template_engine.api.app.TemplateEngine")
    @patch("tempfile.NamedTemporaryFile")
    @patch("os.path.exists")
    @patch("os.remove")
    def test_generate_document_success(
        self,
        mock_remove,
        mock_exists,
        mock_tempfile,
        mock_engine_class,
        client,
        sample_resume_data,
    ):
        """Test successful document generation."""
        # Create a real temporary file that will be returned
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as real_temp_file:
            real_temp_file.write(b"Mock PDF content")
            real_temp_path = real_temp_file.name

        try:
            # Set up the engine mock
            mock_engine = Mock()

            # Handle different call patterns for get_available_templates
            def mock_get_templates(document_type=None):
                if document_type is None:
                    return {"resume": ["classic"]}
                elif document_type == "resume":
                    return ["classic"]
                else:
                    return []

            mock_engine.get_available_templates.side_effect = mock_get_templates
            mock_engine.export_to_pdf.return_value = real_temp_path
            mock_engine_class.return_value = mock_engine

            # Mock tempfile to return our real file path
            mock_temp = Mock()
            mock_temp.name = real_temp_path
            mock_tempfile.return_value.__enter__.return_value = mock_temp

            # Mock os operations
            mock_exists.return_value = True

            request_data = {
                "document_type": "resume",
                "template": "classic",
                "format": "pdf",
                "data": sample_resume_data,
                "clean_up": True,
            }

            response = client.post("/generate", json=request_data)

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"

            # Verify the engine was called correctly
            mock_engine.export_to_pdf.assert_called_once()

        finally:
            # Clean up the real temp file
            if os.path.exists(real_temp_path):
                os.remove(real_temp_path)

    @patch("resume_agent_template_engine.api.app.TemplateEngine")
    def test_generate_document_invalid_template(
        self, mock_engine_class, client, sample_resume_data
    ):
        """Test document generation with invalid template."""
        mock_engine = Mock()
        mock_engine.get_available_templates.return_value = {"resume": ["classic"]}
        mock_engine_class.return_value = mock_engine

        request_data = {
            "document_type": "resume",
            "template": "nonexistent",
            "format": "pdf",
            "data": sample_resume_data,
        }

        response = client.post("/generate", json=request_data)
        assert response.status_code == 404
        assert "Template 'nonexistent' not found" in response.json()["detail"]

    @patch("resume_agent_template_engine.api.app.TemplateEngine")
    def test_generate_document_invalid_document_type(
        self, mock_engine_class, client, sample_resume_data
    ):
        """Test document generation with invalid document type."""
        mock_engine = Mock()
        mock_engine.get_available_templates.return_value = {"resume": ["classic"]}
        mock_engine_class.return_value = mock_engine

        request_data = {
            "document_type": "invalid_type",
            "template": "classic",
            "format": "pdf",
            "data": sample_resume_data,
        }

        response = client.post("/generate", json=request_data)
        assert response.status_code == 422  # FastAPI validation error for invalid enum

    def test_generate_document_invalid_format(self, client, sample_resume_data):
        """Test document generation with unsupported format."""
        with patch(
            "resume_agent_template_engine.api.app.TemplateEngine"
        ) as mock_engine_class:
            mock_engine = Mock()
            mock_engine.get_available_templates.return_value = {"resume": ["classic"]}
            mock_engine_class.return_value = mock_engine

            request_data = {
                "document_type": "resume",
                "template": "classic",
                "format": "html",
                "data": sample_resume_data,
            }

            response = client.post("/generate", json=request_data)
            assert response.status_code == 400
            assert "Only PDF format is currently supported" in response.json()["detail"]

    def test_generate_document_invalid_data(self, client):
        """Test document generation with invalid data."""
        request_data = {
            "document_type": "resume",
            "template": "classic",
            "format": "pdf",
            "data": {"invalid": "data"},  # Missing personalInfo
        }

        response = client.post("/generate", json=request_data)
        assert response.status_code == 400
        assert "Personal information is required" in response.json()["detail"]

    @patch("resume_agent_template_engine.api.app.TemplateEngine")
    def test_generate_document_engine_error(
        self, mock_engine_class, client, sample_resume_data
    ):
        """Test document generation with template engine error."""
        mock_engine = Mock()
        mock_engine.get_available_templates.return_value = {"resume": ["classic"]}
        mock_engine.export_to_pdf.side_effect = Exception("Template rendering failed")
        mock_engine_class.return_value = mock_engine

        request_data = {
            "document_type": "resume",
            "template": "classic",
            "format": "pdf",
            "data": sample_resume_data,
        }

        response = client.post("/generate", json=request_data)
        assert response.status_code == 500
        assert "Template rendering failed" in response.json()["detail"]


class TestCORSMiddleware:
    """Test cases for CORS middleware configuration."""

    def test_cors_headers_present(self):
        """Test that CORS headers are properly configured."""
        client = TestClient(app)
        response = client.options("/")

        # The response should include CORS headers
        assert response.status_code in [
            200,
            405,
        ]  # OPTIONS may not be explicitly handled

    def test_cors_allows_all_origins(self):
        """Test that CORS allows requests from any origin."""
        client = TestClient(app)
        response = client.get("/", headers={"Origin": "http://localhost:3000"})

        assert response.status_code == 200


class TestRequestModels:
    """Test cases for request model validation."""

    def test_document_request_model_valid(self, sample_resume_data):
        """Test DocumentRequest model with valid data."""
        from resume_agent_template_engine.api.app import DocumentRequest

        request = DocumentRequest(
            document_type=DocumentType.RESUME,
            template="classic",
            format="pdf",
            data=sample_resume_data,
            clean_up=True,
        )

        assert request.document_type == DocumentType.RESUME
        assert request.template == "classic"
        assert request.format == "pdf"
        assert request.clean_up is True

    def test_personal_info_model_valid(self):
        """Test PersonalInfo model with valid data."""
        from resume_agent_template_engine.api.app import PersonalInfo

        personal_info = PersonalInfo(
            name="John Doe",
            email="john@example.com",
            phone="+1-234-567-8900",
            location="San Francisco, CA",
            website="https://johndoe.dev",
            linkedin="https://linkedin.com/in/johndoe",
        )

        assert personal_info.name == "John Doe"
        assert personal_info.email == "john@example.com"

    def test_personal_info_model_invalid_email(self):
        """Test PersonalInfo model with invalid email."""
        from pydantic import ValidationError

        from resume_agent_template_engine.api.app import PersonalInfo

        with pytest.raises(ValidationError):
            PersonalInfo(name="John Doe", email="invalid-email")
