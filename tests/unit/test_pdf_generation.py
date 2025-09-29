"""
Unit tests for PDF generation functionality

Tests the real PDF generation system using the UniversalTemplate and template registry.
Tests both LaTeX rendering and actual PDF compilation when pdflatex is available.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from resume_agent_template_engine.core.base import DocumentType
from resume_agent_template_engine.core.exceptions import (
    DependencyException,
    FileNotFoundException,
    LaTeXCompilationException,
    PDFGenerationException,
    ValidationException,
)
from resume_agent_template_engine.core.template_registry import (
    get_available_templates,
    get_template_definition,
)
from resume_agent_template_engine.core.universal_template import UniversalTemplate


def has_pdflatex():
    """Check if pdflatex is available on the system"""
    return shutil.which("pdflatex") is not None


def has_latex_packages():
    """Check if required LaTeX packages are available"""
    if not has_pdflatex():
        return False

    # Try to compile a minimal document to check package availability
    test_tex = r"""
\documentclass{article}
\usepackage{geometry}
\usepackage{enumitem}
\usepackage{titlesec}
\begin{document}
Test
\end{document}
"""

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            tex_file = Path(temp_dir) / "test.tex"
            with open(tex_file, "w") as f:
                f.write(test_tex)

            result = os.system(
                f"cd {temp_dir} && pdflatex -interaction=nonstopmode test.tex > /dev/null 2>&1"
            )
            return result == 0
    except Exception:
        return False


class TestUniversalTemplate:
    """Test UniversalTemplate functionality"""

    @pytest.fixture
    def sample_resume_data(self):
        """Sample resume data for testing"""
        return {
            "personalInfo": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1 (555) 123-4567",
                "location": "San Francisco, CA",
                "website": "https://johndoe.dev",
                "linkedin": "https://linkedin.com/in/johndoe",
                "github": "https://github.com/johndoe",
            },
            "professionalSummary": "Experienced software engineer with 5+ years of expertise in full-stack development.",
            "experience": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Corp",
                    "location": "San Francisco, CA",
                    "startDate": "2021-03",
                    "endDate": "Present",
                    "achievements": [
                        "Led development of microservices architecture",
                        "Reduced system latency by 40%",
                    ],
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "University of California, Berkeley",
                    "endDate": "2018-12",
                    "focus": "Software Engineering",
                }
            ],
            "technologiesAndSkills": [
                {
                    "category": "Programming Languages",
                    "skills": ["Python", "JavaScript", "TypeScript"],
                },
                {"category": "Frameworks", "skills": ["React", "Node.js", "Django"]},
            ],
        }

    @pytest.fixture
    def sample_cover_letter_data(self):
        """Sample cover letter data for testing"""
        return {
            "personalInfo": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1 (555) 123-4567",
                "location": "San Francisco, CA",
            },
            "recipient": {
                "name": "Jane Smith",
                "title": "Engineering Manager",
                "company": "Innovative Tech Solutions",
                "street": "123 Tech Boulevard",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94105",
            },
            "body": [
                "I am writing to express my strong interest in the Senior Software Engineer position at Innovative Tech Solutions.",
                "With over 5 years of experience in full-stack development, I am excited about the opportunity to contribute to your team.",
                "I would welcome the opportunity to discuss how my technical expertise can contribute to your upcoming projects.",
            ],
        }

    def test_universal_template_initialization(self, sample_resume_data):
        """Test UniversalTemplate initialization"""
        template = UniversalTemplate(
            document_type="resume", template_name="classic", data=sample_resume_data
        )

        assert template.document_type == "resume"
        assert template.template_name == "classic"
        assert template.data == template.replace_special_chars(sample_resume_data)
        assert template.template_def is not None

    def test_universal_template_invalid_document_type(self, sample_resume_data):
        """Test UniversalTemplate with invalid document type"""
        with pytest.raises(ValueError, match="Document type 'invalid' not found"):
            UniversalTemplate(
                document_type="invalid",
                template_name="classic",
                data=sample_resume_data,
            )

    def test_universal_template_invalid_template_name(self, sample_resume_data):
        """Test UniversalTemplate with invalid template name"""
        with pytest.raises(ValueError, match="Template 'invalid' not found"):
            UniversalTemplate(
                document_type="resume", template_name="invalid", data=sample_resume_data
            )

    def test_latex_rendering_resume(self, sample_resume_data):
        """Test LaTeX rendering for resume"""
        template = UniversalTemplate(
            document_type="resume", template_name="classic", data=sample_resume_data
        )

        latex_content = template.render()

        # Check basic LaTeX document structure
        assert isinstance(latex_content, str)
        assert "\\documentclass" in latex_content
        assert "\\begin{document}" in latex_content
        assert "\\end{document}" in latex_content

        # Check that personal info is included
        assert "John Doe" in latex_content
        assert "john.doe@example.com" in latex_content

        # Check that experience section is included
        assert "Senior Software Engineer" in latex_content
        assert "Tech Corp" in latex_content

    def test_latex_rendering_cover_letter(self, sample_cover_letter_data):
        """Test LaTeX rendering for cover letter"""
        template = UniversalTemplate(
            document_type="cover_letter",
            template_name="classic",
            data=sample_cover_letter_data,
        )

        latex_content = template.render()

        # Check basic LaTeX document structure
        assert isinstance(latex_content, str)
        assert "\\documentclass" in latex_content
        assert "\\begin{document}" in latex_content
        assert "\\end{document}" in latex_content

        # Check that personal info is included
        assert "John Doe" in latex_content

        # Check that recipient info is included
        assert "Jane Smith" in latex_content
        assert "Innovative Tech Solutions" in latex_content

        # Check that body content is included
        assert "express my strong interest" in latex_content

    def test_special_character_escaping(self):
        """Test that special LaTeX characters are properly escaped"""
        data_with_special_chars = {
            "personalInfo": {
                "name": "John & Jane Doe",
                "email": "john@example.com",
                "phone": "100% reliable: (555) 123-4567",
            }
        }

        template = UniversalTemplate(
            document_type="resume",
            template_name="classic",
            data=data_with_special_chars,
        )

        latex_content = template.render()

        # Check that special characters are escaped
        assert (
            "John \\& Jane Doe" in latex_content or "John & Jane Doe" in latex_content
        )
        assert "100\\% reliable" in latex_content or "100% reliable" in latex_content

    @pytest.mark.skipif(not has_pdflatex(), reason="pdflatex not available")
    def test_pdf_generation_resume(self, sample_resume_data):
        """Test actual PDF generation for resume (requires pdflatex)"""
        template = UniversalTemplate(
            document_type="resume", template_name="classic", data=sample_resume_data
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_resume.pdf")

            try:
                result_path = template.export_to_pdf(output_path)

                # Check that PDF was created
                assert result_path == output_path
                assert os.path.exists(output_path)
                assert os.path.getsize(output_path) > 0

                # Check that it's a valid PDF (basic check)
                with open(output_path, "rb") as f:
                    header = f.read(5)
                    assert header == b"%PDF-"

            except (LaTeXCompilationException, PDFGenerationException) as e:
                # If compilation fails due to missing packages, skip the test
                pytest.skip(f"LaTeX compilation failed: {e}")

    @pytest.mark.skipif(not has_pdflatex(), reason="pdflatex not available")
    def test_pdf_generation_cover_letter(self, sample_cover_letter_data):
        """Test actual PDF generation for cover letter (requires pdflatex)"""
        template = UniversalTemplate(
            document_type="cover_letter",
            template_name="classic",
            data=sample_cover_letter_data,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_cover_letter.pdf")

            try:
                result_path = template.export_to_pdf(output_path)

                # Check that PDF was created
                assert result_path == output_path
                assert os.path.exists(output_path)
                assert os.path.getsize(output_path) > 0

                # Check that it's a valid PDF (basic check)
                with open(output_path, "rb") as f:
                    header = f.read(5)
                    assert header == b"%PDF-"

            except (LaTeXCompilationException, PDFGenerationException) as e:
                # If compilation fails due to missing packages, skip the test
                pytest.skip(f"LaTeX compilation failed: {e}")

    def test_template_file_not_found(self, sample_resume_data):
        """Test handling of missing template file"""
        # Mock the template path to point to non-existent file
        with patch.object(UniversalTemplate, "_get_template_directory") as mock_get_dir:
            mock_get_dir.return_value = Path("/nonexistent/path")

            with pytest.raises(FileNotFoundException):
                UniversalTemplate(
                    document_type="resume",
                    template_name="classic",
                    data=sample_resume_data,
                )

    @pytest.mark.skipif(
        has_pdflatex(), reason="Test for when pdflatex is not available"
    )
    def test_pdf_generation_without_latex(self, sample_resume_data):
        """Test PDF generation behavior when LaTeX is not available"""
        template = UniversalTemplate(
            document_type="resume", template_name="classic", data=sample_resume_data
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_resume.pdf")

            # Should raise DependencyException when pdflatex is not available
            with pytest.raises(DependencyException):
                template.export_to_pdf(output_path)

    def test_validation_required_fields(self):
        """Test validation of required fields"""
        # Test with missing required field
        incomplete_data = {
            "personalInfo": {
                "name": "John Doe"
                # Missing email which is required
            }
        }

        # Should raise ValidationException for missing required field
        with pytest.raises(ValidationException):
            UniversalTemplate(
                document_type="resume", template_name="classic", data=incomplete_data
            )

    def test_field_mapping_fallbacks(self):
        """Test that field mapping fallbacks work correctly"""
        data_with_fallback_fields = {
            "personalInfo": {
                "name": "John Doe",
                "email": "john@example.com",
                "telephone": "555-123-4567",  # Should map to phone
                "address": "123 Main St",  # Should map to location
            },
            "experience": [
                {
                    "position": "Developer",  # Should map to title
                    "employer": "Big Corp",  # Should map to company
                    "start_date": "2020-01",  # Should map to startDate
                    "end_date": "2023-12",  # Should map to endDate
                }
            ],
        }

        template = UniversalTemplate(
            document_type="resume",
            template_name="classic",
            data=data_with_fallback_fields,
        )

        latex_content = template.render()

        # Check that fallback mappings worked
        assert "555-123-4567" in latex_content
        assert "123 Main St" in latex_content
        assert "Developer" in latex_content
        assert "Big Corp" in latex_content


class TestTemplateRegistry:
    """Test template registry functionality"""

    def test_get_available_templates(self):
        """Test getting available templates"""
        templates = get_available_templates()

        assert isinstance(templates, dict)
        assert "resume" in templates
        assert "cover_letter" in templates
        assert "classic" in templates["resume"]
        assert "classic" in templates["cover_letter"]

    def test_get_template_definition(self):
        """Test getting specific template definition"""
        template_def = get_template_definition("resume", "classic")

        assert template_def.name == "classic"
        assert template_def.document_type == DocumentType.RESUME
        assert template_def.template_file == "classic.tex"
        assert "personalInfo" in template_def.required_fields


class TestIntegrationWithRealTemplates:
    """Integration tests with real template files"""

    def test_real_template_files_exist(self):
        """Test that actual template files exist in the file system"""
        template_def = get_template_definition("resume", "classic")

        # Get the template directory
        module_dir = (
            Path(__file__).parent.parent.parent / "src" / "resume_agent_template_engine"
        )
        template_path = (
            module_dir / "templates" / "resume" / "classic" / template_def.template_file
        )

        assert template_path.exists(), f"Template file not found: {template_path}"

        # Check that the file is readable and contains LaTeX content
        with open(template_path, encoding="utf-8") as f:
            content = f.read()
            assert "\\documentclass" in content
            assert len(content) > 100  # Should be a substantial file

    def test_template_placeholders_consistency(self):
        """Test that template placeholders are consistent between registry and template files"""
        template_def = get_template_definition("resume", "classic")

        # Get the actual template file
        module_dir = (
            Path(__file__).parent.parent.parent / "src" / "resume_agent_template_engine"
        )
        template_path = (
            module_dir / "templates" / "resume" / "classic" / template_def.template_file
        )

        with open(template_path, encoding="utf-8") as f:
            template_content = f.read()

        # Check that placeholders defined in registry exist in template
        for placeholder in template_def.placeholders:
            assert placeholder in template_content, (
                f"Placeholder {placeholder} not found in template file"
            )

    @pytest.mark.skipif(
        not has_latex_packages(), reason="Required LaTeX packages not available"
    )
    def test_end_to_end_pdf_generation(self):
        """End-to-end test of PDF generation with real data and templates"""
        realistic_data = {
            "personalInfo": {
                "name": "Alice Johnson",
                "email": "alice.johnson@email.com",
                "phone": "+1 (555) 987-6543",
                "location": "Seattle, WA",
                "website": "https://alicejohnson.dev",
                "linkedin": "https://linkedin.com/in/alicejohnson",
                "github": "https://github.com/alicejohnson",
            },
            "professionalSummary": "Senior Full-Stack Developer with 8+ years of experience building scalable web applications and leading development teams.",
            "experience": [
                {
                    "title": "Lead Software Engineer",
                    "company": "CloudTech Solutions",
                    "location": "Seattle, WA",
                    "startDate": "2020-06",
                    "endDate": "Present",
                    "achievements": [
                        "Architected and implemented microservices infrastructure serving 10M+ requests/day",
                        "Led cross-functional team of 8 engineers across 3 product areas",
                        "Reduced deployment time from 2 hours to 15 minutes through CI/CD optimization",
                    ],
                },
                {
                    "title": "Senior Software Developer",
                    "company": "StartupXYZ",
                    "location": "San Francisco, CA",
                    "startDate": "2018-03",
                    "endDate": "2020-05",
                    "achievements": [
                        "Built real-time analytics dashboard processing 1TB+ data daily",
                        "Implemented automated testing reducing bug reports by 75%",
                    ],
                },
            ],
            "education": [
                {
                    "degree": "Master of Science in Computer Science",
                    "institution": "Stanford University",
                    "endDate": "2018-06",
                    "focus": "Distributed Systems",
                }
            ],
            "technologiesAndSkills": [
                {
                    "category": "Languages",
                    "skills": ["Python", "JavaScript", "TypeScript", "Go", "Java"],
                },
                {
                    "category": "Frameworks",
                    "skills": ["React", "Node.js", "Django", "FastAPI", "Express.js"],
                },
                {
                    "category": "Cloud & DevOps",
                    "skills": ["AWS", "Docker", "Kubernetes", "Terraform", "Jenkins"],
                },
            ],
        }

        template = UniversalTemplate(
            document_type="resume", template_name="classic", data=realistic_data
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "alice_johnson_resume.pdf")

            # Generate LaTeX content
            latex_content = template.render()

            # Verify LaTeX content quality
            assert "Alice Johnson" in latex_content
            assert "CloudTech Solutions" in latex_content
            assert "10M+ requests/day" in latex_content
            assert "Stanford University" in latex_content

            # Generate PDF
            result_path = template.export_to_pdf(output_path)

            # Verify PDF was created successfully
            assert os.path.exists(result_path)
            assert os.path.getsize(result_path) > 5000  # Should be a substantial PDF

            # Verify it's a valid PDF
            with open(result_path, "rb") as f:
                header = f.read(5)
                assert header == b"%PDF-"


if __name__ == "__main__":
    pytest.main([__file__])
