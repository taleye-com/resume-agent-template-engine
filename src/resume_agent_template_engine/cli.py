#!/usr/bin/env python3
"""
Resume Agent Template Engine CLI

A command-line interface for generating professional resumes and cover letters
using configurable templates.
"""

import argparse
import json
import logging
import sys
from typing import Any

import yaml

from resume_agent_template_engine.core.template_engine import (
    OutputFormat,
    TemplateEngine,
)


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def load_data_file(file_path: str) -> dict[str, Any]:
    """Load data from JSON or YAML file"""
    try:
        with open(file_path, encoding="utf-8") as f:
            # Determine file format based on extension
            if file_path.lower().endswith((".yaml", ".yml")):
                return yaml.safe_load(f)
            else:
                # Default to JSON for backwards compatibility
                return json.load(f)
    except FileNotFoundError:
        print(f"Error: Data file not found: {file_path}")
        sys.exit(1)
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        file_format = (
            "YAML" if file_path.lower().endswith((".yaml", ".yml")) else "JSON"
        )
        print(f"Error: Invalid {file_format} in {file_path}: {e}")
        sys.exit(1)


def create_sample_data(document_type: str, output_path: str):
    """Create a sample data file for the specified document type"""
    sample_data = {}

    if document_type == "resume":
        sample_data = {
            "personalInfo": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1 (555) 123-4567",
                "location": "New York, NY",
                "website": "https://johndoe.dev",
                "linkedin": "https://linkedin.com/in/johndoe",
                "website_display": "https://johndoe.dev",
                "linkedin_display": "https://linkedin.com/in/johndoe",
            },
            "professionalSummary": "Experienced software engineer with 5+ years of expertise in full-stack development, cloud architecture, and team leadership.",
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "University of Technology",
                    "startDate": "2015-09",
                    "endDate": "2019-05",
                    "focus": "Software Engineering and Algorithms",
                    "notableCourseWorks": [
                        "Data Structures",
                        "Algorithms",
                        "Software Engineering",
                        "Database Systems",
                    ],
                    "projects": [
                        "Distributed Chat Application",
                        "E-commerce Web Platform",
                    ],
                }
            ],
            "experience": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Corp",
                    "startDate": "2020-01",
                    "endDate": "Present",
                    "achievements": [
                        "Reduced system latency by 40% through optimization",
                        "Led team of 5 engineers in agile development practices",
                        "Implemented microservices architecture serving 1M+ users",
                    ],
                }
            ],
            "projects": [
                {
                    "name": "Cloud Native Application Platform",
                    "description": [
                        "Scalable microservices platform",
                        "Real-time data processing",
                    ],
                    "tools": ["Python", "Docker", "Kubernetes", "AWS"],
                    "achievements": [
                        "Processed 1TB+ daily data with 99.9% uptime",
                        "Reduced deployment time by 70%",
                    ],
                }
            ],
            "articlesAndPublications": [
                {
                    "title": "Microservices Architecture Best Practices",
                    "date": "2023-03",
                },
                {"title": "Scaling Applications with Kubernetes", "date": "2022-11"},
            ],
            "achievements": [
                "AWS Certified Solutions Architect",
                "Led migration of legacy system to cloud-native architecture",
                "Mentored 10+ junior developers",
            ],
            "certifications": [
                "AWS Certified Solutions Architect - Professional (2023)",
                "Certified Kubernetes Application Developer (2022)",
                "Google Cloud Professional Cloud Architect (2021)",
            ],
            "technologiesAndSkills": [
                {
                    "category": "Programming Languages",
                    "skills": ["Python", "JavaScript", "TypeScript", "Go", "Java"],
                },
                {
                    "category": "Frameworks & Libraries",
                    "skills": ["React", "Node.js", "Django", "Flask", "Express.js"],
                },
                {
                    "category": "Cloud & DevOps",
                    "skills": ["AWS", "Docker", "Kubernetes", "Terraform", "Jenkins"],
                },
                {
                    "category": "Databases",
                    "skills": ["PostgreSQL", "MongoDB", "Redis", "DynamoDB"],
                },
            ],
        }

    elif document_type == "cover_letter":
        sample_data = {
            "personalInfo": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1 (555) 123-4567",
                "location": "New York, NY",
                "website": "https://johndoe.dev",
                "website_display": "johndoe.dev",
            },
            "recipient": {
                "name": "Jane Smith",
                "title": "Hiring Manager",
                "company": "Innovative Tech Solutions",
                "address": ["123 Business Ave", "New York, NY 10001"],
            },
            "date": "March 15, 2024",
            "salutation": "Dear Ms. Smith,",
            "body": [
                "I am writing to express my strong interest in the Senior Software Engineer position at Innovative Tech Solutions. With over 5 years of experience in full-stack development and a proven track record of delivering scalable solutions, I am excited about the opportunity to contribute to your team's success.",
                "In my current role at Tech Corp, I have led the development of cloud-native applications serving over 1 million users, where I reduced system latency by 40% through strategic optimization and architectural improvements. My experience in leading agile development teams and implementing best practices aligns perfectly with your requirements for this position.",
                "I am particularly drawn to Innovative Tech Solutions' commitment to cutting-edge technology and innovation. I would welcome the opportunity to discuss how my skills in Python, cloud architecture, and team leadership can contribute to your upcoming projects.",
            ],
            "closing": "Sincerely,\nJohn Doe",
        }

    try:
        # Determine output format based on extension
        if output_path.lower().endswith((".yaml", ".yml")):
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(sample_data, f, default_flow_style=False, indent=2)
            print(f"Sample {document_type} YAML data created: {output_path}")
        else:
            # Default to JSON for backwards compatibility
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(sample_data, f, indent=2)
            print(f"Sample {document_type} JSON data created: {output_path}")
    except Exception as e:
        print(f"Error creating sample data: {e}")
        sys.exit(1)


def list_templates(engine: TemplateEngine, document_type: str = None):
    """List available templates"""
    templates = engine.get_available_templates(document_type)

    if document_type:
        print(f"\nAvailable {document_type} templates:")
        for template in templates:
            print(f"  - {template}")
    else:
        print("\nAvailable templates:")
        for doc_type, template_list in templates.items():
            print(f"\n{doc_type}:")
            for template in template_list:
                print(f"  - {template}")


def show_template_info(engine: TemplateEngine, document_type: str, template_name: str):
    """Show detailed information about a template"""
    try:
        info = engine.get_template_info(document_type, template_name)
        print("\nTemplate Information:")
        print(f"  Name: {info['name']}")
        print(f"  Document Type: {info['document_type']}")
        print(f"  Description: {info['description']}")
        print(f"  Class: {info['class_name']}")
        print(f"  Required Fields: {', '.join(info['required_fields'])}")
        if info["preview_path"]:
            print(f"  Preview: {info['preview_path']}")
    except Exception as e:
        print(f"Error getting template info: {e}")
        sys.exit(1)


def generate_document(
    engine: TemplateEngine,
    document_type: str,
    template_name: str,
    data_file: str,
    output_path: str,
    output_format: str,
):
    """Generate a document using the template engine"""

    # Load data
    data = load_data_file(data_file)

    # Validate template
    if not engine.validate_template(document_type, template_name):
        print(
            f"Error: Template '{template_name}' not found for document type '{document_type}'"
        )
        available = engine.get_available_templates(document_type)
        print(f"Available templates: {', '.join(available)}")
        sys.exit(1)

    try:
        if output_format.lower() == "pdf":
            # Generate PDF
            result_path = engine.export_to_pdf(
                document_type, template_name, data, output_path
            )
            print(f"PDF generated successfully: {result_path}")

        elif output_format.lower() == "latex":
            # Generate LaTeX content
            content = engine.render_document(
                document_type, template_name, data, OutputFormat.LATEX
            )
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"LaTeX content generated: {output_path}")

        else:
            print(f"Error: Unsupported output format: {output_format}")
            sys.exit(1)

    except Exception as e:
        print(f"Error generating document: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Resume Agent Template Engine CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available templates
  python -m resume_agent_template_engine.cli list

  # List templates for a specific document type
  python -m resume_agent_template_engine.cli list --type resume

  # Show information about a template
  python -m resume_agent_template_engine.cli info resume classic

  # Generate sample data files (JSON and YAML supported)
  python -m resume_agent_template_engine.cli sample resume resume_data.json
  python -m resume_agent_template_engine.cli sample resume resume_data.yaml

  # Generate a PDF resume (supports both JSON and YAML input)
  python -m resume_agent_template_engine.cli generate resume classic resume_data.json resume.pdf
  python -m resume_agent_template_engine.cli generate resume classic resume_data.yaml resume.pdf

  # Generate LaTeX source
  python -m resume_agent_template_engine.cli generate cover_letter classic cover_letter_data.yaml cover_letter.tex --format latex
        """,
    )

    parser.add_argument("--config", "-c", help="Path to YAML configuration file")
    parser.add_argument("--templates-path", "-t", help="Path to templates directory")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List available templates")
    list_parser.add_argument(
        "--type", choices=["resume", "cover_letter"], help="Filter by document type"
    )

    # Info command
    info_parser = subparsers.add_parser("info", help="Show template information")
    info_parser.add_argument(
        "document_type", choices=["resume", "cover_letter"], help="Document type"
    )
    info_parser.add_argument("template_name", help="Template name")

    # Sample command
    sample_parser = subparsers.add_parser("sample", help="Create sample data file")
    sample_parser.add_argument(
        "document_type", choices=["resume", "cover_letter"], help="Document type"
    )
    sample_parser.add_argument("output_path", help="Output file path")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate document")
    generate_parser.add_argument(
        "document_type", choices=["resume", "cover_letter"], help="Document type"
    )
    generate_parser.add_argument("template_name", help="Template name")
    generate_parser.add_argument("data_file", help="JSON or YAML data file")
    generate_parser.add_argument("output_path", help="Output file path")
    generate_parser.add_argument(
        "--format",
        "-f",
        choices=["pdf", "latex"],
        default="pdf",
        help="Output format (default: pdf)",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level)

    # Handle case where no command is provided
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Handle sample command (doesn't need template engine)
    if args.command == "sample":
        create_sample_data(args.document_type, args.output_path)
        return

    # Initialize template engine
    try:
        engine = TemplateEngine(
            config_path=args.config, templates_path=args.templates_path
        )
    except Exception as e:
        print(f"Error initializing template engine: {e}")
        sys.exit(1)

    # Execute commands
    if args.command == "list":
        list_templates(engine, args.type)

    elif args.command == "info":
        show_template_info(engine, args.document_type, args.template_name)

    elif args.command == "generate":
        generate_document(
            engine,
            args.document_type,
            args.template_name,
            args.data_file,
            args.output_path,
            args.format,
        )


if __name__ == "__main__":
    main()
