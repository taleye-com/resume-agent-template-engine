"""
Custom Exception Hierarchy for Resume Compiler
Provides structured exceptions with error codes and automatic message formatting
"""

from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

from .errors import (
    ErrorCode,
    ErrorCategory,
    ErrorSeverity,
    error_registry,
    get_error_definition,
)


class ResumeCompilerException(Exception):
    """Base exception for all resume compiler errors"""

    def __init__(
        self,
        error_code: ErrorCode,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
        request_id: Optional[str] = None,
    ):
        """
        Initialize base exception

        Args:
            error_code: Standardized error code
            context: Additional context for error message formatting
            original_exception: Original exception that caused this error
            request_id: Request ID for correlation (auto-generated if not provided)
        """
        self.error_code = error_code
        self.context = context or {}
        self.original_exception = original_exception
        self.request_id = request_id or str(uuid.uuid4())[:8]
        self.timestamp = datetime.utcnow()

        # Get error definition
        self.error_def = get_error_definition(error_code)
        if not self.error_def:
            raise ValueError(f"Unknown error code: {error_code}")

        # Format message with context
        self.formatted_message = error_registry.format_message(
            error_code, **self.context
        )

        # Call parent constructor
        super().__init__(self.formatted_message)

    @property
    def category(self) -> ErrorCategory:
        """Get error category"""
        return self.error_def.category

    @property
    def severity(self) -> ErrorSeverity:
        """Get error severity"""
        return self.error_def.severity

    @property
    def http_status_code(self) -> int:
        """Get HTTP status code for this error"""
        return self.error_def.http_status_code or 500

    @property
    def suggested_fix(self) -> Optional[str]:
        """Get suggested fix for this error"""
        return self.error_def.suggested_fix

    @property
    def is_user_facing(self) -> bool:
        """Check if this error should be shown to users"""
        return self.error_def.user_facing

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format"""
        result = {
            "error": {
                "code": self.error_code.value,
                "category": self.category.value,
                "severity": self.severity.value,
                "title": self.error_def.title,
                "message": self.formatted_message,
                "suggested_fix": self.suggested_fix,
                "request_id": self.request_id,
                "timestamp": self.timestamp.isoformat() + "Z",
            }
        }

        # Add context if available
        if self.context:
            result["error"]["context"] = self.context

        # Add original exception info if available (for debugging)
        if self.original_exception and not self.is_user_facing:
            result["error"]["original_error"] = {
                "type": type(self.original_exception).__name__,
                "message": str(self.original_exception),
            }

        return result


class ValidationException(ResumeCompilerException):
    """Exception for data validation errors"""

    def __init__(
        self,
        error_code: ErrorCode,
        field_path: Optional[str] = None,
        field_value: Any = None,
        **kwargs,
    ):
        """
        Initialize validation exception

        Args:
            error_code: Validation error code
            field_path: Path to the field that failed validation
            field_value: Value that failed validation
            **kwargs: Additional context parameters
        """
        context = kwargs.get("context", {})
        if field_path:
            context["field"] = field_path
        if field_value is not None:
            context["value"] = field_value

        kwargs["context"] = context
        super().__init__(error_code, **kwargs)

        self.field_path = field_path
        self.field_value = field_value


class DataValidationException(ValidationException):
    """Exception for data format and structure validation errors"""

    pass


class SchemaValidationException(ValidationException):
    """Exception for JSON/YAML schema validation errors"""

    pass


class FormatValidationException(ValidationException):
    """Exception for field format validation errors (email, phone, etc.)"""

    pass


class SecurityValidationException(ValidationException):
    """Exception for security-related validation errors"""

    pass


class TemplateException(ResumeCompilerException):
    """Exception for template-related errors"""

    def __init__(
        self,
        error_code: ErrorCode,
        template_name: Optional[str] = None,
        document_type: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize template exception

        Args:
            error_code: Template error code
            template_name: Name of the template
            document_type: Type of document
            **kwargs: Additional context parameters
        """
        context = kwargs.get("context", {})
        if template_name:
            context["template"] = template_name
        if document_type:
            context["document_type"] = document_type

        kwargs["context"] = context
        super().__init__(error_code, **kwargs)

        self.template_name = template_name
        self.document_type = document_type


class TemplateNotFoundException(TemplateException):
    """Exception for template not found errors"""

    def __init__(
        self,
        template_name: str,
        document_type: str,
        available_templates: List[str] = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        if available_templates:
            context["available_templates"] = ", ".join(available_templates)
        kwargs["context"] = context
        super().__init__(ErrorCode.TPL001, template_name, document_type, **kwargs)


class TemplateCompilationException(TemplateException):
    """Exception for template compilation errors"""

    def __init__(self, template_name: str, details: str, **kwargs):
        context = kwargs.get("context", {})
        context["details"] = details
        kwargs["context"] = context
        super().__init__(ErrorCode.TPL002, template_name, **kwargs)


class TemplateRenderingException(TemplateException):
    """Exception for template rendering errors"""

    def __init__(self, template_name: str, details: str, **kwargs):
        context = kwargs.get("context", {})
        context["details"] = details
        kwargs["context"] = context
        super().__init__(ErrorCode.TPL003, template_name, **kwargs)


class LaTeXCompilationException(TemplateException):
    """Exception for LaTeX compilation errors"""

    def __init__(self, details: str, template_name: Optional[str] = None, **kwargs):
        context = kwargs.get("context", {})
        context["details"] = details
        kwargs["context"] = context
        super().__init__(ErrorCode.TPL007, template_name, **kwargs)


class PDFGenerationException(TemplateException):
    """Exception for PDF generation errors"""

    def __init__(self, details: str, template_name: Optional[str] = None, **kwargs):
        context = kwargs.get("context", {})
        context["details"] = details
        kwargs["context"] = context
        super().__init__(ErrorCode.TPL008, template_name, **kwargs)


class APIException(ResumeCompilerException):
    """Exception for API-related errors"""

    def __init__(
        self,
        error_code: ErrorCode,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize API exception

        Args:
            error_code: API error code
            endpoint: API endpoint that caused the error
            method: HTTP method used
            **kwargs: Additional context parameters
        """
        context = kwargs.get("context", {})
        if endpoint:
            context["endpoint"] = endpoint
        if method:
            context["method"] = method

        kwargs["context"] = context
        super().__init__(error_code, **kwargs)

        self.endpoint = endpoint
        self.method = method


class InvalidRequestException(APIException):
    """Exception for invalid API requests"""

    def __init__(self, details: str, **kwargs):
        context = kwargs.get("context", {})
        context["details"] = details
        kwargs["context"] = context
        super().__init__(ErrorCode.API001, **kwargs)


class MissingParameterException(APIException):
    """Exception for missing required parameters"""

    def __init__(self, parameter: str, **kwargs):
        context = kwargs.get("context", {})
        context["parameter"] = parameter
        kwargs["context"] = context
        super().__init__(ErrorCode.API002, **kwargs)


class InvalidParameterException(APIException):
    """Exception for invalid parameter values"""

    def __init__(self, parameter: str, value: Any, **kwargs):
        context = kwargs.get("context", {})
        context["parameter"] = parameter
        context["value"] = str(value)
        kwargs["context"] = context
        super().__init__(ErrorCode.API003, **kwargs)


class ResourceNotFoundException(APIException):
    """Exception for resource not found errors"""

    def __init__(self, resource: str, **kwargs):
        context = kwargs.get("context", {})
        context["resource"] = resource
        kwargs["context"] = context
        super().__init__(ErrorCode.API011, **kwargs)


class SystemException(ResumeCompilerException):
    """Exception for system-level errors"""

    def __init__(
        self, error_code: ErrorCode, component: Optional[str] = None, **kwargs
    ):
        """
        Initialize system exception

        Args:
            error_code: System error code
            component: System component that caused the error
            **kwargs: Additional context parameters
        """
        context = kwargs.get("context", {})
        if component:
            context["component"] = component

        kwargs["context"] = context
        super().__init__(error_code, **kwargs)

        self.component = component


class InternalServerException(SystemException):
    """Exception for internal server errors"""

    def __init__(self, details: str, **kwargs):
        context = kwargs.get("context", {})
        context["details"] = details
        kwargs["context"] = context
        super().__init__(ErrorCode.SYS001, **kwargs)


class DependencyException(SystemException):
    """Exception for missing dependencies"""

    def __init__(self, dependency: str, **kwargs):
        context = kwargs.get("context", {})
        context["dependency"] = dependency
        kwargs["context"] = context
        super().__init__(ErrorCode.SYS006, **kwargs)


class FileSystemException(ResumeCompilerException):
    """Exception for file system operations"""

    def __init__(
        self,
        error_code: ErrorCode,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize file system exception

        Args:
            error_code: File system error code
            file_path: Path to the file
            operation: File operation being performed
            **kwargs: Additional context parameters
        """
        context = kwargs.get("context", {})
        if file_path:
            context["file_path"] = file_path
        if operation:
            context["operation"] = operation

        kwargs["context"] = context
        super().__init__(error_code, **kwargs)

        self.file_path = file_path
        self.operation = operation


class FileNotFoundException(FileSystemException):
    """Exception for file not found errors"""

    def __init__(self, file_path: str, **kwargs):
        super().__init__(ErrorCode.FIL001, file_path, **kwargs)


class FilePermissionException(FileSystemException):
    """Exception for file permission errors"""

    def __init__(self, file_path: str, **kwargs):
        super().__init__(ErrorCode.FIL002, file_path, **kwargs)


class DiskSpaceException(FileSystemException):
    """Exception for insufficient disk space"""

    def __init__(self, **kwargs):
        super().__init__(ErrorCode.FIL003, **kwargs)


# Convenience functions for creating common exceptions


def create_validation_error(
    error_code: ErrorCode, field_path: str, field_value: Any = None, **context
) -> ValidationException:
    """Create a validation exception with field context"""
    return ValidationException(
        error_code=error_code,
        field_path=field_path,
        field_value=field_value,
        context=context,
    )


def create_template_error(
    error_code: ErrorCode, template_name: str, document_type: str = None, **context
) -> TemplateException:
    """Create a template exception with template context"""
    return TemplateException(
        error_code=error_code,
        template_name=template_name,
        document_type=document_type,
        context=context,
    )


def create_api_error(
    error_code: ErrorCode, endpoint: str = None, method: str = None, **context
) -> APIException:
    """Create an API exception with request context"""
    return APIException(
        error_code=error_code, endpoint=endpoint, method=method, context=context
    )
