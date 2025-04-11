import streamlit as st
import os
import json
from resume_template_editing import TemplateEditing
from templates.template_manager import TemplateManager
import base64
from PIL import Image

# Set page config
st.set_page_config(
    page_title="Resume Builder",
    page_icon="📄",
    layout="wide"
)

# Title and description
st.title("Resume Builder - JSON Input")
st.markdown("""
This application helps you create a professional resume or cover letter using LaTeX templates. 
Simply paste your JSON data, select a document type and template to generate a PDF.
""")

def load_templates():
    """Load available templates from the templates directory using TemplateManager."""
    template_manager = TemplateManager()
    return template_manager.get_available_templates()

# Sidebar for template selection and preview
st.sidebar.header("Template Selection")
templates_by_category = load_templates()

# Document type selection (resume or cover letter)
document_type = st.sidebar.radio("Select document type:", list(templates_by_category.keys()))

# Template selection based on document type
available_templates = templates_by_category[document_type]
selected_template = st.sidebar.selectbox("Choose a template:", available_templates)

# Find and show template preview from the template directory
st.sidebar.header("Template Preview")
template_dir = os.path.join("templates", document_type, selected_template)
preview_found = False

# Check for common image formats
for ext in ['.png', '.jpg', '.jpeg']:
    preview_path = os.path.join(template_dir, f"preview{ext}")
    if os.path.exists(preview_path):
        preview_found = True
        preview_image = Image.open(preview_path)
        st.sidebar.image(preview_image, caption=f"{selected_template} template preview", use_column_width=True)
        break

if not preview_found:
    st.sidebar.warning("No preview available for this template")

# JSON input area with placeholder based on document type
st.header(f"Paste your {document_type.capitalize()} JSON")

# Different placeholders for each document type
if document_type == "resume":
    placeholder = '''{
    "personalInfo": {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "location": "New York, NY",
        "website": "https://johndoe.com",
        "website_display": "johndoe.com",
        "linkedin": "https://linkedin.com/in/johndoe",
        "linkedin_display": "linkedin.com/in/johndoe",
        "links": []
    },
    "professionalSummary": "Experienced software engineer...",
    "education": [{
        "degree": "BS Computer Science",
        "institution": "University Example",
        "startDate": "2018",
        "endDate": "2022",
        "focus": "Software Engineering",
        "notableCourseWorks": ["Algorithms", "Data Structures"],
        "projects": ["Senior Thesis", "Capstone Project"]
    }],
    "experience": [],
    "projects": [],
    "articlesAndPublications": [],
    "achievements": [],
    "certifications": [],
    "technologiesAndSkills": []
}'''
else:  # cover_letter
    placeholder = '''{
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
        "I am writing to express my interest in the Senior Software Engineer position...",
        "In my current role at XYZ Corp, I have successfully led the development...",
        "I am particularly impressed by your company's commitment to innovation..."
    ],
    "closing": "Sincerely,"
}'''

json_input = st.text_area("", height=400, placeholder=placeholder)

# Generate button
if st.button(f"Generate {document_type.capitalize()}"):
    try:
        # Parse JSON
        data = json.loads(json_input)
        
        # Create output directory if it doesn't exist
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate unique filename
        if document_type == "resume":
            output_filename = f"resume_{data['personalInfo']['name'].replace(' ', '_')}.pdf"
        else:
            output_filename = f"cover_letter_{data['personalInfo']['name'].replace(' ', '_')}.pdf"
        
        output_path = os.path.join(output_dir, output_filename)
        
        # Create TemplateEditing instance and generate PDF
        template_editor = TemplateEditing(data, document_type, selected_template)
        template_editor.export_to_pdf(output_path)
        
        # Show success message
        st.success(f"{document_type.capitalize()} generated successfully!")
        
        # Display download button
        with open(output_path, "rb") as pdf_file:
            PDFbyte = pdf_file.read()
            st.download_button(
                label=f"Download {document_type.capitalize()} PDF",
                data=PDFbyte,
                file_name=os.path.basename(output_path),
                mime='application/pdf'
            )
            
    except json.JSONDecodeError:
        st.error("Invalid JSON format. Please check your input.")
    except Exception as e:
        st.error(f"Error generating {document_type}: {str(e)}") 