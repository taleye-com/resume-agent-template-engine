"""
UI Configuration for Resume Agent Template Engine

This module contains configuration settings for the Streamlit UI application.
It handles environment variables, paths, and UI-specific settings.
"""

import os
from typing import Any


class UIConfig:
    """Configuration class for the UI application"""

    # Server Configuration
    UI_HOST = os.getenv("UI_HOST", "0.0.0.0")
    UI_PORT = int(os.getenv("UI_PORT", "8502"))
    API_HOST = os.getenv("API_HOST", "localhost")
    API_PORT = int(os.getenv("API_PORT", "8501"))

    # UI Settings
    PAGE_TITLE = "Resume Agent Template Engine"
    PAGE_ICON = "📄"
    LAYOUT = "wide"
    INITIAL_SIDEBAR_STATE = "expanded"

    # File Upload Settings
    MAX_FILE_SIZE_MB = 10
    ALLOWED_EXTENSIONS = [".pdf", ".tex", ".txt"]

    # Session State Keys
    SESSION_KEYS = {
        "generated_file": "generated_file",
        "num_experiences": "num_experiences",
        "num_education": "num_education",
        "num_projects": "num_projects",
        "user_data": "user_data",
    }

    # Form Validation
    REQUIRED_FIELDS = ["name", "email"]
    DATE_FORMAT = "%Y-%m"

    # Template Settings
    DEFAULT_TEMPLATE_TYPE = "resume"
    TEMPLATE_PREVIEW_SIZE = (300, 400)

    # Error Messages
    ERROR_MESSAGES = {
        "missing_required": "Please fill in all required fields (marked with *)",
        "invalid_email": "Please enter a valid email address",
        "invalid_date": "Please use YYYY-MM format for dates",
        "template_not_found": "Selected template is not available",
        "generation_failed": "Failed to generate document. Please check your data and try again.",
        "file_too_large": f"File size must be less than {MAX_FILE_SIZE_MB}MB",
    }

    # Success Messages
    SUCCESS_MESSAGES = {
        "document_generated": "✅ Document generated successfully!",
        "template_loaded": "Template loaded successfully",
        "data_saved": "Your data has been saved",
    }

    # UI Text
    UI_TEXT = {
        "title": "📄 Resume Agent Template Engine",
        "subtitle": "Generate professional resumes and cover letters with customizable templates",
        "navigation_header": "Navigation",
        "pages": {
            "generate": "Generate Document",
            "gallery": "Template Gallery",
            "schema": "Data Schema",
            "about": "About",
        },
    }

    # Development Settings
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    RELOAD_ON_CHANGE = os.getenv("RELOAD_ON_CHANGE", "false").lower() == "true"

    @classmethod
    def get_api_url(cls) -> str:
        """Get the full API base URL"""
        return f"http://{cls.API_HOST}:{cls.API_PORT}"

    @classmethod
    def get_streamlit_config(cls) -> dict[str, Any]:
        """Get Streamlit page configuration"""
        return {
            "page_title": cls.PAGE_TITLE,
            "page_icon": cls.PAGE_ICON,
            "layout": cls.LAYOUT,
            "initial_sidebar_state": cls.INITIAL_SIDEBAR_STATE,
        }

    @classmethod
    def get_server_config(cls) -> dict[str, Any]:
        """Get server configuration for launching Streamlit"""
        return {
            "host": cls.UI_HOST,
            "port": cls.UI_PORT,
            "debug": cls.DEBUG,
            "reload": cls.RELOAD_ON_CHANGE,
        }

    @classmethod
    def validate_environment(cls) -> bool:
        """Validate that all required environment variables are set"""
        # Add any required environment validation here
        return True


# Global configuration instance
ui_config = UIConfig()
