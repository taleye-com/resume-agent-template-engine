import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Validation issue severity levels - centralized"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationIssue:
    """Represents a validation issue - centralized"""

    def __init__(
        self,
        severity: ValidationSeverity,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        field_name: Optional[str] = None,
    ):
        self.severity = severity
        self.message = message
        self.file_path = file_path
        self.line_number = line_number
        self.field_name = field_name

    def __str__(self) -> str:
        location = ""
        if self.file_path:
            location = f" in {self.file_path}"
            if self.line_number:
                location += f" (line {self.line_number})"

        field_info = f" [{self.field_name}]" if self.field_name else ""
        return f"[{self.severity.value.upper()}]{location}{field_info}: {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "severity": self.severity.value,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "field_name": self.field_name,
        }


class ValidationError(Exception):
    """Custom exception for validation errors - centralized"""

    def __init__(
        self,
        message: str,
        errors: List[str] = None,
        issues: List[ValidationIssue] = None,
    ):
        super().__init__(message)
        self.errors = errors or []
        self.issues = issues or []

    def add_error(self, error: str) -> None:
        """Add a simple error message"""
        self.errors.append(error)

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add a validation issue"""
        self.issues.append(issue)

    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0 or any(
            issue.severity == ValidationSeverity.ERROR for issue in self.issues
        )

    def get_all_errors(self) -> List[str]:
        """Get all error messages"""
        all_errors = self.errors.copy()
        all_errors.extend(
            [
                str(issue)
                for issue in self.issues
                if issue.severity == ValidationSeverity.ERROR
            ]
        )
        return all_errors


class BaseValidator(ABC):
    """Base validator class implementing DRY validation patterns"""

    def __init__(self):
        """Initialize base validator"""
        self.issues: List[ValidationIssue] = []
        self.current_context: Optional[str] = None

    def reset_issues(self) -> None:
        """Reset validation issues"""
        self.issues.clear()
        self.current_context = None

    def set_context(self, context: str) -> None:
        """Set current validation context"""
        self.current_context = context

    def add_issue(
        self,
        severity: ValidationSeverity,
        message: str,
        field_name: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> None:
        """Add validation issue using current context"""
        issue = ValidationIssue(
            severity=severity,
            message=message,
            file_path=self.current_context,
            field_name=field_name,
            line_number=line_number,
        )
        self.issues.append(issue)

    def add_error(
        self,
        message: str,
        field_name: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> None:
        """Add error issue"""
        self.add_issue(ValidationSeverity.ERROR, message, field_name, line_number)

    def add_warning(
        self,
        message: str,
        field_name: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> None:
        """Add warning issue"""
        self.add_issue(ValidationSeverity.WARNING, message, field_name, line_number)

    def add_info(
        self,
        message: str,
        field_name: Optional[str] = None,
        line_number: Optional[int] = None,
    ) -> None:
        """Add info issue"""
        self.add_issue(ValidationSeverity.INFO, message, field_name, line_number)

    def validate_required_fields(
        self, data: Dict[str, Any], required_fields: List[str], context: str = "data"
    ) -> None:
        """Validate required fields - DRY helper"""
        for field in required_fields:
            if "." in field:
                # Handle nested fields like "personalInfo.name"
                parts = field.split(".")
                current_data = data

                try:
                    for part in parts:
                        current_data = current_data[part]

                    if not current_data:
                        self.add_error(f"Required field '{field}' is empty", field)
                except (KeyError, TypeError):
                    self.add_error(f"Required field '{field}' is missing", field)
            else:
                # Handle simple fields
                if field not in data or not data[field]:
                    self.add_error(f"Required field '{field}' is missing", field)

    def validate_email_format(self, email: str, field_name: str = "email") -> bool:
        """Validate email format - DRY helper"""
        import re

        if not email:
            self.add_error(f"Email field '{field_name}' is required", field_name)
            return False

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            self.add_error(
                f"Invalid email format in '{field_name}': {email}", field_name
            )
            return False

        return True

    def validate_date_format(self, date_str: str, field_name: str = "date") -> bool:
        """Validate date format - DRY helper"""
        from datetime import datetime

        if not date_str:
            return True  # Optional field

        try:
            if len(date_str) == 7:  # YYYY-MM
                datetime.strptime(date_str, "%Y-%m")
            elif len(date_str) == 10:  # YYYY-MM-DD
                datetime.strptime(date_str, "%Y-%m-%d")
            else:
                # Check for specific field name patterns for better error messages
                if "startDate" in field_name:
                    self.add_error(
                        f"Invalid start date format: {date_str}. Use YYYY-MM or YYYY-MM-DD",
                        field_name,
                    )
                elif "endDate" in field_name:
                    self.add_error(
                        f"Invalid end date format: {date_str}. Use YYYY-MM or YYYY-MM-DD",
                        field_name,
                    )
                else:
                    self.add_error(
                        f"Invalid date format in '{field_name}': {date_str}. Use YYYY-MM or YYYY-MM-DD",
                        field_name,
                    )
                return False
            return True
        except ValueError:
            # Check for specific field name patterns for better error messages
            if "startDate" in field_name:
                self.add_error(
                    f"Invalid start date format: {date_str}. Use YYYY-MM or YYYY-MM-DD",
                    field_name,
                )
            elif "endDate" in field_name:
                self.add_error(
                    f"Invalid end date format: {date_str}. Use YYYY-MM or YYYY-MM-DD",
                    field_name,
                )
            else:
                self.add_error(
                    f"Invalid date format in '{field_name}': {date_str}. Use YYYY-MM or YYYY-MM-DD",
                    field_name,
                )
            return False

    def validate_file_exists(self, file_path: str, field_name: str = "file") -> bool:
        """Validate file exists - DRY helper"""
        from pathlib import Path

        if not file_path:
            self.add_error(f"File path '{field_name}' is required", field_name)
            return False

        path = Path(file_path)
        if not path.exists():
            self.add_error(f"File not found: {file_path}", field_name)
            return False

        return True

    def validate_string_length(
        self,
        value: str,
        field_name: str,
        min_length: int = 0,
        max_length: Optional[int] = None,
    ) -> bool:
        """Validate string length - DRY helper"""
        if not value:
            if min_length > 0:
                self.add_error(f"Field '{field_name}' cannot be empty", field_name)
                return False
            return True

        if len(value) < min_length:
            self.add_error(
                f"Field '{field_name}' must be at least {min_length} characters",
                field_name,
            )
            return False

        if max_length and len(value) > max_length:
            self.add_error(
                f"Field '{field_name}' must be no more than {max_length} characters",
                field_name,
            )
            return False

        return True

    def get_error_summary(self) -> Dict[str, Any]:
        """Get validation error summary"""
        errors = [
            issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR
        ]
        warnings = [
            issue
            for issue in self.issues
            if issue.severity == ValidationSeverity.WARNING
        ]
        infos = [
            issue for issue in self.issues if issue.severity == ValidationSeverity.INFO
        ]

        return {
            "total_issues": len(self.issues),
            "errors": len(errors),
            "warnings": len(warnings),
            "infos": len(infos),
            "has_errors": len(errors) > 0,
            "issues": [issue.to_dict() for issue in self.issues],
        }

    @abstractmethod
    def validate(self, *args, **kwargs) -> List[ValidationIssue]:
        """Abstract validation method to be implemented by subclasses"""
        pass


class DataValidator(BaseValidator):
    """Specialized validator for data objects"""

    def validate_personal_info(self, personal_info: Dict[str, Any]) -> None:
        """Validate personal info section - DRY implementation"""
        required_fields = ["name", "email"]
        self.validate_required_fields(personal_info, required_fields, "personalInfo")

        # Validate email format if present
        if personal_info.get("email"):
            self.validate_email_format(personal_info["email"], "personalInfo.email")

    def validate_experience_dates(self, experience_list: List[Dict[str, Any]]) -> None:
        """Validate experience dates - DRY implementation"""
        for i, exp in enumerate(experience_list):
            context = f"experience[{i}]"

            if "startDate" in exp:
                self.validate_date_format(exp["startDate"], f"{context}.startDate")

            if "endDate" in exp and exp["endDate"] != "Present":
                self.validate_date_format(exp["endDate"], f"{context}.endDate")

    def validate(
        self, data: Dict[str, Any], document_type: str
    ) -> List[ValidationIssue]:
        """Validate data based on document type"""
        self.reset_issues()
        self.set_context(f"{document_type}_data")

        # Check for required personalInfo section
        if "personalInfo" not in data:
            self.add_error("Personal information is required", "personalInfo")
        else:
            self.validate_personal_info(data["personalInfo"])

        if "experience" in data and isinstance(data["experience"], list):
            self.validate_experience_dates(data["experience"])

        # Document-type specific validations
        if document_type == "cover_letter":
            self._validate_cover_letter_specific(data)
        elif document_type == "resume":
            self._validate_resume_specific(data)

        return self.issues

    def _validate_cover_letter_specific(self, data: Dict[str, Any]) -> None:
        """Validate cover letter specific fields"""
        required_fields = ["recipient", "content"]
        self.validate_required_fields(data, required_fields)

        if "content" in data:
            content_required = ["opening", "body", "closing"]
            self.validate_required_fields(data["content"], content_required, "content")

    def _validate_resume_specific(self, data: Dict[str, Any]) -> None:
        """Validate resume specific fields"""
        # Resume-specific validations can be added here
        pass
