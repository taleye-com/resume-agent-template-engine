import re
import os
import json
from resume_agent_template_engine.core.template_engine import TemplateEngine
import tempfile
from typing import Dict, Any, Optional
from resume_agent_template_engine.core.errors import ErrorCode
from resume_agent_template_engine.core.exceptions import TemplateNotFoundException


class TemplateEditing:
    """
    A class to generate a LaTeX resume or cover letter from JSON data.
    Now uses the new TemplateEngine architecture.

    Note: This class is maintained for backward compatibility.
    For new code, use TemplateEngine directly.
    """

    def __init__(
        self, data: Dict[str, Any], template_category: str, template_name: str
    ):
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
        self.output_path: Optional[str] = None

        # Initialize the new template engine
        self.template_engine = TemplateEngine()

        # Validate that the template exists
        available_templates = self.template_engine.get_available_templates(
            template_category
        )
        if template_name not in available_templates:
            raise TemplateNotFoundException(
                template_name=template_name,
                document_type=template_category,
                available_templates=available_templates
            )

    def generate_document(self):
        """
        Generate the document content using the template.

        Returns:
            str: The generated LaTeX content
        """
        # Use the new template engine to render the document
        return self.template_engine.render_document(
            self.template_category, self.template_name, self.data
        )

    def export_to_pdf(self, output_path: str | None = None) -> str:
        """
        Compile LaTeX content to PDF using the template.

        Args:
            output_path (str | None, optional): Path to save the PDF. If None, uses a default path.

        Returns:
            str: The path to the generated PDF
        """
        # Set default output path if not provided
        if output_path is None:
            output_path = f"{self.template_category}_{self.template_name}.pdf"

        self.output_path = output_path

        # Use the new template engine to generate the PDF
        return self.template_engine.export_to_pdf(
            self.template_category, self.template_name, self.data, output_path
        )
