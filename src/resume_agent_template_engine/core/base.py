"""
Base classes and interfaces for the template engine.

This module contains abstract base classes and interfaces that are used
throughout the template system to avoid circular imports.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class DocumentType(str, Enum):
    """Supported document types"""

    RESUME = "resume"
    COVER_LETTER = "cover_letter"


class TemplateInterface(ABC):
    """Abstract base class for all templates"""

    def __init__(self, data: dict[str, Any], config: dict[str, Any] = None):
        """
        Initialize template with data and configuration

        Args:
            data: Document data
            config: Template-specific configuration
        """
        self.data = data
        self.config = config or {}
        self.validate_data()

    @abstractmethod
    def validate_data(self) -> None:
        """Validate the input data"""
        pass

    @abstractmethod
    def render(self) -> str:
        """Render the template to string content"""
        pass

    @property
    @abstractmethod
    def required_fields(self) -> list[str]:
        """List of required data fields for this template"""
        pass

    @property
    @abstractmethod
    def template_type(self) -> DocumentType:
        """The document type this template handles"""
        pass

    @abstractmethod
    def export_to_pdf(self, output_path: str = "output.pdf") -> str:
        """Export the template to PDF format"""
        pass
