import os
import importlib.util
import warnings
from resume_agent_template_engine.core.template_engine import TemplateEngine
from resume_agent_template_engine.core.errors import ErrorCode
from resume_agent_template_engine.core.exceptions import (
    FileSystemException,
    FileNotFoundException,
    TemplateNotFoundException,
    TemplateException,
)


class TemplateManager:
    """
    A class for managing and accessing different templates in the resume agent system.

    WARNING: This class is deprecated. Use TemplateEngine from resume_agent_template_engine.core.template_engine instead.
    This class is maintained for backward compatibility only.
    """

    def __init__(self, templates_dir="templates"):
        """
        Initialize the TemplateManager.

        Args:
            templates_dir (str): Path to the templates directory
        """
        warnings.warn(
            "TemplateManager is deprecated. Use TemplateEngine from "
            "resume_agent_template_engine.core.template_engine instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        self.templates_dir = templates_dir
        # Use the new TemplateEngine internally for backward compatibility
        self._engine = TemplateEngine(templates_path=templates_dir)
        self.available_templates = self._engine.get_available_templates()

    def _discover_templates(self):
        """
        Discover available templates by scanning the templates directory.

        Returns:
            dict: A dictionary mapping template categories to template names
        """
        templates = {}

        # Check if templates directory exists
        if not os.path.exists(self.templates_dir):
            raise FileNotFoundException(
                file_path=self.templates_dir,
                context={"details": "Templates directory not found"},
            )

        # Scan for template categories (resume, cover_letter, etc.)
        for category in os.listdir(self.templates_dir):
            category_path = os.path.join(self.templates_dir, category)

            # Skip files and special directories
            if not os.path.isdir(category_path) or category.startswith("__"):
                continue

            templates[category] = []

            # Scan for template styles within each category
            for template_name in os.listdir(category_path):
                template_path = os.path.join(category_path, template_name)

                # Skip files and special directories
                if not os.path.isdir(template_path) or template_name.startswith("__"):
                    continue

                # Verify it has a helper.py file and a .tex file
                helper_path = os.path.join(template_path, "helper.py")
                tex_files = [f for f in os.listdir(template_path) if f.endswith(".tex")]

                if os.path.exists(helper_path) and tex_files:
                    templates[category].append(template_name)

        return templates

    def get_available_templates(self, category=None):
        """
        Get available templates.

        Args:
            category (str, optional): The category to list templates for.
                                     If None, returns all categories and templates.

        Returns:
            dict or list: Available templates
        """
        return self._engine.get_available_templates(category)

    def load_template(self, category, template_name):
        """
        Load a template class by category and name.

        Args:
            category (str): The category of the template
            template_name (str): The name of the template

        Returns:
            class: The template class

        Raises:
            TemplateNotFoundException: If template is not found
            TemplateException: If there's an error loading the template
        """
        return self._engine.registry.load_template_class(category, template_name)

    def create_template_instance(self, category, template_name, data, config=None):
        """
        Create an instance of a template with the given data.

        Args:
            category (str): The category of the template
            template_name (str): The name of the template
            data (dict): The data for the template
            config (dict, optional): Configuration for the template

        Returns:
            TemplateInterface: An instance of the template

        Raises:
            TemplateNotFoundException: If template is not found
            TemplateException: If there's an error creating the instance
        """
        return self._engine.create_template(category, template_name, data)

    def render_template(self, category, template_name, data, config=None):
        """
        Render a template with the given data.

        Args:
            category (str): The category of the template
            template_name (str): The name of the template
            data (dict): The data for the template
            config (dict, optional): Configuration for the template

        Returns:
            str: The rendered template

        Raises:
            TemplateNotFoundException: If template is not found
            TemplateException: If there's an error rendering the template
        """
        return self._engine.render_document(category, template_name, data)

    def export_template_to_pdf(self, category, template_name, data, output_path, config=None):
        """
        Export a template to PDF.

        Args:
            category (str): The category of the template
            template_name (str): The name of the template
            data (dict): The data for the template
            output_path (str): Path for the output PDF
            config (dict, optional): Configuration for the template

        Returns:
            str: Path to the generated PDF

        Raises:
            TemplateNotFoundException: If template is not found
            TemplateException: If there's an error exporting to PDF
        """
        return self._engine.export_to_pdf(category, template_name, data, output_path)

    def validate_template_data(self, category, template_name, data):
        """
        Validate template data.

        Args:
            category (str): The category of the template
            template_name (str): The name of the template
            data (dict): The data to validate

        Returns:
            bool: True if data is valid

        Raises:
            ValidationException: If data is invalid
        """
        template = self._engine.create_template(category, template_name, data)
        return True  # If no exception is raised, data is valid

    def get_template_info(self, category, template_name):
        """
        Get information about a template.

        Args:
            category (str): The category of the template
            template_name (str): The name of the template

        Returns:
            dict: Template information
        """
        return self._engine.get_template_info(category, template_name)