import streamlit as st
import json
import os
import sys
import tempfile
from typing import Dict, Any

# Add the src directory to the Python path
current_dir = os.path.dirname(__file__)
src_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
project_root = os.path.abspath(os.path.join(src_dir, ".."))
sys.path.insert(0, src_dir)

from resume_agent_template_engine.core.template_engine import TemplateEngine

# Configure Streamlit page
st.set_page_config(
    page_title="Resume Agent Template Engine",
    page_icon="📄",
    layout="wide"
)

def main():
    st.title("📄 Resume Agent Template Engine")
    st.markdown("### Simple JSON to PDF Generator")
    
    # Initialize session state
    if 'generated_file' not in st.session_state:
        st.session_state.generated_file = None
    
    # Get available templates
    try:
        engine = TemplateEngine()
        available_templates = engine.get_available_templates()
    except Exception as e:
        st.error(f"Error loading templates: {str(e)}")
        return
    
    # Document type and template selection
    col1, col2 = st.columns(2)
    
    with col1:
        document_type = st.selectbox(
            "Document Type",
            list(available_templates.keys()) if available_templates else ["resume"],
            help="Choose the type of document you want to generate"
        )
    
    with col2:
        templates = available_templates.get(document_type, [])
        if templates:
            template = st.selectbox(
                "Template",
                templates,
                help="Choose a template for your document"
            )
        else:
            st.warning(f"No templates available for {document_type}")
            return
    
    # JSON input section
    st.subheader("📝 JSON Data Input")
    
    # Show example JSON structure
    with st.expander("📋 View Example JSON Structure", expanded=False):
        example_json = {
            "personalInfo": {
                "name": "John Doe",
                "email": "john.doe@email.com",
                "phone": "+1 (555) 123-4567",
                "location": "San Francisco, CA",
                "website": "https://johndoe.com",
                "linkedin": "https://linkedin.com/in/johndoe"
            },
            "professionalSummary": "Experienced software engineer with 5+ years of experience...",
            "experience": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Corp",
                    "location": "San Francisco, CA",
                    "startDate": "2021-03",
                    "endDate": "Present",
                    "details": [
                        "Led development of microservices architecture",
                        "Improved system performance by 40%",
                        "Mentored junior developers"
                    ]
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "University of California",
                    "location": "Berkeley, CA",
                    "date": "2019-05",
                    "details": ["GPA: 3.8/4.0", "Dean's List"]
                }
            ],
            "skills": ["Python", "JavaScript", "React", "Node.js", "AWS", "Docker"],
            "projects": [
                {
                    "name": "E-commerce Platform",
                    "description": "Built a full-stack e-commerce application",
                    "technologies": ["React", "Node.js", "MongoDB"]
                }
            ]
        }
        st.json(example_json)
    
    # JSON input text area
    json_input = st.text_area(
        "Paste your JSON data here:",
        height=400,
        placeholder="Paste your JSON data here...",
        help="Enter valid JSON data following the structure shown in the example above"
    )
    
    # Generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_button = st.button("🎯 Generate PDF", type="primary", use_container_width=True)
    
    if generate_button:
        if not json_input.strip():
            st.error("Please enter JSON data before generating the document.")
            return
        
        try:
            # Parse JSON
            data = json.loads(json_input)
            
            # Validate required fields
            if not data.get("personalInfo", {}).get("name"):
                st.error("JSON must contain personalInfo.name field")
                return
            
            if not data.get("personalInfo", {}).get("email"):
                st.error("JSON must contain personalInfo.email field")
                return
            
            # Generate document
            with st.spinner("Generating PDF... Please wait..."):
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                    output_path = tmp_file.name
                
                engine.export_to_pdf(document_type, template, data, output_path)
                
                # Read the generated file
                with open(output_path, 'rb') as file:
                    file_data = file.read()
                
                # Store in session state
                person_name = data.get("personalInfo", {}).get("name", "document").replace(" ", "_")
                st.session_state.generated_file = {
                    'data': file_data,
                    'filename': f"{document_type}_{template}_{person_name}.pdf"
                }
                
                # Clean up
                os.unlink(output_path)
                
                st.success("✅ PDF generated successfully!")
        
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
    
    # Display download button and PDF preview if file is generated
    if st.session_state.generated_file:
        st.markdown("---")
        
        # Download button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.download_button(
                label="📥 Download PDF",
                data=st.session_state.generated_file['data'],
                file_name=st.session_state.generated_file['filename'],
                mime="application/pdf",
                use_container_width=True
            )
        
        # PDF preview
        st.subheader("📄 PDF Preview")
        try:
            st.write("Your generated PDF is ready for download above. Preview may vary depending on your browser's PDF support.")
            # Display the PDF in an iframe
            import base64
            b64_pdf = base64.b64encode(st.session_state.generated_file['data']).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        except Exception as e:
            st.info("PDF preview not available. Please download the file to view it.")

if __name__ == "__main__":
    main() 