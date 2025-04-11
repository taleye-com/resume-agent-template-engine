#!/usr/bin/env python3
import json
from templates.template_manager import TemplateManager
from resume_template_editing import TemplateEditing

def main():
    # Sample resume data
    resume_data = {
        "personalInfo": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "123-456-7890",
            "location": "San Francisco, CA",
            "website": "https://johndoe.com",
            "website_display": "johndoe.com",
            "linkedin": "https://linkedin.com/in/johndoe",
            "linkedin_display": "linkedin.com/in/johndoe"
        },
        "professionalSummary": "Experienced software engineer with expertise in Python, JavaScript, and cloud technologies.",
        "education": [
            {
                "degree": "Bachelor of Science in Computer Science",
                "institution": "Stanford University",
                "startDate": "2015",
                "endDate": "2019",
                "focus": "Artificial Intelligence",
                "notableCourseWorks": ["Machine Learning", "Data Structures", "Algorithms"],
                "projects": ["Senior Project: AI-based Recommendation System"]
            }
        ],
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "Tech Company Inc.",
                "startDate": "2019",
                "endDate": "Present",
                "achievements": [
                    "Developed scalable backend services using Python and FastAPI",
                    "Optimized database queries resulting in 30% performance improvement",
                    "Led a team of 5 engineers to deliver critical features on time"
                ]
            }
        ],
        "projects": [
            {
                "name": "AI Resume Builder",
                "description": ["An automated resume generation tool"],
                "tools": ["Python", "LaTeX", "NLP Libraries"],
                "achievements": [
                    "Built a system that generates professional resumes from simple JSON input",
                    "Implemented intelligent formatting and styling based on industry best practices"
                ]
            }
        ],
        "articlesAndPublications": [
            {
                "title": "Modern Approaches to Resume Building with AI",
                "date": "2022"
            }
        ],
        "achievements": [
            "Employee of the Year Award 2021",
            "Speaker at PyCon 2022"
        ],
        "certifications": [
            "AWS Certified Solutions Architect",
            "Google Cloud Professional Data Engineer"
        ],
        "technologiesAndSkills": [
            {
                "category": "Programming Languages",
                "skills": ["Python", "JavaScript", "TypeScript", "Java"]
            },
            {
                "category": "Frameworks & Libraries",
                "skills": ["React", "FastAPI", "Django", "Flask"]
            }
        ]
    }
    
    # Sample data for cover letter
    cover_letter_data = {
        "personalInfo": {
            "name": "John Smith",
            "email": "john.smith@example.com",
            "phone": "(555) 123-4567",
            "location": "New York City Metro Area",
            "website": "https://johnsmith.com/",
            "website_display": "johnsmith.com"
        },
        "recipient": {
            "name": "Sarah Johnson",
            "title": "HR Manager",
            "company": "Tech Innovations Inc.",
            "address": [
                "123 Corporate Drive",
                "New York, NY 10001"
            ]
        },
        "date": "June 15, 2023",
        "salutation": "Dear Ms. Johnson,",
        "body": [
            "I am writing to express my interest in the Senior Software Engineer position at Tech Innovations Inc., as advertised on your company website. With my extensive experience in full-stack development and passion for creating innovative solutions, I believe I would be a valuable addition to your team.",
            
            "In my current role at XYZ Corp, I have successfully led the development of several key projects that improved efficiency and scalability. My expertise includes Python, JavaScript, React, and cloud infrastructure, which aligns perfectly with the requirements mentioned in your job description.",
            
            "I am particularly impressed by Tech Innovations' commitment to leveraging technology for positive social impact, and I am excited about the possibility of contributing to your mission. My background in developing AI-powered solutions would bring a valuable perspective to your team.",
            
            "I would welcome the opportunity to discuss how my skills and experience can benefit Tech Innovations Inc. I am available for an interview at your convenience and look forward to the possibility of working with your team."
        ],
        "closing": "Sincerely,"
    }
    
    # Example 1: List available templates
    print("Available Templates:")
    template_manager = TemplateManager()
    available_templates = template_manager.get_available_templates()
    for category, templates in available_templates.items():
        print(f"  {category.capitalize()}:")
        for template in templates:
            print(f"    - {template}")
    print()
    
    # Example 2: Generate a resume using the classic template
    print("Generating resume with classic template...")
    resume_editor = TemplateEditing(resume_data, "resume", "classic")
    resume_output = resume_editor.export_to_pdf("output_resume.pdf")
    print(f"Resume generated: {resume_output}")
    
    # Example 3: Generate a cover letter using the classic template
    print("\nGenerating cover letter with classic template...")
    try:
        cover_letter_editor = TemplateEditing(cover_letter_data, "cover_letter", "classic")
        cover_letter_output = cover_letter_editor.export_to_pdf("output_cover_letter.pdf")
        print(f"Cover letter generated: {cover_letter_output}")
    except Exception as e:
        print(f"Error generating cover letter: {e}")
    
    # Example 4: Alternative approach - directly using the template class
    print("\nAlternative approach - Directly using template class:")
    try:
        # Find the correct template class - the class is named ModernCoverLetterTemplate but in the classic folder
        CoverLetterTemplate = template_manager.load_template("cover_letter", "classic")
        template = CoverLetterTemplate(cover_letter_data)
        direct_output_path = "direct_cover_letter.pdf"
        template.export_to_pdf(direct_output_path)
        print(f"Cover letter generated directly: {direct_output_path}")
    except Exception as e:
        print(f"Error with direct approach: {e}")

if __name__ == "__main__":
    main() 