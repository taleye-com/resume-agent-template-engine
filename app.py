import streamlit as st
import os
import json
from resume_template_editing import TemplateEditing
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
This application helps you create a professional resume using LaTeX templates. 
Simply paste your JSON data and select a template to generate a PDF resume.
""")

def load_templates():
    """Load available templates from the templates directory."""
    templates_dir = "templates"
    templates = []
    for file in os.listdir(templates_dir):
        if file.endswith(".tex"):
            templates.append(file[:-4])  # Remove .tex extension
    return templates

# Sidebar for template selection and preview
st.sidebar.header("Template Selection")
templates = load_templates()
selected_template = st.sidebar.selectbox("Choose a template:", templates)

# Show template preview
st.sidebar.header("Template Preview")
preview_path = os.path.join("template_previews", f"{selected_template}.png")
if os.path.exists(preview_path):
    preview_image = Image.open(preview_path)
    st.sidebar.image(preview_image, caption=f"{selected_template} template preview", use_column_width=True)
else:
    st.sidebar.warning("No preview available for this template")

# JSON input area
st.header("Paste your Resume JSON")
json_input = st.text_area("", height=400, placeholder='''{
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
}''')

# Generate button
if st.button("Generate Resume"):
    try:
        # Parse JSON
        resume_data = json.loads(json_input)
        
        # Create output directory if it doesn't exist
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate unique filename
        output_path = os.path.join(output_dir, f"resume_{resume_data['personalInfo']['name'].replace(' ', '_')}.pdf")
        
        # Create TemplateEditing instance and generate PDF
        template_editor = TemplateEditing(resume_data, selected_template)
        template_editor.export_to_pdf(output_path)
        
        # Show success message
        st.success("Resume generated successfully!")
        
        # Display download button
        with open(output_path, "rb") as pdf_file:
            PDFbyte = pdf_file.read()
            st.download_button(
                label="Download Resume PDF",
                data=PDFbyte,
                file_name=os.path.basename(output_path),
                mime='application/pdf'
            )
            
    except json.JSONDecodeError:
        st.error("Invalid JSON format. Please check your input.")
    except Exception as e:
        st.error(f"Error generating resume: {str(e)}") 