"""
Dynamic Schema Generator

Generates JSON schemas and examples based on the template registry definitions.
"""

from typing import Any

from resume_agent_template_engine.core.base import DocumentType


class SchemaGenerator:
    """Generates schemas dynamically from template registry"""

    @staticmethod
    def generate_resume_schema() -> dict[str, Any]:
        """Generate comprehensive resume schema"""
        return {
            "type": "object",
            "required": ["personalInfo"],
            "properties": {
                "personalInfo": {
                    "type": "object",
                    "required": ["name", "email"],
                    "properties": {
                        "name": {"type": "string", "description": "Full name"},
                        "email": {
                            "type": "string",
                            "format": "email",
                            "description": "Email address",
                        },
                        "phone": {"type": "string", "description": "Phone number"},
                        "location": {
                            "type": "string",
                            "description": "Current location",
                        },
                        "website": {
                            "type": "string",
                            "format": "uri",
                            "description": "Personal website URL",
                        },
                        "linkedin": {
                            "type": "string",
                            "format": "uri",
                            "description": "LinkedIn profile URL",
                        },
                        "github": {
                            "type": "string",
                            "format": "uri",
                            "description": "GitHub profile URL",
                        },
                        "twitter": {
                            "type": "string",
                            "format": "uri",
                            "description": "Twitter profile URL",
                        },
                        "x": {
                            "type": "string",
                            "format": "uri",
                            "description": "X (formerly Twitter) profile URL",
                        },
                        "website_display": {
                            "type": "string",
                            "description": "Display text for website",
                        },
                        "linkedin_display": {
                            "type": "string",
                            "description": "Display text for LinkedIn",
                        },
                        "github_display": {
                            "type": "string",
                            "description": "Display text for GitHub",
                        },
                        "twitter_display": {
                            "type": "string",
                            "description": "Display text for Twitter",
                        },
                        "x_display": {
                            "type": "string",
                            "description": "Display text for X",
                        },
                    },
                },
                "professionalSummary": {
                    "type": "string",
                    "description": "Brief professional summary or objective",
                },
                "experience": {
                    "type": "array",
                    "description": "Work experience entries",
                    "items": {
                        "type": "object",
                        "required": ["position", "company", "startDate"],
                        "properties": {
                            "position": {"type": "string", "description": "Job title"},
                            "company": {
                                "type": "string",
                                "description": "Company name",
                            },
                            "location": {
                                "type": "string",
                                "description": "Work location",
                            },
                            "startDate": {
                                "type": "string",
                                "pattern": "^\\d{4}-\\d{2}(-\\d{2})?$",
                                "description": "Start date (YYYY-MM or YYYY-MM-DD)",
                            },
                            "endDate": {
                                "type": "string",
                                "description": "End date (YYYY-MM, YYYY-MM-DD, or 'Present')",
                            },
                            "description": {
                                "type": "string",
                                "description": "Job description",
                            },
                            "achievements": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Key achievements",
                            },
                            "technologies": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Technologies used",
                            },
                        },
                    },
                },
                "education": {
                    "type": "array",
                    "description": "Education entries",
                    "items": {
                        "type": "object",
                        "required": ["degree", "institution"],
                        "properties": {
                            "degree": {
                                "type": "string",
                                "description": "Degree or certification name",
                            },
                            "institution": {
                                "type": "string",
                                "description": "Educational institution",
                            },
                            "location": {
                                "type": "string",
                                "description": "Institution location",
                            },
                            "graduationDate": {
                                "type": "string",
                                "pattern": "^\\d{4}-\\d{2}(-\\d{2})?$",
                                "description": "Graduation date",
                            },
                            "gpa": {
                                "type": "string",
                                "description": "Grade point average",
                            },
                            "coursework": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Relevant coursework",
                            },
                            "honors": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Academic honors",
                            },
                        },
                    },
                },
                "projects": {
                    "type": "array",
                    "description": "Project entries",
                    "items": {
                        "type": "object",
                        "required": ["name", "description"],
                        "properties": {
                            "name": {"type": "string", "description": "Project name"},
                            "description": {
                                "type": "string",
                                "description": "Project description",
                            },
                            "technologies": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Technologies used",
                            },
                            "url": {
                                "type": "string",
                                "format": "uri",
                                "description": "Project URL",
                            },
                            "startDate": {
                                "type": "string",
                                "description": "Start date",
                            },
                            "endDate": {"type": "string", "description": "End date"},
                            "achievements": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Project achievements",
                            },
                        },
                    },
                },
                "skills": {
                    "type": "object",
                    "description": "Skills categorized by type",
                    "properties": {
                        "technical": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Technical skills",
                        },
                        "soft": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Soft skills",
                        },
                        "languages": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Programming languages",
                        },
                        "frameworks": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Frameworks and libraries",
                        },
                        "tools": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tools and software",
                        },
                    },
                },
                "certifications": {
                    "type": "array",
                    "description": "Professional certifications",
                    "items": {
                        "type": "object",
                        "required": ["name", "issuer"],
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Certification name",
                            },
                            "issuer": {
                                "type": "string",
                                "description": "Issuing organization",
                            },
                            "date": {"type": "string", "description": "Issue date"},
                            "expiry": {"type": "string", "description": "Expiry date"},
                            "credential_id": {
                                "type": "string",
                                "description": "Credential ID",
                            },
                            "url": {
                                "type": "string",
                                "format": "uri",
                                "description": "Verification URL",
                            },
                        },
                    },
                },
                "publications": {
                    "type": "array",
                    "description": "Publications and papers",
                    "items": {
                        "type": "object",
                        "required": ["title", "authors", "venue", "date"],
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Publication title",
                            },
                            "authors": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of authors",
                            },
                            "venue": {
                                "type": "string",
                                "description": "Publication venue",
                            },
                            "date": {
                                "type": "string",
                                "description": "Publication date",
                            },
                            "url": {
                                "type": "string",
                                "format": "uri",
                                "description": "Publication URL",
                            },
                            "doi": {
                                "type": "string",
                                "description": "Digital Object Identifier",
                            },
                        },
                    },
                },
                "achievements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Notable achievements",
                },
                "awards": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Awards and recognitions",
                },
                "languages": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Spoken languages",
                },
                "interests": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Personal interests and hobbies",
                },
            },
        }

    @staticmethod
    def generate_cover_letter_schema() -> dict[str, Any]:
        """Generate comprehensive cover letter schema"""
        return {
            "type": "object",
            "required": ["personalInfo", "body"],
            "properties": {
                "personalInfo": {
                    "type": "object",
                    "required": ["name", "email"],
                    "properties": {
                        "name": {"type": "string", "description": "Full name"},
                        "email": {
                            "type": "string",
                            "format": "email",
                            "description": "Email address",
                        },
                        "phone": {"type": "string", "description": "Phone number"},
                        "location": {
                            "type": "string",
                            "description": "Current location",
                        },
                        "website": {
                            "type": "string",
                            "format": "uri",
                            "description": "Personal website URL",
                        },
                        "linkedin": {
                            "type": "string",
                            "format": "uri",
                            "description": "LinkedIn profile URL",
                        },
                        "github": {
                            "type": "string",
                            "format": "uri",
                            "description": "GitHub profile URL",
                        },
                        "website_display": {
                            "type": "string",
                            "description": "Display text for website",
                        },
                        "linkedin_display": {
                            "type": "string",
                            "description": "Display text for LinkedIn",
                        },
                        "github_display": {
                            "type": "string",
                            "description": "Display text for GitHub",
                        },
                    },
                },
                "recipient": {
                    "type": "object",
                    "description": "Letter recipient information",
                    "properties": {
                        "name": {"type": "string", "description": "Recipient's name"},
                        "title": {
                            "type": "string",
                            "description": "Recipient's job title",
                        },
                        "company": {"type": "string", "description": "Company name"},
                        "department": {"type": "string", "description": "Department"},
                        "address": {
                            "type": ["string", "array"],
                            "items": {"type": "string"},
                            "description": "Address lines",
                        },
                        "street": {"type": "string", "description": "Street address"},
                        "city": {"type": "string", "description": "City"},
                        "state": {"type": "string", "description": "State/Province"},
                        "zip": {"type": "string", "description": "ZIP/Postal code"},
                        "country": {"type": "string", "description": "Country"},
                    },
                },
                "date": {
                    "type": "string",
                    "description": "Letter date (auto-generated if not provided)",
                },
                "salutation": {
                    "type": "string",
                    "description": "Letter greeting (auto-generated if not provided)",
                },
                "body": {
                    "type": ["string", "array"],
                    "items": {"type": "string"},
                    "description": "Letter body content (string or array of paragraphs)",
                },
                "closing": {
                    "type": "string",
                    "description": "Letter closing (auto-generated if not provided)",
                },
            },
        }

    @staticmethod
    def generate_resume_example() -> dict[str, Any]:
        """Generate realistic resume example"""
        return {
            "personalInfo": {
                "name": "John Doe",
                "email": "john.doe@email.com",
                "phone": "+1 (555) 123-4567",
                "location": "San Francisco, CA",
                "website": "https://johndoe.dev",
                "linkedin": "https://linkedin.com/in/johndoe",
                "github": "https://github.com/johndoe",
                "website_display": "johndoe.dev",
                "linkedin_display": "linkedin.com/in/johndoe",
                "github_display": "github.com/johndoe",
            },
            "professionalSummary": "Experienced Software Engineer with 5+ years of expertise in full-stack development, cloud architecture, and team leadership. Proven track record of delivering scalable solutions that drive business growth.",
            "experience": [
                {
                    "position": "Senior Software Engineer",
                    "company": "Tech Innovations Inc.",
                    "location": "San Francisco, CA",
                    "startDate": "2021-03",
                    "endDate": "Present",
                    "description": "Lead development of cloud-native microservices architecture serving 1M+ users daily",
                    "achievements": [
                        "Reduced system latency by 40% through performance optimization",
                        "Led team of 5 engineers in successful product launches",
                        "Implemented CI/CD pipeline reducing deployment time by 60%",
                    ],
                    "technologies": ["Python", "React", "AWS", "Docker", "Kubernetes"],
                },
                {
                    "position": "Software Engineer",
                    "company": "StartupXYZ",
                    "location": "Palo Alto, CA",
                    "startDate": "2019-01",
                    "endDate": "2021-02",
                    "description": "Developed scalable web applications and APIs for fintech platform",
                    "achievements": [
                        "Built payment processing system handling $10M+ monthly volume",
                        "Improved application security through comprehensive testing",
                    ],
                    "technologies": ["Node.js", "PostgreSQL", "Redis", "Stripe API"],
                },
            ],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "University of California, Berkeley",
                    "location": "Berkeley, CA",
                    "graduationDate": "2018-12",
                    "gpa": "3.8/4.0",
                    "coursework": [
                        "Data Structures",
                        "Algorithms",
                        "Database Systems",
                        "Software Engineering",
                    ],
                    "honors": ["Dean's List", "Cum Laude"],
                }
            ],
            "projects": [
                {
                    "name": "E-commerce Platform",
                    "description": "Full-stack e-commerce platform with real-time inventory management",
                    "technologies": ["React", "Node.js", "PostgreSQL", "Redis"],
                    "url": "https://github.com/johndoe/ecommerce-platform",
                    "achievements": [
                        "Supports 1000+ concurrent users",
                        "99.9% uptime over 6 months",
                    ],
                }
            ],
            "skills": {
                "technical": [
                    "Python",
                    "JavaScript",
                    "React",
                    "Node.js",
                    "AWS",
                    "Docker",
                ],
                "soft": [
                    "Leadership",
                    "Communication",
                    "Problem Solving",
                    "Team Collaboration",
                ],
                "languages": ["Python", "JavaScript", "TypeScript", "SQL"],
                "frameworks": ["React", "Django", "Express.js", "FastAPI"],
                "tools": ["Git", "Docker", "Kubernetes", "Jenkins", "Jira"],
            },
            "certifications": [
                {
                    "name": "AWS Certified Solutions Architect",
                    "issuer": "Amazon Web Services",
                    "date": "2023-06",
                    "expiry": "2026-06",
                    "credential_id": "AWS-ASA-12345",
                }
            ],
        }

    @staticmethod
    def generate_cover_letter_example() -> dict[str, Any]:
        """Generate realistic cover letter example"""
        return {
            "personalInfo": {
                "name": "John Doe",
                "email": "john.doe@email.com",
                "phone": "+1 (555) 123-4567",
                "location": "San Francisco, CA",
                "website": "https://johndoe.dev",
                "linkedin": "https://linkedin.com/in/johndoe",
            },
            "recipient": {
                "name": "Jane Smith",
                "title": "Engineering Manager",
                "company": "Innovative Tech Solutions",
                "street": "123 Tech Boulevard",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94105",
            },
            "date": "March 15, 2024",
            "salutation": "Dear Ms. Smith,",
            "body": [
                "I am writing to express my strong interest in the Senior Software Engineer position at Innovative Tech Solutions. With over 5 years of experience in full-stack development and cloud architecture, I am excited about the opportunity to contribute to your team's continued success.",
                "In my current role at Tech Innovations Inc., I have led the development of scalable microservices that serve over 1 million users daily. My experience with modern technologies like Python, React, and AWS, combined with my proven track record of reducing system latency by 40% and leading successful product launches, aligns perfectly with your requirements.",
                "I am particularly drawn to your company's commitment to innovation and would welcome the opportunity to discuss how my technical expertise and leadership experience can contribute to your upcoming projects.",
            ],
            "closing": "Sincerely,\nJohn Doe",
        }

    @classmethod
    def get_schema_for_document_type(cls, document_type: str) -> dict[str, Any]:
        """Get schema for specific document type"""
        if document_type == DocumentType.RESUME:
            return {
                "schema": cls.generate_resume_schema(),
                "json_example": cls.generate_resume_example(),
                "yaml_example": cls._dict_to_yaml(cls.generate_resume_example()),
            }
        elif document_type == DocumentType.COVER_LETTER:
            return {
                "schema": cls.generate_cover_letter_schema(),
                "json_example": cls.generate_cover_letter_example(),
                "yaml_example": cls._dict_to_yaml(cls.generate_cover_letter_example()),
            }
        else:
            raise ValueError(f"Unsupported document type: {document_type}")

    @staticmethod
    def _dict_to_yaml(data: dict[str, Any]) -> str:
        """Convert dictionary to YAML string"""
        try:
            import yaml

            return yaml.dump(data, default_flow_style=False, indent=2, sort_keys=False)
        except ImportError:
            # Fallback to basic YAML-like format if yaml module is not available
            return SchemaGenerator._dict_to_basic_yaml(data)

    @staticmethod
    def _dict_to_basic_yaml(data: dict[str, Any], indent: int = 0) -> str:
        """Convert dictionary to basic YAML-like format without yaml module"""
        lines = []
        indent_str = "  " * indent

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{indent_str}{key}:")
                lines.append(SchemaGenerator._dict_to_basic_yaml(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{indent_str}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(f"{indent_str}  -")
                        for sub_key, sub_value in item.items():
                            lines.append(f"{indent_str}    {sub_key}: {sub_value}")
                    else:
                        lines.append(f"{indent_str}  - {item}")
            else:
                lines.append(f"{indent_str}{key}: {value}")

        return "\n".join(lines)
