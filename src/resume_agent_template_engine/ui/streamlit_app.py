import json
import os
import sys
import tempfile
from typing import Any

import streamlit as st
import yaml

# Add the src directory to the Python path
current_dir = os.path.dirname(__file__)
src_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
project_root = os.path.abspath(os.path.join(src_dir, ".."))
sys.path.insert(0, src_dir)

from resume_agent_template_engine.core.errors import ErrorCode
from resume_agent_template_engine.core.exceptions import ValidationException
from resume_agent_template_engine.core.template_engine import TemplateEngine

# Configure Streamlit page
st.set_page_config(
    page_title="Resume Agent Template Engine", page_icon="📄", layout="wide"
)


def parse_input_data(input_text: str, input_format: str) -> dict[str, Any]:
    """Parse input data based on format (JSON or YAML)"""
    try:
        if input_format.lower() == "yaml":
            return yaml.safe_load(input_text)
        else:
            return json.loads(input_text)
    except json.JSONDecodeError as e:
        raise ValidationException(
            error_code=ErrorCode.VAL013,
            field_path="input_data",
            context={"details": str(e)},
        )
    except yaml.YAMLError as e:
        raise ValidationException(
            error_code=ErrorCode.VAL014,
            field_path="input_data",
            context={"details": str(e)},
        )


def main():
    st.title("📄 Resume Agent Template Engine")
    st.markdown("### JSON & YAML to PDF Generator")

    # Initialize session state
    if "generated_file" not in st.session_state:
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
            help="Choose the type of document you want to generate",
        )

    with col2:
        templates = available_templates.get(document_type, [])
        if templates:
            template = st.selectbox(
                "Template", templates, help="Choose a template for your document"
            )
        else:
            st.warning(f"No templates available for {document_type}")
            return

    # Data input section with tabs for JSON and YAML
    st.subheader("📝 Data Input")

    tab1, tab2 = st.tabs(["JSON Input", "YAML Input"])

    with tab1:
        st.markdown("#### JSON Format")

        # Show example JSON structure
        with st.expander("📋 View Example JSON Structure", expanded=False):
            st.info(
                "📝 Note: Only personalInfo with name and email are required. All other sections are optional!"
            )
            example_json = {
                "personalInfo": {
                    "name": "John Doe",  # Required
                    "email": "john.doe@email.com",  # Required
                    "phone": "+1 (555) 123-4567",  # Optional
                    "location": "San Francisco, CA",  # Optional
                    "website": "https://johndoe.com",  # Optional
                    "linkedin": "https://linkedin.com/in/johndoe",  # Optional
                    "website_display": "https://johndoe.dev",  # Optional
                    "linkedin_display": "https://linkedin.com/in/johndoe",  # Optional
                },
                "professionalSummary": "Experienced software engineer with 5+ years of experience...",  # Optional
                "experience": [  # Optional section
                    {
                        "title": "Senior Software Engineer",
                        "company": "Tech Corp",
                        "location": "San Francisco, CA",
                        "startDate": "2021-03",
                        "endDate": "Present",
                        "details": [
                            "Led development of microservices architecture",
                            "Improved system performance by 40%",
                            "Mentored junior developers",
                        ],
                    }
                ],
                "education": [  # Optional section
                    {
                        "degree": "Bachelor of Science in Computer Science",
                        "institution": "University of California",
                        "location": "Berkeley, CA",
                        "date": "2019-05",
                        "details": ["GPA: 3.8/4.0", "Dean's List"],
                    }
                ],
                "skills": [
                    "Python",
                    "JavaScript",
                    "React",
                    "Node.js",
                    "AWS",
                    "Docker",
                ],  # Optional section
                "projects": [  # Optional section
                    {
                        "name": "E-commerce Platform",
                        "description": "Built a full-stack e-commerce application",
                        "technologies": ["React", "Node.js", "MongoDB"],
                    }
                ],
            }
            st.json(example_json)

        # JSON input text area
        json_input = st.text_area(
            "Paste your JSON data here:",
            height=400,
            placeholder="Paste your JSON data here...",
            help="Enter valid JSON data following the structure shown in the example above",
            key="json_input",
        )

    with tab2:
        st.markdown("#### YAML Format")

        # Show example YAML structure
        with st.expander("📋 View Example YAML Structure", expanded=False):
            st.info(
                "📝 Note: Only personalInfo with name and email are required. All other sections are optional!"
            )
            example_yaml = """personalInfo:
  name: John Doe  # Required
  email: john.doe@email.com  # Required
  phone: "+1 (555) 123-4567"  # Optional
  location: San Francisco, CA  # Optional
  website: https://johndoe.com  # Optional
  linkedin: https://linkedin.com/in/johndoe  # Optional
  website_display: https://johndoe.dev  # Optional
  linkedin_display: https://linkedin.com/in/johndoe  # Optional

# All sections below are optional
professionalSummary: "Experienced software engineer with 5+ years of experience..."

experience:
  - title: Senior Software Engineer
    company: Tech Corp
    location: San Francisco, CA
    startDate: "2021-03"
    endDate: Present
    details:
      - Led development of microservices architecture
      - Improved system performance by 40%
      - Mentored junior developers

education:
  - degree: Bachelor of Science in Computer Science
    institution: University of California
    location: Berkeley, CA
    date: "2019-05"
    details:
      - "GPA: 3.8/4.0"
      - "Dean's List"

skills:
  - Python
  - JavaScript
  - React
  - Node.js
  - AWS
  - Docker

projects:
  - name: E-commerce Platform
    description: Built a full-stack e-commerce application
    technologies:
      - React
      - Node.js
      - MongoDB"""
            st.code(example_yaml, language="yaml")

        # YAML input text area
        yaml_input = st.text_area(
            "Paste your YAML data here:",
            height=400,
            placeholder="Paste your YAML data here...",
            help="Enter valid YAML data following the structure shown in the example above",
            key="yaml_input",
        )

    # Determine which input has data and set format accordingly
    json_has_data = json_input.strip()
    yaml_has_data = yaml_input.strip()

    if json_has_data and yaml_has_data:
        st.warning(
            "⚠️ Both JSON and YAML inputs contain data. Please use only one format at a time. JSON will be prioritized."
        )
        input_format = "JSON"
        data_input = json_input
    elif json_has_data:
        input_format = "JSON"
        data_input = json_input
    elif yaml_has_data:
        input_format = "YAML"
        data_input = yaml_input
    else:
        input_format = "JSON"  # Default format for error messages
        data_input = ""

    # Generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        output_format = st.selectbox(
            "Output format",
            options=["pdf", "docx"],
            index=0,
        )
        generate_button = st.button(
            f"🎯 Generate {output_format.upper()} from {input_format}",
            type="primary",
            use_container_width=True,
        )

    if generate_button:
        if not data_input.strip():
            st.error("Please enter JSON or YAML data before generating the document.")
            return

        try:
            # Parse data based on format
            data = parse_input_data(data_input, input_format)

            # Validate required fields
            if not data.get("personalInfo", {}).get("name"):
                st.error(f"{input_format} must contain personalInfo.name field")
                return

            if not data.get("personalInfo", {}).get("email"):
                st.error(f"{input_format} must contain personalInfo.email field")
                return

            # Generate document
            with st.spinner(f"Generating {output_format.upper()}... Please wait..."):
                suffix = ".pdf" if output_format == "pdf" else ".docx"
                with tempfile.NamedTemporaryFile(
                    suffix=suffix, delete=False
                ) as tmp_file:
                    output_path = tmp_file.name

                if output_format == "pdf":
                    engine.export_to_pdf(document_type, template, data, output_path)
                else:
                    engine.export_to_docx(document_type, template, data, output_path)

                # Read the generated file
                with open(output_path, "rb") as file:
                    file_data = file.read()

                # Store in session state
                person_name = (
                    data.get("personalInfo", {})
                    .get("name", "document")
                    .replace(" ", "_")
                )
                filename = (
                    f"{document_type}_{template}_{person_name}.pdf"
                    if output_format == "pdf"
                    else f"{document_type}_{template}_{person_name}.docx"
                )
                st.session_state.generated_file = {
                    "data": file_data,
                    "filename": filename,
                    "type": output_format,
                }

                # Clean up
                os.unlink(output_path)

                st.success(
                    f"✅ {output_format.upper()} generated successfully from {input_format} data!"
                )

        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Error generating {output_format.upper()}: {str(e)}")

    # Display download button and PDF preview if file is generated
    if st.session_state.generated_file:
        st.markdown("---")

        # Download button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            mime = (
                "application/pdf"
                if st.session_state.generated_file.get("type") == "pdf"
                else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            st.download_button(
                label="📥 Download File",
                data=st.session_state.generated_file["data"],
                file_name=st.session_state.generated_file["filename"],
                mime=mime,
                use_container_width=True,
            )

        # PDF preview
        if st.session_state.generated_file.get("type") == "pdf":
            st.subheader("📄 PDF Preview")
            try:
                st.write(
                    "Your generated PDF is ready for download above. Preview may vary depending on your browser's PDF support."
                )
                # Display the PDF in an iframe
                import base64

                b64_pdf = base64.b64encode(st.session_state.generated_file["data"]).decode(
                    "utf-8"
                )
                pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
            except Exception:
                st.info("PDF preview not available. Please download the file to view it.")


if __name__ == "__main__":
    main()
