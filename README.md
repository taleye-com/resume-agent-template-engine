# Resume AI Agent - Template Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)

Part of the Resume AI Agent project by [Fenil Sonani](https://fenilsonani.com). This component handles the generation of professional resumes using customizable templates and JSON data.

## About Resume AI Agent Template Engine

The Template Engine is a crucial component of the Resume AI Agent ecosystem, designed to transform structured resume data into beautifully formatted documents. It provides a flexible templating system that supports multiple output formats and styling options.

### Project Components

The Resume AI Agent project consists of several integrated components:

- **Template Engine** (this repository) - Converts structured resume data into formatted documents
- **Resume AI** - Intelligent resume analysis and optimization
- **Data Manager** - Handles resume data storage and validation
- **Web Interface** - User-friendly web application for resume management

Visit [fenilsonani.com](https://fenilsonani.com) to learn more about the complete Resume AI Agent project.

## Features

- Convert structured resume data into formatted documents
- Multiple template options with customizable styles
- Support for various output formats (PDF, HTML, etc.)
- Easy-to-use template creation system
- Real-time preview capabilities
- Extensible template architecture
- Built-in validation and error handling

## Prerequisites

### System Requirements

- Python 3.8 or higher
- pip package manager
- LaTeX distribution (for PDF output)

### Installing LaTeX

For PDF output support, a LaTeX distribution is required. Here's how to install it on different platforms:

#### macOS

1. Install MacTeX (recommended):
   ```bash
   # Using Homebrew
   brew install --cask mactex
   
   # OR download and install manually from:
   # https://www.tug.org/mactex/
   ```

2. After installation, verify LaTeX is installed:
   ```bash
   pdflatex --version
   ```

3. Install additional packages (if needed):
   ```bash
   sudo tlmgr update --self
   sudo tlmgr install collection-fontsrecommended
   ```

#### Windows

1. Install MiKTeX:
   - Download the installer from [MiKTeX website](https://miktex.org/download)
   - Run the installer and follow the installation wizard
   - Choose "Install missing packages on the fly" when prompted

2. After installation:
   - Open MiKTeX Console
   - Go to Updates and install any available updates
   - Verify installation by opening Command Prompt and typing:
     ```cmd
     pdflatex --version
     ```

#### Linux (Ubuntu/Debian)

1. Install TeX Live (full installation recommended):
   ```bash
   sudo apt update
   sudo apt install texlive-full
   sudo apt install texlive-latex-extra
   ```

2. Install additional tools:
   ```bash
   sudo apt install latexmk
   ```

3. Verify installation:
   ```bash
   pdflatex --version
   ```

#### Linux (Fedora)

1. Install TeX Live:
   ```bash
   sudo dnf install texlive-scheme-full
   sudo dnf install latexmk
   ```

2. Verify installation:
   ```bash
   pdflatex --version
   ```

#### Linux (Arch)

1. Install TeX Live:
   ```bash
   sudo pacman -S texlive-most texlive-lang
   sudo pacman -S latexmk
   ```

2. Verify installation:
   ```bash
   pdflatex --version
   ```

### Troubleshooting LaTeX Installation

1. If you encounter missing package errors:
   - On MacTeX/TeX Live:
     ```bash
     sudo tlmgr install [package-name]
     ```
   - On MiKTeX: The package will be installed automatically when needed

2. Common issues:
   - **Path not found**: Add LaTeX binaries to your system PATH
   - **Permission errors**: Run package manager with sudo/admin privileges
   - **Missing fonts**: Install `collection-fontsrecommended`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/resume-agent-template-engine.git
cd resume-agent-template-engine
```

2. Create and activate a virtual environment (optional but recommended):
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the template engine service:
```bash
python main.py
```

2. The service will be available at http://localhost:8501

3. To generate a resume:
   - Submit your resume data in JSON format
   - Select a template
   - Choose output format
   - Generate and download the formatted resume

## Template Format

Templates are written in a combination of LaTeX and HTML, with special placeholders for dynamic content. Here's the basic structure:

```
template/
├── basic/
│   ├── template.tex
│   ├── style.sty
│   └── preview.png
├── modern/
│   ├── template.html
│   ├── style.css
│   └── preview.png
└── ...
```

## Data Format

The template engine accepts resume data in the following JSON format:

```json
{
  "personalInfo": {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1 (123) 456-7890",
    "location": "San Francisco, CA",
    "links": [
      {
        "title": "LinkedIn",
        "url": "https://linkedin.com/in/johndoe"
      },
      {
        "title": "GitHub",
        "url": "https://github.com/johndoe"
      }
    ]
  },
  "professionalSummary": "Your professional summary text here...",
  "education": [
    {
      "degree": "Bachelor of Science",
      "institution": "Example University",
      "startDate": "Sep 2018",
      "endDate": "May 2022",
      "focus": "Computer Science"
    }
  ],
  "experience": [
    {
      "title": "Software Engineer",
      "company": "Example Company",
      "startDate": "Jun 2022",
      "endDate": "Present",
      "achievements": [
        "Achievement 1",
        "Achievement 2"
      ]
    }
  ],
  "skills": [
    {
      "category": "Programming Languages",
      "skills": ["Python", "JavaScript", "TypeScript"]
    }
  ]
}
```

## Creating New Templates

1. Create a new directory in the `templates` folder with your template name
2. Add the required files:
   * `template.tex` or `template.html` - Main template file
   * `style.sty` or `style.css` - Styling definitions
   * `preview.png` - Template preview image
3. Define placeholders using the standard format:
   * `{{personal_info}}` - For personal details
   * `{{professional_summary}}`
   * `{{education}}`
   * `{{experience}}`
   * `{{skills}}`
4. Add template metadata in `template.json`
5. Update the template registry
6. Add tests for the new template

## API Integration

The template engine can be integrated with other services via its REST API:

```python
import requests

response = requests.post('http://localhost:8501/generate', 
    json={
        'template': 'modern',
        'format': 'pdf',
        'data': your_resume_data
    }
)
```

## Contributing

We welcome contributions! Please feel free to submit a Pull Request. Make sure to read the [Contribution Guidelines](CONTRIBUTING.md) first.

## Security

For security concerns, please review our [Security Policy](SECURITY.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Code of Conduct

This project adheres to the Contributor Covenant Code of Conduct. By participating, you are expected to uphold this code. Please see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details. 