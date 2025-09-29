"""
Unit tests for the exception system

Tests all custom exception classes, error code system, and error handling
functionality including ValidationException, SecurityValidationException,
and other custom exceptions.
"""

import pytest

from resume_agent_template_engine.core.errors import ErrorCode
from resume_agent_template_engine.core.exceptions import (
    APIException,
    ResumeCompilerException,
    SecurityValidationException,
    TemplateCompilationException,
    TemplateException,
    TemplateNotFoundException,
    ValidationException,
)


class TestErrorCode:
    """Test ErrorCode enum functionality"""

    def test_error_code_values(self):
        """Test that error codes have correct values"""
        assert ErrorCode.VAL001.value == "VAL001"
        assert ErrorCode.VAL002.value == "VAL002"
        assert ErrorCode.VAL003.value == "VAL003"
        assert ErrorCode.VAL012.value == "VAL012"

    def test_error_code_enum_existence(self):
        """Test that expected error codes exist"""
        # Test a few key error codes exist
        assert hasattr(ErrorCode, "VAL001")
        assert hasattr(ErrorCode, "VAL003")
        assert hasattr(ErrorCode, "VAL012")


class TestResumeCompilerException:
    """Test base ResumeCompilerException"""

    def test_base_exception_creation(self):
        """Test creating base exception"""
        exception = ResumeCompilerException(
            error_code=ErrorCode.VAL001, context={"test": "value"}
        )

        assert exception.error_code == ErrorCode.VAL001
        assert exception.context == {"test": "value"}

    def test_base_exception_inheritance(self):
        """Test that base exception inherits from Exception"""
        exception = ResumeCompilerException(ErrorCode.VAL001)
        assert isinstance(exception, Exception)

    def test_base_exception_properties(self):
        """Test base exception properties"""
        exception = ResumeCompilerException(ErrorCode.VAL001)

        # These properties should exist
        assert hasattr(exception, "error_code")
        assert hasattr(exception, "context")
        assert hasattr(exception, "request_id")
        assert hasattr(exception, "timestamp")


class TestValidationException:
    """Test ValidationException functionality"""

    def test_validation_exception_creation(self):
        """Test creating ValidationException"""
        exception = ValidationException(
            error_code=ErrorCode.VAL003, field_path="personalInfo.email"
        )

        assert exception.error_code == ErrorCode.VAL003
        assert exception.field_path == "personalInfo.email"

    def test_validation_exception_inheritance(self):
        """Test ValidationException inherits from ResumeCompilerException"""
        exception = ValidationException(ErrorCode.VAL001)
        assert isinstance(exception, ResumeCompilerException)
        assert isinstance(exception, Exception)

    def test_validation_exception_with_field_value(self):
        """Test ValidationException with field value"""
        exception = ValidationException(
            error_code=ErrorCode.VAL003,
            field_path="personalInfo.email",
            field_value="invalid-email",
        )

        assert exception.field_path == "personalInfo.email"
        assert exception.field_value == "invalid-email"


class TestSecurityValidationException:
    """Test SecurityValidationException functionality"""

    def test_security_exception_creation(self):
        """Test creating SecurityValidationException"""
        exception = SecurityValidationException(
            error_code=ErrorCode.VAL012, field_path="personalInfo.name"
        )

        assert exception.error_code == ErrorCode.VAL012

    def test_security_exception_inheritance(self):
        """Test SecurityValidationException inherits from ValidationException"""
        exception = SecurityValidationException(ErrorCode.VAL012)
        assert isinstance(exception, ValidationException)
        assert isinstance(exception, ResumeCompilerException)
        assert isinstance(exception, Exception)


class TestTemplateException:
    """Test TemplateException functionality"""

    def test_template_exception_creation(self):
        """Test creating TemplateException"""
        exception = TemplateException(
            error_code=ErrorCode.TPL001, template_name="modern_resume"
        )

        assert exception.error_code == ErrorCode.TPL001
        assert exception.template_name == "modern_resume"

    def test_template_exception_inheritance(self):
        """Test TemplateException inherits from ResumeCompilerException"""
        exception = TemplateException(ErrorCode.TPL001)
        assert isinstance(exception, ResumeCompilerException)
        assert isinstance(exception, Exception)


class TestSpecificExceptions:
    """Test specific exception subclasses"""

    def test_template_not_found_exception(self):
        """Test TemplateNotFoundException"""
        exception = TemplateNotFoundException(
            template_name="nonexistent", document_type="resume"
        )

        assert exception.template_name == "nonexistent"
        assert exception.document_type == "resume"
        assert exception.error_code == ErrorCode.TPL001

    def test_template_compilation_exception(self):
        """Test TemplateCompilationException"""
        exception = TemplateCompilationException(
            template_name="broken_template", details="Syntax error in template"
        )

        assert exception.template_name == "broken_template"
        assert exception.error_code == ErrorCode.TPL002

    def test_api_exception(self):
        """Test APIException"""
        exception = APIException(
            error_code=ErrorCode.API001, endpoint="/generate", method="POST"
        )

        assert exception.error_code == ErrorCode.API001
        assert exception.endpoint == "/generate"
        assert exception.method == "POST"


class TestExceptionIntegration:
    """Integration tests for exception system"""

    def test_exception_to_dict(self):
        """Test converting exceptions to dictionary format"""
        exception = ValidationException(
            error_code=ErrorCode.VAL003,
            field_path="personalInfo.email",
            field_value="invalid",
        )

        exception_dict = exception.to_dict()

        assert "error" in exception_dict
        assert "code" in exception_dict["error"]
        assert "message" in exception_dict["error"]
        assert exception_dict["error"]["code"] == "VAL003"

    def test_exception_context_handling(self):
        """Test that exception context is properly handled"""
        context = {"field": "email", "value": "invalid"}
        exception = ValidationException(error_code=ErrorCode.VAL003, context=context)

        # Context should be preserved
        assert "field" in exception.context
        assert exception.context["field"] == "email"

    def test_exception_request_id(self):
        """Test that exceptions have request IDs"""
        exception = ResumeCompilerException(ErrorCode.VAL001)

        assert hasattr(exception, "request_id")
        assert exception.request_id is not None
        assert len(exception.request_id) > 0

    def test_exception_timestamp(self):
        """Test that exceptions have timestamps"""
        exception = ResumeCompilerException(ErrorCode.VAL001)

        assert hasattr(exception, "timestamp")
        assert exception.timestamp is not None


if __name__ == "__main__":
    pytest.main([__file__])
