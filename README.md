# Resume Agent Template Engine

A powerful template engine for generating professional resumes and cover letters using LaTeX.

[![CI/CD](https://github.com/yourusername/resume-agent-template-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/resume-agent-template-engine/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/yourusername/resume-agent-template-engine/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/resume-agent-template-engine)

## Features

- **Multiple Template Support**: Choose from a variety of professionally designed templates
- **Dynamic Content Generation**: Automatically generate content based on user input
- **LaTeX-based Templates**: High-quality, customizable templates
- **RESTful API**: Easy integration with other applications
- **Template Preview**: Preview templates before generating the final document
- **Cover Letter Support**: Generate matching cover letters for your resume
- **Customizable Sections**: Add, remove, or modify sections as needed

## Project Structure

```
resume-agent-template-engine/
├── src/
│   └── resume_agent_template_engine/
│       ├── core/
│       │   ├── resume_template_editing.py
│       │   └── template_utils.py
│       ├── templates/
│       │   ├── resume/
│       │   │   └── [template_name]/
│       │   │       ├── template.tex
│       │   │       ├── helper.py
│       │   │       ├── preview.png
│       │   │       └── README.md
│       │   └── cover_letter/
│       │       └── [template_name]/
│       │           ├── template.tex
│       │           ├── helper.py
│       │           ├── preview.png
│       │           └── README.md
│       ├── api/
│       │   └── routes.py
│       ├── examples/
│       │   └── example_usage.py
│       └── app.py
├── tests/
├── docs/
├── .github/
│   └── workflows/
│       └── ci.yml
├── requirements.txt
└── run.py
```

## System Requirements

- Python 3.8+
- LaTeX distribution (MiKTeX, TeX Live, or MacTeX)
- Required Python packages (see requirements.txt)

## Installation

### Quick Setup (Recommended for Developers)

1. Clone the repository:
   ```bash
   git clone https://github.com/taleye-com/resume-agent-template-engine
   cd resume-agent-template-engine
   ```

2. Run the development setup script:
   ```bash
   chmod +x setup-dev.sh
   ./setup-dev.sh
   ```

This script will:
- Create a virtual environment
- Install all dependencies
- Set up pre-commit hooks
- Format the code
- Run tests to ensure everything works

### Manual Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/taleye-com/resume-agent-template-engine
   cd resume-agent-template-engine
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

4. Install pre-commit hooks (for development):
   ```bash
   pre-commit install
   ```

5. Install LaTeX:
   - **Windows**: Install [MiKTeX](https://miktex.org/download)
   - **macOS**: Install [MacTeX](https://www.tug.org/mactex/)
   - **Linux**: Install TeX Live:
     ```bash
     sudo apt-get install texlive-full
     ```

## Usage

### Option 1: Streamlit UI (Recommended for Users)

Launch the user-friendly web interface:

```bash
# Install dependencies
pip install -r requirements.txt

# Launch the UI
python run_ui.py
```

Navigate to `http://localhost:8502` for an intuitive form-based interface to:
- Fill in your information using dynamic forms
- Select from available templates
- Generate and download professional PDFs
- Preview templates and understand data schemas

See [UI_README.md](UI_README.md) for detailed UI documentation.

### Option 2: API (For Developers and Integration)

1. Start the server:
   ```bash
   python run.py
   ```

2. Access the API:
   - Resume generation: `http://localhost:8501/generate-resume`
   - Cover letter generation: `http://localhost:8501/generate-cover-letter`
   - Template preview: `http://localhost:8501/preview-template`

3. Example API request:
   ```bash
   curl -X POST http://localhost:8501/generate-resume \
     -H "Content-Type: application/json" \
     -d '{
       "template": "modern",
       "data": {
         "professional_summary": "...",
         "education": [...],
         "experience": [...],
         "projects": [...],
         "articles_and_publications": [...],
         "achievements": [...],
         "certifications": [...],
         "technologies_and_skills": [...]
       }
     }'
   ```

## Template Format

Templates are organized in two main categories:
1. **Resume Templates**: Located in `templates/resume/`
2. **Cover Letter Templates**: Located in `templates/cover_letter/`

Each template directory contains:
- `template.tex`: The main LaTeX template file
- `helper.py`: Template-specific helper functions
- `preview.png`: Template preview image
- `README.md`: Template-specific documentation

## Data Format

The template engine expects data in the following format:

```json
{
  "template": "template_name",
  "data": {
    "professional_summary": "string",
    "education": [
      {
        "degree": "string",
        "institution": "string",
        "location": "string",
        "date": "string",
        "details": ["string"]
      }
    ],
    "experience": [
      {
        "title": "string",
        "company": "string",
        "location": "string",
        "date": "string",
        "details": ["string"]
      }
    ],
    "projects": [
      {
        "name": "string",
        "description": "string",
        "technologies": ["string"]
      }
    ],
    "articles_and_publications": [
      {
        "title": "string",
        "publisher": "string",
        "date": "string",
        "url": "string"
      }
    ],
    "achievements": ["string"],
    "certifications": [
      {
        "name": "string",
        "issuer": "string",
        "date": "string"
      }
    ],
    "technologies_and_skills": ["string"]
  }
}
```

## Development

### Code Quality and CI/CD

The project uses GitHub Actions for continuous integration and deployment. The workflow includes:

- **Linting**: Code formatting checks with Black and type checking with MyPy
- **Testing**: Comprehensive test suite with coverage reporting
- **Code Coverage**: Automated coverage reporting with Codecov

#### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

#### Running Tests

```bash
# Run all tests with coverage
cd src
PYTHONPATH=$PYTHONPATH:$(pwd) pytest ../tests/ --cov=resume_agent_template_engine --cov-report=term

# Run specific test types
pytest ../tests/unit/          # Unit tests only
pytest ../tests/integration/   # Integration tests only
pytest ../tests/e2e/          # End-to-end tests only
```

#### Code Formatting

```bash
# Format code
black src/ tests/

# Check formatting without making changes
black --check src/ tests/
```

### CI/CD Pipeline

The GitHub Actions workflow (`/.github/workflows/ci.yml`) runs:

1. **Lint Job**: Code formatting and type checking
2. **Test Job**: Comprehensive test suite with coverage reporting

### Troubleshooting CI Issues

If the CI is failing:

1. **Code Formatting Issues**: Run `black src/ tests/` locally and commit the changes
2. **Test Failures**: Run tests locally to identify and fix issues
3. **Codecov Rate Limiting**: This is temporary and doesn't affect the build status

To contribute, please follow the guidelines in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 