from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import json
from resume_template_editing import TemplateEditing
import tempfile
import uvicorn

app = FastAPI(
    title="Resume AI Agent Template Engine API",
    description="API for generating professional resumes from JSON data using customizable templates",
    version="1.0.0"
)

class ResumeRequest(BaseModel):
    template: str
    format: str = "pdf"
    data: Dict[str, Any]

@app.post("/generate")
async def generate_resume(request: ResumeRequest):
    """
    Generate a resume from the provided JSON data using the specified template.
    
    Args:
        request: ResumeRequest object containing template choice, format, and resume data
        
    Returns:
        FileResponse containing the generated resume
    """
    try:
        # Validate template exists
        templates_dir = "templates"
        if not os.path.exists(os.path.join(templates_dir, f"{request.template}.tex")):
            raise HTTPException(status_code=404, detail=f"Template '{request.template}' not found")
            
        # Validate format (currently only PDF is supported)
        if request.format.lower() != "pdf":
            raise HTTPException(status_code=400, detail="Only PDF format is currently supported")
            
        # Create temporary file for the output
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            output_path = tmp_file.name
            
        # Generate the resume
        template_editor = TemplateEditing(request.data, request.template)
        template_editor.export_to_pdf(output_path)
        
        # Return the generated file
        return FileResponse(
            output_path,
            media_type='application/pdf',
            filename=f"resume_{request.data.get('personalInfo', {}).get('name', 'output').replace(' ', '_')}.pdf"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/templates")
async def list_templates():
    """List all available resume templates."""
    templates_dir = "templates"
    templates = []
    for file in os.listdir(templates_dir):
        if file.endswith(".tex"):
            templates.append(file[:-4])  # Remove .tex extension
    return {"templates": templates}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8501) 