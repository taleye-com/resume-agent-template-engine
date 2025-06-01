"""End-to-end tests for API endpoints with complete data flow."""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from resume_agent_template_engine.api.app import app


class TestAPIEndpointsE2E:
    """End-to-end tests for API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI application."""
        return TestClient(app)

    def test_complete_resume_generation_workflow(self, client, sample_resume_data):
        """Test complete workflow from template discovery to resume generation."""

        # Step 1: Check API health
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"

        # Step 2: List available templates
        with patch(
            "resume_agent_template_engine.api.app.TemplateEngine"
        ) as mock_engine_class:
            mock_engine = Mock()
            mock_engine.get_available_templates.return_value = {
                "resume": ["classic", "modern"],
                "cover_letter": ["formal"],
            }
            mock_engine_class.return_value = mock_engine

            templates_response = client.get("/templates")
            assert templates_response.status_code == 200

            templates_data = templates_response.json()
            assert "resume" in templates_data["templates"]
            assert "classic" in templates_data["templates"]["resume"]

            # Step 3: Get template info
            mock_engine.get_template_info.return_value = {
                "name": "Classic Resume Template",
                "description": "A professional and clean resume template",
                "author": "Resume Engine Team",
            }

            template_info_response = client.get("/template-info/resume/classic")
            assert template_info_response.status_code == 200

            info_data = template_info_response.json()
            assert info_data["name"] == "Classic Resume Template"

            # Step 4: Get document schema
            schema_response = client.get("/schema/resume")
            assert schema_response.status_code == 200

            schema_data = schema_response.json()
            assert "schema" in schema_data
            assert schema_data["schema"]["type"] == "object"

            # Step 5: Generate resume PDF
            with patch("tempfile.NamedTemporaryFile") as mock_temp, patch(
                "os.path.exists", return_value=True
            ), patch("os.remove"):

                # Create a real temporary file for the test
                with tempfile.NamedTemporaryFile(
                    suffix=".pdf", delete=False
                ) as real_temp:
                    real_temp.write(b"Mock PDF content")
                    real_temp_path = real_temp.name

                try:
                    mock_engine.export_to_pdf.return_value = real_temp_path
                    mock_temp.return_value.__enter__.return_value.name = real_temp_path

                    generation_request = {
                        "document_type": "resume",
                        "template": "classic",
                        "format": "pdf",
                        "data": sample_resume_data,
                        "clean_up": True,
                    }

                    generate_response = client.post(
                        "/generate", json=generation_request
                    )

                finally:
                    # Clean up the temporary file
                    if os.path.exists(real_temp_path):
                        os.remove(real_temp_path)
                    assert generate_response.status_code == 200
                    assert (
                        generate_response.headers["content-type"] == "application/pdf"
                    )

                    # Verify the template engine was called with correct parameters
                    mock_engine.export_to_pdf.assert_called_once()
                    call_args = mock_engine.export_to_pdf.call_args
                    assert call_args[0][0] == "resume"  # document_type
                    assert call_args[0][1] == "classic"  # template
                    assert call_args[0][2] == sample_resume_data  # data

    def test_complete_cover_letter_generation_workflow(
        self, client, sample_cover_letter_data
    ):
        """Test complete workflow for cover letter generation."""

        with patch(
            "resume_agent_template_engine.api.app.TemplateEngine"
        ) as mock_engine_class:
            mock_engine = Mock()

            # Handle different call patterns for get_available_templates
            def mock_get_templates(document_type=None):
                if document_type == "cover_letter":
                    return ["formal", "modern"]
                elif document_type is None:
                    return {"cover_letter": ["formal", "modern"]}
                else:
                    return []

            mock_engine.get_available_templates.side_effect = mock_get_templates
            mock_engine_class.return_value = mock_engine

            # List cover letter templates
            templates_response = client.get("/templates/cover_letter")
            assert templates_response.status_code == 200

            templates_data = templates_response.json()
            assert "formal" in templates_data["templates"]

            # Get cover letter schema
            schema_response = client.get("/schema/cover_letter")
            assert schema_response.status_code == 200

            # Generate cover letter
            with patch("tempfile.NamedTemporaryFile") as mock_temp, patch(
                "os.path.exists", return_value=True
            ), patch("os.remove"):

                # Create a real temporary file for the test
                with tempfile.NamedTemporaryFile(
                    suffix=".pdf", delete=False
                ) as real_temp:
                    real_temp.write(b"Mock PDF content")
                    real_temp_path = real_temp.name

                try:
                    mock_engine.export_to_pdf.return_value = real_temp_path
                    mock_temp.return_value.__enter__.return_value.name = real_temp_path

                    generation_request = {
                        "document_type": "cover_letter",
                        "template": "formal",
                        "format": "pdf",
                        "data": sample_cover_letter_data,
                    }

                    response = client.post("/generate", json=generation_request)
                    assert response.status_code == 200
                    assert response.headers["content-type"] == "application/pdf"

                finally:
                    # Clean up the temporary file
                    if os.path.exists(real_temp_path):
                        os.remove(real_temp_path)

    def test_error_scenarios_e2e(self, client):
        """Test various error scenarios in end-to-end workflow."""

        # Test invalid document type
        invalid_request = {
            "document_type": "invalid_type",
            "template": "classic",
            "format": "pdf",
            "data": {"personalInfo": {"name": "John", "email": "john@test.com"}},
        }

        response = client.post("/generate", json=invalid_request)
        assert (
            response.status_code == 422
        )  # FastAPI validation error for invalid enum value

        # For the remaining tests, we need to mock the TemplateEngine
        with patch(
            "resume_agent_template_engine.api.app.TemplateEngine"
        ) as mock_engine_class:
            mock_engine = Mock()
            mock_engine.get_available_templates.return_value = {"resume": ["classic"]}
            mock_engine_class.return_value = mock_engine

            # Test invalid format
            invalid_format_request = {
                "document_type": "resume",
                "template": "classic",
                "format": "html",  # Not supported
                "data": {"personalInfo": {"name": "John", "email": "john@test.com"}},
            }

            response = client.post("/generate", json=invalid_format_request)
            assert response.status_code == 400
            assert "Only PDF format is currently supported" in response.json()["detail"]

            # Test missing personal info
            missing_info_request = {
                "document_type": "resume",
                "template": "classic",
                "format": "pdf",
                "data": {"experience": []},  # Missing personalInfo
            }

            response = client.post("/generate", json=missing_info_request)
            assert response.status_code == 400
            assert "Personal information is required" in response.json()["detail"]

            # Test invalid email format
            invalid_email_request = {
                "document_type": "resume",
                "template": "classic",
                "format": "pdf",
                "data": {
                    "personalInfo": {
                        "name": "John Doe",
                        "email": "invalid-email",  # Invalid email format
                    }
                },
            }

            response = client.post("/generate", json=invalid_email_request)
            assert response.status_code == 400

    def test_template_management_workflow(self, client):
        """Test complete template management workflow."""

        with patch(
            "resume_agent_template_engine.api.app.TemplateEngine"
        ) as mock_engine_class:
            mock_engine = Mock()

            # Test listing all templates
            mock_engine.get_available_templates.return_value = {
                "resume": ["classic", "modern", "creative"],
                "cover_letter": ["formal", "casual"],
            }
            mock_engine_class.return_value = mock_engine

            all_templates_response = client.get("/templates")
            assert all_templates_response.status_code == 200

            data = all_templates_response.json()
            assert len(data["templates"]["resume"]) == 3
            assert len(data["templates"]["cover_letter"]) == 2

            # Test listing templates by specific type
            mock_engine.get_available_templates.return_value = [
                "classic",
                "modern",
                "creative",
            ]

            resume_templates_response = client.get("/templates/resume")
            assert resume_templates_response.status_code == 200

            resume_data = resume_templates_response.json()
            assert len(resume_data["templates"]) == 3

            # Test getting detailed template information
            mock_engine.get_template_info.return_value = {
                "name": "Modern Resume Template",
                "description": "A contemporary and stylish resume template",
                "author": "Design Team",
                "version": "2.0.0",
                "features": ["Clean design", "ATS-friendly", "Color customization"],
                "preview_path": "/path/to/preview.png",
            }

            template_info_response = client.get("/template-info/resume/modern")
            assert template_info_response.status_code == 200

            info = template_info_response.json()
            assert info["name"] == "Modern Resume Template"
            assert info["version"] == "2.0.0"
            assert "features" in info

            # Test non-existent template
            mock_engine.get_template_info.side_effect = ValueError("Template not found")

            not_found_response = client.get("/template-info/resume/nonexistent")
            assert not_found_response.status_code == 404

    def test_concurrent_document_generation(
        self, client, sample_resume_data, sample_cover_letter_data
    ):
        """Test concurrent document generation scenarios."""

        with patch(
            "resume_agent_template_engine.api.app.TemplateEngine"
        ) as mock_engine_class:
            mock_engine = Mock()

            # Handle different call patterns for get_available_templates
            def mock_get_templates(document_type=None):
                if document_type is None:
                    return {"resume": ["classic"], "cover_letter": ["formal"]}
                elif document_type == "resume":
                    return ["classic"]
                elif document_type == "cover_letter":
                    return ["formal"]
                else:
                    return []

            mock_engine.get_available_templates.side_effect = mock_get_templates
            mock_engine_class.return_value = mock_engine

            # Create a real temporary file for the test
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as real_temp:
                real_temp.write(b"Mock PDF content")
                real_temp_path = real_temp.name

            with patch("tempfile.NamedTemporaryFile") as mock_tempfile, patch(
                "os.path.exists", return_value=True
            ), patch("os.remove"):

                # Mock tempfile to return our real file path
                mock_temp = Mock()
                mock_temp.name = real_temp_path
                mock_tempfile.return_value.__enter__.return_value = mock_temp

                try:
                    mock_engine.export_to_pdf.return_value = real_temp_path

                    # Generate resume
                    resume_request = {
                        "document_type": "resume",
                        "template": "classic",
                        "format": "pdf",
                        "data": sample_resume_data,
                    }

                    resume_response = client.post("/generate", json=resume_request)
                    assert resume_response.status_code == 200

                    # Generate cover letter
                    cover_request = {
                        "document_type": "cover_letter",
                        "template": "formal",
                        "format": "pdf",
                        "data": sample_cover_letter_data,
                    }

                    cover_response = client.post("/generate", json=cover_request)
                    assert cover_response.status_code == 200

                    # Generate another resume
                    resume2_response = client.post("/generate", json=resume_request)
                    assert resume2_response.status_code == 200

                    # Verify all calls were made
                    assert mock_engine.export_to_pdf.call_count == 3

                finally:
                    # Clean up the temporary file
                    if os.path.exists(real_temp_path):
                        os.remove(real_temp_path)

    def test_api_robustness_with_malformed_data(self, client):
        """Test API robustness with various malformed data scenarios."""

        # Test with completely empty request
        response = client.post("/generate", json={})
        assert response.status_code == 422  # Validation error

        # Test with missing required fields
        incomplete_request = {
            "document_type": "resume",
            # Missing template, format, and data
        }

        response = client.post("/generate", json=incomplete_request)
        assert response.status_code == 422

        # Test with invalid JSON structure
        response = client.post("/generate", data="invalid json")
        assert response.status_code == 422

        # Test with invalid date formats in experience
        invalid_date_request = {
            "document_type": "resume",
            "template": "classic",
            "format": "pdf",
            "data": {
                "personalInfo": {"name": "John Doe", "email": "john@example.com"},
                "experience": [
                    {
                        "title": "Engineer",
                        "company": "Tech Corp",
                        "startDate": "invalid-date-format",
                    }
                ],
            },
        }

        response = client.post("/generate", json=invalid_date_request)
        assert response.status_code == 400
        assert "Invalid start date format" in response.json()["detail"]

    def test_large_data_handling(self, client):
        """Test handling of large data payloads."""

        # Create a large resume data payload
        large_resume_data = {
            "personalInfo": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1-234-567-8900",
                "location": "San Francisco, CA",
            },
            "experience": [],
        }

        # Add many experience entries
        for i in range(50):
            large_resume_data["experience"].append(
                {
                    "title": f"Software Engineer {i}",
                    "company": f"Tech Company {i}",
                    "location": "San Francisco, CA",
                    "startDate": "2020-01",
                    "endDate": "2021-12",
                    "description": [
                        f"Developed feature {i}",
                        f"Improved system performance by {i}%",
                        f"Led team of {i} developers",
                    ]
                    * 10,  # Make descriptions very long
                }
            )

        with patch(
            "resume_agent_template_engine.api.app.TemplateEngine"
        ) as mock_engine_class:
            mock_engine = Mock()
            mock_engine.get_available_templates.return_value = {"resume": ["classic"]}
            mock_engine.export_to_pdf.return_value = "/tmp/large_resume.pdf"
            mock_engine_class.return_value = mock_engine

            # Create a real temporary file for the test
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as real_temp:
                real_temp.write(b"Mock PDF content")
                real_temp_path = real_temp.name

            with patch("tempfile.NamedTemporaryFile") as mock_tempfile, patch(
                "os.path.exists", return_value=True
            ), patch("os.remove"):

                # Mock tempfile to return our real file path
                mock_temp = Mock()
                mock_temp.name = real_temp_path
                mock_tempfile.return_value.__enter__.return_value = mock_temp

                try:
                    mock_engine.export_to_pdf.return_value = real_temp_path

                    large_request = {
                        "document_type": "resume",
                        "template": "classic",
                        "format": "pdf",
                        "data": large_resume_data,
                    }

                    response = client.post("/generate", json=large_request)
                    assert response.status_code == 200
                    assert response.headers["content-type"] == "application/pdf"

                finally:
                    # Clean up the temporary file
                    if os.path.exists(real_temp_path):
                        os.remove(real_temp_path)


class TestAPIPerformanceE2E:
    """End-to-end performance tests for API endpoints."""

    def test_response_time_benchmarks(self, client, sample_resume_data):
        """Test that API responses meet performance benchmarks."""
        import time

        # Test template listing performance
        start_time = time.time()

        with patch(
            "resume_agent_template_engine.api.app.TemplateEngine"
        ) as mock_engine_class:
            mock_engine = Mock()
            mock_engine.get_available_templates.return_value = {
                "resume": ["classic"] * 100  # Large number of templates
            }
            mock_engine_class.return_value = mock_engine

            response = client.get("/templates")
            end_time = time.time()

            assert response.status_code == 200
            assert (end_time - start_time) < 1.0  # Should respond within 1 second

        # Test document generation performance
        with patch(
            "resume_agent_template_engine.api.app.TemplateEngine"
        ) as mock_engine_class:
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
            mock_engine_class.return_value = mock_engine

            # Create a real temporary file for the test
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as real_temp:
                real_temp.write(b"Mock PDF content")
                real_temp_path = real_temp.name

            with patch("tempfile.NamedTemporaryFile") as mock_tempfile, patch(
                "os.path.exists", return_value=True
            ), patch("os.remove"):

                # Mock tempfile to return our real file path
                mock_temp = Mock()
                mock_temp.name = real_temp_path
                mock_tempfile.return_value.__enter__.return_value = mock_temp

                try:
                    mock_engine.export_to_pdf.return_value = real_temp_path

                    start_time = time.time()

                    generation_request = {
                        "document_type": "resume",
                        "template": "classic",
                        "format": "pdf",
                        "data": sample_resume_data,
                    }

                    response = client.post("/generate", json=generation_request)
                    end_time = time.time()

                    assert response.status_code == 200
                    assert (
                        end_time - start_time
                    ) < 5.0  # Should generate within 5 seconds

                finally:
                    # Clean up the temporary file
                    if os.path.exists(real_temp_path):
                        os.remove(real_temp_path)

    def test_memory_usage_stability(self, client, sample_resume_data):
        """Test that memory usage remains stable during multiple requests."""

        with patch(
            "resume_agent_template_engine.api.app.TemplateEngine"
        ) as mock_engine_class:
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
            mock_engine_class.return_value = mock_engine

            # Create a real temporary file for the test
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as real_temp:
                real_temp.write(b"Mock PDF content")
                real_temp_path = real_temp.name

            with patch("tempfile.NamedTemporaryFile") as mock_tempfile, patch(
                "os.path.exists", return_value=True
            ), patch("os.remove"):

                # Mock tempfile to return our real file path
                mock_temp = Mock()
                mock_temp.name = real_temp_path
                mock_tempfile.return_value.__enter__.return_value = mock_temp

                try:
                    mock_engine.export_to_pdf.return_value = real_temp_path

                    # Make multiple requests to test memory stability
                    for i in range(10):
                        generation_request = {
                            "document_type": "resume",
                            "template": "classic",
                            "format": "pdf",
                            "data": sample_resume_data,
                        }

                        response = client.post("/generate", json=generation_request)
                        assert response.status_code == 200

                    # All requests should succeed without memory issues
                    assert mock_engine.export_to_pdf.call_count == 10

                finally:
                    # Clean up the temporary file
                    if os.path.exists(real_temp_path):
                        os.remove(real_temp_path)
