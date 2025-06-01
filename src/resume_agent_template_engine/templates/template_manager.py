import os
import importlib.util
import warnings
from resume_agent_template_engine.core.template_engine import TemplateEngine


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
            stacklevel=2
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
            raise FileNotFoundError(
                f"Templates directory not found: {self.templates_dir}")

        # Scan for template categories (resume, cover_letter, etc.)
        for category in os.listdir(self.templates_dir):
            category_path = os.path.join(self.templates_dir, category)

            # Skip files and special directories
            if not os.path.isdir(category_path) or category.startswith('__'):
                continue

            templates[category] = []

            # Scan for template styles within each category
            for template_name in os.listdir(category_path):
                template_path = os.path.join(category_path, template_name)

                # Skip files and special directories
                if not os.path.isdir(template_path) or template_name.startswith('__'):
                    continue

                # Verify it has a helper.py file and a .tex file
                helper_path = os.path.join(template_path, "helper.py")
                tex_files = [f for f in os.listdir(
                    template_path) if f.endswith('.tex')]

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
        
        DEPRECATED: This method is kept for backward compatibility.
        Use TemplateEngine.create_template() instead.

        Args:
            category (str): The template category (e.g., 'resume', 'cover_letter')
            template_name (str): The name of the template

        Returns:
            class: The template class
        """
        # Validate category and template name
        if category not in self.available_templates:
            raise ValueError(f"Category not found: {category}")

        if template_name not in self.available_templates[category]:
            raise ValueError(f"Template not found: {template_name}")

        # Construct the path to the helper.py file
        helper_path = os.path.join(
            self.templates_dir, category, template_name, "helper.py")

        # Load the module dynamically
        spec = importlib.util.spec_from_file_location(
            f"{category}_{template_name}", helper_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find the class in the module
        # First try conventional name format: ModernCoverLetterTemplate
        class_name_options = []

        # For categories with underscores like "cover_letter", convert to CamelCase
        if "_" in category:
            category_camel = ''.join(x.capitalize()
                                     for x in category.split('_'))
        else:
            category_camel = category.capitalize()

        # Try multiple naming patterns
        class_name_options = [
            # ModernCoverLetterTemplate
            f"{template_name.capitalize()}{category_camel}Template",
            # CoverLetterModernTemplate
            f"{category_camel}{template_name.capitalize()}Template",
            # ModernTemplate
            f"{template_name.capitalize()}Template"
        ]

        # Try each possible class name
        for class_name in class_name_options:
            if hasattr(module, class_name):
                return getattr(module, class_name)

        # If we get here, no matching class was found
        class_list = [name for name in dir(module) if not name.startswith(
            '_') and name.endswith('Template')]
        if class_list:
            # If we found any template class, return the first one
            return getattr(module, class_list[0])

        raise ValueError(
            f"Template class not found in {helper_path}. Tried: {', '.join(class_name_options)}")

    def create_template(self, category, template_name, data):
        """
        Create a template instance with the provided data.

        Args:
            category (str): The template category (e.g., 'resume', 'cover_letter')
            template_name (str): The name of the template
            data (dict): The data to initialize the template with

        Returns:
            object: An instance of the template class
        """
        return self._engine.create_template(category, template_name, data)

    def generate_pdf(self, category, template_name, data, output_path=None):
        """
        Generate a PDF from a template.

        Args:
            category (str): The template category (e.g., 'resume', 'cover_letter')
            template_name (str): The name of the template
            data (dict): The data to generate the document with
            output_path (str, optional): Path to save the PDF. If None, uses a default path.

        Returns:
            str: The path to the generated PDF
        """
        # Set default output path if not provided
        if output_path is None:
            output_path = f"{category}_{template_name}.pdf"

        # Use the new template engine
        return self._engine.export_to_pdf(category, template_name, data, output_path)
