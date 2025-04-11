import re
import os
import json
from resume_agent_template_engine.templates.template_manager import TemplateManager
import tempfile

class TemplateEditing:
    """
    A class to generate a LaTeX resume or cover letter from JSON data based on new requirements.
    Uses the new template management system.
    """

    def __init__(self, data: dict, template_category: str, template_name: str):
        """
        Initialize the TemplateEditing class.

        Args:
            data (dict): The JSON data containing document information.
            template_category (str): The category of the template (e.g., 'resume', 'cover_letter').
            template_name (str): The name of the template style.
        """
        self.data = data
        self.template_category = template_category
        self.template_name = template_name
        self.output_path = None
        
        # Initialize the template manager
        self.template_manager = TemplateManager()
        
        # Validate that the template exists
        available_templates = self.template_manager.get_available_templates(template_category)
        if template_name not in available_templates:
            raise ValueError(f"Template '{template_name}' not found in category '{template_category}'")

    def generate_document(self):
        """
        Generate the document content using the template.
        
        Returns:
            str: The generated LaTeX content
        """
        # Create a template instance
        template = self.template_manager.create_template(
            self.template_category, 
            self.template_name, 
            self.data
        )
        
        # Generate content based on template category
        if self.template_category == 'resume':
            return template.generate_resume()
        elif self.template_category == 'cover_letter':
            return template.generate_cover_letter()
        else:
            raise ValueError(f"Unsupported template category: {self.template_category}")

    def export_to_pdf(self, output_path: str = None):
        """
        Compile LaTeX content to PDF using the template.
        
        Args:
            output_path (str, optional): Path to save the PDF. If None, uses a default path.
        
        Returns:
            str: The path to the generated PDF
        """
        # Set default output path if not provided
        if output_path is None:
            output_path = f"{self.template_category}_{self.template_name}.pdf"
        
        self.output_path = output_path
        
        # Use the template manager to generate the PDF
        return self.template_manager.generate_pdf(
            self.template_category,
            self.template_name,
            self.data,
            output_path
        )