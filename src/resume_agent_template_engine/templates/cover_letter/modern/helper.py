import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import tempfile
import subprocess
import logging
from datetime import datetime

from ....core.template_engine import TemplateInterface, DocumentType
from ....core.macro_system import MacroRegistry, MacroProcessor
from ....core.template_inheritance import BaseTemplate
from ....core.base_validator import DataValidator
from ....core.common_utils import StringUtils, SubprocessRunner, TemporaryDirectory

logger = logging.getLogger(__name__)


class ModernCoverLetterTemplate(BaseTemplate, TemplateInterface):
    """Modern cover letter template - fast compiler without content enhancement"""

    def __init__(self, data: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        """Initialize modern cover letter template"""
        super().__init__(data, config)

        # Set up macro system
        self.macro_registry = MacroRegistry()
        self.macro_processor = MacroProcessor(self.macro_registry)

        # Template directory
        self.template_dir = Path(__file__).parent

    @property
    def template_type(self) -> DocumentType:
        """Return document type"""
        return DocumentType.COVER_LETTER

    @property
    def required_fields(self) -> List[str]:
        """Return required data fields"""
        return [
            "personalInfo.name",
            "personalInfo.email",
            "recipient.company",
            "content.opening",
            "content.body",
            "content.closing",
        ]

    def validate_data(self) -> None:
        """Validate that required data fields are present"""
        validator = DataValidator()
        issues = validator.validate(self.data, "cover_letter")

        # Convert issues to errors for backward compatibility
        errors = [str(issue) for issue in issues if issue.severity.value == "error"]

        if errors:
            raise ValueError("Data validation failed: " + "; ".join(errors))

    def _format_date(self, date_str: Optional[str] = None) -> str:
        """Format date for display"""
        if date_str:
            parsed_date = StringUtils.parse_date_flexible(date_str)
            if parsed_date:
                return StringUtils.format_datetime(parsed_date)
            return date_str

        return StringUtils.format_datetime()

    def _format_address(self, address_info: Dict[str, Any]) -> str:
        """Format address information"""
        parts = []

        if address_info.get("street"):
            parts.append(address_info["street"])

        city_state_zip = []
        if address_info.get("city"):
            city_state_zip.append(address_info["city"])
        if address_info.get("state"):
            city_state_zip.append(address_info["state"])
        if address_info.get("zipCode"):
            city_state_zip.append(address_info["zipCode"])

        if city_state_zip:
            parts.append(" ".join(city_state_zip))

        if address_info.get("country") and address_info["country"].lower() not in [
            "usa",
            "us",
            "united states",
        ]:
            parts.append(address_info["country"])

        return " \\\\ ".join(parts)

    def _generate_salutation(self, recipient: Dict[str, Any]) -> str:
        """Generate appropriate salutation"""
        hiring_manager = recipient.get("hiringManager", "")

        if hiring_manager:
            return f"Dear {hiring_manager},"

        # Default professional salutation
        return "Dear Hiring Manager,"

    def _format_body_paragraphs(self, body_content: Any) -> str:
        """Format body paragraphs with proper spacing"""
        if isinstance(body_content, list):
            formatted_paragraphs = []
            for paragraph in body_content:
                if isinstance(paragraph, str):
                    formatted_paragraphs.append(paragraph.strip())
                elif isinstance(paragraph, dict):
                    # Handle structured paragraph data
                    if "text" in paragraph:
                        formatted_paragraphs.append(paragraph["text"].strip())

            return "\n\n".join(formatted_paragraphs)

        elif isinstance(body_content, str):
            # Split on double newlines to preserve paragraph structure
            paragraphs = [p.strip() for p in body_content.split("\n\n") if p.strip()]
            return "\n\n".join(paragraphs)

        return str(body_content)

    def render_blocks(self) -> Dict[str, str]:
        """Render template blocks for inheritance"""
        personal_info = self.data.get("personalInfo", {})
        recipient = self.data.get("recipient", {})
        content = self.data.get("content", {})

        blocks = {
            "header": self._render_header_block(personal_info),
            "date": self._render_date_block(),
            "recipient": self._render_recipient_block(recipient),
            "salutation": self._render_salutation_block(recipient),
            "body": self._render_body_block(content),
            "closing": self._render_closing_block(content),
            "signature": self._render_signature_block(personal_info),
        }

        return blocks

    def _render_header_block(self, personal_info: Dict[str, Any]) -> str:
        """Render header with contact information"""
        name = personal_info.get("name", "")
        email = personal_info.get("email", "")
        phone = personal_info.get("phone", "")
        address = personal_info.get("address", {})

        header_parts = [rf"\textbf{{\Large {name}}}"]

        contact_info = []
        if email:
            contact_info.append(rf"\href{{mailto:{email}}}{{{email}}}")
        if phone:
            contact_info.append(phone)

        if isinstance(address, dict) and address:
            address_str = self._format_address(address)
            if address_str:
                contact_info.append(address_str)
        elif isinstance(address, str) and address:
            contact_info.append(address)

        if contact_info:
            header_parts.append(" \\\\ ".join(contact_info))

        return "\n\\\\\n".join(header_parts)

    def _render_date_block(self) -> str:
        """Render date block"""
        date_str = self.data.get("date")
        formatted_date = self._format_date(date_str)
        return rf"\begin{{flushright}}{formatted_date}\end{{flushright}}"

    def _render_recipient_block(self, recipient: Dict[str, Any]) -> str:
        """Render recipient address block"""
        parts = []

        if recipient.get("hiringManager"):
            parts.append(recipient["hiringManager"])

        if recipient.get("company"):
            parts.append(recipient["company"])

        if recipient.get("address"):
            if isinstance(recipient["address"], dict):
                address_str = self._format_address(recipient["address"])
                if address_str:
                    parts.append(address_str)
            elif isinstance(recipient["address"], str):
                parts.append(recipient["address"])

        return " \\\\ ".join(parts)

    def _render_salutation_block(self, recipient: Dict[str, Any]) -> str:
        """Render salutation"""
        return self._generate_salutation(recipient)

    def _render_body_block(self, content: Dict[str, Any]) -> str:
        """Render body content - pure compilation without enhancement"""
        opening = content.get("opening", "")
        body = content.get("body", "")

        # Format opening paragraph
        formatted_opening = opening.strip()

        # Format body paragraphs
        formatted_body = self._format_body_paragraphs(body)

        return f"{formatted_opening}\n\n{formatted_body}"

    def _render_closing_block(self, content: Dict[str, Any]) -> str:
        """Render closing paragraph"""
        closing = content.get("closing", "")
        return closing.strip()

    def _render_signature_block(self, personal_info: Dict[str, Any]) -> str:
        """Render signature block"""
        name = personal_info.get("name", "")
        return rf"""
\vspace{{1cm}}

Sincerely,

\vspace{{1.5cm}}

{name}"""

    def _render_with_blocks(self, blocks: Dict[str, str]) -> str:
        """Render complete template with blocks"""
        # Read the main template file
        template_file = self.template_dir / "modern.tex"

        try:
            with open(template_file, "r", encoding="utf-8") as f:
                template_content = f.read()
        except FileNotFoundError:
            # Fallback to embedded template
            template_content = self._get_embedded_template()

        # Replace block placeholders
        for block_name, block_content in blocks.items():
            placeholder = f"{{{{ {block_name} }}}}"
            template_content = template_content.replace(placeholder, block_content)

        return template_content

    def render(self) -> str:
        """Render the complete cover letter"""
        self.validate_data()

        blocks = self.render_blocks()
        return self._render_with_blocks(blocks)

    def _get_embedded_template(self) -> str:
        """Get embedded template as fallback"""
        return r"""
\documentclass[11pt,letterpaper]{article}

% Packages
\usepackage[margin=1in]{geometry}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{microtype}
\usepackage{hyperref}
\usepackage{xcolor}

% Hyperlink setup
\hypersetup{
    colorlinks=true,
    linkcolor=black,
    urlcolor=blue,
    citecolor=black
}

% Remove page numbering
\pagestyle{empty}

% Reduce paragraph indentation
\setlength{\parindent}{0pt}
\setlength{\parskip}{1em}

\begin{document}

% Header
{{ header }}

\vspace{1em}

% Date
{{ date }}

\vspace{1em}

% Recipient
{{ recipient }}

\vspace{1em}

% Salutation
{{ salutation }}

\vspace{0.5em}

% Opening and Body
{{ body }}

\vspace{0.5em}

% Closing
{{ closing }}

% Signature
{{ signature }}

\end{document}
"""

    def export_to_pdf(self, output_path: str) -> str:
        """Export cover letter to PDF"""
        latex_content = self.render()

        # Add macro definitions
        macro_preamble = self.macro_processor.generate_macro_preamble(latex_content)
        if macro_preamble:
            # Insert after documentclass
            doc_class_pos = latex_content.find("\\begin{document}")
            if doc_class_pos != -1:
                latex_content = (
                    latex_content[:doc_class_pos]
                    + macro_preamble
                    + "\n\n"
                    + latex_content[doc_class_pos:]
                )

        with TemporaryDirectory(prefix="cover_letter_") as temp_dir:
            tex_file = temp_dir / "cover_letter.tex"

            # Write LaTeX content
            from ....core.common_utils import FileOperations

            if not FileOperations.write_file_safe(tex_file, latex_content):
                raise RuntimeError("Failed to write LaTeX file")

            # Compile LaTeX to PDF using common utility
            result = SubprocessRunner.run_latex_compilation(
                tex_file, "pdflatex", str(temp_dir)
            )

            if not result["success"]:
                error_msg = f"LaTeX compilation failed: {result.get('error_message', result.get('stderr', 'Unknown error'))}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            if result["pdf_created"]:
                # Copy to output location using common utility
                if FileOperations.safe_copy(result["pdf_path"], output_path):
                    return output_path
                else:
                    raise RuntimeError("Failed to copy PDF to output location")
            else:
                raise RuntimeError("PDF file was not generated")


# Export the template class
CoverLetterTemplate = ModernCoverLetterTemplate
