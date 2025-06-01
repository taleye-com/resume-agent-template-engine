"""Pytest configuration and common fixtures for all tests."""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Generator
import json
from unittest.mock import MagicMock, patch

# Add the src directory to Python path for imports
import sys
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from resume_agent_template_engine.core.template_engine import TemplateEngine, DocumentType
from resume_agent_template_engine.templates.template_manager import TemplateManager


@pytest.fixture(scope="session")
def project_root_path() -> Path:
    """Get the project root path."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def templates_path(project_root_path: Path) -> Path:
    """Get the templates directory path."""
    return project_root_path / "src" / "resume_agent_template_engine" / "templates"


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_personal_info() -> Dict[str, Any]:
    """Sample personal information data."""
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-234-567-8900",
        "location": "San Francisco, CA",
        "website": "https://johndoe.dev",
        "linkedin": "https://linkedin.com/in/johndoe",
        "website_display": "https://johndoe.dev",
        "linkedin_display": "https://linkedin.com/in/johndoe"
    }


@pytest.fixture
def sample_resume_data(sample_personal_info: Dict[str, Any]) -> Dict[str, Any]:
    """Sample resume data for testing."""
    return {
        "personalInfo": sample_personal_info,
        "summary": "Experienced software engineer with 5+ years of experience in Python and web development.",
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "Tech Corp",
                "location": "San Francisco, CA",
                "startDate": "2021-01",
                "endDate": "Present",
                "description": [
                    "Led development of microservices architecture",
                    "Mentored junior developers",
                    "Improved system performance by 40%"
                ]
            },
            {
                "title": "Software Engineer",
                "company": "StartupXYZ",
                "location": "Mountain View, CA",
                "startDate": "2019-06",
                "endDate": "2020-12",
                "description": [
                    "Developed RESTful APIs using FastAPI",
                    "Implemented CI/CD pipelines",
                    "Built responsive web applications"
                ]
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science in Computer Science",
                "school": "University of California, Berkeley",
                "location": "Berkeley, CA",
                "graduationDate": "2019-05"
            }
        ],
        "skills": {
            "programming": ["Python", "JavaScript", "TypeScript", "Java"],
            "frameworks": ["FastAPI", "React", "Node.js", "Django"],
            "databases": ["PostgreSQL", "MongoDB", "Redis"],
            "tools": ["Docker", "Kubernetes", "AWS", "Git"]
        },
        "projects": [
            {
                "name": "Resume Builder API",
                "description": "A FastAPI-based service for generating professional resumes from JSON data",
                "technologies": ["Python", "FastAPI", "PostgreSQL"],
                "url": "https://github.com/johndoe/resume-api"
            }
        ]
    }


@pytest.fixture
def sample_cover_letter_data(sample_personal_info: Dict[str, Any]) -> Dict[str, Any]:
    """Sample cover letter data for testing."""
    return {
        "personalInfo": sample_personal_info,
        "recipient": {
            "name": "Jane Smith",
            "title": "Hiring Manager",
            "company": "Amazing Company",
            "address": "123 Business St, San Francisco, CA 94105"
        },
        "jobTitle": "Senior Software Engineer",
        "content": {
            "opening": "I am writing to express my strong interest in the Senior Software Engineer position at Amazing Company.",
            "body": [
                "With over 5 years of experience in software development, I have developed strong skills in Python, web development, and system architecture.",
                "In my current role at Tech Corp, I have successfully led multiple projects and mentored junior developers, resulting in improved team productivity and code quality."
            ],
            "closing": "I am excited about the opportunity to contribute to Amazing Company's innovative projects and would welcome the chance to discuss how my skills align with your team's needs."
        },
        "date": "2024-01-15"
    }


@pytest.fixture
def template_engine() -> TemplateEngine:
    """Create a template engine instance for testing."""
    return TemplateEngine()


@pytest.fixture
def template_manager() -> TemplateManager:
    """Create a template manager instance for testing."""
    return TemplateManager()


@pytest.fixture
def mock_template_dir(temp_dir: Path) -> Path:
    """Create a mock template directory structure."""
    # Create resume templates
    resume_dir = temp_dir / "resume" / "classic"
    resume_dir.mkdir(parents=True)
    
    # Create helper.py
    helper_content = '''
from resume_agent_template_engine.core.template_engine import TemplateInterface, DocumentType
from typing import Dict, Any, List

class ClassicResumeTemplate(TemplateInterface):
    def validate_data(self) -> None:
        required = ["personalInfo"]
        for field in required:
            if field not in self.data:
                raise ValueError(f"Required field missing: {field}")
    
    def render(self) -> str:
        return "\\\\documentclass{article}\\n\\\\begin{document}Test Resume\\\\end{document}"
    
    def export_to_pdf(self, output_path: str) -> str:
        with open(output_path, "wb") as f:
            f.write(b"Mock PDF content")
        return output_path
    
    @property
    def required_fields(self) -> List[str]:
        return ["personalInfo"]
    
    @property
    def template_type(self) -> DocumentType:
        return DocumentType.RESUME
'''
    
    (resume_dir / "helper.py").write_text(helper_content)
    (resume_dir / "template.tex").write_text("\\documentclass{article}")
    
    # Create cover letter templates
    cover_dir = temp_dir / "cover_letter" / "classic"
    cover_dir.mkdir(parents=True)
    
    cover_helper_content = '''
from resume_agent_template_engine.core.template_engine import TemplateInterface, DocumentType
from typing import Dict, Any, List

class ClassicCoverLetterTemplate(TemplateInterface):
    def validate_data(self) -> None:
        required = ["personalInfo", "recipient"]
        for field in required:
            if field not in self.data:
                raise ValueError(f"Required field missing: {field}")
    
    def render(self) -> str:
        return "\\\\documentclass{letter}\\n\\\\begin{document}Test Cover Letter\\\\end{document}"
    
    def export_to_pdf(self, output_path: str) -> str:
        with open(output_path, "wb") as f:
            f.write(b"Mock PDF content")
        return output_path
    
    @property
    def required_fields(self) -> List[str]:
        return ["personalInfo", "recipient"]
    
    @property
    def template_type(self) -> DocumentType:
        return DocumentType.COVER_LETTER
'''
    
    (cover_dir / "helper.py").write_text(cover_helper_content)
    (cover_dir / "template.tex").write_text("\\documentclass{letter}")
    
    return temp_dir


@pytest.fixture
def api_client():
    """Create a test client for the FastAPI application."""
    from fastapi.testclient import TestClient
    from resume_agent_template_engine.api.app import app
    
    return TestClient(app)


@pytest.fixture
def client():
    """Alias for api_client fixture for backward compatibility."""
    from fastapi.testclient import TestClient
    from resume_agent_template_engine.api.app import app
    
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_logging():
    """Setup logging for tests."""
    import logging
    logging.basicConfig(level=logging.DEBUG)


# Mock fixtures for external dependencies
@pytest.fixture
def mock_pdflatex():
    """Mock pdflatex command for testing."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b"pdflatex output"
        mock_run.return_value.stderr = b""
        yield mock_run


@pytest.fixture
def mock_file_operations():
    """Mock file operations for testing."""
    with patch('os.path.exists') as mock_exists, \
         patch('os.makedirs') as mock_makedirs, \
         patch('shutil.copy2') as mock_copy:
        mock_exists.return_value = True
        yield {
            'exists': mock_exists,
            'makedirs': mock_makedirs,
            'copy': mock_copy
        } 