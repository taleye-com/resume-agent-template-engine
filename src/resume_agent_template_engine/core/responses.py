"""
Standardized Response Formats for Resume Compiler
Provides consistent API response structures and formatting utilities
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Union

from .errors import ErrorCode
from .exceptions import ResumeCompilerException


@dataclass
class ErrorResponse:
    """Standardized error response structure"""

    code: str
    category: str
    severity: str
    title: str
    message: str
    request_id: str
    timestamp: str
    suggested_fix: Optional[str] = None
    field: Optional[str] = None
    context: Optional[dict[str, Any]] = None
    documentation_url: Optional[str] = None

    @classmethod
    def from_exception(cls, exception: ResumeCompilerException) -> "ErrorResponse":
        """Create ErrorResponse from ResumeCompilerException"""
        return cls(
            code=exception.error_code.value,
            category=exception.category.value,
            severity=exception.severity.value,
            title=exception.error_def.title,
            message=exception.formatted_message,
            request_id=exception.request_id,
            timestamp=exception.timestamp.isoformat() + "Z",
            suggested_fix=exception.suggested_fix,
            field=getattr(exception, "field_path", None),
            context=exception.context if exception.context else None,
            documentation_url=exception.error_def.documentation_url,
        )

    @classmethod
    def from_error_code(
        cls, code: ErrorCode, request_id: Optional[str] = None, **context
    ) -> "ErrorResponse":
        """Create ErrorResponse from error code and context"""
        from .errors import error_registry, get_error_definition

        error_def = get_error_definition(code)
        if not error_def:
            # This is an internal error - system has invalid error code
            from .exceptions import InternalServerException

            raise InternalServerException(details=f"Unknown error code: {code}")

        formatted_message = error_registry.format_message(code, **context)

        return cls(
            code=code.value,
            category=error_def.category.value,
            severity=error_def.severity.value,
            title=error_def.title,
            message=formatted_message,
            request_id=request_id or str(uuid.uuid4())[:8],
            timestamp=datetime.utcnow().isoformat() + "Z",
            suggested_fix=error_def.suggested_fix,
            context=context if context else None,
            documentation_url=error_def.documentation_url,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for JSON serialization"""
        result = {
            "error": {
                "code": self.code,
                "category": self.category,
                "severity": self.severity,
                "title": self.title,
                "message": self.message,
                "request_id": self.request_id,
                "timestamp": self.timestamp,
            }
        }

        # Add optional fields if present
        if self.suggested_fix:
            result["error"]["suggested_fix"] = self.suggested_fix

        if self.field:
            result["error"]["field"] = self.field

        if self.context:
            result["error"]["context"] = self.context

        if self.documentation_url:
            result["error"]["documentation_url"] = self.documentation_url

        return result


@dataclass
class ValidationErrorDetail:
    """Detailed validation error information"""

    code: str
    category: str
    severity: str
    field: str
    message: str
    suggested_fix: Optional[str] = None
    original_value: Any = None
    corrected_value: Any = None


@dataclass
class ValidationResponse:
    """Response for validation operations"""

    is_valid: bool
    request_id: str
    timestamp: str
    errors: list[ValidationErrorDetail] = field(default_factory=list)
    warnings: list[ValidationErrorDetail] = field(default_factory=list)
    normalized_data: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None

    @classmethod
    def create_success(
        cls,
        normalized_data: Optional[dict[str, Any]] = None,
        warnings: Optional[list[ValidationErrorDetail]] = None,
        metadata: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> "ValidationResponse":
        """Create a successful validation response"""
        return cls(
            is_valid=True,
            request_id=request_id or str(uuid.uuid4())[:8],
            timestamp=datetime.utcnow().isoformat() + "Z",
            errors=[],
            warnings=warnings or [],
            normalized_data=normalized_data,
            metadata=metadata,
        )

    @classmethod
    def create_failure(
        cls,
        errors: list[ValidationErrorDetail],
        warnings: Optional[list[ValidationErrorDetail]] = None,
        metadata: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> "ValidationResponse":
        """Create a failed validation response"""
        return cls(
            is_valid=False,
            request_id=request_id or str(uuid.uuid4())[:8],
            timestamp=datetime.utcnow().isoformat() + "Z",
            errors=errors,
            warnings=warnings or [],
            normalized_data=None,
            metadata=metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for JSON serialization"""
        result = {
            "is_valid": self.is_valid,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "errors": [self._error_detail_to_dict(error) for error in self.errors],
            "warnings": [
                self._error_detail_to_dict(warning) for warning in self.warnings
            ],
        }

        if self.normalized_data is not None:
            result["normalized_data"] = self.normalized_data

        if self.metadata:
            result["metadata"] = self.metadata

        return result

    @staticmethod
    def _error_detail_to_dict(detail: ValidationErrorDetail) -> dict[str, Any]:
        """Convert ValidationErrorDetail to dictionary"""
        result = {
            "code": detail.code,
            "category": detail.category,
            "severity": detail.severity,
            "field": detail.field,
            "message": detail.message,
        }

        if detail.suggested_fix:
            result["suggested_fix"] = detail.suggested_fix

        if detail.original_value is not None:
            result["original_value"] = detail.original_value

        if detail.corrected_value is not None:
            result["corrected_value"] = detail.corrected_value

        return result


@dataclass
class SuccessResponse:
    """Standardized success response structure"""

    message: str
    request_id: str
    timestamp: str
    data: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None

    @classmethod
    def create(
        cls,
        message: str,
        data: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> "SuccessResponse":
        """Create a success response"""
        return cls(
            message=message,
            request_id=request_id or str(uuid.uuid4())[:8],
            timestamp=datetime.utcnow().isoformat() + "Z",
            data=data,
            metadata=metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for JSON serialization"""
        result = {
            "success": True,
            "message": self.message,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
        }

        if self.data:
            result["data"] = self.data

        if self.metadata:
            result["metadata"] = self.metadata

        return result


class ResponseFormatter:
    """Utility class for formatting API responses"""

    @staticmethod
    def format_error_response(
        exception: Union[ResumeCompilerException, Exception],
        request_id: Optional[str] = None,
        include_debug_info: bool = False,
    ) -> dict[str, Any]:
        """Format an exception into a standardized error response"""

        if isinstance(exception, ResumeCompilerException):
            error_response = ErrorResponse.from_exception(exception)
        else:
            # Handle unexpected exceptions
            from .errors import ErrorCode

            error_response = ErrorResponse.from_error_code(
                ErrorCode.SYS001, request_id=request_id, details=str(exception)
            )

        result = error_response.to_dict()

        # Add debug information for non-user-facing errors
        if include_debug_info and isinstance(exception, ResumeCompilerException):
            if not exception.is_user_facing:
                result["debug"] = {
                    "exception_type": type(exception).__name__,
                    "original_exception": (
                        str(exception.original_exception)
                        if exception.original_exception
                        else None
                    ),
                }

        return result

    @staticmethod
    def format_validation_response(
        validation_result,  # ValidationResult from validation.py
        request_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Format validation result into standardized response"""

        # Convert ValidationError objects to ValidationErrorDetail
        errors = []
        warnings = []

        for error in validation_result.errors:
            detail = ValidationErrorDetail(
                code=getattr(error, "error_code", "VAL999"),  # Fallback code
                category="validation",
                severity=error.severity,
                field=error.field_path,
                message=error.message,
                suggested_fix=error.suggested_fix,
                original_value=error.original_value,
                corrected_value=error.corrected_value,
            )
            errors.append(detail)

        for warning in validation_result.warnings:
            detail = ValidationErrorDetail(
                code=getattr(warning, "error_code", "VAL999"),  # Fallback code
                category="validation",
                severity=warning.severity,
                field=warning.field_path,
                message=warning.message,
                suggested_fix=warning.suggested_fix,
                original_value=warning.original_value,
                corrected_value=warning.corrected_value,
            )
            warnings.append(detail)

        if validation_result.is_valid:
            response = ValidationResponse.create_success(
                normalized_data=validation_result.normalized_data,
                warnings=warnings,
                metadata=validation_result.metadata,
                request_id=request_id,
            )
        else:
            response = ValidationResponse.create_failure(
                errors=errors,
                warnings=warnings,
                metadata=validation_result.metadata,
                request_id=request_id,
            )

        return response.to_dict()

    @staticmethod
    def format_success_response(
        message: str,
        data: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Format a success response"""
        response = SuccessResponse.create(
            message=message, data=data, metadata=metadata, request_id=request_id
        )
        return response.to_dict()

    @staticmethod
    def get_http_status_code(
        exception: Union[ResumeCompilerException, Exception],
    ) -> int:
        """Get appropriate HTTP status code for an exception"""
        if isinstance(exception, ResumeCompilerException):
            return exception.http_status_code
        else:
            # Default to 500 for unexpected exceptions
            return 500


# Convenience functions for common response patterns


def create_error_response(
    error_code: ErrorCode, request_id: Optional[str] = None, **context
) -> dict[str, Any]:
    """Create an error response from error code"""
    error_response = ErrorResponse.from_error_code(
        error_code, request_id=request_id, **context
    )
    return error_response.to_dict()


def create_validation_error_response(
    field: str,
    message: str,
    error_code: str = "VAL999",
    suggested_fix: Optional[str] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    """Create a validation error response"""
    error_detail = ValidationErrorDetail(
        code=error_code,
        category="validation",
        severity="error",
        field=field,
        message=message,
        suggested_fix=suggested_fix,
    )

    response = ValidationResponse.create_failure(
        errors=[error_detail], request_id=request_id
    )

    return response.to_dict()


def create_success_response(
    message: str,
    data: Optional[dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    """Create a success response"""
    return ResponseFormatter.format_success_response(
        message=message, data=data, request_id=request_id
    )
