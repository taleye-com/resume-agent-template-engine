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


class TwoColumnResumeTemplate(TemplateInterface):
    """
    Helper class for generating a Two-Column LaTeX resume from JSON data.
    Features a sidebar with contact info and skills, main content with experience.
    Handles special characters: &, %, $, #
    """

    def __init__(self, data: dict[str, Any], config: dict[str, Any] = None) -> None:
        """
        Initialize the TwoColumnResumeTemplate class.

        Args:
            data (dict): The JSON data containing resume information.
            config (dict): Template-specific configuration.
        """
        # Initialize parent class
        super().__init__(data, config)

        self.data = self.replace_special_chars(data)
        self.output_path: str = "output.pdf"
        self.template_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_path = os.path.join(self.template_dir, "two_column.tex")

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

    def generate_personal_info(self) -> str:
        """
        Generate the header block dynamically from self.data['personalInfo'].
        Creates a clean header layout for two-column design.
        """
        info = self.data["personalInfo"]
        header_lines = []
        header_lines.append(r"\begin{header}")

        # Name (large font, centered) - force line break after
        header_lines.append(
            r"    \fontsize{20pt}{20pt}\selectfont\bfseries\color{primaryColor} "
            + info["name"]
            + r" \\"
        )
        header_lines.append(r"    \vspace{3pt}")

        header_lines.append(r"\end{header}")
        return "\n".join(header_lines)

    def generate_sidebar_contact(self) -> str:
        """Generate sidebar contact information"""
        if not self.data.get("personalInfo"):
            return ""

        info = self.data["personalInfo"]
        contact_lines = []

        # Contact section header
        contact_lines.append(r"{\large\bfseries\MakeUppercase{Contact}}")
        contact_lines.append(r"\vspace{0.2cm}")
        contact_lines.append(r"\hrule")
        contact_lines.append(r"\vspace{0.3cm}")

        # Email
        if info.get("email"):
            contact_lines.append(
                r"\contactitem{Email}{\href{mailto:"
                + info["email"]
                + r"}{"
                + info["email"]
                + r"}}"
            )

        # Phone
        if info.get("phone"):
            contact_lines.append(
                r"\contactitem{Phone}{\href{tel:"
                + info["phone"]
                + r"}{"
                + info["phone"]
                + r"}}"
            )

        # Location
        if info.get("location"):
            contact_lines.append(r"\contactitem{Location}{" + info["location"] + r"}")

        # Website
        if info.get("website") and info.get("website_display"):
            contact_lines.append(
                r"\contactitem{Website}{\href{"
                + info["website"]
                + r"}{"
                + info["website_display"]
                + r"}}"
            )

        # LinkedIn
        if info.get("linkedin") and info.get("linkedin_display"):
            contact_lines.append(
                r"\contactitem{LinkedIn}{\href{"
                + info["linkedin"]
                + r"}{"
                + info["linkedin_display"]
                + r"}}"
            )

        # GitHub
        if info.get("github") and info.get("github_display"):
            contact_lines.append(
                r"\contactitem{GitHub}{\href{"
                + info["github"]
                + r"}{"
                + info["github_display"]
                + r"}}"
            )

        return "\n".join(contact_lines)

    def generate_sidebar_skills(self) -> str:
        """Generate sidebar skills section"""
        skills_data = self.get_field_with_fallback(
            self.data,
            "technologiesAndSkills",
            ["skills", "technologies", "tech_skills"],
            [],
        )

        if not skills_data:
            return ""

        skills_lines = []
        skills_lines.append(r"{\large\bfseries\MakeUppercase{Skills}}")
        skills_lines.append(r"\vspace{0.2cm}")
        skills_lines.append(r"\hrule")
        skills_lines.append(r"\vspace{0.3cm}")

        if isinstance(skills_data, list) and all(
            isinstance(skill, str) for skill in skills_data
        ):
            # Simple list of skills
            skills_lines.append(r"\skillslist{" + ", ".join(skills_data) + r"}")
        elif isinstance(skills_data, dict):
            # Dictionary-based skills (e.g., {"technical": [...], "soft": [...]})
            for category, skill_list in skills_data.items():
                if isinstance(skill_list, list) and skill_list:
                    # Ensure all items are strings
                    skill_strings = [str(skill) for skill in skill_list]
                    skills_lines.append(r"\textbf{" + str(category).title() + r"} \\")
                    skills_lines.append(r"\skillslist{" + ", ".join(skill_strings) + r"}")
        else:
            # Structured skills with categories
            for skill_group in skills_data:
                if isinstance(skill_group, dict):
                    category = self.get_field_with_fallback(
                        skill_group, "category", ["name", "type"], "Skills"
                    )
                    skill_list = self.get_field_with_fallback(
                        skill_group, "skills", ["items", "technologies"], []
                    )

                    if skill_list and isinstance(skill_list, list):
                        # Ensure all items are strings
                        skill_strings = [str(skill) for skill in skill_list]
                        skills_lines.append(r"\textbf{" + str(category) + r"} \\")
                        skills_lines.append(r"\skillslist{" + ", ".join(skill_strings) + r"}")

        return "\n".join(skills_lines)

    def generate_sidebar_education(self) -> str:
        """Generate sidebar education section"""
        if not self.data.get("education"):
            return ""

        education_lines = []
        education_lines.append(r"{\large\bfseries\MakeUppercase{Education}}")
        education_lines.append(r"\vspace{0.2cm}")
        education_lines.append(r"\hrule")
        education_lines.append(r"\vspace{0.3cm}")

        for edu in self.data["education"]:
            degree = self.get_field_with_fallback(
                edu, "degree", ["title", "qualification"], "Degree"
            )
            institution = self.get_field_with_fallback(
                edu, "institution", ["school", "university", "college"], "Institution"
            )
            end_date = self.get_field_with_fallback(
                edu, "endDate", ["end_date", "date", "graduationDate"], ""
            )
            focus = self.get_field_with_fallback(
                edu, "focus", ["major", "specialization", "concentration"], ""
            )

            education_lines.append(
                r"\educationentry{"
                + degree
                + r"}{"
                + institution
                + r"}{"
                + end_date
                + r"}{"
                + focus
                + r"}"
            )

        return "\n".join(education_lines)

    def _extract_cert_icon(self, cert_text: str) -> tuple[str, str]:
        """
        Extract source icon from certification text.
        Returns: (icon, clean_name)
        """
        # Icon mapping
        icon_map = {
            "linkedin": "LI",
            "hackerrank": "HR",
            "workato": "WK",
            "coursera": "CR",
            "udemy": "UD",
            "edx": "EX",
            "aws": "AWS",
            "google": "GG",
            "microsoft": "MS",
        }

        cert_lower = cert_text.lower()

        # Check for source in parentheses
        if "(" in cert_text and ")" in cert_text:
            # Extract source from parentheses
            start_idx = cert_text.rfind("(")
            end_idx = cert_text.rfind(")")
            source = cert_text[start_idx + 1 : end_idx].strip().lower()
            clean_name = cert_text[:start_idx].strip()

            # Map source to icon
            for key, icon in icon_map.items():
                if key in source:
                    return icon, clean_name

        # Check for dash-separated source
        if " - " in cert_text:
            parts = cert_text.rsplit(" - ", 1)
            if len(parts) == 2:
                clean_name = parts[0].strip()
                source = parts[1].strip().lower()

                for key, icon in icon_map.items():
                    if key in source:
                        return icon, clean_name

        # Default: no icon found, return original
        return "", cert_text

    def _format_category_name(self, category_key: str) -> str:
        """
        Format category key to display name.
        e.g., 'ai_ml' -> 'AI ML', 'cloud_architecture' -> 'Cloud Architecture'
        """
        # Replace underscores with spaces and title case each word
        return category_key.replace("_", " ").title()

    def generate_sidebar_certifications(self) -> str:
        """Generate sidebar certifications section in compact comma-separated format"""
        certifications = self.get_field_with_fallback(
            self.data, "certifications", ["certificates", "credentials", "licenses"], {}
        )

        if not certifications:
            return ""

        output = []
        output.append(r"{\large\bfseries\MakeUppercase{Certifications}}")
        output.append(r"\vspace{0.2cm}")
        output.append(r"\hrule")
        output.append(r"\vspace{0.2cm}")

        # Handle dictionary format: {"ai_ml": [...], "cloud": [...]}
        if isinstance(certifications, dict):
            for category_key, items in certifications.items():
                if not items or not isinstance(items, list):
                    continue

                category_name = self._format_category_name(category_key)

                # Extract all certification names
                cert_names = []
                for cert in items:
                    _, clean_name = self._extract_cert_icon(str(cert))
                    cert_names.append(clean_name)

                # Create single paragraph for category
                output.append(r"\noindent\textbf{\small " + category_name + r":} ")
                output.append(r"\small " + ", ".join(cert_names))
                output.append(r"\\[0.3cm]")

        # Handle list format: [{"category": "AI", "items": [...]}, ...]
        elif isinstance(certifications, list):
            if certifications and isinstance(certifications[0], dict):
                for cert_group in certifications:
                    category = cert_group.get("category", "")
                    items = cert_group.get("items", [])

                    if not items:
                        continue

                    # Extract all certification names
                    cert_names = []
                    for cert in items:
                        _, clean_name = self._extract_cert_icon(str(cert))
                        cert_names.append(clean_name)

                    # Create single paragraph for category
                    output.append(r"\noindent\textbf{\small " + str(category) + r":} ")
                    output.append(r"\small " + ", ".join(cert_names))
                    output.append(r"\\[0.3cm]")
            else:
                # Flat list - all certs in one paragraph
                cert_names = []
                for cert in certifications:
                    _, clean_name = self._extract_cert_icon(str(cert))
                    cert_names.append(clean_name)

                output.append(r"\small " + ", ".join(cert_names))

        return "\n".join(output)

    def generate_professional_summary(self) -> str:
        """Generate professional summary section"""
        if not self.data.get("professionalSummary"):
            return ""

        summary_lines = []
        summary_lines.append(r"\mainsection{Professional Summary}")
        summary_lines.append(self.data["professionalSummary"])
        summary_lines.append(r"\vspace{0.3cm}")

        return "\n".join(summary_lines)

    def generate_experience(self) -> str:
        """Generate experience section"""
        if not self.data.get("experience"):
            return ""

        exp_lines = []
        exp_lines.append(r"\mainsection{Experience}")

        for exp in self.data["experience"]:
            title = self.get_field_with_fallback(
                exp, "title", ["position", "role"], "Position"
            )
            company = self.get_field_with_fallback(
                exp, "company", ["employer", "organization"], "Company"
            )
            location = exp.get("location", "")
            start_date = exp.get("startDate", "")
            end_date = self.get_field_with_fallback(
                exp, "endDate", ["end_date"], "Present"
            )

            date_range = f"{start_date} - {end_date}" if start_date else end_date

            achievements = self.get_field_with_fallback(
                exp, "achievements", ["details", "responsibilities", "duties"], []
            )

            exp_lines.append(
                r"\begin{experienceentry}{"
                + title
                + r"}{"
                + date_range
                + r"}{"
                + company
                + r"}{"
                + location
                + r"}"
            )

            for achievement in achievements:
                exp_lines.append(r"\item " + str(achievement))

            exp_lines.append(r"\end{experienceentry}")

        return "\n".join(exp_lines)

    def generate_projects(self) -> str:
        """Generate projects section"""
        if not self.data.get("projects"):
            return ""

        project_lines = []
        project_lines.append(r"\mainsection{Projects}")

        for proj in self.data["projects"]:
            name = self.get_field_with_fallback(
                proj, "name", ["title", "project_name"], "Project"
            )
            description = self.get_field_with_fallback(
                proj, "description", ["summary", "desc"], ""
            )
            tools = self.get_field_with_fallback(
                proj, "tools", ["technologies", "tech_stack", "stack"], []
            )

            project_lines.append(r"\textbf{" + str(name) + r"} \\")
            if description:
                project_lines.append(str(description) + r" \\")
            if tools and isinstance(tools, list):
                tool_strings = [str(tool) for tool in tools]
                project_lines.append(
                    r"\textit{Technologies: " + ", ".join(tool_strings) + r"} \\[0.3cm]"
                )

        return "\n".join(project_lines)

    def generate_achievements(self) -> str:
        """Generate achievements section"""
        achievements = self.get_field_with_fallback(
            self.data, "achievements", ["accomplishments", "awards", "honors"], []
        )

        if not achievements:
            return ""

        achievement_lines = []
        achievement_lines.append(r"\mainsection{Achievements}")

        for achievement in achievements:
            achievement_lines.append(r"• " + str(achievement) + r" \\")

        achievement_lines.append(r"\vspace{0.3cm}")
        return "\n".join(achievement_lines)

    def generate_publications(self) -> str:
        """Generate publications section"""
        publications = self.get_field_with_fallback(
            self.data,
            "articlesAndPublications",
            ["publications", "articles", "papers"],
            [],
        )

        if not publications:
            return ""

        pub_lines = []
        pub_lines.append(r"\mainsection{Publications}")

        for pub in publications:
            title = self.get_field_with_fallback(pub, "title", ["name"], "Publication")
            date = self.get_field_with_fallback(
                pub, "date", ["published_date", "year"], ""
            )

            pub_lines.append(r"• \textbf{" + str(title) + r"}")
            if date:
                pub_lines.append(r" (" + str(date) + r")")
            pub_lines.append(r" \\")

        pub_lines.append(r"\vspace{0.3cm}")
        return "\n".join(pub_lines)

    def generate_resume(self):
        """Generate the final LaTeX resume by replacing placeholders."""
        # Generate content for each section
        personal_info = self.generate_personal_info()
        sidebar_contact = self.generate_sidebar_contact()
        sidebar_skills = self.generate_sidebar_skills()
        sidebar_education = self.generate_sidebar_education()
        sidebar_certifications = self.generate_sidebar_certifications()
        professional_summary = self.generate_professional_summary()
        experience = self.generate_experience()
        projects = self.generate_projects()
        achievements = self.generate_achievements()
        publications = self.generate_publications()

        # Section replacements
        section_replacements = {
            "{{personal_info}}": personal_info,
            "{{sidebar_contact}}": sidebar_contact,
            "{{sidebar_skills}}": sidebar_skills,
            "{{sidebar_education}}": sidebar_education,
            "{{sidebar_certifications}}": sidebar_certifications,
            "{{professional_summary}}": professional_summary,
            "{{experience}}": experience,
            "{{projects}}": projects,
            "{{achievements}}": achievements,
            "{{publications}}": publications,
        }

        resume = self.template
        for placeholder, content in section_replacements.items():
            resume = resume.replace(placeholder, content)

        # Check for unreplaced placeholders
        if re.search(r"{{.*?}}", resume):
            unreplaced_matches = re.findall(r"{{(.*?)}}", resume)
            raise TemplateRenderingException(
                template_name="two_column",
                details=f"Unreplaced placeholders detected: {', '.join(unreplaced_matches)}",
            )

        return resume

    def render(self) -> str:
        """Render the template to LaTeX content"""
        return self.generate_resume()

    @property
    def required_fields(self) -> list[str]:
        """List of required data fields for this template"""
        return ["personalInfo"]

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
                # Run pdflatex twice for proper cross-references
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
                    template_name="two_column",
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
                    details="PDF output not generated", template_name="two_column"
                )

        return output_path

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
                    template_name="two_column",
                    details=f"pandoc failed with return code {e.returncode}",
                ) from e

        return output_path
