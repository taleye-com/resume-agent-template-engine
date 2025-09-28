"""
Enhanced validation system for resume compiler
Provides schema validation, data normalization, fallback handling, and LaTeX injection prevention
"""

import re
import json
import urllib.parse
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import logging

from .errors import ErrorCode, ErrorSeverity, error_registry
from .exceptions import ValidationException, SecurityValidationException

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation strictness levels"""

    STRICT = "strict"  # Fail on any validation error
    LENIENT = "lenient"  # Warn on non-critical errors, fix what we can
    PERMISSIVE = "permissive"  # Fix everything possible, minimal errors


@dataclass
class ValidationError:
    """Represents a validation error with context and error code"""

    field_path: str
    error_code: ErrorCode
    message: str
    severity: ErrorSeverity
    suggested_fix: Optional[str] = None
    original_value: Any = None
    corrected_value: Any = None

    # Backward compatibility properties
    @property
    def error_type(self) -> str:
        """Get error type from error code for backward compatibility"""
        return self.error_code.value

    @classmethod
    def create(
        cls,
        field_path: str,
        error_code: ErrorCode,
        severity: Optional[ErrorSeverity] = None,
        suggested_fix: Optional[str] = None,
        original_value: Any = None,
        corrected_value: Any = None,
        **context,
    ) -> "ValidationError":
        """Create a ValidationError with formatted message from error registry"""

        # Get error definition and format message
        message = error_registry.format_message(error_code, field=field_path, **context)

        # Use severity from error registry if not provided
        if severity is None:
            error_def = error_registry.get_error(error_code)
            severity = error_def.severity if error_def else ErrorSeverity.ERROR

        # Use suggested fix from error registry if not provided
        if suggested_fix is None:
            error_def = error_registry.get_error(error_code)
            suggested_fix = error_def.suggested_fix if error_def else None

        return cls(
            field_path=field_path,
            error_code=error_code,
            message=message,
            severity=severity,
            suggested_fix=suggested_fix,
            original_value=original_value,
            corrected_value=corrected_value,
        )


@dataclass
class ValidationResult:
    """Result of validation process"""

    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    normalized_data: Dict[str, Any]
    metadata: Dict[str, Any]


class LaTeXSanitizer:
    """Sanitizes text to prevent LaTeX injection attacks"""

    # Characters that need escaping in LaTeX
    LATEX_SPECIAL_CHARS = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "^": r"\textasciicircum{}",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "\\": r"\textbackslash{}",
    }

    # Dangerous LaTeX commands to block
    DANGEROUS_COMMANDS = [
        r"\\input\s*\{",
        r"\\include\s*\{",
        r"\\write\s*\{",
        r"\\immediate\s*\\write",
        r"\\openout",
        r"\\closeout",
        r"\\execute",
        r"\\shell",
        r"\\system",
        r"\\catcode",
        r"\\def\s*\\",
        r"\\gdef\s*\\",
        r"\\edef\s*\\",
        r"\\xdef\s*\\",
        r"\\csname",
        r"\\expandafter",
        r"\\noexpand",
        r"\\futurelet",
        r"\\aftergroup",
        r"\\afterassignment",
    ]

    @classmethod
    def sanitize_text(cls, text: str, allow_basic_formatting: bool = True) -> str:
        """
        Sanitize text for safe LaTeX compilation

        Args:
            text: Input text to sanitize
            allow_basic_formatting: Whether to allow basic LaTeX formatting commands

        Returns:
            Sanitized text safe for LaTeX compilation
        """
        if not isinstance(text, str):
            return str(text)

        # First, check for dangerous commands
        for dangerous_pattern in cls.DANGEROUS_COMMANDS:
            if re.search(dangerous_pattern, text, re.IGNORECASE):
                logger.warning(
                    f"Dangerous LaTeX command detected and removed: {dangerous_pattern}"
                )
                # Raise security exception for dangerous commands
                raise SecurityValidationException(
                    ErrorCode.VAL012,
                    field_path="text_input",
                    context={"command": dangerous_pattern},
                )
                text = re.sub(dangerous_pattern, "", text, flags=re.IGNORECASE)

        # Escape special characters
        for char, escaped in cls.LATEX_SPECIAL_CHARS.items():
            text = text.replace(char, escaped)

        # If basic formatting is allowed, restore safe commands
        if allow_basic_formatting:
            # Allow basic text formatting
            safe_commands = [
                (r"\\textbf\s*\{([^}]*)\}", r"\\textbf{\1}"),
                (r"\\textit\s*\{([^}]*)\}", r"\\textit{\1}"),
                (r"\\emph\s*\{([^}]*)\}", r"\\emph{\1}"),
                (r"\\underline\s*\{([^}]*)\}", r"\\underline{\1}"),
            ]

            for pattern, replacement in safe_commands:
                text = re.sub(pattern, replacement, text)

        return text

    @classmethod
    def sanitize_url(cls, url: str) -> str:
        """Sanitize URL for safe LaTeX compilation"""
        if not url:
            return ""

        # Basic URL validation
        if not re.match(r"^https?://", url):
            url = "https://" + url

        # Escape special characters in URLs
        return cls.sanitize_text(url, allow_basic_formatting=False)


class DataNormalizer:
    """Normalizes various data types to standard formats"""

    @staticmethod
    def normalize_date(
        date_input: Union[str, dict, None],
    ) -> Tuple[str, List[ValidationError]]:
        """
        Normalize date to YYYY-MM or YYYY-MM-DD format

        Args:
            date_input: Date in various formats

        Returns:
            Tuple of (normalized_date, validation_errors)
        """
        errors = []

        if not date_input:
            return "", errors

        if isinstance(date_input, dict):
            # Handle structured date objects
            year = date_input.get("year")
            month = date_input.get("month")
            day = date_input.get("day")

            if not year:
                errors.append(
                    ValidationError.create(
                        field_path="date.year",
                        error_code=ErrorCode.VAL001,
                        section="date object",
                    )
                )
                return "", errors

            try:
                if day:
                    normalized = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
                elif month:
                    normalized = f"{int(year):04d}-{int(month):02d}"
                else:
                    normalized = f"{int(year):04d}"
                return normalized, errors
            except (ValueError, TypeError):
                errors.append(
                    ValidationError.create(
                        field_path="date",
                        error_code=ErrorCode.VAL006,
                        original_value=date_input,
                        date=str(date_input),
                    )
                )
                return "", errors

        if isinstance(date_input, str):
            date_str = date_input.strip()

            # Handle "Present" or similar
            if date_str.lower() in ["present", "current", "now", "ongoing"]:
                return "Present", errors

            # Try various date formats
            date_patterns = [
                (
                    r"^(\d{4})-(\d{1,2})-(\d{1,2})$",
                    lambda m: f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}",
                ),
                (
                    r"^(\d{4})-(\d{1,2})$",
                    lambda m: f"{int(m.group(1)):04d}-{int(m.group(2)):02d}",
                ),
                (r"^(\d{4})$", lambda m: f"{int(m.group(1)):04d}"),
                (
                    r"^(\d{1,2})/(\d{1,2})/(\d{4})$",
                    lambda m: f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}",
                ),
                (
                    r"^(\d{1,2})/(\d{4})$",
                    lambda m: f"{int(m.group(2)):04d}-{int(m.group(1)):02d}",
                ),
                (
                    r"^(\w+)\s+(\d{4})$",
                    lambda m: DataNormalizer._parse_month_year(m.group(1), m.group(2)),
                ),
                (
                    r"^(\w+)\s+(\d{1,2}),?\s+(\d{4})$",
                    lambda m: DataNormalizer._parse_month_day_year(
                        m.group(1), m.group(2), m.group(3)
                    ),
                ),
            ]

            for pattern, formatter in date_patterns:
                match = re.match(pattern, date_str, re.IGNORECASE)
                if match:
                    try:
                        normalized = formatter(match)
                        if normalized != date_str:
                            errors.append(
                                ValidationError.create(
                                    field_path="date",
                                    error_code=ErrorCode.VAL006,
                                    severity=ErrorSeverity.INFO,
                                    original_value=date_str,
                                    corrected_value=normalized,
                                    date=normalized,
                                )
                            )
                        return normalized, errors
                    except Exception as e:
                        continue

            # If no pattern matched
            errors.append(
                ValidationError.create(
                    field_path="date",
                    error_code=ErrorCode.VAL006,
                    original_value=date_str,
                    date=date_str,
                )
            )
            return "", errors

        errors.append(
            ValidationError.create(
                field_path="date",
                error_code=ErrorCode.VAL002,
                original_value=date_input,
                expected_type="string or object",
                actual_type=type(date_input).__name__,
            )
        )
        return "", errors

    @staticmethod
    def _parse_month_year(month_str: str, year_str: str) -> str:
        """Parse month name and year to YYYY-MM format"""
        month_map = {
            "january": 1,
            "jan": 1,
            "february": 2,
            "feb": 2,
            "march": 3,
            "mar": 3,
            "april": 4,
            "apr": 4,
            "may": 5,
            "june": 6,
            "jun": 6,
            "july": 7,
            "jul": 7,
            "august": 8,
            "aug": 8,
            "september": 9,
            "sep": 9,
            "october": 10,
            "oct": 10,
            "november": 11,
            "nov": 11,
            "december": 12,
            "dec": 12,
        }

        month_num = month_map.get(month_str.lower())
        if not month_num:
            raise ValidationException(
                error_code=ErrorCode.VAL006,
                field_path="date.month",
                context={"date": month_str},
            )

        return f"{int(year_str):04d}-{month_num:02d}"

    @staticmethod
    def _parse_month_day_year(month_str: str, day_str: str, year_str: str) -> str:
        """Parse month name, day, and year to YYYY-MM-DD format"""
        month_map = {
            "january": 1,
            "jan": 1,
            "february": 2,
            "feb": 2,
            "march": 3,
            "mar": 3,
            "april": 4,
            "apr": 4,
            "may": 5,
            "june": 6,
            "jun": 6,
            "july": 7,
            "jul": 7,
            "august": 8,
            "aug": 8,
            "september": 9,
            "sep": 9,
            "october": 10,
            "oct": 10,
            "november": 11,
            "nov": 11,
            "december": 12,
            "dec": 12,
        }

        month_num = month_map.get(month_str.lower())
        if not month_num:
            raise ValidationException(
                error_code=ErrorCode.VAL006,
                field_path="date.month",
                context={"date": month_str},
            )

        return f"{int(year_str):04d}-{month_num:02d}-{int(day_str):02d}"

    @staticmethod
    def normalize_phone(phone: str) -> Tuple[str, List[ValidationError]]:
        """
        Normalize phone number to consistent format

        Args:
            phone: Phone number in various formats

        Returns:
            Tuple of (normalized_phone, validation_errors)
        """
        errors = []

        if not phone:
            return "", errors

        # Remove all non-digit characters except + at the beginning
        original_phone = phone
        phone_clean = re.sub(r"[^\d+]", "", phone)

        # Handle international format
        if phone_clean.startswith("+"):
            # Keep international format
            if len(phone_clean) < 8:
                errors.append(
                    ValidationError(
                        field_path="phone",
                        error_type="invalid_format",
                        message="Phone number too short",
                        severity="error",
                        original_value=original_phone,
                    )
                )
                return original_phone, errors

            # Format international number
            normalized = (
                phone_clean[:2] + " " + phone_clean[2:]
            )  # +1 1234567890 -> +1 1234567890
            if len(phone_clean) == 12 and phone_clean.startswith("+1"):  # US format
                normalized = (
                    f"+1 ({phone_clean[2:5]}) {phone_clean[5:8]}-{phone_clean[8:]}"
                )
        else:
            # Handle US domestic format
            digits_only = re.sub(r"\D", "", phone)

            if len(digits_only) == 10:
                # Format as (XXX) XXX-XXXX
                normalized = f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
            elif len(digits_only) == 11 and digits_only.startswith("1"):
                # Format as +1 (XXX) XXX-XXXX
                normalized = (
                    f"+1 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
                )
            elif len(digits_only) == 7:
                # Format as XXX-XXXX
                normalized = f"{digits_only[:3]}-{digits_only[3:]}"
            else:
                errors.append(
                    ValidationError(
                        field_path="phone",
                        error_type="invalid_format",
                        message=f"Unrecognized phone format: '{original_phone}'. Expected 10 digits for US numbers.",
                        severity="warning",
                        original_value=original_phone,
                        suggested_fix="Use format like '(555) 123-4567' or '+1 (555) 123-4567'",
                    )
                )
                return original_phone, errors

        if normalized != original_phone:
            errors.append(
                ValidationError(
                    field_path="phone",
                    error_type="format_normalized",
                    message=f"Phone format normalized from '{original_phone}' to '{normalized}'",
                    severity="info",
                    original_value=original_phone,
                    corrected_value=normalized,
                )
            )

        return normalized, errors

    @staticmethod
    def normalize_url(url: str) -> Tuple[str, List[ValidationError]]:
        """
        Normalize URL to standard format

        Args:
            url: URL in various formats

        Returns:
            Tuple of (normalized_url, validation_errors)
        """
        errors = []

        if not url:
            return "", errors

        original_url = url.strip()

        # Add protocol if missing
        if not re.match(r"^https?://", original_url, re.IGNORECASE):
            url = "https://" + original_url
            errors.append(
                ValidationError(
                    field_path="url",
                    error_type="format_normalized",
                    message=f"Added https:// protocol to URL",
                    severity="info",
                    original_value=original_url,
                    corrected_value=url,
                )
            )

        # Basic URL validation
        try:
            parsed = urllib.parse.urlparse(url)
            if not parsed.netloc:
                errors.append(
                    ValidationError(
                        field_path="url",
                        error_type="invalid_format",
                        message=f"Invalid URL format: '{original_url}'",
                        severity="error",
                        original_value=original_url,
                    )
                )
                return original_url, errors
        except Exception:
            errors.append(
                ValidationError(
                    field_path="url",
                    error_type="invalid_format",
                    message=f"Invalid URL format: '{original_url}'",
                    severity="error",
                    original_value=original_url,
                )
            )
            return original_url, errors

        return url, errors

    @staticmethod
    def normalize_email(email: str) -> Tuple[str, List[ValidationError]]:
        """
        Normalize email address

        Args:
            email: Email address

        Returns:
            Tuple of (normalized_email, validation_errors)
        """
        errors = []

        if not email:
            return "", errors

        original_email = email.strip()
        normalized_email = original_email.lower()

        # Basic email validation
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, normalized_email):
            errors.append(
                ValidationError(
                    field_path="email",
                    error_type="invalid_format",
                    message=f"Invalid email format: '{original_email}'",
                    severity="error",
                    original_value=original_email,
                    suggested_fix="Use format like 'user@domain.com'",
                )
            )
            return original_email, errors

        if normalized_email != original_email:
            errors.append(
                ValidationError(
                    field_path="email",
                    error_type="format_normalized",
                    message=f"Email normalized to lowercase",
                    severity="info",
                    original_value=original_email,
                    corrected_value=normalized_email,
                )
            )

        return normalized_email, errors


class ResumeValidator:
    """Enhanced validator for resume JSON data"""

    def __init__(self, validation_level: ValidationLevel = ValidationLevel.LENIENT):
        """
        Initialize validator

        Args:
            validation_level: How strict to be with validation
        """
        self.validation_level = validation_level
        self.sanitizer = LaTeXSanitizer()
        self.normalizer = DataNormalizer()

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate and normalize resume data

        Args:
            data: Resume data to validate

        Returns:
            ValidationResult with errors, warnings, and normalized data
        """
        errors = []
        warnings = []
        normalized_data = {}

        try:
            # Deep copy the data to avoid modifying original
            import copy

            working_data = copy.deepcopy(data)

            # Validate required sections
            errors.extend(self._validate_required_fields(working_data))

            # Process and normalize each section
            normalized_data = self._process_sections(working_data, errors, warnings)

            # Apply LaTeX sanitization
            normalized_data = self._sanitize_all_text(normalized_data)

            # Determine if validation passed
            is_valid = len([e for e in errors if e.severity == "error"]) == 0

            if self.validation_level == ValidationLevel.STRICT:
                is_valid = is_valid and len(warnings) == 0

            return ValidationResult(
                is_valid=is_valid,
                errors=[e for e in errors if e.severity == "error"],
                warnings=[e for e in errors if e.severity == "warning"] + warnings,
                normalized_data=normalized_data,
                metadata={
                    "validation_level": self.validation_level.value,
                    "total_issues": len(errors) + len(warnings),
                    "normalization_applied": True,
                    "latex_sanitization_applied": True,
                },
            )

        except Exception as e:
            logger.exception("Unexpected error during validation")
            return ValidationResult(
                is_valid=False,
                errors=[
                    ValidationError(
                        field_path="root",
                        error_type="validation_error",
                        message=f"Unexpected validation error: {str(e)}",
                        severity="error",
                    )
                ],
                warnings=[],
                normalized_data=data,
                metadata={"validation_failed": True},
            )

    def _validate_required_fields(self, data: Dict[str, Any]) -> List[ValidationError]:
        """Validate required fields are present"""
        errors = []

        # Check for personalInfo section
        if "personalInfo" not in data:
            errors.append(
                ValidationError(
                    field_path="personalInfo",
                    error_type="missing_required",
                    message="personalInfo section is required",
                    severity="error",
                    suggested_fix="Add personalInfo object with at least name and email",
                )
            )
            return errors

        personal_info = data["personalInfo"]
        if not isinstance(personal_info, dict):
            errors.append(
                ValidationError(
                    field_path="personalInfo",
                    error_type="invalid_type",
                    message="personalInfo must be an object",
                    severity="error",
                    original_value=type(personal_info).__name__,
                )
            )
            return errors

        # Check required fields in personalInfo
        required_fields = ["name", "email"]
        for field in required_fields:
            if field not in personal_info or not personal_info[field]:
                errors.append(
                    ValidationError(
                        field_path=f"personalInfo.{field}",
                        error_type="missing_required",
                        message=f"{field} is required in personalInfo",
                        severity="error",
                        suggested_fix=f"Add {field} field to personalInfo",
                    )
                )

        return errors

    def _process_sections(
        self,
        data: Dict[str, Any],
        errors: List[ValidationError],
        warnings: List[ValidationError],
    ) -> Dict[str, Any]:
        """Process and normalize all sections"""
        normalized = {}

        # Process personalInfo
        if "personalInfo" in data:
            normalized["personalInfo"] = self._process_personal_info(
                data["personalInfo"], errors, warnings
            )

        # Process experience section
        if "experience" in data:
            normalized["experience"] = self._process_experience(
                data["experience"], errors, warnings
            )

        # Process education section
        if "education" in data:
            normalized["education"] = self._process_education(
                data["education"], errors, warnings
            )

        # Process other sections with basic text sanitization
        for section_name in data:
            if section_name not in ["personalInfo", "experience", "education"]:
                normalized[section_name] = self._process_generic_section(
                    data[section_name], f"{section_name}", errors, warnings
                )

        return normalized

    def _process_personal_info(
        self,
        personal_info: Dict[str, Any],
        errors: List[ValidationError],
        warnings: List[ValidationError],
    ) -> Dict[str, Any]:
        """Process and normalize personal information"""
        normalized = {}

        for field, value in personal_info.items():
            if field == "email":
                normalized_value, field_errors = self.normalizer.normalize_email(value)
                self._add_field_errors(
                    field_errors, f"personalInfo.{field}", errors, warnings
                )
                normalized[field] = normalized_value
            elif field in ["website", "linkedin"]:
                normalized_value, field_errors = self.normalizer.normalize_url(value)
                self._add_field_errors(
                    field_errors, f"personalInfo.{field}", errors, warnings
                )
                normalized[field] = normalized_value
            elif field == "phone":
                normalized_value, field_errors = self.normalizer.normalize_phone(value)
                self._add_field_errors(
                    field_errors, f"personalInfo.{field}", errors, warnings
                )
                normalized[field] = normalized_value
            else:
                # Basic text fields
                normalized[field] = str(value) if value else ""

        return normalized

    def _process_experience(
        self,
        experience: List[Dict[str, Any]],
        errors: List[ValidationError],
        warnings: List[ValidationError],
    ) -> List[Dict[str, Any]]:
        """Process and normalize experience section"""
        if not isinstance(experience, list):
            errors.append(
                ValidationError(
                    field_path="experience",
                    error_type="invalid_type",
                    message="experience must be an array",
                    severity="error",
                    original_value=type(experience).__name__,
                )
            )
            return []

        normalized = []
        for i, exp in enumerate(experience):
            if not isinstance(exp, dict):
                errors.append(
                    ValidationError(
                        field_path=f"experience[{i}]",
                        error_type="invalid_type",
                        message="experience item must be an object",
                        severity="error",
                        original_value=type(exp).__name__,
                    )
                )
                continue

            normalized_exp = {}
            for field, value in exp.items():
                if field in ["startDate", "endDate"]:
                    normalized_value, field_errors = self.normalizer.normalize_date(
                        value
                    )
                    self._add_field_errors(
                        field_errors, f"experience[{i}].{field}", errors, warnings
                    )
                    normalized_exp[field] = normalized_value
                else:
                    normalized_exp[field] = value

            normalized.append(normalized_exp)

        return normalized

    def _process_education(
        self,
        education: List[Dict[str, Any]],
        errors: List[ValidationError],
        warnings: List[ValidationError],
    ) -> List[Dict[str, Any]]:
        """Process and normalize education section"""
        if not isinstance(education, list):
            errors.append(
                ValidationError(
                    field_path="education",
                    error_type="invalid_type",
                    message="education must be an array",
                    severity="error",
                    original_value=type(education).__name__,
                )
            )
            return []

        normalized = []
        for i, edu in enumerate(education):
            if not isinstance(edu, dict):
                errors.append(
                    ValidationError(
                        field_path=f"education[{i}]",
                        error_type="invalid_type",
                        message="education item must be an object",
                        severity="error",
                        original_value=type(edu).__name__,
                    )
                )
                continue

            normalized_edu = {}
            for field, value in edu.items():
                if field in ["startDate", "endDate", "graduationDate"]:
                    normalized_value, field_errors = self.normalizer.normalize_date(
                        value
                    )
                    self._add_field_errors(
                        field_errors, f"education[{i}].{field}", errors, warnings
                    )
                    normalized_edu[field] = normalized_value
                else:
                    normalized_edu[field] = value

            normalized.append(normalized_edu)

        return normalized

    def _process_generic_section(
        self,
        section_data: Any,
        section_path: str,
        errors: List[ValidationError],
        warnings: List[ValidationError],
    ) -> Any:
        """Process generic sections with basic validation"""
        # This method handles other sections like skills, projects, etc.
        # For now, just return as-is, but this can be extended
        return section_data

    def _add_field_errors(
        self,
        field_errors: List[ValidationError],
        field_path: str,
        errors: List[ValidationError],
        warnings: List[ValidationError],
    ) -> None:
        """Add field errors to appropriate lists"""
        for error in field_errors:
            error.field_path = field_path
            if error.severity == "error":
                errors.append(error)
            else:
                warnings.append(error)

    def _sanitize_all_text(self, data: Any, path: str = "") -> Any:
        """Recursively sanitize all text in the data structure"""
        if isinstance(data, dict):
            return {
                key: self._sanitize_all_text(value, f"{path}.{key}" if path else key)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [
                self._sanitize_all_text(item, f"{path}[{i}]")
                for i, item in enumerate(data)
            ]
        elif isinstance(data, str):
            # Apply LaTeX sanitization
            return self.sanitizer.sanitize_text(data)
        else:
            return data


def validate_resume_data(
    data: Dict[str, Any], validation_level: ValidationLevel = ValidationLevel.LENIENT
) -> ValidationResult:
    """
    Convenience function to validate resume data

    Args:
        data: Resume data to validate
        validation_level: Validation strictness level

    Returns:
        ValidationResult
    """
    validator = ResumeValidator(validation_level)
    return validator.validate(data)
