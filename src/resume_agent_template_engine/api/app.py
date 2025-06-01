from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional, List
import os
import json
from resume_agent_template_engine.core.template_engine import TemplateEngine, DocumentType, OutputFormat
import tempfile
import uvicorn
from enum import Enum
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import re
from datetime import datetime

app = FastAPI(
    title="Resume and Cover Letter Template Engine API",
    description="API for generating professional resumes and cover letters from JSON data using customizable templates",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Resume Agent Template Engine"}

# DocumentType enum is now imported from template_engine

class PersonalInfo(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None

class DocumentRequest(BaseModel):
    document_type: DocumentType
    template: str
    format: str = "pdf"
    data: Dict[str, Any]
    clean_up: bool = True

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
    """Validate resume data structure and content"""
    if "personalInfo" not in data:
        raise ValueError("Personal information is required")
    
    personal_info = PersonalInfo(**data["personalInfo"])
    
    # Validate dates in experience
    if "experience" in data and isinstance(data["experience"], list):
        for exp in data["experience"]:
            if "startDate" in exp and not validate_date_format(exp["startDate"]):
                raise ValueError(f"Invalid start date format: {exp['startDate']}. Use YYYY-MM or YYYY-MM-DD")
            if "endDate" in exp and exp["endDate"] != "Present" and not validate_date_format(exp["endDate"]):
                raise ValueError(f"Invalid end date format: {exp['endDate']}. Use YYYY-MM or YYYY-MM-DD")

@app.post("/generate")
async def generate_document(request: DocumentRequest, background_tasks: BackgroundTasks):
    """
    Generate a resume or cover letter from the provided JSON data using the specified template.

    Args:
        request: DocumentRequest object containing document type, template choice, format, and data
        background_tasks: BackgroundTasks object to add cleanup tasks
        
    Returns:
        FileResponse containing the generated document
    """
    try:
        # Validate data format
        validate_resume_data(request.data)
        
        # Initialize template engine
        engine = TemplateEngine()
        available_templates = engine.get_available_templates()
        
        # Validate document type
        if request.document_type not in available_templates:
            raise HTTPException(
                status_code=404, 
                detail=f"Document type '{request.document_type}' not supported. Available types: {list(available_templates.keys())}"
            )
            
        # Validate template exists
        if request.template not in available_templates[request.document_type]:
            raise HTTPException(
                status_code=404, 
                detail=f"Template '{request.template}' not found for {request.document_type}. Available templates: {available_templates[request.document_type]}"
            )
            
        # Validate format (currently only PDF is supported)
        if request.format.lower() != "pdf":
            raise HTTPException(status_code=400, detail="Only PDF format is currently supported")
            
        # Create temporary file for the output
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
            
        try:
            # Generate the document using the new template engine
            engine.export_to_pdf(request.document_type, request.template, request.data, output_path)
            
            # Determine filename based on document type
            person_name = request.data.get('personalInfo', {}).get('name', 'output').replace(' ', '_')
            filename = f"{request.document_type}_{person_name}.pdf"
            
            # Add cleanup task if requested
            if request.clean_up:
                background_tasks.add_task(os.remove, output_path)
            
            # Return the generated file
            return FileResponse(
                output_path,
                media_type='application/pdf',
                filename=filename
            )
        except Exception as e:
            # Clean up the temporary file if generation fails
            if os.path.exists(output_path):
                os.remove(output_path)
            raise e
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/templates")
async def list_templates():
    """List all available templates by document type."""
    try:
        engine = TemplateEngine()
        available_templates = engine.get_available_templates()
        return {"templates": available_templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/templates/{document_type}")
async def list_templates_by_type(document_type: DocumentType):
    """List all available templates for a specific document type."""
    try:
        engine = TemplateEngine()
        available_templates = engine.get_available_templates(document_type)
        return {"templates": available_templates}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/template-info/{document_type}/{template_name}")
async def get_template_info(document_type: DocumentType, template_name: str):
    """Get detailed information about a specific template."""
    try:
        engine = TemplateEngine()
        template_info = engine.get_template_info(document_type, template_name)
        
        # Convert preview path to URL if it exists
        if template_info.get('preview_path'):
            preview_filename = os.path.basename(template_info['preview_path'])
            template_info['preview_url'] = f"/templates/{document_type}/{template_name}/{preview_filename}"
        
        return template_info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
                                "linkedin": {"type": "string"}
                            }
                        }
                    }
                },
                "example": {
                    "personalInfo": {
                        "name": "John Doe",
                        "email": "john@example.com"
                    }
                }
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
                                "email": {"type": "string"}
                            }
                        },
                        "content": {"type": "string"}
                    }
                },
                "example": {
                    "personalInfo": {
                        "name": "John Doe",
                        "email": "john@example.com"
                    },
                    "content": "Dear Hiring Manager,..."
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8501) 