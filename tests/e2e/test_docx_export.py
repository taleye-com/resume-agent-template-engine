import os
import tempfile
import pytest

from resume_agent_template_engine.core.template_engine import TemplateEngine


SAMPLE_RESUME = {
    "personalInfo": {
        "name": "Test User",
        "email": "test@example.com",
    }
}


@pytest.mark.parametrize(
    "document_type,template_name",
    [
        ("resume", "classic"),
        ("resume", "two_column"),
        ("cover_letter", "classic"),
        ("cover_letter", "two_column"),
    ],
)
def test_export_to_docx_success(document_type, template_name):
    engine = TemplateEngine()

    # Skip if pandoc is not available in PATH
    from shutil import which

    if which("pandoc") is None:
        pytest.skip("pandoc not installed; skipping DOCX export test")

    data = dict(SAMPLE_RESUME)
    if document_type == "cover_letter":
        data.update(
            {
                "recipient": {
                    "name": "Hiring Manager",
                    "title": "Manager",
                    "company": "Company",
                    "address": ["Line 1"],
                },
                "body": ["Hello world"],
            }
        )

    with tempfile.TemporaryDirectory() as tmp:
        out_path = os.path.join(tmp, "out.docx")
        result = engine.export_to_docx(document_type, template_name, data, out_path)
        assert result == out_path
        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 0


def test_export_to_docx_missing_pandoc(monkeypatch):
    engine = TemplateEngine()

    # Force which("pandoc") to None and PATH lookup to fail by monkeypatching shutil.which
    import shutil

    def _fake_which(_):
        return None

    monkeypatch.setattr(shutil, "which", _fake_which)

    data = SAMPLE_RESUME
    with tempfile.TemporaryDirectory() as tmp:
        out_path = os.path.join(tmp, "out.docx")

        # We expect a DependencyException or TemplateRenderingException from the template
        from resume_agent_template_engine.core.exceptions import DependencyException

        with pytest.raises(DependencyException):
            engine.export_to_docx("resume", "classic", data, out_path)


def test_export_to_docx_invalid_template():
    engine = TemplateEngine()
    with tempfile.TemporaryDirectory() as tmp:
        out_path = os.path.join(tmp, "out.docx")

        from resume_agent_template_engine.core.exceptions import TemplateNotFoundException

        with pytest.raises(TemplateNotFoundException):
            engine.export_to_docx("resume", "nonexistent", SAMPLE_RESUME, out_path)

