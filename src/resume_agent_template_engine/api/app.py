import logging
import os
import tempfile
from datetime import datetime
from typing import Any, Optional, Union

import uvicorn
import yaml
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, EmailStr

from resume_agent_template_engine.core.base import DocumentType
from resume_agent_template_engine.core.errors import ErrorCode
from resume_agent_template_engine.core.exceptions import (
    InternalServerException,
    InvalidParameterException,
    InvalidRequestException,
    ResourceNotFoundException,
    ResumeCompilerException,
    TemplateNotFoundException,
    ValidationException,
)
from resume_agent_template_engine.core.responses import (
    ResponseFormatter,
    create_error_response,
)
from resume_agent_template_engine.core.template_engine import (
    TemplateEngine,
)
from resume_agent_template_engine.core.validation import (
    ValidationLevel,
)
from resume_agent_template_engine.core.validation import (
    validate_resume_data as enhanced_validate_resume_data,
)

from .schema_generator import SchemaGenerator

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Resume and Cover Letter Template Engine API",
    description="""
    **Professional Document Generation API**

    Generate high-quality resumes and cover letters from structured JSON or YAML data using customizable LaTeX templates.

    ## Features
    - **Multiple Document Types**: Resume and cover letter generation
    - **Professional Templates**: LaTeX-based templates for high-quality output
    - **Flexible Input**: Support for both JSON and YAML data formats
    - **Comprehensive Validation**: Built-in data validation and sanitization
    - **Rich Schema Support**: Detailed schemas with examples for all document types

    ## Quick Start
    1. Get the schema for your document type: `GET /schema/{document_type}`
    2. Validate your data (optional): `POST /validate`
    3. Generate your document: `POST /generate`

    ## Supported Document Types
    - `resume`: Professional resume generation
    - `cover_letter`: Professional cover letter generation

    ## Available Templates
    - `classic`: Clean, professional template suitable for all industries
    """,
    version="2.0.0",
    contact={
        "name": "Resume Agent Template Engine",
        "url": "https://github.com/taleye-com/resume-agent-template-engine",
    },
    license_info={"name": "MIT License"},
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(ResumeCompilerException)
async def resume_compiler_exception_handler(
    request: Request, exc: ResumeCompilerException
):
    """Handle all resume compiler exceptions with standardized format"""
    logger.error(f"Resume compiler error: {exc.error_code} - {exc.formatted_message}")

    response_data = ResponseFormatter.format_error_response(
        exc,
        request_id=getattr(request.state, "request_id", None),
        include_debug_info=False,  # Set to True in development
    )

    return JSONResponse(status_code=exc.http_status_code, content=response_data)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions with standardized format"""
    # Convert HTTPException to standardized format
    error_code = ErrorCode.API001  # Default API error

    if exc.status_code == 404:
        error_code = ErrorCode.API011
    elif exc.status_code == 400:
        error_code = ErrorCode.API003

    response_data = create_error_response(
        error_code,
        request_id=getattr(request.state, "request_id", None),
        details=exc.detail,
    )

    return JSONResponse(status_code=exc.status_code, content=response_data)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.exception(f"Unexpected error: {str(exc)}")

    internal_error = InternalServerException(
        details=str(exc), request_id=getattr(request.state, "request_id", None)
    )

    response_data = ResponseFormatter.format_error_response(
        internal_error,
        include_debug_info=False,  # Set to True in development
    )

    return JSONResponse(status_code=500, content=response_data)


@app.get("/", tags=["General"])
async def root():
    """Welcome endpoint with API information."""
    return {
        "message": "Welcome to Resume Agent Template Engine API",
        "version": "2.0.0",
        "documentation": "/docs",
        "health_check": "/health",
        "available_endpoints": {
            "schemas": "/schema/{document_type}",
            "templates": "/templates",
            "generation": "/generate",
            "validation": "/validate",
        },
    }


# DocumentType enum is now imported from base module


# Comprehensive Pydantic Models based on Template Registry


class PersonalInfoModel(BaseModel):
    """Personal information model with all supported fields"""

    name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    twitter: Optional[str] = None
    x: Optional[str] = None
    website_display: Optional[str] = None
    linkedin_display: Optional[str] = None
    github_display: Optional[str] = None
    twitter_display: Optional[str] = None
    x_display: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1 (555) 123-4567",
                "location": "New York, NY",
                "website": "https://johndoe.dev",
                "linkedin": "https://linkedin.com/in/johndoe",
                "website_display": "johndoe.dev",
                "linkedin_display": "linkedin.com/in/johndoe",
            }
        }


class ExperienceModel(BaseModel):
    """Work experience model"""

    position: str
    company: str
    location: Optional[str] = None
    startDate: str  # YYYY-MM or YYYY-MM-DD format
    endDate: Optional[str] = "Present"  # YYYY-MM, YYYY-MM-DD, or "Present"
    description: Optional[str] = None
    achievements: Optional[list[str]] = None
    technologies: Optional[list[str]] = None

    class Config:
        schema_extra = {
            "example": {
                "position": "Senior Software Engineer",
                "company": "Tech Corp",
                "location": "New York, NY",
                "startDate": "2020-01",
                "endDate": "Present",
                "description": "Lead development of cloud-native applications",
                "achievements": [
                    "Reduced system latency by 40%",
                    "Led team of 5 engineers",
                ],
            }
        }


class EducationModel(BaseModel):
    """Education model"""

    degree: str
    institution: str
    location: Optional[str] = None
    graduationDate: Optional[str] = None  # YYYY-MM or YYYY-MM-DD
    gpa: Optional[str] = None
    coursework: Optional[list[str]] = None
    honors: Optional[list[str]] = None

    class Config:
        schema_extra = {
            "example": {
                "degree": "Bachelor of Science in Computer Science",
                "institution": "University of Technology",
                "graduationDate": "2019-05",
                "gpa": "3.8/4.0",
            }
        }


class ProjectModel(BaseModel):
    """Project model"""

    name: str
    description: str
    technologies: Optional[list[str]] = None
    url: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    achievements: Optional[list[str]] = None

    class Config:
        schema_extra = {
            "example": {
                "name": "E-commerce Platform",
                "description": "Built a full-stack e-commerce platform using React and Node.js",
                "technologies": ["React", "Node.js", "PostgreSQL"],
                "url": "https://github.com/johndoe/ecommerce",
            }
        }


class SkillsModel(BaseModel):
    """Skills model"""

    technical: Optional[list[str]] = None
    soft: Optional[list[str]] = None
    languages: Optional[list[str]] = None
    frameworks: Optional[list[str]] = None
    tools: Optional[list[str]] = None

    class Config:
        schema_extra = {
            "example": {
                "technical": ["Python", "JavaScript", "React", "AWS"],
                "soft": ["Leadership", "Communication", "Problem Solving"],
                "languages": ["English", "Spanish"],
                "frameworks": ["Django", "React", "Vue.js"],
            }
        }


class CertificationModel(BaseModel):
    """Certification model"""

    name: str
    issuer: str
    date: Optional[str] = None
    expiry: Optional[str] = None
    credential_id: Optional[str] = None
    url: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "name": "AWS Certified Solutions Architect",
                "issuer": "Amazon Web Services",
                "date": "2023-06",
                "expiry": "2026-06",
            }
        }


class PublicationModel(BaseModel):
    """Publication model"""

    title: str
    authors: list[str]
    venue: str
    date: str
    url: Optional[str] = None
    doi: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "title": "Machine Learning in Production Systems",
                "authors": ["John Doe", "Jane Smith"],
                "venue": "Journal of Software Engineering",
                "date": "2023-12",
            }
        }


class RecipientModel(BaseModel):
    """Cover letter recipient model"""

    name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    address: Optional[Union[str, list[str]]] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "name": "Jane Smith",
                "title": "Hiring Manager",
                "company": "Innovative Tech Solutions",
                "street": "123 Business Ave",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94105",
            }
        }


class ResumeDataModel(BaseModel):
    """Complete resume data model"""

    personalInfo: PersonalInfoModel
    professionalSummary: Optional[str] = None
    experience: Optional[list[ExperienceModel]] = None
    education: Optional[list[EducationModel]] = None
    projects: Optional[list[ProjectModel]] = None
    skills: Optional[SkillsModel] = None
    certifications: Optional[list[CertificationModel]] = None
    publications: Optional[list[PublicationModel]] = None
    achievements: Optional[list[str]] = None
    awards: Optional[list[str]] = None
    languages: Optional[list[str]] = None
    interests: Optional[list[str]] = None

    class Config:
        schema_extra = {
            "example": {
                "personalInfo": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+1 (555) 123-4567",
                    "location": "New York, NY",
                },
                "professionalSummary": "Experienced software engineer with 5+ years of expertise in full-stack development.",
                "experience": [
                    {
                        "position": "Senior Software Engineer",
                        "company": "Tech Corp",
                        "location": "New York, NY",
                        "startDate": "2020-01",
                        "endDate": "Present",
                        "description": "Lead development of cloud-native applications",
                        "achievements": [
                            "Reduced system latency by 40%",
                            "Led team of 5 engineers",
                        ],
                    }
                ],
            }
        }


class CoverLetterDataModel(BaseModel):
    """Complete cover letter data model"""

    personalInfo: PersonalInfoModel
    recipient: Optional[RecipientModel] = None
    date: Optional[str] = None
    salutation: Optional[str] = None
    body: Union[str, list[str]]
    closing: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "personalInfo": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+1 (555) 123-4567",
                    "location": "New York, NY",
                },
                "recipient": {
                    "name": "Jane Smith",
                    "title": "Hiring Manager",
                    "company": "Innovative Tech Solutions",
                },
                "body": [
                    "I am writing to express my strong interest in the Software Engineer position at your company.",
                    "My experience in full-stack development and passion for innovation align perfectly with your requirements.",
                ],
            }
        }


class DocumentRequest(BaseModel):
    """Document generation request with comprehensive data validation"""

    document_type: DocumentType
    template: str
    format: str = "pdf"
    data: Union[ResumeDataModel, CoverLetterDataModel, dict[str, Any]]
    clean_up: bool = True
    ultra_validation: bool = False

    class Config:
        schema_extra = {
            "example": {
                "document_type": "resume",
                "template": "classic",
                "format": "pdf",
                "data": {
                    "personalInfo": {
                        "name": "John Doe",
                        "email": "john@example.com",
                        "phone": "+1 (555) 123-4567",
                        "location": "New York, NY",
                    },
                    "professionalSummary": "Experienced software engineer with 5+ years of expertise.",
                },
            }
        }


class YAMLDocumentRequest(BaseModel):
    """YAML-based document generation request"""

    document_type: DocumentType
    template: str
    format: str = "pdf"
    yaml_data: str
    clean_up: bool = True
    ultra_validation: bool = False

    class Config:
        schema_extra = {
            "example": {
                "document_type": "resume",
                "template": "classic",
                "format": "pdf",
                "yaml_data": "personalInfo:\n  name: John Doe\n  email: john@example.com\nprofessionalSummary: Experienced software engineer...",
            }
        }


class ValidationRequest(BaseModel):
    """Request model for data validation"""

    document_type: DocumentType
    data: Union[ResumeDataModel, CoverLetterDataModel, dict[str, Any]]
    validation_level: str = "standard"  # "standard" or "ultra"

    class Config:
        schema_extra = {
            "example": {
                "document_type": "resume",
                "data": {
                    "personalInfo": {"name": "John Doe", "email": "john@example.com"}
                },
                "validation_level": "standard",
            }
        }


def parse_pydantic_error(
    exception: Exception, field_prefix: str = ""
) -> dict[str, Any]:
    """Parse Pydantic validation errors to extract field, expected type, and actual type"""
    error_str = str(exception)

    # Try to extract field name and error type from Pydantic error
    field_name = field_prefix
    expected_type = "valid data"
    actual_type = "invalid data"

    # Common Pydantic error patterns
    if "email" in error_str and "not a valid email" in error_str:
        field_name = f"{field_prefix}.email" if field_prefix else "email"
        expected_type = "valid email address"
        actual_type = "invalid email format"
    elif "field required" in error_str:
        expected_type = "required field"
        actual_type = "missing value"
    elif "not a valid" in error_str:
        if "string" in error_str:
            expected_type = "string"
            actual_type = "non-string value"
        elif "integer" in error_str:
            expected_type = "integer"
            actual_type = "non-integer value"
        elif "boolean" in error_str:
            expected_type = "boolean"
            actual_type = "non-boolean value"

    return {
        "field": field_name,
        "expected_type": expected_type,
        "actual_type": actual_type,
        "details": error_str,
    }


def parse_yaml_data(yaml_content: str) -> dict[str, Any]:
    """Parse YAML content and return dictionary"""
    try:
        return yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValidationException(
            ErrorCode.VAL014, field_path="yaml_data", context={"details": str(e)}
        )


def validate_date_format(date_str: str) -> bool:
    """Validate date format (YYYY-MM or YYYY-MM-DD)"""
    try:
        if len(date_str) == 7:  # YYYY-MM
            datetime.strptime(date_str, "%Y-%m")
        elif len(date_str) == 10:  # YYYY-MM-DD
            datetime.strptime(date_str, "%Y-%m-%d")
        else:
            return False
        return True
    except ValueError:
        return False


def validate_resume_data(data: dict[str, Any]):
    """Validate resume data structure and content (original validation)"""
    if "personalInfo" not in data:
        raise ValidationException(
            ErrorCode.VAL001, field_path="personalInfo", context={"section": "root"}
        )

    try:
        PersonalInfoModel(**data["personalInfo"])
    except Exception as e:
        # Parse the Pydantic validation error to provide better error messages
        error_context = parse_pydantic_error(e, "personalInfo")
        raise ValidationException(
            ErrorCode.VAL002, field_path=error_context["field"], context=error_context
        )

    # Validate dates in experience
    if "experience" in data and isinstance(data["experience"], list):
        for i, exp in enumerate(data["experience"]):
            if "startDate" in exp and not validate_date_format(exp["startDate"]):
                raise ValidationException(
                    ErrorCode.VAL006,
                    field_path=f"experience[{i}].startDate",
                    context={"date": exp["startDate"]},
                )
            if (
                "endDate" in exp
                and exp["endDate"] != "Present"
                and not validate_date_format(exp["endDate"])
            ):
                raise ValidationException(
                    ErrorCode.VAL006,
                    field_path=f"experience[{i}].endDate",
                    context={"date": exp["endDate"]},
                )


def ultra_validate_and_normalize_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    Ultra validation: Enhanced validation with normalization and LaTeX sanitization

    Args:
        data: Resume data to validate

    Returns:
        Normalized and sanitized data safe for LaTeX compilation

    Raises:
        ValueError: If validation fails with critical errors
    """
    result = enhanced_validate_resume_data(data, ValidationLevel.LENIENT)

    if not result.is_valid:
        # Collect error messages for user-friendly response
        error_messages = []
        for error in result.errors:
            if error.suggested_fix:
                error_messages.append(
                    f"{error.field_path}: {error.message}. {error.suggested_fix}"
                )
            else:
                error_messages.append(f"{error.field_path}: {error.message}")

        # Create a validation exception with aggregated errors
        raise ValidationException(
            error_code=ErrorCode.VAL010,
            field_path="data",
            context={"details": "\n".join(error_messages)},
        )

    return result.normalized_data


@app.post("/validate", tags=["Validation"])
async def validate_document_data(request: ValidationRequest):
    """
    Validate document data against the template requirements without generating the document.

    This endpoint helps you verify that your data structure is correct before attempting
    to generate a document. It supports both standard validation and ultra validation
    with enhanced sanitization.

    **Parameters:**
    - `document_type`: Type of document (resume or cover_letter)
    - `data`: Document data to validate
    - `validation_level`: "standard" for basic validation, "ultra" for enhanced validation

    **Returns:**
    - Validation results with details about any issues found
    - Suggestions for fixing validation errors
    - Confirmation if data is valid for document generation
    """
    try:
        # Convert data to dict for validation
        data_dict = (
            request.data if isinstance(request.data, dict) else request.data.dict()
        )

        if request.validation_level == "ultra":
            try:
                normalized_data = ultra_validate_and_normalize_data(data_dict)
                return {
                    "valid": True,
                    "validation_level": "ultra",
                    "message": "Data successfully validated with ultra validation",
                    "data_summary": {
                        "document_type": request.document_type,
                        "sections_found": list(normalized_data.keys()),
                        "personal_info_complete": "personalInfo" in normalized_data
                        and "name" in normalized_data.get("personalInfo", {})
                        and "email" in normalized_data.get("personalInfo", {}),
                    },
                }
            except ValidationException as e:
                return {
                    "valid": False,
                    "validation_level": "ultra",
                    "errors": [str(e)],
                    "message": "Ultra validation failed. See errors for details.",
                    "suggestions": [
                        "Fix the validation errors listed above",
                        "Consider using standard validation if ultra validation is too strict",
                    ],
                }
        else:
            try:
                validate_resume_data(data_dict)
                return {
                    "valid": True,
                    "validation_level": "standard",
                    "message": "Data successfully validated with standard validation",
                    "data_summary": {
                        "document_type": request.document_type,
                        "sections_found": list(data_dict.keys()),
                        "personal_info_complete": "personalInfo" in data_dict
                        and "name" in data_dict.get("personalInfo", {})
                        and "email" in data_dict.get("personalInfo", {}),
                    },
                }
            except ValidationException as e:
                return {
                    "valid": False,
                    "validation_level": "standard",
                    "errors": [str(e)],
                    "message": "Standard validation failed. See errors for details.",
                    "suggestions": [
                        "Fix the validation errors listed above",
                        "Ensure personalInfo section includes name and email",
                    ],
                }

    except Exception as e:
        raise InternalServerException(details=f"Validation error: {str(e)}")


@app.post("/generate", tags=["Document Generation"])
async def generate_document(
    request: DocumentRequest, background_tasks: BackgroundTasks
):
    """
    **Generate a professional resume or cover letter PDF document**

    This endpoint creates a high-quality PDF document from your structured data using LaTeX templates.
    The generated document will be professionally formatted and ready for use.

    **Request Parameters:**
    - `document_type`: Document type ("resume" or "cover_letter")
    - `template`: Template name (currently supports "classic")
    - `format`: Output format (currently only "pdf" is supported)
    - `data`: Complete document data (use /schema/{document_type} to see the expected structure)
    - `clean_up`: Whether to automatically delete the generated file after serving (default: true)
    - `ultra_validation`: Enable enhanced validation and sanitization (default: false)

    **Response:**
    - Returns a PDF file as binary data with appropriate headers
    - Filename is automatically generated based on document type and person's name

    **Tips:**
    - Use `/validate` endpoint first to check your data
    - Get the complete data schema from `/schema/{document_type}`
    - Enable ultra_validation for enhanced security and data sanitization
    """
    try:
        # Choose validation method based on request
        if request.ultra_validation:
            # Use ultra validation with normalization and sanitization
            data_to_use = ultra_validate_and_normalize_data(request.data)
        else:
            # Use original simple validation
            validate_resume_data(request.data)
            data_to_use = request.data

        # Initialize template engine
        engine = TemplateEngine()
        available_templates = engine.get_available_templates()

        # Validate document type
        if request.document_type not in available_templates:
            raise InvalidParameterException(
                parameter="document_type",
                value=request.document_type,
                context={"available_types": list(available_templates.keys())},
            )

        # Validate template exists
        if request.template not in available_templates[request.document_type]:
            raise TemplateNotFoundException(
                template_name=request.template,
                document_type=request.document_type,
                available_templates=available_templates[request.document_type],
            )

        # Validate format (currently only PDF is supported)
        if request.format.lower() != "pdf":
            raise InvalidParameterException(
                parameter="format",
                value=request.format,
                context={"supported_formats": ["pdf"]},
            )

        # Create temporary file for the output
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            output_path = tmp_file.name

        try:
            # Generate the document using the validated data
            engine.export_to_pdf(
                request.document_type, request.template, data_to_use, output_path
            )

            # Determine filename based on document type
            person_name = (
                request.data.get("personalInfo", {})
                .get("name", "output")
                .replace(" ", "_")
            )
            filename = f"{request.document_type}_{person_name}.pdf"

            # Add cleanup task if requested
            if request.clean_up:
                background_tasks.add_task(os.remove, output_path)

            # Return the generated file
            return FileResponse(
                output_path, media_type="application/pdf", filename=filename
            )
        except Exception as e:
            # Clean up the temporary file if generation fails
            if os.path.exists(output_path):
                os.remove(output_path)
            raise e

    except ValueError as e:
        raise InvalidRequestException(details=str(e))
    except ResumeCompilerException:
        # Re-raise our custom exceptions as-is
        raise
    except Exception as e:
        raise InternalServerException(details=str(e))


@app.post("/generate-yaml", tags=["Document Generation"])
async def generate_document_from_yaml(
    request: YAMLDocumentRequest, background_tasks: BackgroundTasks
):
    """
    **Generate a professional document from YAML data**

    Alternative to the JSON endpoint for users who prefer YAML format.
    Accepts the same data structure but in YAML format.

    **Request Parameters:**
    - `document_type`: Document type ("resume" or "cover_letter")
    - `template`: Template name (currently supports "classic")
    - `format`: Output format (currently only "pdf" is supported)
    - `yaml_data`: Complete document data in YAML format
    - `clean_up`: Whether to automatically delete the generated file after serving
    - `ultra_validation`: Enable enhanced validation and sanitization

    **Tips:**
    - Get YAML examples from `/schema-yaml/{document_type}`
    - YAML format is more human-readable than JSON
    - Supports the same data structure as the JSON endpoint
    """
    try:
        # Parse YAML data
        data = parse_yaml_data(request.yaml_data)

        # Choose validation method based on request
        if request.ultra_validation:
            # Use ultra validation with normalization and sanitization
            data_to_use = ultra_validate_and_normalize_data(data)
        else:
            # Use original simple validation
            validate_resume_data(data)
            data_to_use = data

        # Initialize template engine
        engine = TemplateEngine()
        available_templates = engine.get_available_templates()

        # Validate document type
        if request.document_type not in available_templates:
            raise InvalidParameterException(
                parameter="document_type",
                value=request.document_type,
                context={"available_types": list(available_templates.keys())},
            )

        # Validate template exists
        if request.template not in available_templates[request.document_type]:
            raise TemplateNotFoundException(
                template_name=request.template,
                document_type=request.document_type,
                available_templates=available_templates[request.document_type],
            )

        # Validate format (currently only PDF is supported)
        if request.format.lower() != "pdf":
            raise InvalidParameterException(
                parameter="format",
                value=request.format,
                context={"supported_formats": ["pdf"]},
            )

        # Create temporary file for the output
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            output_path = tmp_file.name

        try:
            # Generate the document using the validated data
            engine.export_to_pdf(
                request.document_type, request.template, data_to_use, output_path
            )

            # Determine filename based on document type
            person_name = (
                data_to_use.get("personalInfo", {})
                .get("name", "output")
                .replace(" ", "_")
            )
            filename = f"{request.document_type}_{person_name}.pdf"

            # Add cleanup task if requested
            if request.clean_up:
                background_tasks.add_task(os.remove, output_path)

            # Return the generated file
            return FileResponse(
                output_path, media_type="application/pdf", filename=filename
            )
        except Exception as e:
            # Clean up the temporary file if generation fails
            if os.path.exists(output_path):
                os.remove(output_path)
            raise e

    except ValueError as e:
        raise InvalidRequestException(details=str(e))
    except ResumeCompilerException:
        # Re-raise our custom exceptions as-is
        raise
    except Exception as e:
        raise InternalServerException(details=str(e))


@app.get("/templates", tags=["Templates"])
async def list_templates():
    """
    **Get all available templates organized by document type**

    Returns a complete list of all templates available in the system,
    organized by document type (resume, cover_letter).

    **Response:**
    - Dictionary with document types as keys
    - Each document type contains an array of available template names
    """
    try:
        engine = TemplateEngine()
        available_templates = engine.get_available_templates()
        return {"templates": available_templates}
    except ResumeCompilerException:
        # Re-raise our custom exceptions as-is
        raise
    except Exception as e:
        raise InternalServerException(details=str(e))


@app.get("/templates/{document_type}", tags=["Templates"])
async def list_templates_by_type(document_type: DocumentType):
    """
    **Get available templates for a specific document type**

    Returns all templates available for the specified document type.

    **Parameters:**
    - `document_type`: The type of document ("resume" or "cover_letter")

    **Response:**
    - Array of template names available for the specified document type
    """
    try:
        engine = TemplateEngine()
        available_templates = engine.get_available_templates(document_type)
        return {"templates": available_templates}
    except ValueError:
        raise ResourceNotFoundException(resource="template listing")
    except ResumeCompilerException:
        # Re-raise our custom exceptions as-is
        raise
    except Exception as e:
        raise InternalServerException(details=str(e))


@app.get("/template-info/{document_type}/{template_name}", tags=["Templates"])
async def get_template_info(document_type: DocumentType, template_name: str):
    """
    **Get detailed information about a specific template**

    Provides comprehensive information about a template including
    required fields, preview information, and template metadata.

    **Parameters:**
    - `document_type`: The type of document ("resume" or "cover_letter")
    - `template_name`: The name of the template (e.g., "classic")

    **Response:**
    - Template metadata and requirements
    - Required data fields
    - Preview information if available
    """
    try:
        engine = TemplateEngine()
        template_info = engine.get_template_info(document_type, template_name)

        # Convert preview path to URL if it exists
        if template_info.get("preview_path"):
            preview_filename = os.path.basename(template_info["preview_path"])
            template_info["preview_url"] = (
                f"/templates/{document_type}/{template_name}/{preview_filename}"
            )

        return template_info
    except ValueError:
        raise ResourceNotFoundException(resource="template listing")
    except ResumeCompilerException:
        # Re-raise our custom exceptions as-is
        raise
    except Exception as e:
        raise InternalServerException(details=str(e))


@app.get("/schema/{document_type}", tags=["Schema"])
async def get_document_schema(document_type: DocumentType):
    """
    **Get comprehensive JSON schema and examples for a document type**

    Returns the complete data structure specification including all supported
    fields, validation rules, and realistic examples for the specified document type.

    **Parameters:**
    - `document_type`: The type of document ("resume" or "cover_letter")

    **Response:**
    - Complete JSON schema with field descriptions
    - Realistic JSON example with all major sections
    - YAML example for reference
    - Field validation requirements

    **Usage:**
    Use this schema to understand exactly what data structure is expected
    for successful document generation.
    """
    try:
        schema_info = SchemaGenerator.get_schema_for_document_type(document_type)
        return {
            "document_type": document_type,
            "schema": schema_info["schema"],
            "json_example": schema_info["json_example"],
            "yaml_example": schema_info["yaml_example"],
            "description": f"Complete schema and examples for {document_type.replace('_', ' ')} generation",
        }
    except ValueError as e:
        raise InvalidParameterException(
            parameter="document_type", value=document_type, context={"error": str(e)}
        )
    except ResumeCompilerException:
        # Re-raise our custom exceptions as-is
        raise
    except Exception as e:
        raise InternalServerException(details=str(e))


@app.get("/schema-yaml/{document_type}", tags=["Schema"])
async def get_document_schema_yaml(document_type: DocumentType):
    """
    **Get comprehensive YAML examples and usage notes**

    Returns detailed YAML examples with all supported fields and
    usage guidelines for the specified document type.

    **Parameters:**
    - `document_type`: The type of document ("resume" or "cover_letter")

    **Response:**
    - Complete YAML example with all sections
    - JSON equivalent for comparison
    - Usage notes and formatting guidelines
    - Information about required vs optional fields

    **Perfect for:**
    - Users who prefer YAML over JSON
    - Understanding the complete data structure
    - Copy-paste templates for quick setup
    """
    try:
        schema_info = SchemaGenerator.get_schema_for_document_type(document_type)
        return {
            "document_type": document_type,
            "yaml_example": schema_info["yaml_example"],
            "json_example": schema_info["json_example"],
            "description": f"Comprehensive YAML example for {document_type.replace('_', ' ')} generation with all supported fields",
            "usage_notes": {
                "required_fields": ["personalInfo"],
                "optional_sections": [
                    "All sections except personalInfo are optional",
                    "Include only the sections relevant to your document",
                    "Arrays can be empty or omitted entirely",
                ],
                "date_format": "Use YYYY-MM or YYYY-MM-DD format for dates",
                "body_format": "For cover letters, body can be a string or array of paragraphs",
            },
        }
    except ValueError as e:
        raise InvalidParameterException(
            parameter="document_type", value=document_type, context={"error": str(e)}
        )
    except ResumeCompilerException:
        # Re-raise our custom exceptions as-is
        raise
    except Exception as e:
        raise InternalServerException(details=str(e))


@app.get("/health", tags=["General"])
async def health_check():
    """
    **API health check endpoint**

    Simple endpoint to verify that the API is running and responsive.
    Used for monitoring and load balancer health checks.

    **Response:**
    - Status confirmation
    - Can be used for uptime monitoring
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8501)
