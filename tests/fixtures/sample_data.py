"""Sample data fixtures for testing."""

from typing import Dict, Any, List
import json
from datetime import datetime


class SampleDataFactory:
    """Factory class for generating sample test data."""
    
    @staticmethod
    def create_personal_info(
        name: str = "John Doe",
        email: str = "john.doe@example.com",
        phone: str = "+1-234-567-8900",
        location: str = "San Francisco, CA",
        website: str = "https://johndoe.dev",
        linkedin: str = "https://linkedin.com/in/johndoe",
        website_display: str = "https://johndoe.dev",
        linkedin_display: str = "https://linkedin.com/in/johndoe"
    ) -> Dict[str, Any]:
        """Create sample personal information data."""
        return {
            "name": name,
            "email": email,
            "phone": phone,
            "location": location,
            "website": website,
            "linkedin": linkedin,
            "website_display": website_display,
            "linkedin_display": linkedin_display
        }
    
    @staticmethod
    def create_experience_entry(
        title: str = "Software Engineer",
        company: str = "Tech Corporation",
        location: str = "San Francisco, CA",
        start_date: str = "2020-01",
        end_date: str = "Present",
        description: List[str] = None
    ) -> Dict[str, Any]:
        """Create a sample work experience entry."""
        if description is None:
            description = [
                "Developed and maintained web applications using Python and JavaScript",
                "Collaborated with cross-functional teams to deliver high-quality software",
                "Implemented automated testing and CI/CD pipelines"
            ]
        
        return {
            "title": title,
            "company": company,
            "location": location,
            "startDate": start_date,
            "endDate": end_date,
            "description": description
        }
    
    @staticmethod
    def create_education_entry(
        degree: str = "Bachelor of Science in Computer Science",
        school: str = "University of California, Berkeley",
        location: str = "Berkeley, CA",
        graduation_date: str = "2019-05",
        gpa: str = None,
        honors: List[str] = None
    ) -> Dict[str, Any]:
        """Create a sample education entry."""
        entry = {
            "degree": degree,
            "school": school,
            "location": location,
            "graduationDate": graduation_date
        }
        
        if gpa:
            entry["gpa"] = gpa
        if honors:
            entry["honors"] = honors
            
        return entry
    
    @staticmethod
    def create_project_entry(
        name: str = "Resume Builder API",
        description: str = "A FastAPI-based service for generating professional resumes",
        technologies: List[str] = None,
        url: str = "https://github.com/user/resume-api",
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """Create a sample project entry."""
        if technologies is None:
            technologies = ["Python", "FastAPI", "PostgreSQL", "Docker"]
        
        project = {
            "name": name,
            "description": description,
            "technologies": technologies,
            "url": url
        }
        
        if start_date:
            project["startDate"] = start_date
        if end_date:
            project["endDate"] = end_date
            
        return project
    
    @staticmethod
    def create_skills_section(
        programming: List[str] = None,
        frameworks: List[str] = None,
        databases: List[str] = None,
        tools: List[str] = None,
        soft_skills: List[str] = None
    ) -> Dict[str, List[str]]:
        """Create a sample skills section."""
        return {
            "programming": programming or ["Python", "JavaScript", "TypeScript", "Java", "Go"],
            "frameworks": frameworks or ["FastAPI", "React", "Node.js", "Django", "Flask"],
            "databases": databases or ["PostgreSQL", "MongoDB", "Redis", "MySQL"],
            "tools": tools or ["Docker", "Kubernetes", "AWS", "Git", "Jenkins"],
            "soft_skills": soft_skills or ["Leadership", "Communication", "Problem Solving", "Team Collaboration"]
        }
    
    @staticmethod
    def create_complete_resume_data(
        personal_info: Dict[str, Any] = None,
        summary: str = None,
        experience: List[Dict[str, Any]] = None,
        education: List[Dict[str, Any]] = None,
        skills: Dict[str, List[str]] = None,
        projects: List[Dict[str, Any]] = None,
        certifications: List[Dict[str, Any]] = None,
        languages: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a complete sample resume data structure."""
        
        if personal_info is None:
            personal_info = SampleDataFactory.create_personal_info()
        
        if summary is None:
            summary = "Experienced software engineer with 5+ years of experience in full-stack development, specializing in Python, web technologies, and cloud infrastructure. Proven track record of delivering scalable solutions and leading development teams."
        
        if experience is None:
            experience = [
                SampleDataFactory.create_experience_entry(
                    title="Senior Software Engineer",
                    company="Tech Innovation Inc.",
                    start_date="2021-03",
                    end_date="Present",
                    description=[
                        "Led development of microservices architecture serving 1M+ users",
                        "Mentored team of 5 junior developers and conducted code reviews",
                        "Improved system performance by 40% through optimization and caching",
                        "Implemented automated testing reducing deployment bugs by 60%"
                    ]
                ),
                SampleDataFactory.create_experience_entry(
                    title="Software Engineer",
                    company="StartupXYZ",
                    location="Mountain View, CA",
                    start_date="2019-06",
                    end_date="2021-02",
                    description=[
                        "Developed RESTful APIs using FastAPI and Python",
                        "Built responsive web applications with React and TypeScript",
                        "Implemented CI/CD pipelines using Jenkins and Docker",
                        "Collaborated with product team to define technical requirements"
                    ]
                ),
                SampleDataFactory.create_experience_entry(
                    title="Junior Software Developer",
                    company="Digital Solutions LLC",
                    location="Palo Alto, CA",
                    start_date="2018-08",
                    end_date="2019-05",
                    description=[
                        "Assisted in development of web applications using Django",
                        "Wrote unit tests and performed debugging",
                        "Participated in agile development processes"
                    ]
                )
            ]
        
        if education is None:
            education = [
                SampleDataFactory.create_education_entry(
                    degree="Master of Science in Computer Science",
                    school="Stanford University",
                    location="Stanford, CA",
                    graduation_date="2018-06",
                    gpa="3.8/4.0"
                ),
                SampleDataFactory.create_education_entry(
                    degree="Bachelor of Science in Computer Engineering",
                    school="University of California, Berkeley",
                    location="Berkeley, CA",
                    graduation_date="2016-05",
                    gpa="3.7/4.0",
                    honors=["Magna Cum Laude", "Phi Beta Kappa"]
                )
            ]
        
        if skills is None:
            skills = SampleDataFactory.create_skills_section()
        
        if projects is None:
            projects = [
                SampleDataFactory.create_project_entry(
                    name="E-commerce Platform",
                    description="Full-stack e-commerce platform built with React and FastAPI",
                    technologies=["React", "FastAPI", "PostgreSQL", "Redis", "Docker"],
                    url="https://github.com/johndoe/ecommerce-platform"
                ),
                SampleDataFactory.create_project_entry(
                    name="ML Model Deployment Pipeline",
                    description="Automated pipeline for deploying machine learning models to production",
                    technologies=["Python", "Kubernetes", "MLflow", "AWS", "Terraform"],
                    url="https://github.com/johndoe/ml-pipeline"
                ),
                SampleDataFactory.create_project_entry(
                    name="Resume Template Engine",
                    description="Template engine for generating professional resumes and cover letters",
                    technologies=["Python", "LaTeX", "Jinja2", "FastAPI"],
                    url="https://github.com/johndoe/resume-engine"
                )
            ]
        
        resume_data = {
            "personalInfo": personal_info,
            "summary": summary,
            "experience": experience,
            "education": education,
            "skills": skills,
            "projects": projects
        }
        
        if certifications:
            resume_data["certifications"] = certifications
        
        if languages:
            resume_data["languages"] = languages
            
        return resume_data
    
    @staticmethod
    def create_cover_letter_data(
        personal_info: Dict[str, Any] = None,
        recipient: Dict[str, Any] = None,
        job_title: str = "Senior Software Engineer",
        company: str = "Amazing Tech Company",
        content: Dict[str, Any] = None,
        date: str = None
    ) -> Dict[str, Any]:
        """Create sample cover letter data."""
        
        if personal_info is None:
            personal_info = SampleDataFactory.create_personal_info()
        
        if recipient is None:
            recipient = {
                "name": "Sarah Johnson",
                "title": "Engineering Manager",
                "company": company,
                "address": "123 Innovation Drive, San Francisco, CA 94105"
            }
        
        if content is None:
            content = {
                "opening": f"I am writing to express my strong interest in the {job_title} position at {company}. With my extensive background in software development and passion for innovative technology solutions, I am excited about the opportunity to contribute to your team.",
                "body": [
                    "In my current role as Senior Software Engineer at Tech Innovation Inc., I have successfully led the development of microservices architecture serving over one million users. My experience includes mentoring development teams, implementing automated testing frameworks, and optimizing system performance to achieve 40% improvement in response times.",
                    "What particularly attracts me to this opportunity is your company's commitment to cutting-edge technology and collaborative culture. I am eager to bring my expertise in Python, cloud infrastructure, and agile development practices to help drive your engineering initiatives forward.",
                    "My track record of delivering scalable solutions, combined with strong communication skills and leadership experience, positions me well to make meaningful contributions to your team. I thrive in environments that challenge me to grow while working alongside talented professionals."
                ],
                "closing": f"I would welcome the opportunity to discuss how my skills and enthusiasm align with {company}'s goals. Thank you for considering my application. I look forward to hearing from you soon."
            }
        
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        return {
            "personalInfo": personal_info,
            "recipient": recipient,
            "jobTitle": job_title,
            "content": content,
            "date": date
        }


# Predefined sample data instances
SAMPLE_PERSONAL_INFO = SampleDataFactory.create_personal_info()

SAMPLE_RESUME_DATA = SampleDataFactory.create_complete_resume_data()

SAMPLE_COVER_LETTER_DATA = SampleDataFactory.create_cover_letter_data()

# Additional sample data for edge cases and testing
MINIMAL_RESUME_DATA = {
    "personalInfo": SampleDataFactory.create_personal_info()
}

INVALID_RESUME_DATA = {
    "personalInfo": {
        "name": "John Doe",
        "email": "invalid-email-format"  # Invalid email
    },
    "experience": [
        {
            "title": "Engineer",
            "company": "Tech Corp",
            "startDate": "invalid-date"  # Invalid date format
        }
    ]
}

LARGE_RESUME_DATA = SampleDataFactory.create_complete_resume_data(
    experience=[
        SampleDataFactory.create_experience_entry(
            title=f"Software Engineer {i}",
            company=f"Company {i}",
            start_date=f"20{20-i:02d}-01",
            end_date=f"20{21-i:02d}-12",
            description=[f"Task {j} description" for j in range(10)]
        ) for i in range(20)
    ],
    projects=[
        SampleDataFactory.create_project_entry(
            name=f"Project {i}",
            description=f"Description for project {i}"
        ) for i in range(15)
    ]
)

# Sample data for different languages/locales
SAMPLE_RESUME_DATA_MULTILANG = {
    "en": SAMPLE_RESUME_DATA,
    "es": SampleDataFactory.create_complete_resume_data(
        personal_info=SampleDataFactory.create_personal_info(
            name="Juan Pérez",
            email="juan.perez@ejemplo.com",
            location="Madrid, España"
        ),
        summary="Ingeniero de software experimentado con más de 5 años de experiencia en desarrollo full-stack."
    ),
    "fr": SampleDataFactory.create_complete_resume_data(
        personal_info=SampleDataFactory.create_personal_info(
            name="Jean Dupont",
            email="jean.dupont@exemple.com",
            location="Paris, France"
        ),
        summary="Ingénieur logiciel expérimenté avec plus de 5 ans d'expérience en développement full-stack."
    )
}

# Sample data for different industries
SAMPLE_RESUME_DATA_BY_INDUSTRY = {
    "tech": SAMPLE_RESUME_DATA,
    "finance": SampleDataFactory.create_complete_resume_data(
        experience=[
            SampleDataFactory.create_experience_entry(
                title="Financial Analyst",
                company="Investment Bank Corp",
                description=[
                    "Analyzed market trends and investment opportunities",
                    "Prepared financial models and reports",
                    "Managed portfolio worth $50M+"
                ]
            )
        ],
        skills=SampleDataFactory.create_skills_section(
            programming=["Python", "R", "SQL", "VBA"],
            tools=["Excel", "Bloomberg Terminal", "Tableau", "Power BI"]
        )
    ),
    "healthcare": SampleDataFactory.create_complete_resume_data(
        experience=[
            SampleDataFactory.create_experience_entry(
                title="Healthcare Data Analyst",
                company="Medical Center",
                description=[
                    "Analyzed patient data to improve healthcare outcomes",
                    "Developed reporting dashboards for clinical staff",
                    "Ensured HIPAA compliance in all data handling"
                ]
            )
        ]
    )
}


def get_sample_data(data_type: str, variant: str = "default") -> Dict[str, Any]:
    """
    Retrieve sample data by type and variant.
    
    Args:
        data_type: Type of data ("resume", "cover_letter", "personal_info")
        variant: Variant of the data ("default", "minimal", "large", "invalid")
    
    Returns:
        Sample data dictionary
    """
    data_map = {
        "resume": {
            "default": SAMPLE_RESUME_DATA,
            "minimal": MINIMAL_RESUME_DATA,
            "large": LARGE_RESUME_DATA,
            "invalid": INVALID_RESUME_DATA
        },
        "cover_letter": {
            "default": SAMPLE_COVER_LETTER_DATA
        },
        "personal_info": {
            "default": SAMPLE_PERSONAL_INFO
        }
    }
    
    return data_map.get(data_type, {}).get(variant, {})


def save_sample_data_to_file(data: Dict[str, Any], filename: str) -> None:
    """Save sample data to a JSON file for external testing."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False) 