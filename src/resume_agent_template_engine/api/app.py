from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional, List, Union, Tuple
import os
import json
import yaml
from resume_agent_template_engine.core.template_engine import (
    TemplateEngine,
    OutputFormat,
)
from resume_agent_template_engine.core.base import DocumentType
from resume_agent_template_engine.core.validation import (
    validate_resume_data as enhanced_validate_resume_data,
    ValidationLevel,
    ValidationResult,
    ValidationError,
)
from resume_agent_template_engine.core.errors import ErrorCode
from resume_agent_template_engine.core.exceptions import (
    ResumeCompilerException,
    ValidationException,
    TemplateNotFoundException,
    InvalidRequestException,
    MissingParameterException,
    InvalidParameterException,
    InternalServerException,
)
from resume_agent_template_engine.core.responses import (
    ResponseFormatter,
    create_error_response,
    create_success_response,
)
import tempfile
import uvicorn
from enum import Enum
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Resume and Cover Letter Template Engine API",
    description="API for generating professional resumes and cover letters from JSON or YAML data using customizable templates",
    version="1.0.0",
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
        internal_error, include_debug_info=False  # Set to True in development
    )

    return JSONResponse(status_code=500, content=response_data)


@app.get("/")
async def root():
    return {"message": "Welcome to Resume Agent Template Engine"}


# DocumentType enum is now imported from base module


class PersonalInfo(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    website_display: Optional[str] = None
    linkedin_display: Optional[str] = None


class DocumentRequest(BaseModel):
    document_type: DocumentType
    template: str
    format: str = "pdf"
    data: Dict[str, Any]
    clean_up: bool = True
    ultra_validation: bool = False  # Optional enhanced validation


class YAMLDocumentRequest(BaseModel):
    document_type: DocumentType
    template: str
    format: str = "pdf"
    yaml_data: str
    clean_up: bool = True
    ultra_validation: bool = False  # Optional enhanced validation


def parse_yaml_data(yaml_content: str) -> Dict[str, Any]:
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


def validate_resume_data(data: Dict[str, Any]):
    """Validate resume data structure and content (original validation)"""
    if "personalInfo" not in data:
        raise ValidationException(
            ErrorCode.VAL001, field_path="personalInfo", context={"section": "root"}
        )

    try:
        personal_info = PersonalInfo(**data["personalInfo"])
    except Exception as e:
        raise ValidationException(
            ErrorCode.VAL002, field_path="personalInfo", context={"details": str(e)}
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


def ultra_validate_and_normalize_data(data: Dict[str, Any]) -> Dict[str, Any]:
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


@app.post("/generate")
async def generate_document(
    request: DocumentRequest, background_tasks: BackgroundTasks
):
    """
    Generate a resume or cover letter from the provided JSON data using the specified template.

    Args:
        request: DocumentRequest object containing document type, template choice, format, and data
        background_tasks: BackgroundTasks object to add cleanup tasks

    Returns:
        FileResponse containing the generated document
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
            # Generate the document using normalized data
            engine.export_to_pdf(
                request.document_type, request.template, normalized_data, output_path
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


@app.post("/generate-yaml")
async def generate_document_from_yaml(
    request: YAMLDocumentRequest, background_tasks: BackgroundTasks
):
    """
    Generate a resume or cover letter from the provided YAML data using the specified template.

    Args:
        request: YAMLDocumentRequest object containing document type, template choice, format, and YAML data
        background_tasks: BackgroundTasks object to add cleanup tasks

    Returns:
        FileResponse containing the generated document
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


@app.get("/templates")
async def list_templates():
    """List all available templates by document type."""
    try:
        engine = TemplateEngine()
        available_templates = engine.get_available_templates()
        return {"templates": available_templates}
    except ResumeCompilerException:
        # Re-raise our custom exceptions as-is
        raise
    except Exception as e:
        raise InternalServerException(details=str(e))


@app.get("/templates/{document_type}")
async def list_templates_by_type(document_type: DocumentType):
    """List all available templates for a specific document type."""
    try:
        engine = TemplateEngine()
        available_templates = engine.get_available_templates(document_type)
        return {"templates": available_templates}
    except ValueError as e:
        raise ResourceNotFoundException(resource="template listing")
    except ResumeCompilerException:
        # Re-raise our custom exceptions as-is
        raise
    except Exception as e:
        raise InternalServerException(details=str(e))


@app.get("/template-info/{document_type}/{template_name}")
async def get_template_info(document_type: DocumentType, template_name: str):
    """Get detailed information about a specific template."""
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
    except ValueError as e:
        raise ResourceNotFoundException(resource="template listing")
    except ResumeCompilerException:
        # Re-raise our custom exceptions as-is
        raise
    except Exception as e:
        raise InternalServerException(details=str(e))


@app.get("/schema/{document_type}")
async def get_document_schema(document_type: DocumentType):
    """Get the expected JSON schema for a specific document type."""
    try:
        if document_type == DocumentType.RESUME:
            return {
                "schema": {
                    "type": "object",
                    "required": ["personalInfo"],
                    "properties": {
                        "personalInfo": {
                            "type": "object",
                            "required": ["name", "email"],
                            "properties": {
                                "name": {"type": "string"},
                                "email": {"type": "string"},
                                "phone": {"type": "string"},
                                "location": {"type": "string"},
                                "website": {"type": "string"},
                                "linkedin": {"type": "string"},
                                "website_display": {"type": "string"},
                                "linkedin_display": {"type": "string"},
                            },
                        }
                    },
                },
                "json_example": {
                    "personalInfo": {"name": "John Doe", "email": "john@example.com"}
                },
                "yaml_example": "personalInfo:\n  name: John Doe\n  email: john@example.com",
            }
        else:
            return {
                "schema": {
                    "type": "object",
                    "required": ["personalInfo", "content"],
                    "properties": {
                        "personalInfo": {
                            "type": "object",
                            "required": ["name", "email"],
                            "properties": {
                                "name": {"type": "string"},
                                "email": {"type": "string"},
                            },
                        },
                        "content": {"type": "string"},
                    },
                },
                "json_example": {
                    "personalInfo": {"name": "John Doe", "email": "john@example.com"},
                    "content": "Dear Hiring Manager,...",
                },
                "yaml_example": "personalInfo:\n  name: John Doe\n  email: john@example.com\ncontent: Dear Hiring Manager,...",
            }
    except ResumeCompilerException:
        # Re-raise our custom exceptions as-is
        raise
    except Exception as e:
        raise InternalServerException(details=str(e))


@app.get("/schema-yaml/{document_type}")
async def get_document_schema_yaml(document_type: DocumentType):
    """Get example YAML format for a specific document type."""
    try:
        if document_type == DocumentType.RESUME:
            example_data = {
                "personalInfo": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+1 (555) 123-4567",
                    "location": "New York, NY",
                    "website": "https://johndoe.dev",
                    "linkedin": "https://linkedin.com/in/johndoe",
                    "website_display": "https://johndoe.dev",
                    "linkedin_display": "https://linkedin.com/in/johndoe",
                },
                "professionalSummary": "Experienced software engineer with 5+ years of expertise in full-stack development.",
                "experience": [
                    {
                        "position": "Senior Software Engineer",
                        "company": "Tech Corp",
                        "startDate": "2020-01",
                        "endDate": "Present",
                        "location": "New York, NY",
                        "description": "Lead development of cloud-native applications",
                        "achievements": [
                            "Reduced system latency by 40%",
                            "Led team of 5 engineers",
                        ],
                    }
                ],
                "education": [
                    {
                        "degree": "Bachelor of Science in Computer Science",
                        "institution": "University of Technology",
                        "graduationDate": "2019-05",
                        "gpa": "3.8/4.0",
                    }
                ],
                "skills": {
                    "technical": ["Python", "JavaScript", "React", "AWS"],
                    "soft": ["Leadership", "Communication"],
                },
            }
        else:
            example_data = {
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
                "date": "March 15, 2024",
                "salutation": "Dear Ms. Smith,",
                "body": [
                    "I am writing to express my strong interest in the position.",
                    "My experience aligns perfectly with your requirements.",
                ],
                "closing": "Sincerely,\nJohn Doe",
            }

        yaml_content = yaml.dump(example_data, default_flow_style=False, indent=2)
        return {
            "yaml_example": yaml_content,
            "description": f"Example YAML format for {document_type} generation",
        }
    except ResumeCompilerException:
        # Re-raise our custom exceptions as-is
        raise
    except Exception as e:
        raise InternalServerException(details=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8501)
