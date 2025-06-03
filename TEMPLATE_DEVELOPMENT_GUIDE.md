# Template Development Guide

This comprehensive guide covers everything you need to know about developing templates for the Resume AI Agent Template Engine.

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Template Architecture](#template-architecture)
4. [Creating a New Template](#creating-a-new-template)
5. [LaTeX Template Development](#latex-template-development)
6. [Python Helper Development](#python-helper-development)
7. [Template Configuration](#template-configuration)
8. [Data Schema and Validation](#data-schema-and-validation)
9. [Template Inheritance](#template-inheritance)
10. [Testing Your Template](#testing-your-template)
11. [Advanced Features](#advanced-features)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)
14. [Contributing Templates](#contributing-templates)

## Overview

The Resume AI Agent Template Engine uses a sophisticated template system that combines:
- **LaTeX Templates**: For PDF generation and professional formatting
- **Python Helpers**: For data processing, validation, and logic
- **YAML Configuration**: For template metadata and settings
- **Inheritance System**: For code reuse and maintainability

### Template Types

The engine supports two main document types:
- **Resume Templates**: Located in `src/resume_agent_template_engine/templates/resume/`
- **Cover Letter Templates**: Located in `src/resume_agent_template_engine/templates/cover_letter/`

## Getting Started

### Prerequisites

1. **LaTeX Environment**: Install TeX Live, MiKTeX, or MacTeX
2. **Python 3.8+**: With required packages from `requirements.txt`
3. **Development Environment**: Familiarity with LaTeX and Python

### Development Setup

1. Clone the repository and set up the development environment:
   ```bash
   git clone https://github.com/taleye-com/resume-agent-template-engine
   cd resume-agent-template-engine
   chmod +x setup-dev.sh
   ./setup-dev.sh
   ```

2. Activate the virtual environment:
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Test the existing templates to ensure everything works:
   ```bash
   python -m pytest tests/unit/test_templates.py -v
   ```

## Template Architecture

### Directory Structure

Each template follows a standardized directory structure:

```
templates/
├── resume/
│   └── your_template_name/
│       ├── template.tex          # Main LaTeX template
│       ├── helper.py            # Python helper class
│       ├── template.yaml        # Template configuration
│       ├── README.md            # Template documentation
│       ├── preview.png          # Template preview image
│       └── assets/              # Optional assets directory
│           ├── fonts/           # Custom fonts
│           ├── images/          # Template images
│           └── styles/          # Additional style files
└── cover_letter/
    └── your_template_name/
        └── [same structure as above]
```

### Required Files

1. **`template.tex`**: The main LaTeX template file
2. **`helper.py`**: Python class that implements `TemplateInterface`
3. **`README.md`**: Documentation for the template
4. **`preview.png`**: Visual preview of the template output

### Optional Files

1. **`template.yaml`**: Template configuration and metadata
2. **`assets/`**: Directory for template-specific assets
3. **Custom LaTeX files**: Additional `.tex` files for modular design

## Creating a New Template

### Step 1: Choose Your Template Name and Type

```bash
# For a resume template
TEMPLATE_TYPE="resume"
TEMPLATE_NAME="modern_professional"

# For a cover letter template
TEMPLATE_TYPE="cover_letter"
TEMPLATE_NAME="executive_style"
```

### Step 2: Create Directory Structure

```bash
mkdir -p "src/resume_agent_template_engine/templates/${TEMPLATE_TYPE}/${TEMPLATE_NAME}"
cd "src/resume_agent_template_engine/templates/${TEMPLATE_TYPE}/${TEMPLATE_NAME}"
```

### Step 3: Create Basic Files

Create the essential files with templates provided in the following sections.

## LaTeX Template Development

### Basic Template Structure

Create `template.tex` with this basic structure:

```latex
\documentclass[11pt,a4paper,sans]{moderncv}

% Template configuration
\moderncvstyle{classic}
\moderncvcolor{blue}

% Packages
\usepackage[utf8]{inputenc}
\usepackage[scale=0.75]{geometry}
\usepackage{import}

% Custom commands and styling
\newcommand{\cvdoublecolumn}[2]{%
  \cvitem[0.75em]{}{%
    \begin{minipage}[t]{\listdoubleitemcolumnwidth}#1\end{minipage}%
    \hfill%
    \begin{minipage}[t]{\listdoubleitemcolumnwidth}#2\end{minipage}%
  }%
}

% Template variables (will be replaced by the engine)
\name{{{personal_info.name}}}
\title{{{personal_info.title}}}
\address{{{personal_info.address}}}
\phone{{{personal_info.phone}}}
\email{{{personal_info.email}}}

\begin{document}

\makecvtitle

% Professional Summary
{{#if professional_summary}}
\section{Professional Summary}
\cvitem{}{{{professional_summary.summary}}}
{{/if}}

% Experience Section
{{#if experience}}
\section{Experience}
{{#each experience}}
\cventry{{{start_date}}}--{{#if end_date}}{{{end_date}}}{{else}}Present{{/if}}}
        {{{title}}}
        {{{company}}}
        {{{location}}}
        {}
        {{{description}}}
{{/each}}
{{/if}}

% Education Section
{{#if education}}
\section{Education}
{{#each education}}
\cventry{{{start_date}}}--{{#if end_date}}{{{end_date}}}{{else}}Present{{/if}}}
        {{{degree}}}
        {{{institution}}}
        {{{location}}}
        {{#if gpa}}\textit{GPA: {{{gpa}}}}{{/if}}
        {{{description}}}
{{/each}}
{{/if}}

% Skills Section
{{#if skills}}
\section{Skills}
{{#each skills}}
\cvitem{{{category}}}{{{skills_list}}}
{{/each}}
{{/if}}

\end{document}
```

### Template Variables

The engine supports several variable formats:

1. **Simple Variables**: `{{{variable_name}}}`
2. **Nested Variables**: `{{{personal_info.name}}}`
3. **Conditional Blocks**: 
   ```latex
   {{#if section_name}}
   Content here
   {{/if}}
   ```
4. **Loops**: 
   ```latex
   {{#each items}}
   Item: {{{title}}}
   {{/each}}
   ```

### Advanced LaTeX Features

#### Custom Macros

Define reusable LaTeX macros:

```latex
% Custom section header
\newcommand{\customsection}[2]{%
  \section{#1}
  \vspace{-2mm}
  \hrule height 0.5pt
  \vspace{2mm}
  #2
}

% Custom skill item
\newcommand{\skillitem}[2]{%
  \cvitem{\textbf{#1}}{#2}
}
```

#### Font Management

```latex
% Font configuration
\usepackage{fontspec}
\setmainfont{Source Sans Pro}
\setsansfont{Source Sans Pro}
\setmonofont{Source Code Pro}

% Or for pdflatex compatibility
\usepackage[T1]{fontenc}
\usepackage{lmodern}
```

#### Color Schemes

```latex
% Define custom colors
\usepackage{xcolor}
\definecolor{primary}{RGB}{41, 128, 185}
\definecolor{secondary}{RGB}{52, 73, 94}
\definecolor{accent}{RGB}{155, 89, 182}

% Use colors in template
\moderncvcolor{primary}
```

## Python Helper Development

### Basic Helper Class

Create `helper.py` with your template class:

```python
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from ...core.template_engine import TemplateInterface, DocumentType
from ...core.validation import BaseValidator, ValidationIssue, ValidationSeverity
from ...core.latex_processor import LaTeXProcessor
from ...utils.date_utils import format_date_range
from ...utils.text_utils import sanitize_latex

logger = logging.getLogger(__name__)


class YourTemplateNameTemplate(TemplateInterface):
    """Your template description here"""
    
    def __init__(self, data: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        """Initialize template with data and configuration"""
        super().__init__(data, config)
        self.latex_processor = LaTeXProcessor()
        self.template_dir = Path(__file__).parent
        
    @property
    def template_type(self) -> DocumentType:
        """Return the document type this template handles"""
        return DocumentType.RESUME  # or DocumentType.COVER_LETTER
    
    @property
    def required_fields(self) -> List[str]:
        """List of required data fields for this template"""
        return [
            "personalInfo",
            "professionalSummary",
            "experience",
            "education",
            "skills"
        ]
    
    def validate_data(self) -> None:
        """Validate that required data fields are present"""
        missing_fields = []
        for field in self.required_fields:
            if field not in self.data or not self.data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Additional custom validation
        self._validate_personal_info()
        self._validate_experience()
    
    def _validate_personal_info(self) -> None:
        """Validate personal information"""
        personal_info = self.data.get("personalInfo", {})
        required_personal_fields = ["name", "email"]
        
        for field in required_personal_fields:
            if not personal_info.get(field):
                raise ValueError(f"Missing required personal info field: {field}")
    
    def _validate_experience(self) -> None:
        """Validate experience data"""
        experience = self.data.get("experience", [])
        if not isinstance(experience, list):
            raise ValueError("Experience must be a list")
        
        for i, exp in enumerate(experience):
            if not exp.get("title"):
                raise ValueError(f"Experience item {i+1} missing title")
            if not exp.get("company"):
                raise ValueError(f"Experience item {i+1} missing company")
    
    def render(self) -> str:
        """Render the template to LaTeX content"""
        try:
            # Load the LaTeX template
            template_path = self.template_dir / "template.tex"
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Process the data
            processed_data = self._process_data()
            
            # Render with the LaTeX processor
            rendered_content = self.latex_processor.render_template(
                template_content, 
                processed_data,
                self.config
            )
            
            return rendered_content
            
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            raise
    
    def _process_data(self) -> Dict[str, Any]:
        """Process and transform data for template rendering"""
        processed = self.data.copy()
        
        # Process personal information
        if "personalInfo" in processed:
            processed["personal_info"] = self._process_personal_info(
                processed["personalInfo"]
            )
        
        # Process experience
        if "experience" in processed:
            processed["experience"] = self._process_experience(
                processed["experience"]
            )
        
        # Process education
        if "education" in processed:
            processed["education"] = self._process_education(
                processed["education"]
            )
        
        # Process skills
        if "skills" in processed:
            processed["skills"] = self._process_skills(
                processed["skills"]
            )
        
        return processed
    
    def _process_personal_info(self, personal_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process personal information for LaTeX rendering"""
        processed = personal_info.copy()
        
        # Sanitize text fields
        for field in ["name", "title", "address"]:
            if field in processed:
                processed[field] = sanitize_latex(processed[field])
        
        # Format contact information
        if "phone" in processed:
            processed["phone"] = self._format_phone(processed["phone"])
        
        return processed
    
    def _process_experience(self, experience: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process experience data"""
        processed = []
        
        for exp in experience:
            processed_exp = exp.copy()
            
            # Sanitize text fields
            for field in ["title", "company", "location", "description"]:
                if field in processed_exp:
                    processed_exp[field] = sanitize_latex(processed_exp[field])
            
            # Format date range
            if "startDate" in processed_exp:
                date_range = format_date_range(
                    processed_exp.get("startDate"),
                    processed_exp.get("endDate")
                )
                processed_exp["date_range"] = date_range
            
            processed.append(processed_exp)
        
        return processed
    
    def _process_education(self, education: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process education data"""
        processed = []
        
        for edu in education:
            processed_edu = edu.copy()
            
            # Sanitize text fields
            for field in ["degree", "institution", "location", "description"]:
                if field in processed_edu:
                    processed_edu[field] = sanitize_latex(processed_edu[field])
            
            # Format date range
            if "startDate" in processed_edu:
                date_range = format_date_range(
                    processed_edu.get("startDate"),
                    processed_edu.get("endDate")
                )
                processed_edu["date_range"] = date_range
            
            processed.append(processed_edu)
        
        return processed
    
    def _process_skills(self, skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process skills data"""
        processed = []
        
        for skill_group in skills:
            processed_group = skill_group.copy()
            
            if "category" in processed_group:
                processed_group["category"] = sanitize_latex(processed_group["category"])
            
            if "skills" in processed_group:
                if isinstance(processed_group["skills"], list):
                    # Join skills with commas
                    skills_list = [sanitize_latex(str(skill)) for skill in processed_group["skills"]]
                    processed_group["skills_list"] = ", ".join(skills_list)
                else:
                    processed_group["skills_list"] = sanitize_latex(str(processed_group["skills"]))
            
            processed.append(processed_group)
        
        return processed
    
    def _format_phone(self, phone: str) -> str:
        """Format phone number for display"""
        # Remove non-digit characters
        digits = ''.join(filter(str.isdigit, phone))
        
        # Format US phone numbers
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return phone  # Return original if can't format
    
    def export_to_pdf(self, output_path: str) -> str:
        """Export the rendered content to PDF"""
        try:
            # Render the template
            latex_content = self.render()
            
            # Use the LaTeX processor to compile to PDF
            pdf_path = self.latex_processor.compile_to_pdf(
                latex_content,
                output_path,
                config=self.config
            )
            
            logger.info(f"Successfully exported PDF to: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error exporting to PDF: {e}")
            raise
```

### Helper Class Best Practices

1. **Inheritance**: Extend `TemplateInterface` for consistency
2. **Validation**: Implement thorough data validation
3. **Error Handling**: Use proper exception handling and logging
4. **Data Processing**: Sanitize and format data appropriately
5. **Modularity**: Break complex logic into private methods

## Template Configuration

### Template Metadata (`template.yaml`)

```yaml
# Template metadata
name: "Modern Professional"
description: "A modern, clean resume template suitable for professional roles"
version: "1.0.0"
author: "Your Name"
license: "MIT"
tags: ["modern", "professional", "clean"]

# Template configuration
config:
  # LaTeX compilation settings
  latex:
    engine: "pdflatex"
    packages:
      - "moderncv"
      - "fontawesome"
      - "xcolor"
    compile_twice: true
  
  # Typography settings
  typography:
    font_family: "Source Sans Pro"
    font_size: "11pt"
    line_spacing: 1.15
  
  # Layout settings
  layout:
    page_format: "a4paper"
    margins:
      top: "0.75in"
      bottom: "0.75in"
      left: "0.75in"
      right: "0.75in"
    columns: 1
  
  # Color scheme
  colors:
    primary: "#2980b9"
    secondary: "#34495e"
    accent: "#e74c3c"
  
  # Section configuration
  sections:
    - name: "personalInfo"
      required: true
      order: 1
    - name: "professionalSummary"
      required: false
      order: 2
    - name: "experience"
      required: true
      order: 3
    - name: "education"
      required: true
      order: 4
    - name: "skills"
      required: false
      order: 5
    - name: "certifications"
      required: false
      order: 6

# Template inheritance (optional)
inheritance:
  parent: null  # No parent template
  extends: []   # No extended templates

# Validation rules
validation:
  strict_mode: false
  required_fields:
    - "personalInfo.name"
    - "personalInfo.email"
    - "experience"
    - "education"
  
  field_constraints:
    personalInfo:
      name:
        max_length: 100
      email:
        format: "email"
    experience:
      min_items: 1
      max_items: 10
    skills:
      max_items: 8

# Output settings
output:
  formats: ["pdf"]
  quality: "high"
  optimization: true
```

## Data Schema and Validation

### Understanding the Data Schema

The engine expects data in a specific format. Here's the complete schema:

#### Personal Information
```json
{
  "personalInfo": {
    "name": "John Doe",
    "title": "Software Engineer",  // Optional
    "email": "john.doe@example.com",
    "phone": "+1 (555) 123-4567",  // Optional
    "location": "San Francisco, CA",  // Optional
    "website": "https://johndoe.com",  // Optional
    "linkedin": "https://linkedin.com/in/johndoe",  // Optional
    "github": "https://github.com/johndoe"  // Optional
  }
}
```

#### Professional Summary
```json
{
  "professionalSummary": {
    "summary": "Experienced software engineer with 5+ years..."
  }
}
```

#### Experience
```json
{
  "experience": [
    {
      "title": "Senior Software Engineer",
      "company": "Tech Corp",
      "location": "San Francisco, CA",
      "startDate": "2020-01-15",
      "endDate": "2023-12-31",  // Optional (current job)
      "description": "Led development of...",
      "achievements": [  // Optional
        "Increased performance by 40%",
        "Led team of 5 developers"
      ]
    }
  ]
}
```

#### Education
```json
{
  "education": [
    {
      "degree": "Bachelor of Science in Computer Science",
      "institution": "University of California, Berkeley",
      "location": "Berkeley, CA",
      "startDate": "2014-08-15",
      "endDate": "2018-05-20",
      "gpa": "3.8",  // Optional
      "honors": ["Magna Cum Laude"],  // Optional
      "coursework": ["Data Structures", "Algorithms"]  // Optional
    }
  ]
}
```

#### Skills
```json
{
  "skills": [
    {
      "category": "Programming Languages",
      "skills": ["Python", "JavaScript", "Java", "Go"]
    },
    {
      "category": "Frameworks",
      "skills": ["React", "Django", "FastAPI"]
    }
  ]
}
```

### Custom Validation

You can implement custom validation in your helper class:

```python
def _validate_custom_requirements(self) -> None:
    """Implement template-specific validation"""
    
    # Example: Ensure minimum experience years
    experience = self.data.get("experience", [])
    if len(experience) < 2:
        raise ValueError("This template requires at least 2 work experiences")
    
    # Example: Ensure specific skills are present
    skills = self.data.get("skills", [])
    required_skill_categories = ["Programming Languages", "Frameworks"]
    
    skill_categories = [skill.get("category", "") for skill in skills]
    for required_category in required_skill_categories:
        if required_category not in skill_categories:
            raise ValueError(f"Missing required skill category: {required_category}")
```

## Template Inheritance

### Creating a Parent Template

Create a base template that other templates can inherit from:

```python
# In base_modern.py
class BaseModernTemplate(TemplateInterface):
    """Base class for modern-style templates"""
    
    def __init__(self, data: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        super().__init__(data, config)
        self.color_scheme = self.config.get("color_scheme", "blue")
        self.font_size = self.config.get("font_size", "11pt")
    
    def _get_common_latex_header(self) -> str:
        """Return common LaTeX header for modern templates"""
        return f"""
\\documentclass[{self.font_size},a4paper,sans]{{moderncv}}
\\moderncvstyle{{modern}}
\\moderncvcolor{{{self.color_scheme}}}

\\usepackage[utf8]{{inputenc}}
\\usepackage[scale=0.75]{{geometry}}
\\usepackage{{fontawesome}}
"""
    
    def _format_section_header(self, title: str) -> str:
        """Format section headers consistently"""
        return f"\\section{{{title}}}"
```

### Child Template

```python
# In modern_professional.py
from .base_modern import BaseModernTemplate

class ModernProfessionalTemplate(BaseModernTemplate):
    """Modern professional template extending base modern"""
    
    def render(self) -> str:
        """Render using parent class methods"""
        header = self._get_common_latex_header()
        
        # Add template-specific content
        content = self._render_body()
        
        return f"{header}\n\\begin{{document}}\n{content}\n\\end{{document}}"
    
    def _render_body(self) -> str:
        """Render template-specific body content"""
        # Implementation specific to this template
        pass
```

### Inheritance Configuration

In `template.yaml`:

```yaml
inheritance:
  parent: "resume/base_modern"
  extends: ["resume/common_sections"]
  
dependencies:
  - "fontawesome"
  - "moderncv"
```

## Testing Your Template

### Unit Tests

Create comprehensive tests for your template:

```python
# In tests/unit/test_your_template.py
import pytest
from pathlib import Path
import tempfile
import os

from src.resume_agent_template_engine.templates.resume.your_template.helper import YourTemplateTemplate


class TestYourTemplate:
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for testing"""
        return {
            "personalInfo": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "555-123-4567",
                "location": "San Francisco, CA"
            },
            "professionalSummary": {
                "summary": "Experienced software engineer"
            },
            "experience": [
                {
                    "title": "Software Engineer",
                    "company": "Tech Corp",
                    "location": "SF, CA",
                    "startDate": "2020-01-01",
                    "endDate": "2023-12-31",
                    "description": "Developed software applications"
                }
            ],
            "education": [
                {
                    "degree": "BS Computer Science",
                    "institution": "UC Berkeley",
                    "startDate": "2016-08-01",
                    "endDate": "2020-05-15"
                }
            ],
            "skills": [
                {
                    "category": "Programming",
                    "skills": ["Python", "JavaScript"]
                }
            ]
        }
    
    @pytest.fixture
    def template_config(self):
        """Template configuration for testing"""
        return {
            "font_size": "11pt",
            "color_scheme": "blue"
        }
    
    def test_template_initialization(self, sample_data, template_config):
        """Test template initialization"""
        template = YourTemplateTemplate(sample_data, template_config)
        assert template.data == sample_data
        assert template.config == template_config
    
    def test_data_validation_success(self, sample_data, template_config):
        """Test successful data validation"""
        template = YourTemplateTemplate(sample_data, template_config)
        # Should not raise an exception
        template.validate_data()
    
    def test_data_validation_missing_required_field(self, sample_data, template_config):
        """Test validation with missing required field"""
        data = sample_data.copy()
        del data["personalInfo"]["name"]
        
        with pytest.raises(ValueError, match="Missing required"):
            YourTemplateTemplate(data, template_config)
    
    def test_render_latex_content(self, sample_data, template_config):
        """Test LaTeX content rendering"""
        template = YourTemplateTemplate(sample_data, template_config)
        content = template.render()
        
        assert "\\documentclass" in content
        assert "\\begin{document}" in content
        assert "\\end{document}" in content
        assert "John Doe" in content
    
    def test_pdf_export(self, sample_data, template_config):
        """Test PDF export functionality"""
        template = YourTemplateTemplate(sample_data, template_config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_resume.pdf")
            
            try:
                result_path = template.export_to_pdf(output_path)
                assert os.path.exists(result_path)
                assert result_path.endswith(".pdf")
            except Exception as e:
                # LaTeX might not be available in test environment
                pytest.skip(f"LaTeX compilation failed: {e}")
    
    def test_data_processing(self, sample_data, template_config):
        """Test data processing methods"""
        template = YourTemplateTemplate(sample_data, template_config)
        processed = template._process_data()
        
        # Check that personal info is processed
        assert "personal_info" in processed
        assert processed["personal_info"]["name"] == "John Doe"
        
        # Check that experience is processed
        assert "experience" in processed
        assert len(processed["experience"]) == 1
    
    def test_phone_formatting(self, sample_data, template_config):
        """Test phone number formatting"""
        template = YourTemplateTemplate(sample_data, template_config)
        
        # Test various phone formats
        assert template._format_phone("5551234567") == "(555) 123-4567"
        assert template._format_phone("15551234567") == "+1 (555) 123-4567"
        assert template._format_phone("+1-555-123-4567") == "+1 (555) 123-4567"
```

### Integration Tests

```python
# In tests/integration/test_template_integration.py
import pytest
import tempfile
import os
from pathlib import Path

from src.resume_agent_template_engine.core.template_engine import TemplateEngine


class TestTemplateIntegration:
    
    @pytest.fixture
    def template_engine(self):
        """Create template engine for testing"""
        return TemplateEngine()
    
    @pytest.fixture
    def sample_resume_data(self):
        """Complete sample resume data"""
        return {
            # Complete data structure as shown above
        }
    
    def test_template_discovery(self, template_engine):
        """Test that templates are discovered correctly"""
        templates = template_engine.get_available_templates("resume")
        assert "your_template_name" in templates
    
    def test_template_creation(self, template_engine, sample_resume_data):
        """Test template creation through engine"""
        template = template_engine.create_template(
            "resume", "your_template_name", sample_resume_data
        )
        assert template is not None
    
    def test_end_to_end_pdf_generation(self, template_engine, sample_resume_data):
        """Test complete PDF generation process"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "integration_test.pdf")
            
            try:
                result = template_engine.export_to_pdf(
                    "resume", "your_template_name", sample_resume_data, output_path
                )
                assert os.path.exists(result)
            except Exception as e:
                pytest.skip(f"LaTeX compilation failed: {e}")
```

### Running Tests

```bash
# Run unit tests for your template
python -m pytest tests/unit/test_your_template.py -v

# Run integration tests
python -m pytest tests/integration/test_template_integration.py -v

# Run all template tests
python -m pytest tests/ -k "template" -v

# Run with coverage
python -m pytest tests/ --cov=src/resume_agent_template_engine/templates/
```

## Advanced Features

### Custom LaTeX Macros

Register custom macros for your template:

```python
from ...core.macro_system import MacroLibrary

class YourTemplateTemplate(TemplateInterface):
    
    def __init__(self, data: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        super().__init__(data, config)
        self._register_custom_macros()
    
    def _register_custom_macros(self):
        """Register template-specific LaTeX macros"""
        macro_lib = MacroLibrary()
        
        # Custom section macro
        macro_lib.register_macro(
            "customsection",
            r"\newcommand{\customsection}[2]{\section{#1}\vspace{-2mm}\hrule\vspace{2mm}#2}",
            description="Custom section with underline"
        )
        
        # Skill rating macro
        macro_lib.register_macro(
            "skillrating",
            r"\newcommand{\skillrating}[2]{\cvitem{#1}{\foreach \x in {1,...,5}{\ifnum\x<=#2\star\else\circ\fi}}}",
            description="Skill with star rating"
        )
```

### Dynamic Content Generation

```python
def _generate_dynamic_content(self) -> str:
    """Generate content based on data analysis"""
    experience = self.data.get("experience", [])
    
    # Calculate total years of experience
    total_years = self._calculate_experience_years(experience)
    
    # Generate different content based on experience level
    if total_years < 2:
        return "\\textit{Emerging professional with strong foundation}"
    elif total_years < 5:
        return "\\textit{Experienced professional with proven track record}"
    else:
        return "\\textit{Senior professional with extensive expertise}"

def _calculate_experience_years(self, experience: List[Dict[str, Any]]) -> float:
    """Calculate total years of experience"""
    from datetime import datetime
    
    total_days = 0
    for exp in experience:
        start_date = datetime.strptime(exp["startDate"], "%Y-%m-%d")
        end_date = datetime.strptime(
            exp.get("endDate", datetime.now().strftime("%Y-%m-%d")), 
            "%Y-%m-%d"
        )
        total_days += (end_date - start_date).days
    
    return total_days / 365.25
```

### Template Variants

Create template variants with different styles:

```python
class YourTemplateTemplate(TemplateInterface):
    
    VARIANTS = {
        "default": "standard_style.tex",
        "compact": "compact_style.tex",
        "detailed": "detailed_style.tex"
    }
    
    def __init__(self, data: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        super().__init__(data, config)
        self.variant = self.config.get("variant", "default")
    
    def render(self) -> str:
        """Render using the specified variant"""
        template_file = self.VARIANTS.get(self.variant, self.VARIANTS["default"])
        template_path = self.template_dir / template_file
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Process template...
        return processed_content
```

### Internationalization

```python
def _get_localized_labels(self) -> Dict[str, str]:
    """Get localized labels based on configuration"""
    language = self.config.get("language", "en")
    
    labels = {
        "en": {
            "experience": "Experience",
            "education": "Education",
            "skills": "Skills",
            "phone": "Phone",
            "email": "Email"
        },
        "es": {
            "experience": "Experiencia",
            "education": "Educación",
            "skills": "Habilidades",
            "phone": "Teléfono",
            "email": "Correo electrónico"
        },
        "fr": {
            "experience": "Expérience",
            "education": "Éducation",
            "skills": "Compétences",
            "phone": "Téléphone",
            "email": "Email"
        }
    }
    
    return labels.get(language, labels["en"])
```

## Best Practices

### Code Organization

1. **Modular Design**: Break complex logic into small, focused methods
2. **Single Responsibility**: Each method should have one clear purpose
3. **Error Handling**: Implement comprehensive error handling and logging
4. **Documentation**: Document all public methods and complex logic
5. **Type Hints**: Use type hints for better code maintainability

### LaTeX Best Practices

1. **Package Management**: Only include necessary LaTeX packages
2. **Compatibility**: Ensure compatibility with major LaTeX distributions
3. **Escaping**: Properly escape special characters in data
4. **Spacing**: Use consistent spacing and formatting
5. **Comments**: Document complex LaTeX code with comments

### Performance Optimization

```python
from functools import lru_cache
from typing import Dict, Any

class OptimizedTemplate(TemplateInterface):
    
    @lru_cache(maxsize=128)
    def _get_formatted_date(self, date_str: str) -> str:
        """Cached date formatting"""
        # Implementation
        pass
    
    def _batch_process_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple items efficiently"""
        processed = []
        
        # Pre-compile regex patterns
        latex_escape_pattern = re.compile(r'([&%$#_{}~^\\])')
        
        for item in items:
            # Process item efficiently
            processed_item = self._process_single_item(item, latex_escape_pattern)
            processed.append(processed_item)
        
        return processed
```

### Security Considerations

```python
def _sanitize_user_input(self, text: str) -> str:
    """Sanitize user input to prevent LaTeX injection"""
    if not isinstance(text, str):
        text = str(text)
    
    # Remove or escape dangerous LaTeX commands
    dangerous_commands = [
        r'\\input', r'\\include', r'\\write', r'\\immediate',
        r'\\openout', r'\\closeout', r'\\system', r'\\shell'
    ]
    
    for cmd in dangerous_commands:
        text = re.sub(cmd, '', text, flags=re.IGNORECASE)
    
    # Escape special characters
    return sanitize_latex(text)
```

### Version Compatibility

```python
def _check_compatibility(self) -> None:
    """Check for template compatibility"""
    engine_version = self.config.get("engine_version", "1.0.0")
    min_required = "1.2.0"
    
    if version.parse(engine_version) < version.parse(min_required):
        logger.warning(
            f"Template requires engine version {min_required} or higher, "
            f"but {engine_version} is installed"
        )
```

## Troubleshooting

### Common Issues

#### 1. LaTeX Compilation Errors

**Problem**: LaTeX compilation fails with package errors
```
! LaTeX Error: File `moderncv.cls' not found.
```

**Solution**: 
- Ensure required packages are installed
- Add package requirements to `template.yaml`
- Check LaTeX distribution completeness

#### 2. Template Discovery Issues

**Problem**: Template not found by the engine

**Solution**:
- Verify directory structure matches requirements
- Ensure `helper.py` and `.tex` files exist
- Check file permissions
- Restart the application to refresh template cache

#### 3. Data Validation Errors

**Problem**: Template rejects valid data

**Solution**:
- Check `required_fields` in your template class
- Verify data structure matches expected schema
- Add debug logging to validation methods
- Test with minimal sample data

#### 4. Character Encoding Issues

**Problem**: Special characters not rendering correctly

**Solution**:
```python
def _handle_encoding(self, text: str) -> str:
    """Handle character encoding for LaTeX"""
    # Ensure UTF-8 encoding
    if isinstance(text, bytes):
        text = text.decode('utf-8')
    
    # Convert problematic characters
    replacements = {
        '—': '---',  # Em dash
        '–': '--',   # En dash
        '"': '``',   # Left quote
        '"': "''",   # Right quote
        ''': "`",    # Left single quote
        ''': "'",    # Right single quote
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text
```

#### 5. Memory Issues with Large Templates

**Problem**: Out of memory errors during compilation

**Solution**:
- Use the `@memory_efficient_decorator`
- Process data in chunks
- Clear cached data appropriately
- Optimize image processing

### Debugging Tips

1. **Enable Debug Mode**:
   ```python
   template_config = {
       "debug": True,
       "preserve_temp_files": True
   }
   ```

2. **Add Logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   logger = logging.getLogger(__name__)
   
   logger.debug(f"Processing data: {data}")
   logger.info(f"Template rendered successfully")
   ```

3. **Test Incrementally**:
   - Start with minimal data
   - Add sections one by one
   - Test each component separately

4. **Use Template Validator**:
   ```bash
   python -m resume_agent_template_engine.tools.validate_template \
       --template-path "templates/resume/your_template" \
       --sample-data "sample_data/resume/basic.yaml"
   ```

## Contributing Templates

### Submission Process

1. **Fork the Repository**
   ```bash
   git fork https://github.com/taleye-com/resume-agent-template-engine
   git clone https://github.com/yourusername/resume-agent-template-engine
   ```

2. **Create Template Branch**
   ```bash
   git checkout -b feature/add-template-your-template-name
   ```

3. **Develop Your Template**
   - Follow the structure outlined in this guide
   - Include comprehensive tests
   - Add documentation

4. **Quality Checks**
   ```bash
   # Run tests
   python -m pytest tests/unit/test_your_template.py -v
   
   # Check code formatting
   black src/resume_agent_template_engine/templates/
   
   # Type checking
   mypy src/resume_agent_template_engine/templates/
   
   # Template validation
   python -m resume_agent_template_engine.tools.validate_template \
       --template-path "src/resume_agent_template_engine/templates/resume/your_template"
   ```

5. **Submit Pull Request**
   - Include template preview image
   - Add comprehensive description
   - Reference any related issues

### Review Criteria

Templates are evaluated based on:

1. **Code Quality**
   - Follows Python best practices
   - Includes comprehensive error handling
   - Has appropriate type hints and documentation

2. **LaTeX Quality**
   - Professional appearance
   - Cross-platform compatibility
   - Efficient compilation

3. **Testing**
   - Comprehensive unit tests
   - Integration tests
   - Edge case coverage

4. **Documentation**
   - Clear README with examples
   - Template metadata
   - Usage instructions

5. **Uniqueness**
   - Offers distinctive value
   - Not redundant with existing templates
   - Serves specific use cases

### Maintenance Responsibilities

As a template contributor, you're expected to:

1. **Respond to Issues**: Address bug reports and feature requests
2. **Update Documentation**: Keep README and examples current
3. **Compatibility**: Ensure compatibility with engine updates
4. **Security**: Address any security concerns promptly

## Conclusion

This guide provides comprehensive coverage of template development for the Resume AI Agent Template Engine. By following these guidelines, you can create professional, maintainable, and robust templates that provide value to users.

For additional support:
- Check the [GitHub Issues](https://github.com/taleye-com/resume-agent-template-engine/issues)
- Review existing templates for examples
- Consult the [Contributing Guidelines](CONTRIBUTING.md)
- Join the community discussions

Happy template development! 