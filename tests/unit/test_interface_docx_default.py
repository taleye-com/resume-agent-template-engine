import tempfile
import pytest

from resume_agent_template_engine.core.template_engine import TemplateInterface
from resume_agent_template_engine.core.exceptions import TemplateRenderingException


class DummyTemplate(TemplateInterface):
    @property
    def required_fields(self):
        return ["personalInfo"]

    @property
    def template_type(self):
        from resume_agent_template_engine.core.template_engine import DocumentType

        return DocumentType.RESUME

    def validate_data(self):
        pass

    def render(self) -> str:
        return "test"

    def export_to_pdf(self, output_path: str) -> str:
        return output_path


def test_interface_default_docx_not_supported():
    t = DummyTemplate({"personalInfo": {"name": "A", "email": "b"}})
    with tempfile.NamedTemporaryFile(suffix=".docx") as tmp:
        with pytest.raises(TemplateRenderingException):
            t.export_to_docx(tmp.name)

