"""Unit tests for the CLI module."""

import pytest
import sys
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
from io import StringIO
import argparse

from resume_agent_template_engine.cli import (
    main,
    setup_logging,
    load_data_file,
    create_sample_data,
    list_templates,
    show_template_info,
    generate_document,
)
from resume_agent_template_engine.core.template_engine import (
    TemplateEngine,
    OutputFormat,
)


class TestCLIFunctions:
    """Test CLI utility functions"""

    def test_setup_logging_default(self):
        """Test setup_logging with default level"""
        with patch("logging.basicConfig") as mock_config:
            setup_logging()
            mock_config.assert_called_once()
            args, kwargs = mock_config.call_args
            assert kwargs["level"] == 20  # INFO level

    def test_setup_logging_debug(self):
        """Test setup_logging with debug level"""
        with patch("logging.basicConfig") as mock_config:
            setup_logging("DEBUG")
            mock_config.assert_called_once()
            args, kwargs = mock_config.call_args
            assert kwargs["level"] == 10  # DEBUG level

    def test_load_data_file_success(self, tmp_path):
        """Test successful data file loading"""
        data_file = tmp_path / "test_data.json"
        test_data = {"name": "John Doe", "email": "john@example.com"}
        data_file.write_text('{"name": "John Doe", "email": "john@example.com"}')

        result = load_data_file(str(data_file))
        assert result == test_data

    def test_load_data_file_not_found(self):
        """Test data file loading with non-existent file"""
        with pytest.raises(SystemExit):
            load_data_file("nonexistent.json")

    def test_load_data_file_invalid_json(self, tmp_path):
        """Test data file loading with invalid JSON"""
        data_file = tmp_path / "invalid.json"
        data_file.write_text('{"invalid": json}')

        with pytest.raises(SystemExit):
            load_data_file(str(data_file))

    def test_create_sample_data_resume(self, tmp_path):
        """Test creating sample resume data"""
        output_file = tmp_path / "sample_resume.json"

        with patch("builtins.print"):
            create_sample_data("resume", str(output_file))

        assert output_file.exists()
        import json

        data = json.loads(output_file.read_text())
        assert "personalInfo" in data
        assert "experience" in data
        assert "education" in data

    def test_create_sample_data_cover_letter(self, tmp_path):
        """Test creating sample cover letter data"""
        output_file = tmp_path / "sample_cover_letter.json"

        with patch("builtins.print"):
            create_sample_data("cover_letter", str(output_file))

        assert output_file.exists()
        import json

        data = json.loads(output_file.read_text())
        assert "personalInfo" in data
        assert "recipient" in data
        assert "body" in data

    def test_list_templates_all(self):
        """Test listing all templates"""
        mock_engine = Mock()
        mock_engine.get_available_templates.return_value = {
            "resume": ["classic", "modern"],
            "cover_letter": ["formal", "creative"],
        }

        with patch("builtins.print") as mock_print:
            list_templates(mock_engine)

        mock_engine.get_available_templates.assert_called_once_with(None)
        assert mock_print.call_count >= 1

    def test_list_templates_by_type(self):
        """Test listing templates by document type"""
        mock_engine = Mock()
        mock_engine.get_available_templates.return_value = ["classic", "modern"]

        with patch("builtins.print") as mock_print:
            list_templates(mock_engine, "resume")

        mock_engine.get_available_templates.assert_called_once_with("resume")
        assert mock_print.call_count >= 1

    def test_show_template_info_success(self):
        """Test showing template information successfully"""
        mock_engine = Mock()
        mock_info = {
            "name": "classic",
            "document_type": "resume",
            "description": "Classic resume template",
            "class_name": "ClassicResumeTemplate",
            "required_fields": ["personalInfo", "experience"],
            "preview_path": "/path/to/preview.png",
        }
        mock_engine.get_template_info.return_value = mock_info

        with patch("builtins.print") as mock_print:
            show_template_info(mock_engine, "resume", "classic")

        mock_engine.get_template_info.assert_called_once_with("resume", "classic")
        assert mock_print.call_count >= 1

    def test_show_template_info_error(self):
        """Test showing template information with error"""
        mock_engine = Mock()
        mock_engine.get_template_info.side_effect = ValueError("Template not found")

        with pytest.raises(SystemExit):
            show_template_info(mock_engine, "resume", "nonexistent")

    @patch("resume_agent_template_engine.cli.load_data_file")
    def test_generate_document_pdf_success(self, mock_load_data):
        """Test successful PDF document generation"""
        mock_engine = Mock()
        mock_engine.validate_template.return_value = True
        mock_engine.export_to_pdf.return_value = "/path/to/output.pdf"

        mock_load_data.return_value = {"personalInfo": {"name": "John Doe"}}

        with patch("builtins.print") as mock_print:
            generate_document(
                mock_engine, "resume", "classic", "data.json", "output.pdf", "pdf"
            )

        mock_engine.validate_template.assert_called_once_with("resume", "classic")
        mock_engine.export_to_pdf.assert_called_once()
        assert mock_print.call_count >= 1

    @patch("resume_agent_template_engine.cli.load_data_file")
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_document_latex_success(self, mock_file, mock_load_data):
        """Test successful LaTeX document generation"""
        mock_engine = Mock()
        mock_engine.validate_template.return_value = True
        mock_engine.render_document.return_value = "\\documentclass{article}..."

        mock_load_data.return_value = {"personalInfo": {"name": "John Doe"}}

        with patch("builtins.print") as mock_print:
            generate_document(
                mock_engine, "resume", "classic", "data.json", "output.tex", "latex"
            )

        mock_engine.validate_template.assert_called_once_with("resume", "classic")
        mock_engine.render_document.assert_called_once_with(
            "resume", "classic", mock_load_data.return_value, OutputFormat.LATEX
        )
        mock_file.assert_called_once_with("output.tex", "w", encoding="utf-8")

    @patch("resume_agent_template_engine.cli.load_data_file")
    def test_generate_document_invalid_template(self, mock_load_data):
        """Test document generation with invalid template"""
        mock_engine = Mock()
        mock_engine.validate_template.return_value = False
        mock_engine.get_available_templates.return_value = ["classic", "modern"]

        mock_load_data.return_value = {"personalInfo": {"name": "John Doe"}}

        with pytest.raises(SystemExit):
            generate_document(
                mock_engine, "resume", "nonexistent", "data.json", "output.pdf", "pdf"
            )

    @patch("resume_agent_template_engine.cli.load_data_file")
    def test_generate_document_unsupported_format(self, mock_load_data):
        """Test document generation with unsupported format"""
        mock_engine = Mock()
        mock_engine.validate_template.return_value = True

        mock_load_data.return_value = {"personalInfo": {"name": "John Doe"}}

        with pytest.raises(SystemExit):
            generate_document(
                mock_engine, "resume", "classic", "data.json", "output.html", "html"
            )

    @patch("resume_agent_template_engine.cli.load_data_file")
    def test_generate_document_generation_error(self, mock_load_data):
        """Test document generation with generation error"""
        mock_engine = Mock()
        mock_engine.validate_template.return_value = True
        mock_engine.export_to_pdf.side_effect = Exception("Generation failed")

        mock_load_data.return_value = {"personalInfo": {"name": "John Doe"}}

        with pytest.raises(SystemExit):
            generate_document(
                mock_engine, "resume", "classic", "data.json", "output.pdf", "pdf"
            )


class TestCLIMain:
    """Test CLI main function and argument parsing"""

    @patch("sys.argv", ["cli.py"])
    def test_main_no_command(self):
        """Test main function with no command provided"""
        with patch("argparse.ArgumentParser.print_help") as mock_help:
            with pytest.raises(SystemExit):
                main()
            mock_help.assert_called_once()

    @patch("sys.argv", ["cli.py", "sample", "resume", "output.json"])
    @patch("resume_agent_template_engine.cli.create_sample_data")
    def test_main_sample_command(self, mock_create_sample):
        """Test main function with sample command"""
        main()
        mock_create_sample.assert_called_once_with("resume", "output.json")

    @patch("sys.argv", ["cli.py", "list"])
    @patch("resume_agent_template_engine.cli.TemplateEngine")
    @patch("resume_agent_template_engine.cli.list_templates")
    def test_main_list_command(self, mock_list_templates, mock_engine_class):
        """Test main function with list command"""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        main()

        mock_engine_class.assert_called_once()
        mock_list_templates.assert_called_once_with(mock_engine, None)

    @patch("sys.argv", ["cli.py", "list", "--type", "resume"])
    @patch("resume_agent_template_engine.cli.TemplateEngine")
    @patch("resume_agent_template_engine.cli.list_templates")
    def test_main_list_command_with_type(self, mock_list_templates, mock_engine_class):
        """Test main function with list command and type filter"""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        main()

        mock_engine_class.assert_called_once()
        mock_list_templates.assert_called_once_with(mock_engine, "resume")

    @patch("sys.argv", ["cli.py", "info", "resume", "classic"])
    @patch("resume_agent_template_engine.cli.TemplateEngine")
    @patch("resume_agent_template_engine.cli.show_template_info")
    def test_main_info_command(self, mock_show_info, mock_engine_class):
        """Test main function with info command"""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        main()

        mock_engine_class.assert_called_once()
        mock_show_info.assert_called_once_with(mock_engine, "resume", "classic")

    @patch(
        "sys.argv",
        ["cli.py", "generate", "resume", "classic", "data.json", "output.pdf"],
    )
    @patch("resume_agent_template_engine.cli.TemplateEngine")
    @patch("resume_agent_template_engine.cli.generate_document")
    def test_main_generate_command(self, mock_generate, mock_engine_class):
        """Test main function with generate command"""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        main()

        mock_engine_class.assert_called_once()
        mock_generate.assert_called_once_with(
            mock_engine, "resume", "classic", "data.json", "output.pdf", "pdf"
        )

    @patch(
        "sys.argv",
        [
            "cli.py",
            "generate",
            "resume",
            "classic",
            "data.json",
            "output.tex",
            "--format",
            "latex",
        ],
    )
    @patch("resume_agent_template_engine.cli.TemplateEngine")
    @patch("resume_agent_template_engine.cli.generate_document")
    def test_main_generate_command_latex(self, mock_generate, mock_engine_class):
        """Test main function with generate command for LaTeX output"""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        main()

        mock_engine_class.assert_called_once()
        mock_generate.assert_called_once_with(
            mock_engine, "resume", "classic", "data.json", "output.tex", "latex"
        )

    @patch("sys.argv", ["cli.py", "--verbose", "list"])
    @patch("resume_agent_template_engine.cli.TemplateEngine")
    @patch("resume_agent_template_engine.cli.list_templates")
    @patch("resume_agent_template_engine.cli.setup_logging")
    def test_main_verbose_flag(
        self, mock_setup_logging, mock_list_templates, mock_engine_class
    ):
        """Test main function with verbose flag"""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        main()

        mock_setup_logging.assert_called_once_with("DEBUG")

    @patch(
        "sys.argv",
        [
            "cli.py",
            "--config",
            "config.yaml",
            "--templates-path",
            "/custom/templates",
            "list",
        ],
    )
    @patch("resume_agent_template_engine.cli.TemplateEngine")
    @patch("resume_agent_template_engine.cli.list_templates")
    def test_main_with_config_and_templates_path(
        self, mock_list_templates, mock_engine_class
    ):
        """Test main function with config and templates path"""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        main()

        mock_engine_class.assert_called_once_with(
            config_path="config.yaml", templates_path="/custom/templates"
        )

    @patch("sys.argv", ["cli.py", "list"])
    @patch("resume_agent_template_engine.cli.TemplateEngine")
    def test_main_engine_initialization_error(self, mock_engine_class):
        """Test main function with template engine initialization error"""
        mock_engine_class.side_effect = Exception("Initialization failed")

        with pytest.raises(SystemExit):
            main()
