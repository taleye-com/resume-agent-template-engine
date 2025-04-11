from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
import json
from resume_template_editing import TemplateEditing
from templates.template_manager import TemplateManager
import tempfile
import uvicorn
from enum import Enum
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

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

class DocumentType(str, Enum):
    RESUME = "resume"
    COVER_LETTER = "cover_letter"

class DocumentRequest(BaseModel):
    document_type: DocumentType
    template: str
    format: str = "pdf"
    data: Dict[str, Any]
    clean_up: bool = True

@app.post("/generate")
async def generate_document(request: DocumentRequest):
    """
    Generate a resume or cover letter from the provided JSON data using the specified template.
    
    Args:
        request: DocumentRequest object containing document type, template choice, format, and data
        
    Returns:
        FileResponse containing the generated document
    """
    try:
        # Initialize template manager to validate templates
        template_manager = TemplateManager()
        available_templates = template_manager.get_available_templates()
        
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
            
        # Generate the document
        template_editor = TemplateEditing(request.data, request.document_type, request.template)
        template_editor.export_to_pdf(output_path)
        
        # Determine filename based on document type
        person_name = request.data.get('personalInfo', {}).get('name', 'output').replace(' ', '_')
        filename = f"{request.document_type}_{person_name}.pdf"
        
        # Return the generated file
        return FileResponse(
            output_path,
            media_type='application/pdf',
            filename=filename
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/templates")
async def list_templates():
    """List all available templates by document type."""
    template_manager = TemplateManager()
    available_templates = template_manager.get_available_templates()
    return {"templates": available_templates}

@app.get("/templates/{document_type}")
async def list_templates_by_type(document_type: DocumentType):
    """List all available templates for a specific document type."""
    template_manager = TemplateManager()
    try:
        available_templates = template_manager.get_available_templates(document_type)
        return {"templates": available_templates}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/template-info/{document_type}/{template_name}")
async def get_template_info(document_type: DocumentType, template_name: str):
    """Get detailed information about a specific template."""
    template_manager = TemplateManager()
    available_templates = template_manager.get_available_templates()
    
    if document_type not in available_templates:
        raise HTTPException(status_code=404, detail=f"Document type '{document_type}' not found")
    
    if template_name not in available_templates[document_type]:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
    
    template_dir = os.path.join("templates", document_type, template_name)
    
    # Check for preview image
    preview_url = None
    for ext in ['.png', '.jpg', '.jpeg']:
        preview_path = os.path.join(template_dir, f"preview{ext}")
        if os.path.exists(preview_path):
            preview_url = f"/templates/{document_type}/{template_name}/preview{ext}"
            break
    
    return {
        "name": template_name,
        "document_type": document_type,
        "preview_url": preview_url,
        "description": f"{template_name.capitalize()} template for {document_type.replace('_', ' ')}",
    }

@app.get("/schema/{document_type}", 
         summary="Get JSON schema for document type",
         description="Returns the expected JSON schema structure for the specified document type, including required fields and example data.",
         responses={
             200: {
                 "description": "JSON schema for the document type",
                 "content": {
                     "application/json": {
                         "example": {
                             "schema": {
                                 "type": "object",
                                 "required": ["personalInfo"],
                                 "properties": {"personalInfo": {"type": "object"}}
                             },
                             "example": {"personalInfo": {"name": "John Doe"}}
                         }
                     }
                 }
             },
             404: {
                 "description": "Document type not found",
                 "content": {
                     "application/json": {
                         "example": {"detail": "Document type 'invalid_type' not found"}
                     }
                 }
             }
         })
async def get_document_schema(document_type: DocumentType):
    """
    Get the expected JSON schema for a specific document type.
    
    The schema defines the structure of data needed for document generation, including:
    - Required fields
    - Data types for each field
    - Nested object structures
    
    Also returns an example JSON payload that conforms to the schema.
    
    Args:
        document_type: Type of document (resume or cover_letter)
        
    Returns:
        JSON object containing the schema specification and usage example
    """
    if document_type == DocumentType.RESUME:
        return {
            "schema": {
                "type": "object",
                "required": ["personalInfo", "professionalSummary", "education", "experience", 
                            "projects", "articlesAndPublications", "achievements", 
                            "certifications", "technologiesAndSkills"],
                "properties": {
                    "personalInfo": {
                        "type": "object",
                        "required": ["name", "email", "phone", "location", "website", 
                                    "website_display", "linkedin", "linkedin_display"],
                        "properties": {
                            "name": {"type": "string"},
                            "email": {"type": "string"},
                            "phone": {"type": "string"},
                            "location": {"type": "string"},
                            "website": {"type": "string"},
                            "website_display": {"type": "string"},
                            "linkedin": {"type": "string"},
                            "linkedin_display": {"type": "string"},
                            "links": {"type": "array", "items": {"type": "object"}}
                        }
                    },
                    "professionalSummary": {"type": "string"},
                    "education": {"type": "array", "items": {"type": "object"}},
                    "experience": {"type": "array", "items": {"type": "object"}},
                    "projects": {"type": "array", "items": {"type": "object"}},
                    "articlesAndPublications": {"type": "array", "items": {"type": "object"}},
                    "achievements": {"type": "array", "items": {"type": "string"}},
                    "certifications": {"type": "array", "items": {"type": "string"}},
                    "technologiesAndSkills": {"type": "array", "items": {"type": "object"}}
                }
            },
            "example": {
                "personalInfo": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+1234567890",
                    "location": "New York, NY",
                    "website": "https://johndoe.com",
                    "website_display": "johndoe.com",
                    "linkedin": "https://linkedin.com/in/johndoe",
                    "linkedin_display": "linkedin.com/in/johndoe"
                },
                "professionalSummary": "Experienced software engineer...",
                "education": [{"degree": "BS Computer Science", "institution": "University Example"}],
                "experience": [],
                "projects": [],
                "articlesAndPublications": [],
                "achievements": [],
                "certifications": [],
                "technologiesAndSkills": []
            }
        }
    elif document_type == DocumentType.COVER_LETTER:
        return {
            "schema": {
                "type": "object",
                "required": ["personalInfo", "recipient", "date", "salutation", "body", "closing"],
                "properties": {
                    "personalInfo": {
                        "type": "object",
                        "required": ["name", "email", "phone", "location", "website", "website_display"],
                        "properties": {
                            "name": {"type": "string"},
                            "email": {"type": "string"},
                            "phone": {"type": "string"},
                            "location": {"type": "string"},
                            "website": {"type": "string"},
                            "website_display": {"type": "string"}
                        }
                    },
                    "recipient": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "title": {"type": "string"},
                            "company": {"type": "string"},
                            "address": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "date": {"type": "string"},
                    "salutation": {"type": "string"},
                    "body": {"type": "array", "items": {"type": "string"}},
                    "closing": {"type": "string"}
                }
            },
            "example": {
                "personalInfo": {
                    "name": "John Smith",
                    "email": "john.smith@example.com",
                    "phone": "(555) 123-4567",
                    "location": "New York City Metro Area",
                    "website": "https://johnsmith.com/",
                    "website_display": "johnsmith.com"
                },
                "recipient": {
                    "name": "Sarah Johnson",
                    "title": "HR Manager",
                    "company": "Tech Innovations Inc.",
                    "address": [
                        "123 Corporate Drive",
                        "New York, NY 10001"
                    ]
                },
                "date": "June 15, 2023",
                "salutation": "Dear Ms. Johnson,",
                "body": [
                    "I am writing to express my interest in the Senior Software Engineer position...",
                    "In my current role at XYZ Corp, I have successfully led the development..."
                ],
                "closing": "Sincerely,"
            }
        }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8501) 