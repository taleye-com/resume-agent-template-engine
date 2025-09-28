"""
Universal Template Engine

This module provides a single template class that can generate any document
type based on template registry definitions, replacing all individual helper.py files.
"""

import os
import re
import tempfile
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path

from .template_engine import TemplateInterface
from .template_registry import (
    TemplateDefinition,
    SectionDefinition,
    FieldMapping,
    SectionType,
    DocumentType,
    get_template_definition
)
from .errors import ErrorCode
from .exceptions import (
    FileSystemException,
    FileNotFoundException,
    ValidationException,
    TemplateRenderingException,
    LaTeXCompilationException,
    PDFGenerationException,
    DependencyException
)


class UniversalTemplate(TemplateInterface):
    """
    Universal template class that can generate any document type
    based on template registry definitions.

    This replaces all individual helper.py template classes.
    """

    def __init__(
        self,
        document_type: str,
        template_name: str,
        data: Dict[str, Any],
        config: Dict[str, Any] = None
    ):
        """
        Initialize universal template

        Args:
            document_type: Type of document (resume, cover_letter)
            template_name: Name of template (classic, modern, etc.)
            data: Document data
            config: Template configuration
        """
        self.document_type = document_type
        self.template_name = template_name
        self.template_def = get_template_definition(document_type, template_name)

        # Initialize base class
        super().__init__(data, config)

        # Process data with special character escaping
        self.data = self.replace_special_chars(data)
        self.output_path: str = "output.pdf"

        # Load template file
        self.template_dir = self._get_template_directory()
        self.template_path = self.template_dir / self.template_def.template_file

        try:
            with open(self.template_path, "r", encoding="utf-8") as f:
                self.template = f.read()
        except FileNotFoundError as e:
            raise FileNotFoundException(
                file_path=str(self.template_path),
                context={"details": str(e)}
            ) from e
        except PermissionError as e:
            raise FileSystemException(
                error_code=ErrorCode.FIL002,
                file_path=str(self.template_path),
                context={"details": str(e)}
            ) from e
        except Exception as e:
            raise FileSystemException(
                error_code=ErrorCode.FIL006,
                file_path=str(self.template_path),
                context={"details": f"Error reading template file: {e}"}
            ) from e

    def _get_template_directory(self) -> Path:
        """Get template directory path"""
        # Get the path relative to this module
        module_dir = Path(__file__).parent.parent
        return module_dir / "templates" / self.document_type / self.template_name

    def validate_data(self):
        """Validate data based on template definition"""
        self._validate_required_sections()
        self._validate_personal_info()
        self._validate_document_specific_fields()

    def _validate_required_sections(self):
        """Validate required sections from template definition"""
        for field in self.template_def.required_fields:
            if field not in self.data:
                raise ValidationException(
                    error_code=ErrorCode.VAL001,
                    field_path=field,
                    context={"section": f"{self.document_type} data"}
                )

    def _validate_personal_info(self):
        """Validate personal info fields"""
        if "personalInfo" not in self.data:
            return

        personal_info_section = next(
            (section for section in self.template_def.sections
             if section.section_type == SectionType.PERSONAL_INFO),
            None
        )

        if personal_info_section:
            for field_name, field_mapping in personal_info_section.field_mappings.items():
                if field_mapping.required and field_name not in self.data["personalInfo"]:
                    raise ValidationException(
                        error_code=ErrorCode.VAL001,
                        field_path=f"personalInfo.{field_name}",
                        context={"section": "personalInfo"}
                    )

    def _validate_document_specific_fields(self):
        """Validate document-specific fields"""
        # Additional validation based on document type
        if self.document_type == "cover_letter":
            # Body can be string or list
            if "body" in self.data and not isinstance(self.data["body"], (str, list)):
                raise ValidationException(
                    error_code=ErrorCode.VAL002,
                    field_path="body",
                    context={"expected_type": "string or list", "actual_type": type(self.data["body"]).__name__}
                )

            # Recipient should be dict if present
            if "recipient" in self.data and not isinstance(self.data["recipient"], dict):
                raise ValidationException(
                    error_code=ErrorCode.VAL002,
                    field_path="recipient",
                    context={"expected_type": "dict", "actual_type": type(self.data["recipient"]).__name__}
                )

    def replace_special_chars(self, data):
        """Recursively replace special LaTeX characters in strings"""
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

    def get_field_with_fallback(
        self,
        obj: dict,
        field_mapping: FieldMapping,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Get field value using fallback logic from field mapping"""
        # Try primary field
        if field_mapping.primary in obj and obj[field_mapping.primary]:
            return obj[field_mapping.primary]

        # Try fallback fields
        for fallback in field_mapping.fallbacks:
            if fallback in obj and obj[fallback]:
                return obj[fallback]

        # Try smart default function
        if field_mapping.smart_default_fn:
            return field_mapping.smart_default_fn(context_data or self.data)

        # Return default value
        return field_mapping.default

    def generate_personal_info(self) -> str:
        """Generate personal info header dynamically"""
        if "personalInfo" not in self.data:
            return ""

        info = self.data["personalInfo"]
        header_lines = []
        header_lines.append(r"\begin{header}")
        header_lines.append(r"    \fontsize{25pt}{25pt}\selectfont " + info["name"])
        header_lines.append(r"    \vspace{2pt}")
        header_lines.append(r"    \normalsize")

        # Build contact line pieces
        parts = []

        # Get personal info section definition
        personal_section = next(
            (section for section in self.template_def.sections
             if section.section_type == SectionType.PERSONAL_INFO),
            None
        )

        if personal_section:
            # Only add location if it exists
            location = self.get_field_with_fallback(info, personal_section.field_mappings.get("location", FieldMapping("location")))
            if location:
                parts.append(r"\mbox{ " + location + r" }")

            # Email is required
            email = self.get_field_with_fallback(info, personal_section.field_mappings.get("email", FieldMapping("email")))
            if email:
                parts.append(r"\mbox{\href{mailto:" + email + r"}{" + email + r"}}")

            # Add optional fields
            optional_fields = ["phone", "website", "linkedin", "github", "twitter", "x"]
            for field in optional_fields:
                field_mapping = personal_section.field_mappings.get(field)
                if field_mapping:
                    value = self.get_field_with_fallback(info, field_mapping)
                    display_mapping = personal_section.field_mappings.get(f"{field}_display")
                    display_value = self.get_field_with_fallback(info, display_mapping) if display_mapping else None

                    if value and display_value:
                        if field == "phone":
                            parts.append(r"\mbox{\href{tel:" + value + r"}{" + value + r"}}")
                        else:
                            parts.append(r"\mbox{\href{" + value + r"}{" + display_value + r"}}")
                    elif value and field == "phone":
                        parts.append(r"\mbox{\href{tel:" + value + r"}{" + value + r"}}")

        # Join with separators
        if parts:
            contact_line = " \\kern 3pt \\AND \\kern 3pt ".join(parts)
            header_lines.append(r"    " + contact_line)

        header_lines.append(r"\end{header}")
        return "\n".join(header_lines)

    def generate_section_content(self, section: SectionDefinition) -> str:
        """Generate content for a specific section"""
        if section.section_type == SectionType.PERSONAL_INFO:
            return self.generate_personal_info()
        elif section.section_type == SectionType.PROFESSIONAL_SUMMARY:
            return self._generate_professional_summary(section)
        elif section.section_type == SectionType.EXPERIENCE:
            return self._generate_experience(section)
        elif section.section_type == SectionType.EDUCATION:
            return self._generate_education(section)
        elif section.section_type == SectionType.PROJECTS:
            return self._generate_projects(section)
        elif section.section_type == SectionType.PUBLICATIONS:
            return self._generate_publications(section)
        elif section.section_type == SectionType.ACHIEVEMENTS:
            return self._generate_achievements(section)
        elif section.section_type == SectionType.CERTIFICATIONS:
            return self._generate_certifications(section)
        elif section.section_type == SectionType.SKILLS:
            return self._generate_skills(section)
        elif section.section_type == SectionType.RECIPIENT:
            return self._generate_recipient(section)
        elif section.section_type == SectionType.DATE:
            return self._generate_date(section)
        elif section.section_type == SectionType.SALUTATION:
            return self._generate_salutation(section)
        elif section.section_type == SectionType.BODY:
            return self._generate_body(section)
        elif section.section_type == SectionType.CLOSING:
            return self._generate_closing(section)
        else:
            return ""

    def _generate_professional_summary(self, section: SectionDefinition) -> str:
        """Generate professional summary section"""
        content_mapping = section.field_mappings.get("content")
        if not content_mapping:
            return ""

        content = self.get_field_with_fallback(self.data, content_mapping)
        if not content:
            return ""

        return f"\\begin{{onecolentry}}{content}\\end{{onecolentry}}"

    def _generate_experience(self, section: SectionDefinition) -> str:
        """Generate experience section"""
        if not self.data.get("experience"):
            return ""

        sections = []
        for exp in self.data["experience"]:
            # Get field values using mappings
            title = self.get_field_with_fallback(exp, section.field_mappings.get("title", FieldMapping("title", default="Position")))
            company = self.get_field_with_fallback(exp, section.field_mappings.get("company", FieldMapping("company", default="Company")))
            start_date = self.get_field_with_fallback(exp, section.field_mappings.get("startDate", FieldMapping("startDate", default="")))
            end_date = self.get_field_with_fallback(exp, section.field_mappings.get("endDate", FieldMapping("endDate", default="Present")))
            achievements = self.get_field_with_fallback(exp, section.field_mappings.get("achievements", FieldMapping("achievements", default=[])))

            date_range = f"{start_date} -- {end_date}" if start_date else end_date

            entry = (
                f"\\textbf{{{title}}}, {company} \\hfill {date_range}\n"
                "\\begin{highlights}\n"
                + "\n".join([f"\\item {ach}" for ach in achievements])
                + "\n\\end{highlights}"
            )
            sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")

        return "\n".join(sections)

    def _generate_education(self, section: SectionDefinition) -> str:
        """Generate education section"""
        if not self.data.get("education"):
            return ""

        sections = []
        for edu in self.data["education"]:
            degree = self.get_field_with_fallback(edu, section.field_mappings.get("degree", FieldMapping("degree", default="Degree")))
            institution = self.get_field_with_fallback(edu, section.field_mappings.get("institution", FieldMapping("institution", default="Institution")))
            start_date = self.get_field_with_fallback(edu, section.field_mappings.get("startDate", FieldMapping("startDate", default="")))
            end_date = self.get_field_with_fallback(edu, section.field_mappings.get("endDate", FieldMapping("endDate", default="")))
            focus = self.get_field_with_fallback(edu, section.field_mappings.get("focus", FieldMapping("focus", default="")))
            courses = self.get_field_with_fallback(edu, section.field_mappings.get("courses", FieldMapping("courses", default=[])))
            projects = self.get_field_with_fallback(edu, section.field_mappings.get("projects", FieldMapping("projects", default=[])))

            date_range = f"{start_date} -- {end_date}" if start_date and end_date else (end_date or start_date)

            entry = (
                f"\\textbf{{{degree}}} -- {institution} "
                f"\\hfill {date_range}\n"
                "\\begin{highlights}\n"
                f"\\item \\textbf{{Focus:}} {focus}\n"
                f"\\item \\textbf{{Courses:}} {', '.join(courses) if courses else 'N/A'}\n"
                f"\\item \\textbf{{Projects:}} {', '.join(projects) if projects else 'N/A'}\n"
                "\\end{highlights}"
            )
            sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")

        return "\n".join(sections)

    def _generate_projects(self, section: SectionDefinition) -> str:
        """Generate projects section"""
        if not self.data.get("projects"):
            return ""

        sections = []
        for proj in self.data["projects"]:
            name = self.get_field_with_fallback(proj, section.field_mappings.get("name", FieldMapping("name", default="Project")))
            description = self.get_field_with_fallback(proj, section.field_mappings.get("description", FieldMapping("description", default="")))
            tools = self.get_field_with_fallback(proj, section.field_mappings.get("tools", FieldMapping("tools", default=[])))
            achievements = self.get_field_with_fallback(proj, section.field_mappings.get("achievements", FieldMapping("achievements", default=[])))

            if isinstance(description, list):
                desc_points = ", ".join(description)
            else:
                desc_points = description

            entry_lines = [
                f"\\textbf{{{name}}} - \\textit{{{desc_points}}}",
                "\\begin{highlights}"
            ]

            if tools:
                entry_lines.append(f"\\item \\textbf{{Tools:}} {', '.join(tools)}")

            if achievements:
                entry_lines.append("\\item \\textbf{Achievements:}")
                entry_lines.append("    \\begin{itemize}[leftmargin=*]")
                for ach in achievements:
                    entry_lines.append(f"\\item {ach}")
                entry_lines.append("    \\end{itemize}")

            entry_lines.append("\\end{highlights}")
            entry = "\n".join(entry_lines)
            sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")

        return "\n".join(sections)

    def _generate_publications(self, section: SectionDefinition) -> str:
        """Generate publications section"""
        publications_mapping = section.field_mappings.get("publications")
        if not publications_mapping:
            return ""

        publications = self.get_field_with_fallback(self.data, publications_mapping)
        if not publications:
            return ""

        items = []
        for pub in publications:
            title = self.get_field_with_fallback(pub, section.field_mappings.get("title", FieldMapping("title", default="Publication")))
            date = self.get_field_with_fallback(pub, section.field_mappings.get("date", FieldMapping("date", default="")))
            items.append(f"\\item \\textbf{{{title}}} -- {date}")

        items_str = "\n".join(items)
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{items_str}\\end{{highlights}}\\end{{onecolentry}}"

    def _generate_achievements(self, section: SectionDefinition) -> str:
        """Generate achievements section"""
        items_mapping = section.field_mappings.get("items")
        if not items_mapping:
            return ""

        items = self.get_field_with_fallback(self.data, items_mapping)
        if not items:
            return ""

        bullets = "\n".join(f"\\item {item}" for item in items)
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{bullets}\\end{{highlights}}\\end{{onecolentry}}"

    def _generate_certifications(self, section: SectionDefinition) -> str:
        """Generate certifications section"""
        items_mapping = section.field_mappings.get("items")
        if not items_mapping:
            return ""

        items = self.get_field_with_fallback(self.data, items_mapping)
        if not items:
            return ""

        bullets = "\n".join(f"\\item {item}" for item in items)
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{bullets}\\end{{highlights}}\\end{{onecolentry}}"

    def _generate_skills(self, section: SectionDefinition) -> str:
        """Generate skills section"""
        skills_data_mapping = section.field_mappings.get("skills_data")
        if not skills_data_mapping:
            return ""

        skills_data = self.get_field_with_fallback(self.data, skills_data_mapping)
        if not skills_data:
            return ""

        sections = []

        # Simple array of skills
        if isinstance(skills_data, list) and all(isinstance(skill, str) for skill in skills_data):
            entry = f"\\textbf{{Skills}}: {', '.join(skills_data)}"
            sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")
        else:
            # Structured skills with categories
            for skill in skills_data:
                category = self.get_field_with_fallback(skill, section.field_mappings.get("category", FieldMapping("category", default="Skills")))
                skill_list = self.get_field_with_fallback(skill, section.field_mappings.get("skills", FieldMapping("skills", default=[])))

                if skill_list:
                    entry = f"\\textbf{{{category}}}: {', '.join(skill_list)}"
                    sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")

        return "\n".join(sections)

    def _generate_recipient(self, section: SectionDefinition) -> str:
        """Generate recipient address for cover letter"""
        if not self.data.get("recipient"):
            return ""

        recipient = self.data["recipient"]
        lines = []

        # Add recipient info in logical order
        for field in ["name", "title", "company", "department"]:
            field_mapping = section.field_mappings.get(field)
            if field_mapping:
                value = self.get_field_with_fallback(recipient, field_mapping)
                if value:
                    lines.append(value)

        # Handle address
        address_mapping = section.field_mappings.get("address")
        if address_mapping:
            address = self.get_field_with_fallback(recipient, address_mapping)
            if isinstance(address, list):
                lines.extend(filter(None, address))
            elif isinstance(address, str):
                lines.append(address)

        # Add structured address components
        address_fields = ["street", "city", "state", "zip", "country"]
        address_components = []

        for field in address_fields[:1]:  # street
            field_mapping = section.field_mappings.get(field)
            if field_mapping:
                value = self.get_field_with_fallback(recipient, field_mapping)
                if value:
                    address_components.append(value)

        # City, state, zip on one line
        city_state_zip_parts = []
        for field in ["city", "state", "zip"]:
            field_mapping = section.field_mappings.get(field)
            if field_mapping:
                value = self.get_field_with_fallback(recipient, field_mapping)
                if value:
                    city_state_zip_parts.append(value)

        if city_state_zip_parts:
            address_components.append(", ".join(city_state_zip_parts))

        # Country
        country_mapping = section.field_mappings.get("country")
        if country_mapping:
            country = self.get_field_with_fallback(recipient, country_mapping)
            if country:
                address_components.append(country)

        lines.extend(address_components)
        return " \\\\\n".join(filter(None, lines))

    def _generate_date(self, section: SectionDefinition) -> str:
        """Generate date for cover letter"""
        date_mapping = section.field_mappings.get("date")
        if not date_mapping:
            return ""

        return self.get_field_with_fallback(self.data, date_mapping, self.data)

    def _generate_salutation(self, section: SectionDefinition) -> str:
        """Generate salutation for cover letter"""
        salutation_mapping = section.field_mappings.get("salutation")
        if not salutation_mapping:
            return ""

        return self.get_field_with_fallback(self.data, salutation_mapping, self.data)

    def _generate_body(self, section: SectionDefinition) -> str:
        """Generate body content for cover letter"""
        body_mapping = section.field_mappings.get("body")
        if not body_mapping:
            return ""

        body = self.get_field_with_fallback(self.data, body_mapping)

        if isinstance(body, str):
            return body
        elif isinstance(body, list):
            return "\n\n".join(str(paragraph) for paragraph in body if paragraph)
        else:
            return str(body)

    def _generate_closing(self, section: SectionDefinition) -> str:
        """Generate closing for cover letter"""
        closing_mapping = section.field_mappings.get("closing")
        if not closing_mapping:
            return ""

        return self.get_field_with_fallback(self.data, closing_mapping, self.data)

    def _check_section_condition(self, section: SectionDefinition) -> bool:
        """Check if section should be included based on conditional"""
        if not section.conditional:
            return True

        # Split on comma for OR conditions
        conditions = [cond.strip() for cond in section.conditional.split(",")]

        for condition in conditions:
            # Check if field exists and has content
            keys = condition.split(".")
            obj = self.data

            try:
                for key in keys:
                    obj = obj[key]
                if obj:  # Field exists and has content
                    return True
            except (KeyError, TypeError):
                continue

        return False

    def generate_section_with_header(self, section: SectionDefinition) -> str:
        """Generate section with conditional header"""
        content = self.generate_section_content(section)
        if content and section.header_name:
            return f"\\section{{{section.header_name}}}\n{content}"
        return content

    def render(self) -> str:
        """Render the template to LaTeX content"""
        # Generate all section content
        content_map = {}

        for section in self.template_def.sections:
            if self._check_section_condition(section):
                if section.header_name:
                    content = self.generate_section_with_header(section)
                else:
                    content = self.generate_section_content(section)

                # Map to placeholder
                placeholder_key = next(
                    (k for k, v in self.template_def.placeholders.items()
                     if v == section.section_type.value),
                    section.template_pattern
                )
                content_map[placeholder_key] = content
            else:
                # Empty content for missing sections
                placeholder_key = next(
                    (k for k, v in self.template_def.placeholders.items()
                     if v == section.section_type.value),
                    section.template_pattern
                )
                content_map[placeholder_key] = ""

        # Special handling for cover letter name placeholder
        if self.document_type == "cover_letter" and "{{name}}" in self.template_def.placeholders:
            content_map["{{name}}"] = self.data.get("personalInfo", {}).get("name", "")

        # Replace placeholders in template
        result = self.template
        for placeholder, content in content_map.items():
            result = result.replace(placeholder, content)

        # Check for unreplaced placeholders
        if re.search(r"{{.*?}}", result):
            unreplaced_matches = re.findall(r"{{(.*?)}}", result)
            raise TemplateRenderingException(
                template_name=self.template_name,
                details=f"Unreplaced placeholders detected: {', '.join(unreplaced_matches)}"
            )

        return result

    def export_to_pdf(self, output_path: str = "output.pdf") -> str:
        """Export to PDF using LaTeX compilation"""
        self.output_path = output_path
        content = self.render()

        # Ensure pdflatex is in PATH
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
                # Run pdflatex twice for proper compilation
                for _ in range(2):
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
                    template_name=self.template_name,
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
                    template_name=self.template_name
                )

        return output_path

    @property
    def required_fields(self) -> List[str]:
        """List of required data fields for this template"""
        return self.template_def.required_fields

    @property
    def template_type(self) -> DocumentType:
        """The document type this template handles"""
        return self.template_def.document_type