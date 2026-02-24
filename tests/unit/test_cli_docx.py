import os
import tempfile
import json
import pytest

from resume_agent_template_engine.cli import generate_document
from resume_agent_template_engine.core.template_engine import TemplateEngine


def test_cli_generate_docx_skips_without_pandoc(monkeypatch, capsys):
    from shutil import which

    if which("pandoc") is None:
        pytest.skip("pandoc not installed; CLI docx path covered by e2e skip as well")

    engine = TemplateEngine()
    data = {
        "personalInfo": {"name": "User", "email": "u@example.com"},
    }
    with tempfile.TemporaryDirectory() as tmp:
        data_file = os.path.join(tmp, "data.json")
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        out_file = os.path.join(tmp, "out.docx")
        generate_document(
            engine,
            document_type="resume",
            template_name="classic",
            data_file=data_file,
            output_path=out_file,
            output_format="docx",
        )
        captured = capsys.readouterr()
        assert os.path.exists(out_file)
        assert "DOCX generated successfully" in captured.out

