import re
import subprocess
import os
import tempfile
from typing import Dict, Any, List
from resume_agent_template_engine.core.template_engine import (
    TemplateInterface,
    DocumentType,
)
from resume_agent_template_engine.core.errors import ErrorCode
from resume_agent_template_engine.core.exceptions import (
    FileSystemException,
    FileNotFoundException,
    ValidationException,
    TemplateRenderingException,
    LaTeXCompilationException,
    PDFGenerationException,
    DependencyException
)


class ClassicCoverLetterTemplate(TemplateInterface):
    """
    Helper class for generating a Classic LaTeX cover letter from JSON data.
    Handles special characters: &, %, $, #
    """

    def __init__(self, data: Dict[str, Any], config: Dict[str, Any] = None) -> None:
        """
        Initialize the ClassicCoverLetterTemplate class.

        Args:
            data (dict): The JSON data containing cover letter information.
            config (dict): Template-specific configuration.
        """
        # Initialize parent class
        super().__init__(data, config)

        self.data = self.replace_special_chars(data)
        self.output_path: str = "output.pdf"
        self.template_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_path = os.path.join(self.template_dir, "classic.tex")

        try:
            with open(self.template_path, "r", encoding="utf-8") as f:
                self.template = f.read()
        except FileNotFoundError as e:
            raise FileNotFoundException(
                file_path=self.template_path,
                context={"details": str(e)}
            ) from e
        except PermissionError as e:
            raise FileSystemException(
                error_code=ErrorCode.FIL002,
                file_path=self.template_path,
                context={"details": str(e)}
            ) from e
        except Exception as e:
            raise FileSystemException(
                error_code=ErrorCode.FIL006,
                file_path=self.template_path,
                context={"details": f"Error reading template file: {e}"}
            ) from e

    def validate_data(self):
        """Validate essential data fields with consistent error handling"""
        self._validate_required_sections()
        self._validate_personal_info()
        self._validate_document_specific_fields()

    def _validate_required_sections(self):
        """Validate document-type specific required sections"""
        required_sections = ["personalInfo", "body"]
        for section in required_sections:
            if section not in self.data:
                raise ValidationException(
                    error_code=ErrorCode.VAL001,
                    field_path=section,
                    context={"section": "cover letter data"}
                )

    def _validate_personal_info(self):
        """Validate essential personal info fields consistently"""
        required_personal_info = ["name", "email"]
        for field in required_personal_info:
            if field not in self.data["personalInfo"]:
                raise ValidationException(
                    error_code=ErrorCode.VAL001,
                    field_path=f"personalInfo.{field}",
                    context={"section": "personalInfo"}
                )

    def _validate_document_specific_fields(self):
        """Validate cover letter-specific fields"""
        # Validate recipient if present
        if "recipient" in self.data and not isinstance(self.data["recipient"], dict):
            raise ValidationException(
                error_code=ErrorCode.VAL002,
                field_path="recipient",
                context={"expected_type": "dict", "actual_type": type(self.data["recipient"]).__name__}
            )

        # Body can be either string or list of paragraphs
        if not isinstance(self.data["body"], (str, list)):
            raise ValidationException(
                error_code=ErrorCode.VAL002,
                field_path="body",
                context={"expected_type": "string or list", "actual_type": type(self.data["body"]).__name__}
            )

    def replace_special_chars(self, data):
        """Recursively replace special LaTeX characters in strings."""
        if isinstance(data, str):
            return (
                data.replace("&", r"\&")
                .replace("%", r"\%")
                .replace("$", r"\$")
                .replace("#", r"\#")
            )
        if isinstance(data, list):
            return [self.replace_special_chars(item) for item in data]
        if isinstance(data, dict):
            return {k: self.replace_special_chars(v) for k, v in data.items()}
        return data

    def get_field_with_fallback(self, obj: dict, primary_field: str, fallback_fields: List[str] = None, default_value: Any = None):
        """Get field with fallback options and default value"""
        if primary_field in obj and obj[primary_field]:
            return obj[primary_field]

        if fallback_fields:
            for fallback in fallback_fields:
                if fallback in obj and obj[fallback]:
                    return obj[fallback]

        return default_value

    def get_field_with_smart_default(self, path: str, default_value: Any = None, smart_default_fn=None):
        """Get field with smart defaults"""
        keys = path.split('.')
        obj = self.data

        try:
            for key in keys:
                obj = obj[key]
            return obj if obj else (smart_default_fn() if smart_default_fn else default_value)
        except (KeyError, TypeError):
            return smart_default_fn() if smart_default_fn else default_value

    def generate_section_with_header(self, section_name: str, content_generator_fn, header_name: str = None):
        """Generate section with conditional header"""
        content = content_generator_fn()
        if content:
            header = header_name or section_name.replace('_', ' ').title()
            return f"\\section{{{header}}}\n{content}"
        return ""
    
    def generate_personal_info(self) -> str:
        """
        Generate the header block dynamically from self.data['personalInfo'].
        """
        info = self.data["personalInfo"]
        header_lines = []
        header_lines.append(r"\begin{header}")
        header_lines.append(r"    \fontsize{25pt}{25pt}\selectfont " + info["name"])
        header_lines.append(r"    \vspace{2pt}")
        header_lines.append(r"    \normalsize")

        # Build the contact line pieces with optional fields
        parts = []

        # Only add location if it exists
        if info.get("location"):
            parts.append(r"\mbox{ " + info["location"] + r" }")

        # Email is required, so always add it
        parts.append(r"\mbox{\href{mailto:" + info["email"] + r"}{" + info["email"] + r"}}")

        # Only add phone if it exists
        if info.get("phone"):
            parts.append(r"\mbox{\href{tel:" + info["phone"] + r"}{" + info["phone"] + r"}}")

        # Add optional social links only if both URL and display text exist
        if info.get("website") and info.get("website_display"):
            parts.append(r"\mbox{\href{" + info["website"] + r"}{" + info["website_display"] + r"}}")
        if info.get("linkedin") and info.get("linkedin_display"):
            parts.append(r"\mbox{\href{" + info["linkedin"] + r"}{" + info["linkedin_display"] + r"}}")
        if info.get("github") and info.get("github_display"):
            parts.append(r"\mbox{\href{" + info["github"] + r"}{" + info["github_display"] + r"}}")
        if info.get("twitter") and info.get("twitter_display"):
            parts.append(r"\mbox{\href{" + info["twitter"] + r"}{" + info["twitter_display"] + r"}}")
        if info.get("x") and info.get("x_display"):
            parts.append(r"\mbox{\href{" + info["x"] + r"}{" + info["x_display"] + r"}}")

        # Join them with the \AND separators exactly as before
        contact_line = " \\kern 3pt \\AND \\kern 3pt ".join(parts)
        header_lines.append(r"    " + contact_line)
        header_lines.append(r"\end{header}")
        return "\n".join(header_lines)


    def generate_recipient_address(self):
        """Format recipient information with LaTeX line breaks."""
        # Return empty if no recipient data
        if not self.data.get("recipient"):
            return ""

        recipient = self.data["recipient"]
        lines = []

        # Add recipient information in logical order
        if recipient.get("name"):
            lines.append(recipient["name"])
        if recipient.get("title"):
            lines.append(recipient["title"])
        if recipient.get("company"):
            lines.append(recipient["company"])
        if recipient.get("department"):
            lines.append(recipient["department"])

        # Handle different address formats
        if "address" in recipient:
            address = recipient["address"]
            if isinstance(address, list):
                lines.extend(filter(None, address))
            elif isinstance(address, str):
                lines.append(address)

        # Add individual address components if structured
        address_components = []
        if recipient.get("street"):
            address_components.append(recipient["street"])
        if recipient.get("city") or recipient.get("state") or recipient.get("zip"):
            city_state_zip = ", ".join(filter(None, [
                recipient.get("city"),
                recipient.get("state"),
                recipient.get("zip")
            ]))
            if city_state_zip:
                address_components.append(city_state_zip)
        if recipient.get("country"):
            address_components.append(recipient["country"])

        lines.extend(address_components)

        # Filter out empty lines and join with LaTeX line break
        return " \\\\\n".join(filter(None, lines))

    def generate_body_content(self):
        """Generate formatted body content supporting multiple formats."""
        body = self.data.get("body", "")

        if isinstance(body, str):
            # Single string body - split into paragraphs if needed
            if "\n\n" in body:
                return body.replace("\n\n", "\n\n")
            return body
        elif isinstance(body, list):
            # List of paragraphs
            return "\n\n".join(str(paragraph) for paragraph in body if paragraph)
        else:
            # Fallback for unexpected format
            return str(body)

    def generate_salutation(self):
        """Generate appropriate salutation with smart defaults."""
        salutation = self.data.get("salutation", "")

        if salutation:
            return salutation

        # Smart default based on recipient
        recipient = self.data.get("recipient", {})
        if recipient.get("name"):
            return f"Dear {recipient['name']},"
        elif recipient.get("title"):
            return f"Dear {recipient['title']},"
        elif recipient.get("company"):
            return f"Dear Hiring Manager at {recipient['company']},"
        else:
            return "Dear Hiring Manager,"

    def generate_closing(self):
        """Generate appropriate closing with smart defaults."""
        closing = self.data.get("closing", "")

        if closing:
            return closing

        # Smart default
        return "Sincerely,"

    def generate_date(self):
        """Generate date with smart formatting."""
        from datetime import datetime

        date = self.data.get("date", "")

        if date:
            return date

        # Auto-generate current date if not provided
        return datetime.now().strftime("%B %d, %Y")

    def generate_cover_letter(self):
        """Generate the final LaTeX cover letter by replacing placeholders."""
        info = self.data["personalInfo"]

        # Content replacements using smart generation methods
        content_replacements = {
            "{{personal_info}}": self.generate_personal_info(),
            "{{recipient_address}}": self.generate_recipient_address(),
            "{{date}}": self.generate_date(),
            "{{salutation}}": self.generate_salutation(),
            "{{body_content}}": self.generate_body_content(),
            "{{closing}}": self.generate_closing(),
            "{{name}}": info["name"],  # Fix missing name placeholder
        }

        cover_letter = self.template
        for placeholder, content in content_replacements.items():
            cover_letter = cover_letter.replace(placeholder, content)

        # Check for unreplaced placeholders
        if re.search(r"{{.*?}}", cover_letter):
            unreplaced_matches = re.findall(r"{{(.*?)}}", cover_letter)
            raise TemplateRenderingException(
                template_name="classic",
                details=f"Unreplaced placeholders detected: {', '.join(unreplaced_matches)}"
            )

        return cover_letter

    def render(self) -> str:
        """Render the template to LaTeX content"""
        return self.generate_cover_letter()

    @property
    def required_fields(self) -> List[str]:
        """List of required data fields for this template"""
        return ["personalInfo", "body"]  # Only truly essential fields

    @property
    def template_type(self) -> DocumentType:
        """The document type this template handles"""
        return DocumentType.COVER_LETTER

    def export_to_pdf(self, output_path: str = "output.pdf") -> str:
        """Compile LaTeX content to PDF using pdflatex"""
        self.output_path = output_path
        content = self.generate_cover_letter()

        # Ensure pdflatex is in PATH by adding common TeX installation paths
        env = os.environ.copy()
        tex_paths = [
            "/Library/TeX/texbin",
            "/usr/local/texlive/2025basic/bin/universal-darwin",
            "/usr/local/texlive/2024/bin/universal-darwin",
            "/usr/local/bin",
            "/opt/homebrew/bin"
        ]

        current_path = env.get("PATH", "")
        for tex_path in tex_paths:
            if os.path.exists(tex_path) and tex_path not in current_path:
                current_path = f"{tex_path}:{current_path}"
        env["PATH"] = current_path

        with tempfile.TemporaryDirectory() as tmpdir:
            tex_path = os.path.join(tmpdir, "temp.tex")
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(content)

            try:
                subprocess.run(
                    [
                        "pdflatex",
                        "-interaction=nonstopmode",
                        f"-output-directory={tmpdir}",
                        tex_path,
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                    env=env,
                )
                subprocess.run(
                    [
                        "pdflatex",
                        "-interaction=nonstopmode",
                        f"-output-directory={tmpdir}",
                        tex_path,
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                    env=env,
                )
            except subprocess.CalledProcessError as e:
                raise LaTeXCompilationException(
                    details="PDF compilation failed. Ensure pdflatex is installed.",
                    template_name="classic",
                    context={"return_code": e.returncode}
                ) from e
            except FileNotFoundError as e:
                raise DependencyException(
                    dependency="pdflatex",
                    context={
                        "details": "pdflatex not found. Please install BasicTeX or MacTeX:\n"
                                  "brew install --cask basictex\n"
                                  "Then restart your terminal or run: eval \"$(/usr/libexec/path_helper)\""
                    }
                ) from e

            pdf_path = os.path.join(tmpdir, "temp.pdf")
            if os.path.exists(pdf_path):
                os.replace(pdf_path, output_path)
            else:
                raise PDFGenerationException(
                    details="PDF output not generated",
                    template_name="classic"
                )

        return output_path
