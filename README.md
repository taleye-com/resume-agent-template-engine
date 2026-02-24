# Resume Agent Template Engine

A powerful template engine for generating professional resumes and cover letters using LaTeX.

[![CI/CD](https://github.com/yourusername/resume-agent-template-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/resume-agent-template-engine/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/yourusername/resume-agent-template-engine/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/resume-agent-template-engine)

## Features

- **Multiple Template Support**: Choose from a variety of professionally designed templates
- **JSON & YAML Support**: Input data in either JSON or YAML format for flexibility
- **Dynamic Content Generation**: Automatically generate content based on user input
- **LaTeX-based Templates**: High-quality, customizable templates
- **RESTful API**: Easy integration with other applications
- **Template Preview**: Preview templates before generating the final document
- **Cover Letter Support**: Generate matching cover letters for your resume
- **Customizable Sections**: Add, remove, or modify sections as needed
- **CLI Tool**: Command-line interface for batch processing and automation
- **🚀 Redis Caching**: Blazing-fast document generation with intelligent caching (99% faster for duplicates)
- **⚡ Async/Parallel Processing**: Handle 3-5x more concurrent requests with async architecture
- **📊 Performance Metrics**: Real-time monitoring of cache performance and API statistics

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
├── pyproject.toml
├── uv.lock
└── run.py
```

## System Requirements

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) package manager
- LaTeX distribution (MiKTeX, TeX Live, or MacTeX)

## Installation

### Quick Setup (Recommended for Developers)

1. Install uv (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/taleye-com/resume-agent-template-engine
   cd resume-agent-template-engine
   ```

3. Run the development setup script:
   ```bash
   chmod +x setup-dev.sh
   ./setup-dev.sh
   ```

This script will:
- Sync all dependencies with uv
- Set up pre-commit hooks
- Format the code
- Run tests to ensure everything works

### Manual Setup

1. Install uv:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/taleye-com/resume-agent-template-engine
   cd resume-agent-template-engine
   ```

3. Sync dependencies with uv:
   ```bash
   uv sync
   ```

4. Install pre-commit hooks (for development):
   ```bash
   uv run pre-commit install
   ```

5. Install LaTeX:
   - **Windows**: Install [MiKTeX](https://miktex.org/download)
   - **macOS**: Install [MacTeX](https://www.tug.org/mactex/)
   - **Linux**: Install TeX Live:
     ```bash
     sudo apt-get install texlive-full
     ```

### Optional: Redis Cache Setup (for improved performance)

The template engine includes Redis-based caching for significant performance improvements:

1. **Install Redis** (if not already installed):
   - **macOS**:
     ```bash
     brew install redis
     brew services start redis
     ```
   - **Linux**:
     ```bash
     sudo apt-get install redis-server
     sudo systemctl start redis
     ```
   - **Windows**: Use [Redis for Windows](https://github.com/microsoftarchive/redis/releases) or WSL

2. **Configure caching** (optional - caching is enabled by default):
   ```bash
   # Copy the example environment file
   cp .env.example .env

   # Edit .env to customize cache settings
   # Default settings work for local development
   ```

3. **Cache configuration options** (in `.env`):
   - `CACHE_ENABLED=true` - Enable/disable caching
   - `REDIS_HOST=localhost` - Redis server host
   - `REDIS_PORT=6379` - Redis server port
   - `PDF_CACHE_TTL=86400` - Cache PDFs for 24 hours (in seconds)
   - `LATEX_CACHE_TTL=43200` - Cache LaTeX content for 12 hours

**Performance Benefits:**
- **~99% faster** for duplicate requests (cached PDFs served in 5-10ms vs 800ms)
- **3-5x throughput** increase for concurrent requests
- **Automatic cache invalidation** after TTL expiration

**Note:** The engine works without Redis, but caching significantly improves performance for production use.

## Usage

### Option 1: Docker (Recommended for Production) 🐳

**Get running in 2 minutes with full stack:**

```bash
# Start everything (API + Redis + Celery + NGINX)
docker-compose up -d

# Access
open http://localhost/docs      # API Documentation
open http://localhost:5555       # Celery Dashboard
```

**What you get:**
- ✅ Handles 10,000+ concurrent users
- ✅ Redis caching (99% faster)
- ✅ Background job queue (Celery)
- ✅ Load balancer (NGINX)
- ✅ Auto-restart & health checks
- ✅ Complete monitoring

See **[DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md)** for details.

---

### Option 2: Streamlit UI (Recommended for Users)

Launch the user-friendly web interface:

```bash
# Launch the UI
uv run python run.py --ui
```

Navigate to `http://localhost:8502` for an intuitive form-based interface to:
- Fill in your information using dynamic forms
- Input data in JSON or YAML format with syntax highlighting
- Select from available templates
- Generate and download professional PDFs or DOCX files (requires pandoc for DOCX)
- Preview templates and understand data schemas

See [UI_README.md](UI_README.md) for detailed UI documentation.

### Option 2: Command Line Interface (For Automation)

The CLI supports both JSON and YAML input formats:

```bash
# Generate sample data files
uv run python -m resume_agent_template_engine.cli sample resume data.json
uv run python -m resume_agent_template_engine.cli sample resume data.yaml

# Generate PDF from JSON
uv run python -m resume_agent_template_engine.cli generate resume classic data.json output.pdf

# Generate PDF from YAML
uv run python -m resume_agent_template_engine.cli generate resume classic data.yaml output.pdf

# Generate DOCX (Word) from YAML (requires pandoc)
uv run python -m resume_agent_template_engine.cli generate resume classic data.yaml output.docx --format docx

# List available templates
uv run python -m resume_agent_template_engine.cli list

# Get template information
uv run python -m resume_agent_template_engine.cli info resume classic
```

### Option 3: API (For Developers and Integration)

1. Start the server:
   ```bash
   uv run python run.py --api
   ```

2. Access the API:
   - Resume generation (JSON): `http://localhost:8501/generate`
   - Resume generation (YAML): `http://localhost:8501/generate-yaml`
   - Cover letter generation: `http://localhost:8501/generate`
   - Template preview: `http://localhost:8501/templates`
   - Schema information: `http://localhost:8501/schema/{document_type}`
   - **Cache metrics**: `http://localhost:8501/metrics` - Monitor cache performance
   - **Health check**: `http://localhost:8501/health` - API status

3. **Monitor cache performance**:
   ```bash
   # Get cache statistics
   curl http://localhost:8501/metrics
   ```

   Response includes:
   - Cache hit/miss counts
   - Hit rate percentage
   - Number of cached documents
   - Cache connectivity status

4. Example API requests:

   **JSON Format:**
   ```bash
   curl -X POST http://localhost:8501/generate \
     -H "Content-Type: application/json" \
     -d '{
       "document_type": "resume",
       "template": "classic",
       "data": {
         "personalInfo": {
           "name": "John Doe",
           "email": "john@example.com"
         },
         "professionalSummary": "...",
         "education": [...],
         "experience": [...],
         "projects": [...],
         "articlesAndPublications": [...],
         "achievements": [...],
         "certifications": [...],
         "technologiesAndSkills": [...]
       }
     }'
   ```

   **YAML Format:**
   ```bash
   curl -X POST http://localhost:8501/generate-yaml \
     -H "Content-Type: application/json" \
     -d '{
       "document_type": "resume",
       "template": "classic",
       "yaml_data": "personalInfo:\n  name: John Doe\n  email: john@example.com\nprofessionalSummary: ..."
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

The template engine accepts data in both JSON and YAML formats:

### JSON Format

```json
{
  "personalInfo": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1 (555) 123-4567",
    "location": "New York, NY",
    "website": "https://johndoe.dev",
    "linkedin": "https://linkedin.com/in/johndoe",
    "website_display": "https://johndoe.dev",
    "linkedin_display": "https://linkedin.com/in/johndoe"
  },
  "professionalSummary": "Experienced software engineer...",
  "education": [
    {
      "degree": "Bachelor of Science in Computer Science",
      "institution": "University of Technology",
      "startDate": "2015-09",
      "endDate": "2019-05"
    }
  ],
  "experience": [
    {
      "title": "Senior Software Engineer",
      "company": "Tech Corp",
      "startDate": "2020-01",
      "endDate": "Present",
      "achievements": [
        "Reduced system latency by 40%",
        "Led team of 5 engineers"
      ]
    }
  ],
  "projects": [
    {
      "name": "Cloud Platform",
      "description": ["Scalable microservices platform"],
      "tools": ["Python", "Docker", "Kubernetes"]
    }
  ],
  "articlesAndPublications": [
    {
      "title": "Microservices Best Practices",
      "date": "2023-03"
    }
  ],
  "achievements": [
    "AWS Certified Solutions Architect",
    "Led migration to cloud-native architecture"
  ],
  "certifications": [
    "AWS Certified Solutions Architect - Professional (2023)"
  ],
  "technologiesAndSkills": [
    {
      "category": "Programming Languages",
      "skills": ["Python", "JavaScript", "TypeScript"]
    }
  ]
}
```

### YAML Format

```yaml
personalInfo:
  name: John Doe
  email: john@example.com
  phone: "+1 (555) 123-4567"
  location: New York, NY
  website: https://johndoe.dev
  linkedin: https://linkedin.com/in/johndoe
  website_display: https://johndoe.dev
  linkedin_display: https://linkedin.com/in/johndoe

professionalSummary: "Experienced software engineer..."

education:
  - degree: Bachelor of Science in Computer Science
    institution: University of Technology
    startDate: "2015-09"
    endDate: "2019-05"

experience:
  - title: Senior Software Engineer
    company: Tech Corp
    startDate: "2020-01"
    endDate: Present
    achievements:
      - Reduced system latency by 40%
      - Led team of 5 engineers

projects:
  - name: Cloud Platform
    description:
      - Scalable microservices platform
    tools:
      - Python
      - Docker
      - Kubernetes

articlesAndPublications:
  - title: Microservices Best Practices
    date: "2023-03"

achievements:
  - AWS Certified Solutions Architect
  - Led migration to cloud-native architecture

certifications:
  - "AWS Certified Solutions Architect - Professional (2023)"

technologiesAndSkills:
  - category: Programming Languages
    skills:
      - Python
      - JavaScript
      - TypeScript
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
uv run pre-commit install

# Run hooks manually
uv run pre-commit run --all-files
```

#### Running Tests

```bash
# Run all tests with coverage
cd src
PYTHONPATH=$PYTHONPATH:$(pwd) uv run pytest ../tests/ --cov=resume_agent_template_engine --cov-report=term

# Run specific test types
uv run pytest ../tests/unit/          # Unit tests only
uv run pytest ../tests/integration/   # Integration tests only
uv run pytest ../tests/e2e/          # End-to-end tests only
```

#### Code Formatting

```bash
# Format code
uv run black src/ tests/

# Check formatting without making changes
uv run black --check src/ tests/
```

### CI/CD Pipeline

The GitHub Actions workflow (`/.github/workflows/ci.yml`) runs:

1. **Lint Job**: Code formatting and type checking
2. **Test Job**: Comprehensive test suite with coverage reporting

### Troubleshooting CI Issues

If the CI is failing:

1. **Code Formatting Issues**: Run `uv run black src/ tests/` locally and commit the changes
2. **Test Failures**: Run tests locally to identify and fix issues
3. **Codecov Rate Limiting**: This is temporary and doesn't affect the build status

To contribute, please follow the guidelines in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 
