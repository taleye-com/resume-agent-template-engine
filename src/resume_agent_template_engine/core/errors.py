"""
Centralized Error Registry for Resume Compiler
Provides standardized error codes, categories, and message templates
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Error categories for classification"""
    VALIDATION = "validation"
    TEMPLATE = "template"
    API = "api"
    SYSTEM = "system"
    SECURITY = "security"
    DATA = "data"
    FILE = "file"


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    CRITICAL = "critical"  # System cannot continue
    ERROR = "error"        # Operation failed, user action required
    WARNING = "warning"    # Operation succeeded with issues
    INFO = "info"         # Informational, no action required


class ErrorCode(str, Enum):
    """Centralized error codes for the resume compiler"""

    # Validation Errors (VAL001-VAL099)
    VAL001 = "VAL001"  # Missing required field
    VAL002 = "VAL002"  # Invalid field type
    VAL003 = "VAL003"  # Invalid email format
    VAL004 = "VAL004"  # Invalid phone format
    VAL005 = "VAL005"  # Invalid URL format
    VAL006 = "VAL006"  # Invalid date format
    VAL007 = "VAL007"  # Field value too long
    VAL008 = "VAL008"  # Field value too short
    VAL009 = "VAL009"  # Invalid enum value
    VAL010 = "VAL010"  # Schema validation failed
    VAL011 = "VAL011"  # Data normalization failed
    VAL012 = "VAL012"  # LaTeX injection detected
    VAL013 = "VAL013"  # Invalid JSON structure
    VAL014 = "VAL014"  # Invalid YAML structure
    VAL015 = "VAL015"  # Validation level not supported

    # Template Errors (TPL001-TPL099)
    TPL001 = "TPL001"  # Template not found
    TPL002 = "TPL002"  # Template compilation failed
    TPL003 = "TPL003"  # Template rendering failed
    TPL004 = "TPL004"  # Template file corrupted
    TPL005 = "TPL005"  # Template class not found
    TPL006 = "TPL006"  # Template dependency missing
    TPL007 = "TPL007"  # LaTeX compilation failed
    TPL008 = "TPL008"  # PDF generation failed
    TPL009 = "TPL009"  # Template directory not found
    TPL010 = "TPL010"  # Template metadata invalid
    TPL011 = "TPL011"  # Template format not supported
    TPL012 = "TPL012"  # Template placeholder unreplaced

    # API Errors (API001-API099)
    API001 = "API001"  # Invalid request format
    API002 = "API002"  # Missing request parameter
    API003 = "API003"  # Invalid request parameter
    API004 = "API004"  # Request timeout
    API005 = "API005"  # Rate limit exceeded
    API006 = "API006"  # Invalid content type
    API007 = "API007"  # Request too large
    API008 = "API008"  # Invalid HTTP method
    API009 = "API009"  # Authentication required
    API010 = "API010"  # Authorization failed
    API011 = "API011"  # Resource not found
    API012 = "API012"  # Conflict with existing resource
    API013 = "API013"  # Service unavailable

    # System Errors (SYS001-SYS099)
    SYS001 = "SYS001"  # Internal server error
    SYS002 = "SYS002"  # Database connection failed
    SYS003 = "SYS003"  # External service unavailable
    SYS004 = "SYS004"  # Configuration error
    SYS005 = "SYS005"  # Memory allocation failed
    SYS006 = "SYS006"  # Dependency not found
    SYS007 = "SYS007"  # Environment setup failed
    SYS008 = "SYS008"  # Service initialization failed
    SYS009 = "SYS009"  # Resource exhausted
    SYS010 = "SYS010"  # Unexpected exception

    # Security Errors (SEC001-SEC099)
    SEC001 = "SEC001"  # Malicious input detected
    SEC002 = "SEC002"  # File path traversal attempt
    SEC003 = "SEC003"  # Command injection attempt
    SEC004 = "SEC004"  # Unsafe file operation
    SEC005 = "SEC005"  # Invalid file type
    SEC006 = "SEC006"  # File size limit exceeded
    SEC007 = "SEC007"  # Suspicious pattern detected

    # File Operation Errors (FIL001-FIL099)
    FIL001 = "FIL001"  # File not found
    FIL002 = "FIL002"  # File permission denied
    FIL003 = "FIL003"  # Disk space insufficient
    FIL004 = "FIL004"  # File locked by another process
    FIL005 = "FIL005"  # File format not supported
    FIL006 = "FIL006"  # File corrupted
    FIL007 = "FIL007"  # Directory creation failed
    FIL008 = "FIL008"  # File cleanup failed
    FIL009 = "FIL009"  # Temporary file creation failed
    FIL010 = "FIL010"  # File encoding not supported


@dataclass(frozen=True)
class ErrorDefinition:
    """Definition of a specific error with all its metadata"""
    code: ErrorCode
    category: ErrorCategory
    severity: ErrorSeverity
    title: str
    message_template: str
    suggested_fix: Optional[str] = None
    documentation_url: Optional[str] = None
    http_status_code: Optional[int] = None
    user_facing: bool = True


class ErrorRegistry:
    """Centralized registry for all error definitions"""

    def __init__(self):
        """Initialize the error registry with all error definitions"""
        self._errors: Dict[ErrorCode, ErrorDefinition] = {}
        self._initialize_errors()

    def _initialize_errors(self):
        """Initialize all error definitions"""

        # Validation Errors
        self._register_error(ErrorDefinition(
            code=ErrorCode.VAL001,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            title="Required Field Missing",
            message_template="Required field '{field}' is missing from {section}",
            suggested_fix="Add the required field to your data",
            http_status_code=400
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.VAL002,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            title="Invalid Field Type",
            message_template="Field '{field}' must be of type {expected_type}, got {actual_type}",
            suggested_fix="Change the field to the correct data type",
            http_status_code=400
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.VAL003,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            title="Invalid Email Format",
            message_template="Email '{email}' is not in valid format",
            suggested_fix="Use format like 'user@domain.com'",
            http_status_code=400
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.VAL004,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.WARNING,
            title="Invalid Phone Format",
            message_template="Phone number '{phone}' could not be normalized",
            suggested_fix="Use format like '(555) 123-4567' or '+1 (555) 123-4567'",
            http_status_code=400
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.VAL005,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.WARNING,
            title="Invalid URL Format",
            message_template="URL '{url}' is not in valid format",
            suggested_fix="Use format like 'https://domain.com'",
            http_status_code=400
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.VAL006,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            title="Invalid Date Format",
            message_template="Date '{date}' is not in valid format",
            suggested_fix="Use format like 'YYYY-MM' or 'YYYY-MM-DD'",
            http_status_code=400
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.VAL012,
            category=ErrorCategory.SECURITY,
            severity=ErrorSeverity.CRITICAL,
            title="LaTeX Injection Detected",
            message_template="Dangerous LaTeX command detected in field '{field}': {command}",
            suggested_fix="Remove unsafe LaTeX commands from your input",
            http_status_code=400
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.VAL013,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            title="Invalid JSON Structure",
            message_template="JSON parsing failed: {details}",
            suggested_fix="Check JSON syntax and structure",
            http_status_code=400
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.VAL014,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            title="Invalid YAML Structure",
            message_template="YAML parsing failed: {details}",
            suggested_fix="Check YAML syntax and indentation",
            http_status_code=400
        ))

        # Template Errors
        self._register_error(ErrorDefinition(
            code=ErrorCode.TPL001,
            category=ErrorCategory.TEMPLATE,
            severity=ErrorSeverity.ERROR,
            title="Template Not Found",
            message_template="Template '{template}' not found for document type '{document_type}'",
            suggested_fix="Use one of the available templates: {available_templates}",
            http_status_code=404
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.TPL002,
            category=ErrorCategory.TEMPLATE,
            severity=ErrorSeverity.ERROR,
            title="Template Compilation Failed",
            message_template="Failed to compile template '{template}': {details}",
            suggested_fix="Check template syntax and dependencies",
            http_status_code=500
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.TPL003,
            category=ErrorCategory.TEMPLATE,
            severity=ErrorSeverity.ERROR,
            title="Template Rendering Failed",
            message_template="Failed to render template '{template}': {details}",
            suggested_fix="Check data compatibility with template requirements",
            http_status_code=500
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.TPL005,
            category=ErrorCategory.TEMPLATE,
            severity=ErrorSeverity.ERROR,
            title="Template Class Not Found",
            message_template="Template class not found in {module_path}",
            suggested_fix="Ensure template helper.py contains a valid template class",
            http_status_code=500
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.TPL007,
            category=ErrorCategory.TEMPLATE,
            severity=ErrorSeverity.ERROR,
            title="LaTeX Compilation Failed",
            message_template="LaTeX compilation failed: {details}",
            suggested_fix="Ensure pdflatex is installed and template is valid",
            http_status_code=500
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.TPL008,
            category=ErrorCategory.TEMPLATE,
            severity=ErrorSeverity.ERROR,
            title="PDF Generation Failed",
            message_template="Failed to generate PDF output: {details}",
            suggested_fix="Check LaTeX compilation logs for errors",
            http_status_code=500
        ))

        # API Errors
        self._register_error(ErrorDefinition(
            code=ErrorCode.API001,
            category=ErrorCategory.API,
            severity=ErrorSeverity.ERROR,
            title="Invalid Request Format",
            message_template="Request format is invalid: {details}",
            suggested_fix="Check API documentation for correct request format",
            http_status_code=400
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.API002,
            category=ErrorCategory.API,
            severity=ErrorSeverity.ERROR,
            title="Missing Request Parameter",
            message_template="Required parameter '{parameter}' is missing",
            suggested_fix="Include all required parameters in your request",
            http_status_code=400
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.API003,
            category=ErrorCategory.API,
            severity=ErrorSeverity.ERROR,
            title="Invalid Request Parameter",
            message_template="Parameter '{parameter}' has invalid value: {value}",
            suggested_fix="Check parameter format and allowed values",
            http_status_code=400
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.API011,
            category=ErrorCategory.API,
            severity=ErrorSeverity.ERROR,
            title="Resource Not Found",
            message_template="Requested resource '{resource}' not found",
            suggested_fix="Check the resource path and ensure it exists",
            http_status_code=404
        ))

        # System Errors
        self._register_error(ErrorDefinition(
            code=ErrorCode.SYS001,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            title="Internal Server Error",
            message_template="An unexpected error occurred: {details}",
            suggested_fix="Try again later or contact support if the problem persists",
            http_status_code=500,
            user_facing=False
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.SYS006,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            title="Dependency Not Found",
            message_template="Required dependency '{dependency}' not found",
            suggested_fix="Ensure all system dependencies are installed",
            http_status_code=500,
            user_facing=False
        ))

        # File Operation Errors
        self._register_error(ErrorDefinition(
            code=ErrorCode.FIL001,
            category=ErrorCategory.FILE,
            severity=ErrorSeverity.ERROR,
            title="File Not Found",
            message_template="File not found: {file_path}",
            suggested_fix="Check file path and ensure file exists",
            http_status_code=404
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.FIL002,
            category=ErrorCategory.FILE,
            severity=ErrorSeverity.ERROR,
            title="File Permission Denied",
            message_template="Permission denied accessing file: {file_path}",
            suggested_fix="Check file permissions",
            http_status_code=403
        ))

        self._register_error(ErrorDefinition(
            code=ErrorCode.FIL003,
            category=ErrorCategory.FILE,
            severity=ErrorSeverity.ERROR,
            title="Insufficient Disk Space",
            message_template="Insufficient disk space for operation",
            suggested_fix="Free up disk space and try again",
            http_status_code=507
        ))

    def _register_error(self, error_def: ErrorDefinition):
        """Register an error definition"""
        self._errors[error_def.code] = error_def

    def get_error(self, code: ErrorCode) -> Optional[ErrorDefinition]:
        """Get error definition by code"""
        return self._errors.get(code)

    def format_message(self, code: ErrorCode, **kwargs) -> str:
        """Format error message with provided parameters"""
        error_def = self.get_error(code)
        if not error_def:
            return f"Unknown error code: {code}"

        try:
            return error_def.message_template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing parameter {e} for error {code}")
            return error_def.message_template

    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorDefinition]:
        """Get all errors in a specific category"""
        return [error for error in self._errors.values() if error.category == category]

    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorDefinition]:
        """Get all errors with specific severity"""
        return [error for error in self._errors.values() if error.severity == severity]

    def get_all_codes(self) -> List[ErrorCode]:
        """Get all registered error codes"""
        return list(self._errors.keys())

    def get_http_status_code(self, code: ErrorCode) -> int:
        """Get HTTP status code for error, defaults to 500"""
        error_def = self.get_error(code)
        return error_def.http_status_code if error_def else 500


# Global error registry instance
error_registry = ErrorRegistry()


def get_error_definition(code: ErrorCode) -> Optional[ErrorDefinition]:
    """Convenience function to get error definition"""
    return error_registry.get_error(code)


def format_error_message(code: ErrorCode, **kwargs) -> str:
    """Convenience function to format error message"""
    return error_registry.format_message(code, **kwargs)