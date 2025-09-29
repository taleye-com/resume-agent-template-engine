"""
Central Template Registry System

This module replaces all individual helper.py files with a centralized
template registry that defines all templates through configuration.
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
from .base import DocumentType


class SectionType(str, Enum):
    """Types of sections supported in templates"""

    HEADER = "header"
    PERSONAL_INFO = "personal_info"
    PROFESSIONAL_SUMMARY = "professional_summary"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    PROJECTS = "projects"
    ACHIEVEMENTS = "achievements"
    CERTIFICATIONS = "certifications"
    SKILLS = "skills"
    PUBLICATIONS = "publications"
    # Cover letter specific
    RECIPIENT = "recipient"
    DATE = "date"
    SALUTATION = "salutation"
    BODY = "body"
    CLOSING = "closing"


class FieldMapping:
    """Defines field mappings and fallbacks for template fields"""

    def __init__(
        self,
        primary: str,
        fallbacks: Optional[List[str]] = None,
        default: Any = None,
        smart_default_fn: Optional[Callable] = None,
        required: bool = False
    ):
        self.primary = primary
        self.fallbacks = fallbacks or []
        self.default = default
        self.smart_default_fn = smart_default_fn
        self.required = required


class SectionDefinition:
    """Defines how a section should be generated"""

    def __init__(
        self,
        section_type: SectionType,
        template_pattern: str,
        field_mappings: Dict[str, FieldMapping],
        required: bool = False,
        header_name: Optional[str] = None,
        conditional: Optional[str] = None
    ):
        self.section_type = section_type
        self.template_pattern = template_pattern
        self.field_mappings = field_mappings
        self.required = required
        self.header_name = header_name
        self.conditional = conditional


class TemplateDefinition:
    """Complete template definition"""

    def __init__(
        self,
        name: str,
        document_type: DocumentType,
        template_file: str,
        sections: List[SectionDefinition],
        required_fields: List[str],
        validation_rules: Dict[str, Any] = None,
        placeholders: Dict[str, str] = None
    ):
        self.name = name
        self.document_type = document_type
        self.template_file = template_file
        self.sections = sections
        self.required_fields = required_fields
        self.validation_rules = validation_rules or {}
        self.placeholders = placeholders or {}


# Smart default functions
def generate_current_date() -> str:
    """Generate current date in nice format"""
    return datetime.now().strftime("%B %d, %Y")


def generate_smart_salutation(recipient_data: Dict[str, Any]) -> str:
    """Generate smart salutation based on recipient info"""
    if not recipient_data:
        return "Dear Hiring Manager,"

    if recipient_data.get("name"):
        return f"Dear {recipient_data['name']},"
    elif recipient_data.get("title"):
        return f"Dear {recipient_data['title']},"
    elif recipient_data.get("company"):
        return f"Dear Hiring Manager at {recipient_data['company']},"
    else:
        return "Dear Hiring Manager,"


def generate_smart_closing() -> str:
    """Generate appropriate closing"""
    return "Sincerely,"


# =============================================================================
# TEMPLATE REGISTRY - All templates defined here
# =============================================================================

TEMPLATE_REGISTRY: Dict[str, Dict[str, TemplateDefinition]] = {
    # =========================================================================
    # RESUME TEMPLATES
    # =========================================================================
    "resume": {
        "classic": TemplateDefinition(
            name="classic",
            document_type=DocumentType.RESUME,
            template_file="classic.tex",
            required_fields=["personalInfo"],

            sections=[
                # Personal Info Section
                SectionDefinition(
                    section_type=SectionType.PERSONAL_INFO,
                    template_pattern="{{personal_info}}",
                    required=True,
                    field_mappings={
                        "name": FieldMapping("name", required=True),
                        "email": FieldMapping("email", required=True),
                        "phone": FieldMapping("phone", ["telephone", "mobile"]),
                        "location": FieldMapping("location", ["address", "city"]),
                        "website": FieldMapping("website", ["portfolio", "homepage"]),
                        "website_display": FieldMapping("website_display", ["website_text"]),
                        "linkedin": FieldMapping("linkedin", ["linkedin_url"]),
                        "linkedin_display": FieldMapping("linkedin_display", ["linkedin_text"]),
                        "github": FieldMapping("github", ["github_url"]),
                        "github_display": FieldMapping("github_display", ["github_text"]),
                        "twitter": FieldMapping("twitter", ["twitter_url"]),
                        "twitter_display": FieldMapping("twitter_display", ["twitter_text"]),
                        "x": FieldMapping("x", ["x_url"]),
                        "x_display": FieldMapping("x_display", ["x_text"])
                    }
                ),

                # Professional Summary Section
                SectionDefinition(
                    section_type=SectionType.PROFESSIONAL_SUMMARY,
                    template_pattern="{{professional_summary}}",
                    conditional="professionalSummary",
                    header_name="Professional Summary",
                    field_mappings={
                        "content": FieldMapping("professionalSummary", ["summary", "profile"])
                    }
                ),

                # Experience Section
                SectionDefinition(
                    section_type=SectionType.EXPERIENCE,
                    template_pattern="{{experience}}",
                    conditional="experience",
                    header_name="Experience",
                    field_mappings={
                        "title": FieldMapping("title", ["position", "role"], "Position"),
                        "company": FieldMapping("company", ["employer", "organization"], "Company"),
                        "startDate": FieldMapping("startDate", ["start_date"]),
                        "endDate": FieldMapping("endDate", ["end_date"], "Present"),
                        "achievements": FieldMapping("achievements", ["details", "responsibilities", "duties"], []),
                        "location": FieldMapping("location", ["city", "office"])
                    }
                ),

                # Education Section
                SectionDefinition(
                    section_type=SectionType.EDUCATION,
                    template_pattern="{{education}}",
                    conditional="education",
                    header_name="Education",
                    field_mappings={
                        "degree": FieldMapping("degree", ["title", "qualification"], "Degree"),
                        "institution": FieldMapping("institution", ["school", "university", "college"], "Institution"),
                        "startDate": FieldMapping("startDate", ["start_date"]),
                        "endDate": FieldMapping("endDate", ["end_date", "date", "graduationDate"]),
                        "focus": FieldMapping("focus", ["major", "specialization", "concentration"]),
                        "courses": FieldMapping("notableCourseWorks", ["courses", "coursework", "details"], []),
                        "projects": FieldMapping("projects", ["academicProjects"], [])
                    }
                ),

                # Projects Section
                SectionDefinition(
                    section_type=SectionType.PROJECTS,
                    template_pattern="{{projects}}",
                    conditional="projects",
                    header_name="Projects",
                    field_mappings={
                        "name": FieldMapping("name", ["title", "project_name"], "Project"),
                        "description": FieldMapping("description", ["summary", "desc"]),
                        "tools": FieldMapping("tools", ["technologies", "tech_stack", "stack"], []),
                        "achievements": FieldMapping("achievements", ["accomplishments", "results", "outcomes"], [])
                    }
                ),

                # Publications Section
                SectionDefinition(
                    section_type=SectionType.PUBLICATIONS,
                    template_pattern="{{articles_and_publications}}",
                    conditional="articlesAndPublications,publications,articles,papers",
                    header_name="Articles \\& Publications",
                    field_mappings={
                        "publications": FieldMapping("articlesAndPublications", ["publications", "articles", "papers"], []),
                        "title": FieldMapping("title", ["name"], "Publication"),
                        "date": FieldMapping("date", ["published_date", "year"])
                    }
                ),

                # Achievements Section
                SectionDefinition(
                    section_type=SectionType.ACHIEVEMENTS,
                    template_pattern="{{achievements}}",
                    conditional="achievements,accomplishments,awards,honors",
                    header_name="Achievements",
                    field_mappings={
                        "items": FieldMapping("achievements", ["accomplishments", "awards", "honors"], [])
                    }
                ),

                # Certifications Section
                SectionDefinition(
                    section_type=SectionType.CERTIFICATIONS,
                    template_pattern="{{certifications}}",
                    conditional="certifications,certificates,credentials,licenses",
                    header_name="Certifications",
                    field_mappings={
                        "items": FieldMapping("certifications", ["certificates", "credentials", "licenses"], [])
                    }
                ),

                # Skills Section
                SectionDefinition(
                    section_type=SectionType.SKILLS,
                    template_pattern="{{technologies_and_skills}}",
                    conditional="technologiesAndSkills,skills,technologies,tech_skills",
                    header_name="Technologies \\& Skills",
                    field_mappings={
                        "skills_data": FieldMapping("technologiesAndSkills", ["skills", "technologies", "tech_skills"], []),
                        "category": FieldMapping("category", ["name", "type"], "Skills"),
                        "skills": FieldMapping("skills", ["items", "technologies"], [])
                    }
                )
            ],

            placeholders={
                "{{personal_info}}": "personal_info",
                "{{professional_summary}}": "professional_summary",
                "{{education}}": "education",
                "{{experience}}": "experience",
                "{{projects}}": "projects",
                "{{articles_and_publications}}": "articles_and_publications",
                "{{achievements}}": "achievements",
                "{{certifications}}": "certifications",
                "{{technologies_and_skills}}": "technologies_and_skills"
            }
        )
    },

    # =========================================================================
    # COVER LETTER TEMPLATES
    # =========================================================================
    "cover_letter": {
        "classic": TemplateDefinition(
            name="classic",
            document_type=DocumentType.COVER_LETTER,
            template_file="classic.tex",
            required_fields=["personalInfo", "body"],

            sections=[
                # Personal Info Section (shared with resume)
                SectionDefinition(
                    section_type=SectionType.PERSONAL_INFO,
                    template_pattern="{{personal_info}}",
                    required=True,
                    field_mappings={
                        "name": FieldMapping("name", required=True),
                        "email": FieldMapping("email", required=True),
                        "phone": FieldMapping("phone", ["telephone", "mobile"]),
                        "location": FieldMapping("location", ["address", "city"]),
                        "website": FieldMapping("website", ["portfolio", "homepage"]),
                        "website_display": FieldMapping("website_display", ["website_text"]),
                        "linkedin": FieldMapping("linkedin", ["linkedin_url"]),
                        "linkedin_display": FieldMapping("linkedin_display", ["linkedin_text"]),
                        "github": FieldMapping("github", ["github_url"]),
                        "github_display": FieldMapping("github_display", ["github_text"]),
                        "twitter": FieldMapping("twitter", ["twitter_url"]),
                        "twitter_display": FieldMapping("twitter_display", ["twitter_text"]),
                        "x": FieldMapping("x", ["x_url"]),
                        "x_display": FieldMapping("x_display", ["x_text"])
                    }
                ),

                # Recipient Section
                SectionDefinition(
                    section_type=SectionType.RECIPIENT,
                    template_pattern="{{recipient_address}}",
                    field_mappings={
                        "name": FieldMapping("name"),
                        "title": FieldMapping("title"),
                        "company": FieldMapping("company"),
                        "department": FieldMapping("department"),
                        "address": FieldMapping("address"),
                        "street": FieldMapping("street"),
                        "city": FieldMapping("city"),
                        "state": FieldMapping("state"),
                        "zip": FieldMapping("zip", ["zipcode", "postal_code"]),
                        "country": FieldMapping("country")
                    }
                ),

                # Date Section
                SectionDefinition(
                    section_type=SectionType.DATE,
                    template_pattern="{{date}}",
                    field_mappings={
                        "date": FieldMapping("date", smart_default_fn=generate_current_date)
                    }
                ),

                # Salutation Section
                SectionDefinition(
                    section_type=SectionType.SALUTATION,
                    template_pattern="{{salutation}}",
                    field_mappings={
                        "salutation": FieldMapping("salutation", smart_default_fn=lambda data: generate_smart_salutation(data.get("recipient", {})))
                    }
                ),

                # Body Section
                SectionDefinition(
                    section_type=SectionType.BODY,
                    template_pattern="{{body_content}}",
                    required=True,
                    field_mappings={
                        "body": FieldMapping("body", required=True)
                    }
                ),

                # Closing Section
                SectionDefinition(
                    section_type=SectionType.CLOSING,
                    template_pattern="{{closing}}",
                    field_mappings={
                        "closing": FieldMapping("closing", smart_default_fn=generate_smart_closing)
                    }
                )
            ],

            placeholders={
                "{{personal_info}}": "personal_info",
                "{{recipient_address}}": "recipient_address",
                "{{date}}": "date",
                "{{salutation}}": "salutation",
                "{{body_content}}": "body_content",
                "{{closing}}": "closing",
                "{{name}}": "name"
            }
        )
    }
}


def get_template_definition(document_type: str, template_name: str) -> TemplateDefinition:
    """Get template definition from registry"""
    if document_type not in TEMPLATE_REGISTRY:
        raise ValueError(f"Document type '{document_type}' not found in registry")

    if template_name not in TEMPLATE_REGISTRY[document_type]:
        raise ValueError(f"Template '{template_name}' not found for document type '{document_type}'")

    return TEMPLATE_REGISTRY[document_type][template_name]


def get_available_templates() -> Dict[str, List[str]]:
    """Get all available templates from registry"""
    return {
        doc_type: list(templates.keys())
        for doc_type, templates in TEMPLATE_REGISTRY.items()
    }


def register_template(template_def: TemplateDefinition) -> None:
    """Register a new template definition"""
    doc_type = template_def.document_type.value
    if doc_type not in TEMPLATE_REGISTRY:
        TEMPLATE_REGISTRY[doc_type] = {}

    TEMPLATE_REGISTRY[doc_type][template_def.name] = template_def