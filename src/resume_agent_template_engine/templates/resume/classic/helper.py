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
    DependencyException,
)


class ClassicResumeTemplate(TemplateInterface):
    """
    Helper class for generating a Classic LaTeX resume from JSON data.
    Handles special characters: &, %, $, #
    """

    def __init__(self, data: Dict[str, Any], config: Dict[str, Any] = None) -> None:
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

        try:
            with open(self.template_path, "r", encoding="utf-8") as f:
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
        fallback_fields: List[str] = None,
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

    def generate_personal_info(self) -> str:
        """
        Generate the header block dynamically from self.data['personalInfo'].
        """
        info = self.data["personalInfo"]
        # You want the exact same formatting you had before, but built from code
        header_lines = []
        header_lines.append(r"\begin{header}")
        header_lines.append(r"    \fontsize{25pt}{25pt}\selectfont " + info["name"])
        header_lines.append(r"    \vspace{2pt}")
        header_lines.append(r"    \normalsize")
        # Build the contact line pieces
        parts = []

        # Only add location if it exists
        if info.get("location"):
            parts.append(r"\mbox{ " + info["location"] + r" }")

        # Email is required, so always add it
        parts.append(
            r"\mbox{\href{mailto:" + info["email"] + r"}{" + info["email"] + r"}}"
        )

        # Only add phone if it exists
        if info.get("phone"):
            parts.append(
                r"\mbox{\href{tel:" + info["phone"] + r"}{" + info["phone"] + r"}}"
            )

        # Add optional social links only if both URL and display text exist
        if info.get("website") and info.get("website_display"):
            parts.append(
                r"\mbox{\href{"
                + info["website"]
                + r"}{"
                + info["website_display"]
                + r"}}"
            )
        if info.get("linkedin") and info.get("linkedin_display"):
            parts.append(
                r"\mbox{\href{"
                + info["linkedin"]
                + r"}{"
                + info["linkedin_display"]
                + r"}}"
            )
        if info.get("github") and info.get("github_display"):
            parts.append(
                r"\mbox{\href{"
                + info["github"]
                + r"}{"
                + info["github_display"]
                + r"}}"
            )
        if info.get("twitter") and info.get("twitter_display"):
            parts.append(
                r"\mbox{\href{"
                + info["twitter"]
                + r"}{"
                + info["twitter_display"]
                + r"}}"
            )
        if info.get("x") and info.get("x_display"):
            parts.append(
                r"\mbox{\href{" + info["x"] + r"}{" + info["x_display"] + r"}}"
            )

        # Join them with the \AND separators exactly as before
        contact_line = " \\kern 3pt \\AND \\kern 3pt ".join(parts)
        header_lines.append(r"    " + contact_line)
        header_lines.append(r"\end{header}")
        return "\n".join(header_lines)

    def generate_professional_summary(self):
        """Generate the Professional Summary section."""
        if not self.data.get("professionalSummary"):
            return ""
        return f"\\begin{{onecolentry}}{self.data['professionalSummary']}\\end{{onecolentry}}"

    def generate_education(self):
        """Generate the Education section."""
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
        """Generate the Experience section."""
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

            entry = (
                f"\\textbf{{{title}}}, {company} \\hfill {date_range}\n"
                "\\begin{highlights}\n"
                + "\n".join([f"\\item {ach}" for ach in achievements])
                + "\n\\end{highlights}"
            )
            sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")
        return "\n".join(sections)

    def generate_projects(self):
        """Generate the Projects section."""
        if not self.data.get("projects"):
            return ""
        sections = []
        for proj in self.data["projects"]:
            # Use fallback logic for project name
            name = self.get_field_with_fallback(
                proj, "name", ["title", "project_name"], "Project"
            )

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
        """Generate the Certifications section."""
        # Check multiple possible field names
        certifications = self.get_field_with_fallback(
            self.data, "certifications", ["certificates", "credentials", "licenses"], []
        )
        if not certifications:
            return ""
        bullets = "\n".join(f"\\item {item}" for item in certifications)
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{bullets}\\end{{highlights}}\\end{{onecolentry}}"

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
        from datetime import datetime

        date = self.data.get("date", "")
        if date:
            return date

        # For resumes, we typically don't auto-generate dates
        # but this provides consistency with cover letter template
        return ""

    def generate_resume(self):
        """Generate the final LaTeX resume by replacing placeholders."""
        info = self.data["personalInfo"]

        # Generate content for each section using unified pattern
        personal_info = self.generate_personal_info()

        # Use the unified section generation pattern
        professional_summary = self.generate_section_with_header(
            "professional_summary",
            self.generate_professional_summary,
            "Professional Summary",
        )
        education = self.generate_section_with_header(
            "education", self.generate_education, "Education"
        )
        experience = self.generate_section_with_header(
            "experience", self.generate_experience, "Experience"
        )
        projects = self.generate_section_with_header(
            "projects", self.generate_projects, "Projects"
        )
        articles_and_publications = self.generate_section_with_header(
            "articles_and_publications",
            self.generate_articles_and_publications,
            "Articles \\& Publications",
        )
        achievements = self.generate_section_with_header(
            "achievements", self.generate_achievements, "Achievements"
        )
        certifications = self.generate_section_with_header(
            "certifications", self.generate_certifications, "Certifications"
        )
        technologies_and_skills = self.generate_section_with_header(
            "technologies_and_skills",
            self.generate_technologies_and_skills,
            "Technologies \\& Skills",
        )

        # Section replacements
        section_replacements = {
            "{{personal_info}}": personal_info,
            "{{professional_summary}}": professional_summary,
            "{{education}}": education,
            "{{experience}}": experience,
            "{{projects}}": projects,
            "{{articles_and_publications}}": articles_and_publications,
            "{{achievements}}": achievements,
            "{{certifications}}": certifications,
            "{{technologies_and_skills}}": technologies_and_skills,
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

    @property
    def required_fields(self) -> List[str]:
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
                    context={"return_code": e.returncode},
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
