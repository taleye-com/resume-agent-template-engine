import os
import re
import subprocess
import tempfile
from typing import Any

from resume_agent_template_engine.core.errors import ErrorCode
from resume_agent_template_engine.core.exceptions import (
    DependencyException,
    FileNotFoundException,
    FileSystemException,
    LaTeXCompilationException,
    PDFGenerationException,
    TemplateRenderingException,
    ValidationException,
)
from resume_agent_template_engine.core.template_engine import (
    DocumentType,
    TemplateInterface,
)


class ClassicResumeTemplate(TemplateInterface):
    """
    Helper class for generating a Classic LaTeX resume from JSON data.
    Handles special characters: &, %, $, #
    """

    def __init__(self, data: dict[str, Any], config: dict[str, Any] = None) -> None:
        """
        Initialize the ClassicResumeTemplate class.

        Args:
            data (dict): The JSON data containing resume information.
            config (dict): Template-specific configuration.
        """
        # Initialize parent class
        super().__init__(data, config)

        self.data = self.replace_special_chars(data)
        self.output_path: str = "output.pdf"
        self.template_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_path = os.path.join(self.template_dir, "classic.tex")

        # Get spacing mode from config or data
        self.spacing_mode = self.get_spacing_mode()

        try:
            with open(self.template_path, encoding="utf-8") as f:
                self.template = f.read()
        except FileNotFoundError as e:
            raise FileNotFoundException(
                file_path=self.template_path, context={"details": str(e)}
            ) from e
        except PermissionError as e:
            raise FileSystemException(
                error_code=ErrorCode.FIL002,
                file_path=self.template_path,
                context={"details": str(e)},
            ) from e
        except Exception as e:
            raise FileSystemException(
                error_code=ErrorCode.FIL006,
                file_path=self.template_path,
                context={"details": f"Error reading template file: {e}"},
            ) from e

    def validate_data(self):
        """Validate essential data fields with consistent error handling"""
        self._validate_required_sections()
        self._validate_personal_info()
        self._validate_document_specific_fields()

    def _validate_required_sections(self):
        """Validate document-type specific required sections"""
        required_sections = ["personalInfo"]
        for section in required_sections:
            if section not in self.data:
                raise ValidationException(
                    error_code=ErrorCode.VAL001,
                    field_path=section,
                    context={"section": "resume data"},
                )

    def _validate_personal_info(self):
        """Validate essential personal info fields consistently"""
        required_personal_info = ["name", "email"]
        for field in required_personal_info:
            if field not in self.data["personalInfo"]:
                raise ValidationException(
                    error_code=ErrorCode.VAL001,
                    field_path=f"personalInfo.{field}",
                    context={"section": "personalInfo"},
                )

    def _validate_document_specific_fields(self):
        """Validate resume-specific fields"""
        # Resume doesn't have additional required fields beyond personalInfo
        pass

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

    def get_field_with_fallback(
        self,
        obj: dict,
        primary_field: str,
        fallback_fields: list[str] = None,
        default_value: Any = None,
    ):
        """Get field with fallback options and default value"""
        if primary_field in obj and obj[primary_field]:
            return obj[primary_field]

        if fallback_fields:
            for fallback in fallback_fields:
                if fallback in obj and obj[fallback]:
                    return obj[fallback]

        return default_value

    def get_field_with_smart_default(
        self, path: str, default_value: Any = None, smart_default_fn=None
    ):
        """Get field with smart defaults"""
        keys = path.split(".")
        obj = self.data

        try:
            for key in keys:
                obj = obj[key]
            return (
                obj
                if obj
                else (smart_default_fn() if smart_default_fn else default_value)
            )
        except (KeyError, TypeError):
            return smart_default_fn() if smart_default_fn else default_value

    def generate_section_with_header(
        self, section_name: str, content_generator_fn, header_name: str = None
    ):
        """Generate section with conditional header"""
        content = content_generator_fn()
        if content:
            header = header_name or section_name.replace("_", " ").title()
            return f"\\section{{{header}}}\n{content}"
        return ""

    def get_spacing_mode(self) -> str:
        """Get spacing mode from config or data (default: compact for better fit)"""
        # Check config first
        if self.config and "spacing_mode" in self.config:
            return self.config["spacing_mode"]

        # Check data
        if "spacing_mode" in self.data or "spacingMode" in self.data:
            return self.data.get("spacing_mode", self.data.get("spacingMode", "compact"))

        # Default to compact for better page fit
        return "compact"

    def generate_spacing_config(self) -> str:
        """Generate LaTeX spacing configuration based on mode"""
        mode = self.spacing_mode.lower()

        if mode == "compact":
            # Tight spacing for 1-page resumes
            return r"""%
% Compact Mode: Optimized for 1-page resumes
\newcommand{\MarginTop}{0.5cm}
\newcommand{\MarginBottom}{0.5cm}
\newcommand{\MarginLeft}{0.6cm}
\newcommand{\MarginRight}{0.6cm}
\newcommand{\SectionSpacingBefore}{0.2cm}
\newcommand{\SectionSpacingAfter}{0.15cm}
\newcommand{\ItemTopSep}{0.05cm}
\newcommand{\ItemParseSep}{0.05cm}
\newcommand{\ItemSep}{0pt}
"""
        elif mode == "ultra-compact":
            # Ultra-tight for content-heavy resumes
            return r"""%
% Ultra-Compact Mode: Maximum content density
\newcommand{\MarginTop}{0.4cm}
\newcommand{\MarginBottom}{0.4cm}
\newcommand{\MarginLeft}{0.5cm}
\newcommand{\MarginRight}{0.5cm}
\newcommand{\SectionSpacingBefore}{0.15cm}
\newcommand{\SectionSpacingAfter}{0.1cm}
\newcommand{\ItemTopSep}{0.03cm}
\newcommand{\ItemParseSep}{0.03cm}
\newcommand{\ItemSep}{0pt}
"""
        else:  # normal mode
            # Standard spacing for readability
            return r"""%
% Normal Mode: Standard spacing for readability
\newcommand{\MarginTop}{0.8cm}
\newcommand{\MarginBottom}{0.3cm}
\newcommand{\MarginLeft}{0.8cm}
\newcommand{\MarginRight}{0.8cm}
\newcommand{\SectionSpacingBefore}{0.3cm}
\newcommand{\SectionSpacingAfter}{0.2cm}
\newcommand{\ItemTopSep}{0.10cm}
\newcommand{\ItemParseSep}{0.10cm}
\newcommand{\ItemSep}{0pt}
"""

    def generate_personal_info(self) -> str:
        """
        Generate the header block dynamically from self.data['personalInfo'].
        Creates a clean header layout:
        - Line 1: Name (large font, centered)
        - Line 2: Professional Title/Headline (if available)
        - Line 3+: All contact info separated by | (auto-wraps if too long)
        """
        info = self.data["personalInfo"]
        header_lines = []
        header_lines.append(r"\begin{header}")

        # Line 1: Name (compact font, centered) - force line break after
        header_lines.append(
            r"    \fontsize{20pt}{20pt}\selectfont " + info["name"] + r" \\"
        )
        header_lines.append(r"    \vspace{2pt}")

        # Line 2: Professional Title/Headline (if available)
        if info.get("title") or info.get("headline") or info.get("professionalTitle"):
            title = self.get_field_with_fallback(
                info, "title", ["headline", "professionalTitle"], ""
            )
            header_lines.append(r"    \fontsize{10pt}{10pt}\selectfont \textit{" + title + r"} \\")
            header_lines.append(r"    \vspace{2pt}")

        header_lines.append(r"    \normalsize")

        # Build all contact parts
        contact_parts = []

        # Add location if it exists
        if info.get("location"):
            contact_parts.append(info["location"])

        # Email is required
        contact_parts.append(
            r"\href{mailto:" + info["email"] + r"}{" + info["email"] + r"}"
        )

        # Add phone if it exists
        if info.get("phone"):
            contact_parts.append(
                r"\href{tel:" + info["phone"] + r"}{" + info["phone"] + r"}"
            )

        # Add website if both URL and display text exist
        if info.get("website") and info.get("website_display"):
            contact_parts.append(
                r"\href{" + info["website"] + r"}{" + info["website_display"] + r"}"
            )

        # Add LinkedIn if both URL and display text exist
        if info.get("linkedin") and info.get("linkedin_display"):
            contact_parts.append(
                r"\href{" + info["linkedin"] + r"}{" + info["linkedin_display"] + r"}"
            )

        # Add GitHub if both URL and display text exist
        if info.get("github") and info.get("github_display"):
            contact_parts.append(
                r"\href{" + info["github"] + r"}{" + info["github_display"] + r"}"
            )

        # Add Twitter/X if present
        if info.get("twitter") and info.get("twitter_display"):
            contact_parts.append(
                r"\href{" + info["twitter"] + r"}{" + info["twitter_display"] + r"}"
            )
        if info.get("x") and info.get("x_display"):
            contact_parts.append(
                r"\href{" + info["x"] + r"}{" + info["x_display"] + r"}"
            )

        # Join all contact info with AND separators (LaTeX will handle line wrapping)
        if contact_parts:
            contact_line = " \\kern 3pt \\AND \\kern 3pt ".join(contact_parts)
            header_lines.append(r"    " + contact_line)

        header_lines.append(r"\end{header}")
        return "\n".join(header_lines)

    def generate_professional_summary(self):
        """Generate the Professional Summary section."""
        if not self.data.get("professionalSummary"):
            return ""
        return f"\\begin{{onecolentry}}{self.data['professionalSummary']}\\end{{onecolentry}}"

    def generate_education(self):
        """Generate the Education section with clickable links."""
        if not self.data.get("education"):
            return ""
        sections = []
        for edu in self.data["education"]:
            # Use fallback logic for education fields
            degree = self.get_field_with_fallback(
                edu, "degree", ["title", "qualification"], "Degree"
            )
            institution = self.get_field_with_fallback(
                edu, "institution", ["school", "university", "college"], "Institution"
            )

            # Handle institution URL
            url = edu.get("url", "")
            if url:
                institution = f"\\href{{{url}}}{{{institution}}}"

            # Handle date fields with fallbacks
            start_date = edu.get("startDate", "")
            end_date = self.get_field_with_fallback(
                edu, "endDate", ["end_date", "date", "graduationDate"], ""
            )
            date_range = (
                f"{start_date} -- {end_date}"
                if start_date and end_date
                else (end_date or start_date)
            )

            # Use fallback for course details
            courses = self.get_field_with_fallback(
                edu, "notableCourseWorks", ["courses", "coursework", "details"], []
            )
            projects = self.get_field_with_fallback(
                edu, "projects", ["academicProjects"], []
            )
            focus = self.get_field_with_fallback(
                edu, "focus", ["major", "specialization", "concentration"], ""
            )

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

    def generate_experience(self):
        """Generate the Experience section with clickable links."""
        if not self.data.get("experience"):
            return ""
        sections = []
        for exp in self.data["experience"]:
            # Use smart field handling for dates
            start_date = exp.get("startDate", "")
            end_date = self.get_field_with_fallback(
                exp, "endDate", ["end_date"], "Present"
            )
            date_range = f"{start_date} -- {end_date}" if start_date else end_date

            # Use unified fallback logic for achievements/details
            achievements = self.get_field_with_fallback(
                exp, "achievements", ["details", "responsibilities", "duties"], []
            )

            # Use fallback for title and company
            title = self.get_field_with_fallback(
                exp, "title", ["position", "role"], "Position"
            )
            company = self.get_field_with_fallback(
                exp, "company", ["employer", "organization"], "Company"
            )

            # Handle company URL
            url = exp.get("url", "")
            if url:
                company = f"\\href{{{url}}}{{{company}}}"

            entry = (
                f"\\textbf{{{title}}}, {company} \\hfill {date_range}\n"
                "\\begin{highlights}\n"
                + "\n".join([f"\\item {ach}" for ach in achievements])
                + "\n\\end{highlights}"
            )
            sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")
        return "\n".join(sections)

    def generate_projects(self):
        """Generate the Projects section with clickable links."""
        if not self.data.get("projects"):
            return ""
        sections = []
        for proj in self.data["projects"]:
            # Use fallback logic for project name
            name = self.get_field_with_fallback(
                proj, "name", ["title", "project_name"], "Project"
            )

            # Handle project URL
            url = proj.get("url", "")
            if url:
                name = f"\\href{{{url}}}{{{name}}}"

            # Handle both simple string description and list of descriptions with fallbacks
            description = self.get_field_with_fallback(
                proj, "description", ["summary", "desc"], ""
            )
            if isinstance(description, list):
                desc_points = ", ".join(description)
            else:
                desc_points = description

            # Handle different field names for technologies/tools with fallbacks
            tools = self.get_field_with_fallback(
                proj, "tools", ["technologies", "tech_stack", "stack"], []
            )
            achievements = self.get_field_with_fallback(
                proj, "achievements", ["accomplishments", "results", "outcomes"], []
            )

            entry_lines = [
                f"\\textbf{{{name}}} - \\textit{{{desc_points}}}",
                "\\begin{highlights}",
            ]

            # Add tools/technologies if available
            if tools:
                entry_lines.append(f"\\item \\textbf{{Tools:}} {', '.join(tools)}")

            # Add achievements if available
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

    def generate_articles_and_publications(self):
        """Generate the Articles & Publications section."""
        # Check multiple possible field names
        publications = self.get_field_with_fallback(
            self.data,
            "articlesAndPublications",
            ["publications", "articles", "papers"],
            [],
        )
        if not publications:
            return ""

        items = []
        for pub in publications:
            title = self.get_field_with_fallback(pub, "title", ["name"], "Publication")
            date = self.get_field_with_fallback(
                pub, "date", ["published_date", "year"], ""
            )
            items.append(f"\\item \\textbf{{{title}}} -- {date}")

        items_str = "\n".join(items)
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{items_str}\\end{{highlights}}\\end{{onecolentry}}"

    def generate_achievements(self):
        """Generate the Achievements section."""
        # Check multiple possible field names
        achievements = self.get_field_with_fallback(
            self.data, "achievements", ["accomplishments", "awards", "honors"], []
        )
        if not achievements:
            return ""
        bullets = "\n".join(f"\\item {item}" for item in achievements)
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{bullets}\\end{{highlights}}\\end{{onecolentry}}"

    def generate_certifications(self):
        """Generate the Certifications section in compact inline format with optional links."""
        # Check multiple possible field names
        certifications = self.get_field_with_fallback(
            self.data, "certifications", ["certificates", "credentials", "licenses"], []
        )
        if not certifications:
            return ""

        # Handle both object (categorized) and array (flat list) formats
        if isinstance(certifications, dict):
            # Categorized format - display inline with comma separation
            sections = []
            for category, certs in certifications.items():
                if certs and isinstance(certs, list):
                    # Convert category key to readable format (e.g., "ai_ml" -> "AI/ML")
                    category_name = category.replace("_", " ").title()
                    # Handle special cases for better formatting
                    category_name = category_name.replace("Ai Ml", "AI/ML")
                    category_name = category_name.replace("Ai/Ml", "AI/ML")
                    category_name = category_name.replace(" And ", " \\& ")

                    # Process each certification with optional link
                    cert_items = []
                    for cert in certs:
                        cert_text = self._format_certification_with_link(cert)
                        cert_items.append(cert_text)

                    # Join all certifications with comma separator
                    certs_text = ", ".join(cert_items)
                    sections.append(f"\\textbf{{{category_name}}}: {certs_text}")

            if sections:
                # Join all categories with line breaks
                content = " \\\\\n".join(sections)
                return f"\\begin{{onecolentry}}\n{content}\n\\end{{onecolentry}}"
            return ""
        else:
            # Old flat list format - display as comma-separated inline text
            cert_items = []
            for cert in certifications:
                cert_text = self._format_certification_with_link(cert)
                cert_items.append(cert_text)

            certs_text = ", ".join(cert_items)
            return f"\\begin{{onecolentry}}\n{certs_text}\n\\end{{onecolentry}}"

    def _format_certification_with_link(self, cert):
        """Format a single certification with optional link support.

        Supports:
        - String: "Certification Name"
        - Dict: {"name": "Cert Name", "url": "https://..."}
        - Dict: {"title": "Cert Name", "link": "https://..."}
        """
        if isinstance(cert, str):
            # Simple string certification
            return cert
        elif isinstance(cert, dict):
            # Object with name and optional URL
            name = self.get_field_with_fallback(
                cert, "name", ["title", "certification"], ""
            )
            url = self.get_field_with_fallback(
                cert, "url", ["link", "href"], ""
            )

            if url and name:
                # Return hyperlinked certification
                return f"\\href{{{url}}}{{{name}}}"
            elif name:
                # Return just the name
                return name
            else:
                # Fallback to string representation
                return str(cert)
        else:
            # Unknown format, convert to string
            return str(cert)

    def generate_technologies_and_skills(self):
        """Generate the Technologies & Skills section."""
        # Handle multiple possible field names with fallback
        skills_data = self.get_field_with_fallback(
            self.data,
            "technologiesAndSkills",
            ["skills", "technologies", "tech_skills"],
            [],
        )
        if not skills_data:
            return ""

        sections = []

        # If it's a simple array of skills, treat them as general skills
        if isinstance(skills_data, list) and all(
            isinstance(skill, str) for skill in skills_data
        ):
            entry = f"\\textbf{{Skills}}: {', '.join(skills_data)}"
            sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")
        else:
            # Handle structured skills with categories
            for skill in skills_data:
                # Use fallback for category and skills fields
                category = self.get_field_with_fallback(
                    skill, "category", ["name", "type"], "Skills"
                )
                skill_list = self.get_field_with_fallback(
                    skill, "skills", ["items", "technologies"], []
                )

                if skill_list:
                    entry = f"\\textbf{{{category}}}: {', '.join(skill_list)}"
                    sections.append(
                        f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}"
                    )
        return "\n".join(sections)

    def generate_date(self):
        """Generate date with smart formatting for resumes if needed"""

        date = self.data.get("date", "")
        if date:
            return date

        # For resumes, we typically don't auto-generate dates
        # but this provides consistency with cover letter template
        return ""

    def generate_core_competencies(self):
        """Generate Core Competencies section."""
        competencies = self.get_field_with_fallback(
            self.data, "coreCompetencies", ["competencies", "keySkills", "expertise"], []
        )
        if not competencies:
            return ""
        bullets = "\n".join(f"\\item {item}" for item in competencies)
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{bullets}\\end{{highlights}}\\end{{onecolentry}}"

    def generate_leadership_experience(self):
        """Generate Leadership Experience section with clickable links."""
        leadership = self.get_field_with_fallback(
            self.data, "leadershipExperience", ["leadership"], []
        )
        if not leadership:
            return ""

        sections = []
        for exp in leadership:
            title = self.get_field_with_fallback(exp, "title", ["position", "role"], "Leadership Role")
            organization = self.get_field_with_fallback(exp, "organization", ["company"], "")

            # Handle organization URL
            url = exp.get("url", "")
            if url:
                organization = f"\\href{{{url}}}{{{organization}}}"

            start_date = exp.get("startDate", "")
            end_date = self.get_field_with_fallback(exp, "endDate", ["end_date"], "Present")
            date_range = f"{start_date} -- {end_date}" if start_date else end_date

            achievements = self.get_field_with_fallback(
                exp, "achievements", ["details", "responsibilities"], []
            )

            entry = (
                f"\\textbf{{{title}}}, {organization} \\hfill {date_range}\n"
                "\\begin{highlights}\n"
                + "\n".join([f"\\item {ach}" for ach in achievements])
                + "\n\\end{highlights}"
            )
            sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")
        return "\n".join(sections)

    def generate_relevant_coursework(self):
        """Generate Relevant Coursework section."""
        coursework = self.get_field_with_fallback(
            self.data, "relevantCoursework", ["coursework", "courses"], []
        )
        if not coursework:
            return ""

        # Handle both simple list and structured coursework
        if isinstance(coursework, list) and coursework:
            if isinstance(coursework[0], str):
                # Simple list of course names
                courses_str = ", ".join(coursework)
                return f"\\begin{{onecolentry}}\n{courses_str}\\end{{onecolentry}}"
            else:
                # Structured coursework with details
                sections = []
                for course in coursework:
                    name = self.get_field_with_fallback(course, "name", ["title", "courseName"], "Course")
                    description = course.get("description", "")
                    if description:
                        sections.append(f"\\textbf{{{name}}}: {description}")
                    else:
                        sections.append(f"\\textbf{{{name}}}")
                return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n" + "\n".join([f"\\item {s}" for s in sections]) + "\n\\end{{highlights}}\\end{{onecolentry}}"
        return ""

    def generate_technical_skills(self):
        """Generate Technical Skills section (detailed breakdown)."""
        tech_skills = self.get_field_with_fallback(
            self.data, "technicalSkills", ["techSkills"], {}
        )
        if not tech_skills:
            return ""

        sections = []
        for category, skills in tech_skills.items():
            if isinstance(skills, list) and skills:
                category_name = category.replace("_", " ").title()
                entry = f"\\textbf{{{category_name}}}: {', '.join(skills)}"
                sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")
        return "\n".join(sections)

    def generate_core_competencies_and_technical_skills(self):
        """Generate merged Core Competencies & Technical Skills section (prioritizes core competencies to avoid duplication)."""
        # Get core competencies - these already include key technologies
        competencies = self.get_field_with_fallback(
            self.data, "coreCompetencies", ["competencies", "keySkills", "expertise"], []
        )

        # If no competencies, fallback to technical skills
        if not competencies:
            tech_skills = self.get_field_with_fallback(
                self.data, "technicalSkills", ["techSkills"], {}
            )
            if tech_skills:
                all_items = []
                for category, skills in tech_skills.items():
                    if isinstance(skills, list) and skills:
                        category_name = category.replace("_", " ").title()
                        all_items.append(f"\\item \\textbf{{{category_name}}}: {', '.join(skills)}")
                bullets = "\n".join(all_items)
                return f"\\begin{{onecolentry}}\\begin{{highlights}}\n{bullets}\n\\end{{highlights}}\\end{{onecolentry}}"
            return ""

        # Show only core competencies (avoids duplication with technical skills)
        bullets = "\n".join([f"\\item {item}" for item in competencies])
        return f"\\begin{{onecolentry}}\\begin{{highlights}}\n{bullets}\n\\end{{highlights}}\\end{{onecolentry}}"

    def generate_skills_matrix(self):
        """Generate Skills Matrix with proficiency levels."""
        skills_matrix = self.get_field_with_fallback(
            self.data, "skillsMatrix", ["skillsByProficiency"], {}
        )
        if not skills_matrix:
            return ""

        sections = []
        proficiency_order = ["expert", "advanced", "intermediate", "familiar", "beginner"]

        for level in proficiency_order:
            skills = skills_matrix.get(level, [])
            if skills:
                level_name = level.capitalize()
                entry = f"\\textbf{{{level_name}}}: {', '.join(skills)}"
                sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")
        return "\n".join(sections)

    def generate_open_source_contributions(self):
        """Generate Open Source Contributions section."""
        contributions = self.get_field_with_fallback(
            self.data, "openSourceContributions", ["openSource", "ossContributions"], []
        )
        if not contributions:
            return ""

        sections = []
        for contrib in contributions:
            project = self.get_field_with_fallback(contrib, "project", ["name", "repository"], "Project")
            description = self.get_field_with_fallback(contrib, "description", ["summary"], "")
            url = contrib.get("url", "")
            contributions_list = self.get_field_with_fallback(contrib, "contributions", ["details"], [])

            entry_lines = []
            if url:
                entry_lines.append(f"\\textbf{{{project}}} (\\href{{{url}}}{{{url}}}) - \\textit{{{description}}}")
            else:
                entry_lines.append(f"\\textbf{{{project}}} - \\textit{{{description}}}")

            if contributions_list:
                entry_lines.append("\\begin{highlights}")
                entry_lines.extend([f"\\item {c}" for c in contributions_list])
                entry_lines.append("\\end{highlights}")

            sections.append(f"\\begin{{onecolentry}}\n" + "\n".join(entry_lines) + "\\end{{onecolentry}}")
        return "\n".join(sections)

    def generate_research_experience(self):
        """Generate Research Experience section."""
        research = self.get_field_with_fallback(
            self.data, "researchExperience", ["research"], []
        )
        if not research:
            return ""

        sections = []
        for exp in research:
            title = self.get_field_with_fallback(exp, "title", ["position", "role"], "Researcher")
            institution = self.get_field_with_fallback(exp, "institution", ["organization", "lab"], "")
            start_date = exp.get("startDate", "")
            end_date = self.get_field_with_fallback(exp, "endDate", ["end_date"], "Present")
            date_range = f"{start_date} -- {end_date}" if start_date else end_date

            description = self.get_field_with_fallback(exp, "description", ["summary", "details"], [])

            entry = (
                f"\\textbf{{{title}}}, {institution} \\hfill {date_range}\n"
                "\\begin{highlights}\n"
                + "\n".join([f"\\item {desc}" for desc in description])
                + "\n\\end{highlights}"
            )
            sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")
        return "\n".join(sections)

    def generate_publications(self):
        """Generate Publications section (peer-reviewed papers)."""
        publications = self.get_field_with_fallback(
            self.data, "publications", ["academicPublications", "papers"], []
        )
        if not publications:
            return ""

        items = []
        for pub in publications:
            title = self.get_field_with_fallback(pub, "title", ["name"], "Publication")
            authors = pub.get("authors", "")
            venue = self.get_field_with_fallback(pub, "venue", ["journal", "conference"], "")
            date = self.get_field_with_fallback(pub, "date", ["year", "published"], "")
            url = pub.get("url", "")

            pub_str = f"\\textbf{{{title}}}"
            if authors:
                pub_str += f". {authors}"
            if venue:
                pub_str += f". \\textit{{{venue}}}"
            if date:
                pub_str += f", {date}"
            if url:
                pub_str += f". \\href{{{url}}}{{Link}}"

            items.append(f"\\item {pub_str}")

        items_str = "\n".join(items)
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{items_str}\\end{{highlights}}\\end{{onecolentry}}"

    def generate_technical_writing(self):
        """Generate Technical Writing section (blog posts, articles)."""
        writing = self.get_field_with_fallback(
            self.data, "technicalWriting", ["articles", "blogPosts"], []
        )
        if not writing:
            return ""

        items = []
        for article in writing:
            title = self.get_field_with_fallback(article, "title", ["name"], "Article")
            platform = article.get("platform", "")
            date = self.get_field_with_fallback(article, "date", ["published", "year"], "")
            url = article.get("url", "")

            article_str = f"\\textbf{{{title}}}"
            if platform:
                article_str += f" -- {platform}"
            if date:
                article_str += f", {date}"
            if url:
                article_str += f". \\href{{{url}}}{{Link}}"

            items.append(f"\\item {article_str}")

        items_str = "\n".join(items)
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{items_str}\\end{{highlights}}\\end{{onecolentry}}"

    def generate_speaking_engagements(self):
        """Generate Speaking Engagements section."""
        speaking = self.get_field_with_fallback(
            self.data, "speakingEngagements", ["speaking", "talks", "conferences"], []
        )
        if not speaking:
            return ""

        items = []
        for talk in speaking:
            title = self.get_field_with_fallback(talk, "title", ["name", "topic"], "Talk")
            event = self.get_field_with_fallback(talk, "event", ["conference", "venue"], "")
            date = self.get_field_with_fallback(talk, "date", ["year"], "")
            location = talk.get("location", "")

            talk_str = f"\\textbf{{{title}}}"
            if event:
                talk_str += f" -- {event}"
            if location:
                talk_str += f", {location}"
            if date:
                talk_str += f" ({date})"

            items.append(f"\\item {talk_str}")

        items_str = "\n".join(items)
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{items_str}\\end{{highlights}}\\end{{onecolentry}}"

    def generate_awards_and_honors(self):
        """Generate Awards & Honors section."""
        awards = self.get_field_with_fallback(
            self.data, "awardsAndHonors", ["awards", "honors", "recognition"], []
        )
        if not awards:
            return ""

        items = []
        for award in awards:
            if isinstance(award, str):
                items.append(f"\\item {award}")
            else:
                title = self.get_field_with_fallback(award, "title", ["name", "award"], "Award")
                issuer = self.get_field_with_fallback(award, "issuer", ["organization", "from"], "")
                date = self.get_field_with_fallback(award, "date", ["year"], "")

                award_str = f"\\textbf{{{title}}}"
                if issuer:
                    award_str += f" -- {issuer}"
                if date:
                    award_str += f", {date}"

                items.append(f"\\item {award_str}")

        items_str = "\n".join(items)
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{items_str}\\end{{highlights}}\\end{{onecolentry}}"

    def generate_teaching_experience(self):
        """Generate Teaching Experience section."""
        teaching = self.get_field_with_fallback(
            self.data, "teachingExperience", ["teaching"], []
        )
        if not teaching:
            return ""

        sections = []
        for exp in teaching:
            title = self.get_field_with_fallback(exp, "title", ["position", "role"], "Instructor")
            institution = self.get_field_with_fallback(exp, "institution", ["organization", "school"], "")
            start_date = exp.get("startDate", "")
            end_date = self.get_field_with_fallback(exp, "endDate", ["end_date"], "Present")
            date_range = f"{start_date} -- {end_date}" if start_date else end_date

            courses = self.get_field_with_fallback(exp, "courses", ["subjects", "classes"], [])
            details = self.get_field_with_fallback(exp, "details", ["description", "achievements"], [])

            entry = f"\\textbf{{{title}}}, {institution} \\hfill {date_range}\n"
            entry += "\\begin{highlights}\n"

            if courses:
                entry += f"\\item \\textbf{{Courses}}: {', '.join(courses)}\n"

            for detail in details:
                entry += f"\\item {detail}\n"

            entry += "\\end{highlights}"
            sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")
        return "\n".join(sections)

    def generate_mentorship(self):
        """Generate Mentorship section."""
        mentorship = self.get_field_with_fallback(
            self.data, "mentorship", ["mentoringExperience"], []
        )
        if not mentorship:
            return ""

        bullets = []
        for item in mentorship:
            if isinstance(item, str):
                bullets.append(f"\\item {item}")
            else:
                description = self.get_field_with_fallback(item, "description", ["summary", "details"], "")
                count = item.get("menteeCount", "")
                duration = item.get("duration", "")

                mentor_str = description
                if count:
                    mentor_str += f" ({count} mentees)"
                if duration:
                    mentor_str += f" -- {duration}"

                bullets.append(f"\\item {mentor_str}")

        bullets_str = "\n".join(bullets)
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{bullets_str}\\end{{highlights}}\\end{{onecolentry}}"

    def generate_volunteering(self):
        """Generate Volunteering section."""
        volunteering = self.get_field_with_fallback(
            self.data, "volunteering", ["volunteerExperience", "communityService"], []
        )
        if not volunteering:
            return ""

        sections = []
        for vol in volunteering:
            if isinstance(vol, str):
                sections.append(f"\\begin{{onecolentry}}\\item {vol}\\end{{onecolentry}}")
            else:
                role = self.get_field_with_fallback(vol, "role", ["title", "position"], "Volunteer")
                organization = self.get_field_with_fallback(vol, "organization", ["org"], "")
                start_date = vol.get("startDate", "")
                end_date = self.get_field_with_fallback(vol, "endDate", ["end_date"], "Present")
                date_range = f"{start_date} -- {end_date}" if start_date else end_date

                description = self.get_field_with_fallback(vol, "description", ["details"], [])

                entry = f"\\textbf{{{role}}}, {organization} \\hfill {date_range}\n"
                if description:
                    entry += "\\begin{highlights}\n"
                    entry += "\n".join([f"\\item {desc}" for desc in description])
                    entry += "\n\\end{highlights}"

                sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")
        return "\n".join(sections)

    def generate_languages(self):
        """Generate Languages section (spoken languages, not programming)."""
        languages = self.get_field_with_fallback(
            self.data, "languages", ["spokenLanguages"], []
        )
        if not languages:
            return ""

        lang_items = []
        for lang in languages:
            if isinstance(lang, str):
                lang_items.append(lang)
            else:
                language = self.get_field_with_fallback(lang, "language", ["name"], "Language")
                proficiency = self.get_field_with_fallback(
                    lang, "proficiency", ["level", "fluency"], ""
                )

                if proficiency:
                    lang_items.append(f"{language} ({proficiency})")
                else:
                    lang_items.append(language)

        lang_str = ", ".join(lang_items)
        return f"\\begin{{onecolentry}}\n{lang_str}\\end{{onecolentry}}"

    def generate_professional_affiliations(self):
        """Generate Professional Affiliations section."""
        affiliations = self.get_field_with_fallback(
            self.data, "professionalAffiliations", ["affiliations", "memberships"], []
        )
        if not affiliations:
            return ""

        items = []
        for affil in affiliations:
            if isinstance(affil, str):
                items.append(f"\\item {affil}")
            else:
                organization = self.get_field_with_fallback(affil, "organization", ["name"], "Organization")
                role = affil.get("role", "Member")
                date = self.get_field_with_fallback(affil, "date", ["year", "since"], "")

                affil_str = f"\\textbf{{{organization}}} -- {role}"
                if date:
                    affil_str += f" ({date})"

                items.append(f"\\item {affil_str}")

        items_str = "\n".join(items)
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{items_str}\\end{{highlights}}\\end{{onecolentry}}"

    def generate_patents(self):
        """Generate Patents section."""
        patents = self.get_field_with_fallback(
            self.data, "patents", ["intellectualProperty"], []
        )
        if not patents:
            return ""

        items = []
        for patent in patents:
            title = self.get_field_with_fallback(patent, "title", ["name"], "Patent")
            patent_number = patent.get("patentNumber", "")
            status = patent.get("status", "")
            date = self.get_field_with_fallback(patent, "date", ["year", "filed"], "")

            patent_str = f"\\textbf{{{title}}}"
            if patent_number:
                patent_str += f" (Patent No. {patent_number})"
            if status:
                patent_str += f" -- {status}"
            if date:
                patent_str += f", {date}"

            items.append(f"\\item {patent_str}")

        items_str = "\n".join(items)
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{items_str}\\end{{highlights}}\\end{{onecolentry}}"

    def generate_industry_expertise(self):
        """Generate Industry Expertise section."""
        expertise = self.get_field_with_fallback(
            self.data, "industryExpertise", ["industryExperience", "domains"], []
        )
        if not expertise:
            return ""

        items = []
        for industry in expertise:
            if isinstance(industry, str):
                items.append(f"\\item {industry}")
            else:
                name = self.get_field_with_fallback(industry, "name", ["industry", "domain"], "Industry")
                years = industry.get("years", "")
                description = industry.get("description", "")

                industry_str = f"\\textbf{{{name}}}"
                if years:
                    industry_str += f" ({years} years)"
                if description:
                    industry_str += f": {description}"

                items.append(f"\\item {industry_str}")

        items_str = "\n".join(items)
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{items_str}\\end{{highlights}}\\end{{onecolentry}}"

    def generate_referral(self):
        """Generate Referral section (who referred you)."""
        referral = self.get_field_with_fallback(
            self.data, "referral", ["referredBy"], {}
        )
        if not referral:
            return ""

        if isinstance(referral, str):
            # Simple text like "Referred by John Doe"
            return f"\\begin{{onecolentry}}\n{referral}\\end{{onecolentry}}"

        # Detailed referral info
        name = self.get_field_with_fallback(referral, "name", ["referralName"], "")
        title = self.get_field_with_fallback(referral, "title", ["position"], "")
        company = self.get_field_with_fallback(referral, "company", ["organization"], "")
        relationship = referral.get("relationship", "")
        email = referral.get("email", "")

        if not name:
            return ""

        referral_str = f"Referred by \\textbf{{{name}}}"
        if title:
            referral_str += f", {title}"
        if company:
            referral_str += f" at {company}"
        if relationship:
            referral_str += f" ({relationship})"

        return f"\\begin{{onecolentry}}\n{referral_str}\\end{{onecolentry}}"

    def generate_references(self):
        """Generate References section."""
        references = self.get_field_with_fallback(
            self.data, "references", ["professionalReferences"], []
        )
        if not references:
            # Check if there's a simple string indicating references available
            ref_text = self.data.get("referencesAvailable", "")
            if ref_text:
                return f"\\begin{{onecolentry}}\n{ref_text}\\end{{onecolentry}}"
            return ""

        if isinstance(references, str):
            # Simple text like "Available upon request"
            return f"\\begin{{onecolentry}}\n{references}\\end{{onecolentry}}"

        # Detailed references
        items = []
        for ref in references:
            name = self.get_field_with_fallback(ref, "name", ["referenceName"], "")
            title = self.get_field_with_fallback(ref, "title", ["position"], "")
            company = self.get_field_with_fallback(ref, "company", ["organization"], "")
            email = ref.get("email", "")
            phone = ref.get("phone", "")

            ref_str = f"\\textbf{{{name}}}"
            if title:
                ref_str += f", {title}"
            if company:
                ref_str += f" at {company}"

            contact_parts = []
            if email:
                contact_parts.append(f"\\href{{mailto:{email}}}{{{email}}}")
            if phone:
                contact_parts.append(phone)

            if contact_parts:
                ref_str += f" ({', '.join(contact_parts)})"

            items.append(f"\\item {ref_str}")

        items_str = "\n".join(items)
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{items_str}\\end{{highlights}}\\end{{onecolentry}}"

    def generate_resume(self):
        """Generate the final LaTeX resume by replacing placeholders."""
        self.data["personalInfo"]

        # Generate content for each section using unified pattern
        personal_info = self.generate_personal_info()

        # Use the unified section generation pattern for all sections
        professional_summary = self.generate_section_with_header(
            "professional_summary",
            self.generate_professional_summary,
            "Professional Summary",
        )

        # Check if both core competencies and technical skills exist - if so, merge them
        has_core_competencies = bool(self.get_field_with_fallback(
            self.data, "coreCompetencies", ["competencies", "keySkills", "expertise"], []
        ))
        has_technical_skills = bool(self.get_field_with_fallback(
            self.data, "technicalSkills", ["techSkills"], {}
        ))

        # If both exist, use merged section; otherwise use individual sections
        if has_core_competencies and has_technical_skills:
            core_competencies = self.generate_section_with_header(
                "core_competencies_and_technical_skills",
                self.generate_core_competencies_and_technical_skills,
                "Core Competencies \\& Technical Skills",
            )
            technical_skills = ""  # Skip separate technical skills section
        else:
            core_competencies = self.generate_section_with_header(
                "core_competencies",
                self.generate_core_competencies,
                "Core Competencies",
            )
            technical_skills = self.generate_section_with_header(
                "technical_skills",
                self.generate_technical_skills,
                "Technical Skills",
            )

        leadership_experience = self.generate_section_with_header(
            "leadership_experience",
            self.generate_leadership_experience,
            "Leadership Experience",
        )
        experience = self.generate_section_with_header(
            "experience", self.generate_experience, "Experience"
        )
        education = self.generate_section_with_header(
            "education", self.generate_education, "Education"
        )
        relevant_coursework = self.generate_section_with_header(
            "relevant_coursework",
            self.generate_relevant_coursework,
            "Relevant Coursework",
        )
        skills_matrix = self.generate_section_with_header(
            "skills_matrix",
            self.generate_skills_matrix,
            "Skills Matrix",
        )
        technologies_and_skills = self.generate_section_with_header(
            "technologies_and_skills",
            self.generate_technologies_and_skills,
            "Technologies \\& Skills",
        )
        projects = self.generate_section_with_header(
            "projects", self.generate_projects, "Projects"
        )
        open_source_contributions = self.generate_section_with_header(
            "open_source_contributions",
            self.generate_open_source_contributions,
            "Open Source Contributions",
        )
        research_experience = self.generate_section_with_header(
            "research_experience",
            self.generate_research_experience,
            "Research Experience",
        )
        publications = self.generate_section_with_header(
            "publications",
            self.generate_publications,
            "Publications",
        )
        technical_writing = self.generate_section_with_header(
            "technical_writing",
            self.generate_technical_writing,
            "Technical Writing",
        )
        articles_and_publications = self.generate_section_with_header(
            "articles_and_publications",
            self.generate_articles_and_publications,
            "Articles \\& Publications",
        )
        speaking_engagements = self.generate_section_with_header(
            "speaking_engagements",
            self.generate_speaking_engagements,
            "Speaking Engagements",
        )
        awards_and_honors = self.generate_section_with_header(
            "awards_and_honors",
            self.generate_awards_and_honors,
            "Awards \\& Honors",
        )
        achievements = self.generate_section_with_header(
            "achievements", self.generate_achievements, "Achievements"
        )
        certifications = self.generate_section_with_header(
            "certifications", self.generate_certifications, "Certifications"
        )
        teaching_experience = self.generate_section_with_header(
            "teaching_experience",
            self.generate_teaching_experience,
            "Teaching Experience",
        )
        mentorship = self.generate_section_with_header(
            "mentorship",
            self.generate_mentorship,
            "Mentorship",
        )
        volunteering = self.generate_section_with_header(
            "volunteering",
            self.generate_volunteering,
            "Volunteering \\& Community Service",
        )
        languages = self.generate_section_with_header(
            "languages",
            self.generate_languages,
            "Languages",
        )
        professional_affiliations = self.generate_section_with_header(
            "professional_affiliations",
            self.generate_professional_affiliations,
            "Professional Affiliations",
        )
        patents = self.generate_section_with_header(
            "patents",
            self.generate_patents,
            "Patents \\& Intellectual Property",
        )
        industry_expertise = self.generate_section_with_header(
            "industry_expertise",
            self.generate_industry_expertise,
            "Industry Expertise",
        )
        referral = self.generate_section_with_header(
            "referral",
            self.generate_referral,
            "Referral",
        )
        references = self.generate_section_with_header(
            "references",
            self.generate_references,
            "References",
        )

        # Generate spacing configuration
        spacing_config = self.generate_spacing_config()

        # Section replacements - all sections are optional
        section_replacements = {
            "{{spacing_mode}}": spacing_config,
            "{{personal_info}}": personal_info,
            "{{professional_summary}}": professional_summary,
            "{{core_competencies}}": core_competencies,
            "{{leadership_experience}}": leadership_experience,
            "{{experience}}": experience,
            "{{education}}": education,
            "{{relevant_coursework}}": relevant_coursework,
            "{{technical_skills}}": technical_skills,
            "{{skills_matrix}}": skills_matrix,
            "{{technologies_and_skills}}": technologies_and_skills,
            "{{projects}}": projects,
            "{{open_source_contributions}}": open_source_contributions,
            "{{research_experience}}": research_experience,
            "{{publications}}": publications,
            "{{technical_writing}}": technical_writing,
            "{{articles_and_publications}}": articles_and_publications,
            "{{speaking_engagements}}": speaking_engagements,
            "{{awards_and_honors}}": awards_and_honors,
            "{{achievements}}": achievements,
            "{{certifications}}": certifications,
            "{{teaching_experience}}": teaching_experience,
            "{{mentorship}}": mentorship,
            "{{volunteering}}": volunteering,
            "{{languages}}": languages,
            "{{professional_affiliations}}": professional_affiliations,
            "{{patents}}": patents,
            "{{industry_expertise}}": industry_expertise,
            "{{referral}}": referral,
            "{{references}}": references,
        }

        resume = self.template
        for placeholder, content in section_replacements.items():
            resume = resume.replace(placeholder, content)

        # Check for unreplaced placeholders
        if re.search(r"{{.*?}}", resume):
            unreplaced_matches = re.findall(r"{{(.*?)}}", resume)
            raise TemplateRenderingException(
                template_name="classic",
                details=f"Unreplaced placeholders detected: {', '.join(unreplaced_matches)}",
            )

        return resume

    def render(self) -> str:
        """Render the template to LaTeX content"""
        return self.generate_resume()

    def analyze_document(self) -> dict[str, Any]:
        """
        Analyze document content and spacing to help optimize for page length.

        Returns detailed metrics including:
        - Word count per section
        - Character count and density
        - Current spacing configuration
        - Line estimates
        - Page overflow predictions
        """
        analysis = {
            "spacing_mode": self.spacing_mode,
            "spacing_config": self._get_spacing_values(),
            "content_metrics": {},
            "section_analysis": [],
            "total_metrics": {
                "total_words": 0,
                "total_characters": 0,
                "total_lines_estimate": 0,
                "estimated_pages": 0
            },
            "recommendations": []
        }

        # Analyze each section
        sections_to_analyze = [
            ("professionalSummary", "Professional Summary"),
            ("coreCompetencies", "Core Competencies"),
            ("leadershipExperience", "Leadership Experience"),
            ("experience", "Experience"),
            ("education", "Education"),
            ("relevantCoursework", "Relevant Coursework"),
            ("technicalSkills", "Technical Skills"),
            ("skillsMatrix", "Skills Matrix"),
            ("technologiesAndSkills", "Technologies & Skills"),
            ("projects", "Projects"),
            ("openSourceContributions", "Open Source Contributions"),
            ("researchExperience", "Research Experience"),
            ("publications", "Publications"),
            ("technicalWriting", "Technical Writing"),
            ("articlesAndPublications", "Articles & Publications"),
            ("speakingEngagements", "Speaking Engagements"),
            ("awardsAndHonors", "Awards & Honors"),
            ("achievements", "Achievements"),
            ("certifications", "Certifications"),
            ("teachingExperience", "Teaching Experience"),
            ("mentorship", "Mentorship"),
            ("volunteering", "Volunteering"),
            ("languages", "Languages"),
            ("professionalAffiliations", "Professional Affiliations"),
            ("patents", "Patents"),
            ("industryExpertise", "Industry Expertise"),
        ]

        total_words = 0
        total_chars = 0
        total_lines = 0

        for field_name, display_name in sections_to_analyze:
            section_data = self.data.get(field_name)
            if section_data:
                metrics = self._analyze_section_content(section_data, display_name)
                analysis["section_analysis"].append(metrics)

                total_words += metrics["word_count"]
                total_chars += metrics["character_count"]
                total_lines += metrics["estimated_lines"]

        # Update totals
        analysis["total_metrics"]["total_words"] = total_words
        analysis["total_metrics"]["total_characters"] = total_chars
        analysis["total_metrics"]["total_lines_estimate"] = total_lines

        # Estimate pages based on spacing mode
        # ultra-compact: ~58 lines/page, compact: ~52 lines/page, normal: ~45 lines/page
        if self.spacing_mode == "ultra-compact":
            lines_per_page = 58
        elif self.spacing_mode == "compact":
            lines_per_page = 52
        else:  # normal
            lines_per_page = 45
        estimated_pages = max(1, (total_lines + lines_per_page - 1) // lines_per_page)
        analysis["total_metrics"]["estimated_pages"] = estimated_pages

        # Add recommendations
        analysis["recommendations"] = self._generate_recommendations(
            total_words, total_lines, estimated_pages
        )

        return analysis

    def _get_spacing_values(self) -> dict[str, str]:
        """Get current spacing configuration values"""
        if self.spacing_mode == "compact":
            return {
                "margin_top": "0.5cm",
                "margin_bottom": "0.5cm",
                "margin_left": "0.6cm",
                "margin_right": "0.6cm",
                "section_spacing_before": "0.2cm",
                "section_spacing_after": "0.15cm",
                "item_top_sep": "0.05cm",
                "item_parse_sep": "0.05cm",
                "item_sep": "0pt"
            }
        elif self.spacing_mode == "ultra-compact":
            return {
                "margin_top": "0.4cm",
                "margin_bottom": "0.4cm",
                "margin_left": "0.5cm",
                "margin_right": "0.5cm",
                "section_spacing_before": "0.15cm",
                "section_spacing_after": "0.1cm",
                "item_top_sep": "0.03cm",
                "item_parse_sep": "0.03cm",
                "item_sep": "0pt"
            }
        else:  # normal
            return {
                "margin_top": "0.8cm",
                "margin_bottom": "0.8cm",
                "margin_left": "0.8cm",
                "margin_right": "0.8cm",
                "section_spacing_before": "0.3cm",
                "section_spacing_after": "0.2cm",
                "item_top_sep": "0.10cm",
                "item_parse_sep": "0.10cm",
                "item_sep": "0pt"
            }

    def _analyze_section_content(self, content: Any, section_name: str) -> dict[str, Any]:
        """Analyze content metrics for a section"""
        text = self._extract_text_from_content(content)
        words = text.split()
        word_count = len(words)
        char_count = len(text)

        # Estimate lines (assuming ~80 chars per line on average)
        chars_per_line = 75
        estimated_lines = max(1, (char_count + chars_per_line - 1) // chars_per_line)

        # Add overhead for section header and spacing
        estimated_lines += 2  # Section header + spacing

        return {
            "section_name": section_name,
            "word_count": word_count,
            "character_count": char_count,
            "estimated_lines": estimated_lines,
            "average_word_length": round(char_count / word_count, 2) if word_count > 0 else 0,
            "density": "high" if word_count > 100 else "medium" if word_count > 50 else "low"
        }

    def _extract_text_from_content(self, content: Any) -> str:
        """Recursively extract all text from nested data structures"""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            return " ".join(self._extract_text_from_content(item) for item in content)
        elif isinstance(content, dict):
            return " ".join(
                self._extract_text_from_content(value)
                for key, value in content.items()
                if key not in ["url", "website", "linkedin", "github", "email", "phone"]
            )
        return ""

    def _generate_recommendations(
        self, total_words: int, total_lines: int, estimated_pages: int
    ) -> list[str]:
        """Generate recommendations for content optimization"""
        recommendations = []

        if estimated_pages > 2:
            recommendations.append(
                f"Content is estimated to span {estimated_pages} pages. "
                "Consider switching to 'ultra-compact' spacing mode or reducing content."
            )

        if estimated_pages > 1.5 and self.spacing_mode == "normal":
            recommendations.append(
                "Current spacing is 'normal'. Switching to 'compact' mode "
                "could reduce document to 1-2 pages."
            )

        if total_words > 800:
            recommendations.append(
                f"Document has {total_words} words. For optimal readability, "
                "consider keeping it under 700 words for 1-page resumes."
            )

        if total_lines > 100 and self.spacing_mode == "compact":
            recommendations.append(
                "Document has many lines even in compact mode. "
                "Consider using bullet points instead of paragraphs, or switching to 'ultra-compact' mode."
            )

        if not recommendations:
            recommendations.append(
                f"Document is well-optimized at ~{estimated_pages} pages with {total_words} words."
            )

        return recommendations

    @property
    def required_fields(self) -> list[str]:
        """List of required data fields for this template"""
        return [
            "personalInfo",  # Only personalInfo is truly required
        ]

    @property
    def template_type(self) -> DocumentType:
        """The document type this template handles"""
        return DocumentType.RESUME

    def export_to_pdf(self, output_path: str = "output.pdf") -> str:
        """Compile LaTeX content to PDF using pdflatex"""
        self.output_path = output_path
        content = self.generate_resume()

        # Ensure pdflatex is in PATH by adding common TeX installation paths
        env = os.environ.copy()
        tex_paths = [
            "/Library/TeX/texbin",
            "/usr/local/texlive/2025basic/bin/universal-darwin",
            "/usr/local/texlive/2024/bin/universal-darwin",
            "/usr/local/bin",
            "/opt/homebrew/bin",
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
                result = subprocess.run(
                    [
                        "pdflatex",
                        "-interaction=nonstopmode",
                        f"-output-directory={tmpdir}",
                        tex_path,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
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
                    capture_output=True,
                    text=True,
                    env=env,
                )
            except subprocess.CalledProcessError as e:
                log_output = (e.stdout or "") + (e.stderr or "")
                # Get last 1000 chars of log for debugging
                log_tail = log_output[-1000:] if len(log_output) > 1000 else log_output
                raise LaTeXCompilationException(
                    details=f"PDF compilation failed: {log_tail}",
                    template_name="classic",
                    context={"return_code": e.returncode, "log": log_tail},
                ) from e
            except FileNotFoundError as e:
                raise DependencyException(
                    dependency="pdflatex",
                    context={
                        "details": "pdflatex not found. Please install BasicTeX or MacTeX:\n"
                        "brew install --cask basictex\n"
                        'Then restart your terminal or run: eval "$(/usr/libexec/path_helper)"'
                    },
                ) from e

            pdf_path = os.path.join(tmpdir, "temp.pdf")
            if os.path.exists(pdf_path):
                os.replace(pdf_path, output_path)
            else:
                raise PDFGenerationException(
                    details="PDF output not generated", template_name="classic"
                )

        return output_path

    # Optional DOCX export using pandoc if available
    def export_to_docx(self, output_path: str = "output.docx") -> str:
        content = self.generate_resume()
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_path = os.path.join(tmpdir, "temp.tex")
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(content)

            try:
                subprocess.run(
                    ["pandoc", tex_path, "-o", output_path],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                )
            except FileNotFoundError as e:
                raise DependencyException(
                    dependency="pandoc",
                    context={"details": "pandoc not found. Install via brew install pandoc"},
                ) from e
            except subprocess.CalledProcessError as e:
                raise TemplateRenderingException(
                    template_name="classic",
                    details=f"pandoc failed with return code {e.returncode}",
                ) from e

        return output_path
