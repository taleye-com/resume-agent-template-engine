import re
import subprocess
import os
import tempfile
from typing import Dict, Any, List
from resume_agent_template_engine.core.template_engine import (
    TemplateInterface,
    DocumentType,
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
        except Exception as e:
            raise IOError(
                f"Error reading template file {self.template_path}: {e}"
            ) from e

    def validate_data(self):
        """Ensure only essential required sections are present in the JSON data."""
        # Only validate the truly essential sections
        if "personalInfo" not in self.data:
            raise ValueError("Missing required section: personalInfo")

        # Validate only the most essential personal info fields
        required_personal_info = [
            "name",
            "email",
        ]
        for field in required_personal_info:
            if field not in self.data["personalInfo"]:
                raise ValueError(f"Missing required personal info field: {field}")

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
            entry = (
                f"\\textbf{{{edu.get('degree', 'Degree')}}} -- {edu.get('institution', 'Institution')} "
                f"\\hfill {edu.get('startDate', '')} -- {edu.get('endDate', edu.get('date', ''))}\n"
                "\\begin{highlights}\n"
                f"\\item \\textbf{{Focus:}} {edu.get('focus', '')}\n"
                f"\\item \\textbf{{Courses:}} {', '.join(edu.get('notableCourseWorks', edu.get('details', [])))}\n"
                f"\\item \\textbf{{Projects:}} {', '.join(edu.get('projects', []))}\n"
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
            start_date = exp.get("startDate", "")
            end_date = exp.get("endDate", "Present")
            date_range = f"{start_date} -- {end_date}" if start_date else "Present"

            # Use achievements if available, otherwise use details
            achievements = exp.get("achievements", exp.get("details", []))
            
            entry = (
                f"\\textbf{{{exp.get('title', 'Position')}}}, {exp.get('company', 'Company')} \\hfill {date_range}\n"
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
            # Handle both simple string description and list of descriptions
            description = proj.get("description", "")
            if isinstance(description, list):
                desc_points = ", ".join(description)
            else:
                desc_points = description
                
            # Handle different field names for technologies/tools
            tools = proj.get("tools", proj.get("technologies", []))
            achievements = proj.get("achievements", [])

            entry_lines = [
                f"\\textbf{{{proj.get('name', 'Project')}}} - \\textit{{{desc_points}}}",
                "\\begin{highlights}"
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
        if not self.data.get("articlesAndPublications"):
            return ""
        items = "\n".join(
            f"\\item \\textbf{{{pub['title']}}} -- {pub['date']}"
            for pub in self.data["articlesAndPublications"]
        )
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{items}\\end{{highlights}}\\end{{onecolentry}}"

    def generate_achievements(self):
        """Generate the Achievements section."""
        if not self.data.get("achievements"):
            return ""
        bullets = "\n".join(f"\\item {item}" for item in self.data["achievements"])
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{bullets}\\end{{highlights}}\\end{{onecolentry}}"

    def generate_certifications(self):
        """Generate the Certifications section."""
        if not self.data.get("certifications"):
            return ""
        bullets = "\n".join(f"\\item {item}" for item in self.data["certifications"])
        return f"\\begin{{onecolentry}}\n\\begin{{highlights}}\n{bullets}\\end{{highlights}}\\end{{onecolentry}}"

    def generate_technologies_and_skills(self):
        """Generate the Technologies & Skills section."""
        # Handle both structured skills (technologiesAndSkills) and simple skills array
        skills_data = self.data.get("technologiesAndSkills") or self.data.get("skills")
        if not skills_data:
            return ""
            
        sections = []
        
        # If it's a simple array of skills, treat them as general skills
        if isinstance(skills_data, list) and all(isinstance(skill, str) for skill in skills_data):
            entry = f"\\textbf{{Skills}}: {', '.join(skills_data)}"
            sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")
        else:
            # Handle structured skills with categories
            for skill in skills_data:
                entry = f"\\textbf{{{skill['category']}}}: {', '.join(skill['skills'])}"
                sections.append(f"\\begin{{onecolentry}}\n{entry}\\end{{onecolentry}}")
        return "\n".join(sections)

    def generate_resume(self):
        """Generate the final LaTeX resume by replacing placeholders."""
        info = self.data["personalInfo"]

        # Generate content for each section and include header if content exists
        personal_info = self.generate_personal_info()
        
        professional_summary_content = self.generate_professional_summary()
        professional_summary = ("\\section{Professional Summary}\n" + professional_summary_content) if professional_summary_content else ""
        
        education_content = self.generate_education()
        education = ("\\section{Education}\n" + education_content) if education_content else ""
        
        experience_content = self.generate_experience()
        experience = ("\\section{Experience}\n" + experience_content) if experience_content else ""
        
        projects_content = self.generate_projects()
        projects = ("\\section{Projects}\n" + projects_content) if projects_content else ""
        
        articles_content = self.generate_articles_and_publications()
        articles_and_publications = ("\\section{Articles \\& Publications}\n" + articles_content) if articles_content else ""
        
        achievements_content = self.generate_achievements()
        achievements = ("\\section{Achievements}\n" + achievements_content) if achievements_content else ""
        
        certifications_content = self.generate_certifications()
        certifications = ("\\section{Certifications}\n" + certifications_content) if certifications_content else ""
        
        skills_content = self.generate_technologies_and_skills()
        technologies_and_skills = ("\\section{Technologies \\& Skills}\n" + skills_content) if skills_content else ""

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

        # Combine all replacements
        all_replacements = {**section_replacements}

        resume = self.template
        for ph, content in all_replacements.items():
            resume = resume.replace(ph, content)

        if re.search(r"{{.*?}}", resume):
            raise ValueError("Unreplaced placeholders detected")

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
                raise RuntimeError(
                    "PDF compilation failed. Ensure pdflatex is installed."
                ) from e
            except FileNotFoundError as e:
                raise RuntimeError(
                    "pdflatex not found. Please install BasicTeX or MacTeX:\n"
                    "brew install --cask basictex\n"
                    "Then restart your terminal or run: eval \"$(/usr/libexec/path_helper)\""
                ) from e

            pdf_path = os.path.join(tmpdir, "temp.pdf")
            if os.path.exists(pdf_path):
                os.replace(pdf_path, output_path)
            else:
                raise FileNotFoundError("PDF output not generated")

        return output_path
