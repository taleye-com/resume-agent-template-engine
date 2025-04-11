# Contributing to Resume Generator

First off, thank you for considering contributing to Resume Generator! It's people like you that make Resume Generator such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by the [Resume Generator Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include screenshots if possible
* Include your environment details (OS, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* Use a clear and descriptive title
* Provide a step-by-step description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and explain which behavior you expected to see instead
* Explain why this enhancement would be useful
* List some other applications where this enhancement exists, if applicable

### Pull Requests

* Fill in the required template
* Do not include issue numbers in the PR title
* Include screenshots and animated GIFs in your pull request whenever possible
* Follow the Python styleguides
* Include thoughtfully-worded, well-structured tests
* Document new code
* End all files with a newline

## Styleguides

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

### Python Styleguide

* Follow PEP 8
* Use 4 spaces for indentation
* Use docstrings for all public classes and methods
* Keep lines under 80 characters
* Use meaningful variable names

### Documentation Styleguide

* Use Markdown
* Reference functions and classes in backticks: \`MyClass\`
* Use code blocks for examples
* Include examples for new features

## Adding New Templates

1. Create a new template directory in the appropriate category:
   - For resumes: `templates/resume/[template_name]/`
   - For cover letters: `templates/cover_letter/[template_name]/`

2. Each template directory should contain:
   - `template.tex` - The main template file
   - `helper.py` - Template-specific helper functions
   - `preview.png` - Template preview image
   - `README.md` - Template-specific documentation

3. Follow the template structure as shown in existing templates
4. Include all required placeholders:
   * `{{professional_summary}}`
   * `{{education}}`
   * `{{experience}}`
   * `{{projects}}`
   * `{{articles_and_publications}}`
   * `{{achievements}}`
   * `{{certifications}}`
   * `{{technologies_and_skills}}`
5. Update documentation if needed
6. Add tests for the new template

## Development Process

1. Fork the repo
2. Create a new branch for your feature
3. Make your changes
4. Write or update tests
5. Run the test suite:
   ```bash
   python -m pytest
   ```
6. Format your code:
   ```bash
   black .
   mypy src/
   ```
7. Ensure all tests pass in the CI pipeline
8. Push your changes
9. Create a Pull Request

## CI/CD Requirements

All pull requests must pass the following checks:

- Tests must pass on Python 3.9, 3.10, and 3.11
- Code coverage must not decrease
- Code must pass black formatting
- Code must pass mypy type checking
- Package must build successfully

## Setting Up Development Environment

1. Fork and clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install LaTeX if not already installed (see README.md for detailed instructions)
5. Run the development server:
   ```bash
   python run.py
   ```

## Questions?

Feel free to create an issue with the "question" label if you need help.
