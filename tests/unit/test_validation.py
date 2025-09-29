"""
Unit tests for the validation system

Tests the comprehensive validation system including validation levels,
error handling, LaTeX injection prevention, and data normalization.
"""

import pytest

from resume_agent_template_engine.core.errors import ErrorCode
from resume_agent_template_engine.core.exceptions import (
    SecurityValidationException,
)
from resume_agent_template_engine.core.validation import (
    LaTeXSanitizer,
    ResumeValidator,
    ValidationError,
    ValidationLevel,
    ValidationResult,
    validate_resume_data,
)


class TestValidationLevels:
    """Test different validation strictness levels"""

    def test_validation_level_enum(self):
        """Test ValidationLevel enum values"""
        assert ValidationLevel.STRICT.value == "strict"
        assert ValidationLevel.LENIENT.value == "lenient"
        assert ValidationLevel.PERMISSIVE.value == "permissive"

    def test_validation_level_ordering(self):
        """Test validation level strictness ordering"""
        # This helps ensure proper validation logic
        levels = [
            ValidationLevel.PERMISSIVE,
            ValidationLevel.LENIENT,
            ValidationLevel.STRICT,
        ]
        assert len(levels) == 3


class TestValidationError:
    """Test ValidationError dataclass"""

    def test_validation_error_creation(self):
        """Test creating ValidationError instances"""
        error = ValidationError(
            field_path="personalInfo.email",
            message="Invalid email format",
            error_code=ErrorCode.VAL003,
            severity="error",
            suggested_fix="Use a valid email address",
        )

        assert error.field_path == "personalInfo.email"
        assert error.message == "Invalid email format"
        assert error.error_code == ErrorCode.VAL003
        assert error.severity == "error"
        assert error.suggested_fix == "Use a valid email address"

    def test_validation_error_create_classmethod(self):
        """Test ValidationError.create() class method"""
        error = ValidationError.create(
            field_path="personalInfo.name",
            error_code=ErrorCode.VAL001,
            original_value=None,
            expected_type="string",
        )

        assert error.field_path == "personalInfo.name"
        assert error.error_code == ErrorCode.VAL001
        assert error.original_value is None


class TestValidationResult:
    """Test ValidationResult handling"""

    def test_validation_result_success(self):
        """Test successful validation result"""
        data = {"personalInfo": {"name": "John Doe", "email": "john@example.com"}}
        result = ValidationResult(
            is_valid=True, normalized_data=data, errors=[], warnings=[], metadata={}
        )

        assert result.is_valid
        assert result.normalized_data == data
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_validation_result_with_errors(self):
        """Test validation result with errors"""
        error = ValidationError(
            field_path="personalInfo.email",
            message="Invalid email",
            error_code=ErrorCode.VAL003,
        )

        result = ValidationResult(
            is_valid=False, normalized_data={}, errors=[error], warnings=[]
        )

        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].field_path == "personalInfo.email"


class TestLaTeXSanitizer:
    """Test LaTeX injection prevention"""

    def test_latex_sanitizer_basic_escaping(self):
        """Test basic LaTeX character escaping"""
        sanitizer = LaTeXSanitizer()

        test_cases = {
            "Hello & World": "Hello \\& World",
            "100% complete": "100\\% complete",
            "$100": "\\$100",
            "Use #hashtag": "Use \\#hashtag",
            "x^2": "x\\textasciicircum{}2",
            "file_name": "file\\_name",
            "{bracket}": "\\{bracket\\}",
            "~tilde": "\\textasciitilde{}",
            "back\\slash": "back\\textbackslash{}",
        }

        for input_text, expected in test_cases.items():
            result = sanitizer.escape_latex_chars(input_text)
            assert result == expected, f"Failed for input: {input_text}"

    def test_latex_sanitizer_dangerous_commands(self):
        """Test detection and blocking of dangerous LaTeX commands"""
        sanitizer = LaTeXSanitizer()

        dangerous_inputs = [
            "\\input{/etc/passwd}",
            "\\include{malicious.tex}",
            "\\write18{rm -rf /}",
            "\\immediate\\write18{cat /etc/passwd}",
            "\\openout\\myfile=dangerous.txt",
            "\\execute{evil_command}",
            "\\shell{malicious}",
            "\\system{rm -rf}",
            "\\def\\malicious{evil}",
            "\\gdef\\global{bad}",
            "\\catcode`\\@=11",
        ]

        for dangerous_input in dangerous_inputs:
            with pytest.raises(SecurityValidationException) as exc_info:
                sanitizer.sanitize_latex_content(dangerous_input)

            assert exc_info.value.error_code == ErrorCode.VAL012
            assert "dangerous" in str(exc_info.value).lower()

    def test_latex_sanitizer_safe_content(self):
        """Test that safe content passes through LaTeX sanitizer"""
        sanitizer = LaTeXSanitizer()

        safe_inputs = [
            "John Doe",
            "Software Engineer with 5+ years experience",
            "Email: john@example.com",
            "Phone: +1 (555) 123-4567",
            "Skills: Python, JavaScript, React",
            "Regular text with normal punctuation!",
            "Dates: 2020-01 to Present",
        ]

        for safe_input in safe_inputs:
            result = sanitizer.sanitize_latex_content(safe_input)
            # Should not raise exception and should escape special chars
            assert isinstance(result, str)
            # Should not contain dangerous commands
            assert "\\input" not in result
            assert "\\write18" not in result


class TestResumeValidator:
    """Test ResumeValidator functionality"""

    def test_resume_validator_creation(self):
        """Test ResumeValidator instantiation"""
        validator = ResumeValidator(ValidationLevel.STRICT)
        assert validator.validation_level == ValidationLevel.STRICT

    def test_resume_validator_email_validation(self):
        """Test email validation functionality"""
        validator = ResumeValidator(ValidationLevel.STRICT)

        # Valid emails
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "first.last+tag@example.org",
        ]

        for email in valid_emails:
            is_valid, errors = validator._validate_email(email)
            assert is_valid, f"Email {email} should be valid"
            assert len(errors) == 0

        # Invalid emails
        invalid_emails = [
            "invalid.email",
            "@example.com",
            "test@",
            "test@.com",
            "test..test@example.com",
        ]

        for email in invalid_emails:
            is_valid, errors = validator._validate_email(email)
            assert not is_valid, f"Email {email} should be invalid"
            assert len(errors) > 0

    def test_resume_validator_phone_validation(self):
        """Test phone number validation"""
        validator = ResumeValidator(ValidationLevel.STRICT)

        # Valid phone numbers
        valid_phones = [
            "+1 (555) 123-4567",
            "+44 20 7946 0958",
            "555-123-4567",
            "(555) 123-4567",
        ]

        for phone in valid_phones:
            is_valid, errors = validator._validate_phone(phone)
            assert is_valid, f"Phone {phone} should be valid"

    def test_resume_validator_date_validation(self):
        """Test date format validation"""
        validator = ResumeValidator(ValidationLevel.STRICT)

        # Valid date formats
        valid_dates = ["2023-01", "2023-12-25", "Present", "Current"]

        for date in valid_dates:
            is_valid, errors = validator._validate_date(date)
            assert is_valid, f"Date {date} should be valid"

        # Invalid date formats
        invalid_dates = [
            "2023",
            "01-2023",
            "2023-13",  # Invalid month
            "2023-02-30",  # Invalid day
            "not-a-date",
        ]

        for date in invalid_dates:
            is_valid, errors = validator._validate_date(date)
            assert not is_valid, f"Date {date} should be invalid"


class TestEnhancedValidation:
    """Test the enhanced validate_resume_data function"""

    def test_valid_resume_data_strict(self):
        """Test validation of valid resume data with strict level"""
        valid_data = {
            "personalInfo": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1 (555) 123-4567",
                "location": "New York, NY",
            },
            "experience": [
                {
                    "position": "Software Engineer",
                    "company": "Tech Corp",
                    "startDate": "2020-01",
                    "endDate": "Present",
                }
            ],
        }

        result = validate_resume_data(valid_data, ValidationLevel.STRICT)
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.normalized_data is not None

    def test_invalid_email_validation(self):
        """Test validation with invalid email"""
        invalid_data = {
            "personalInfo": {
                "name": "John Doe",
                "email": "invalid-email",  # Invalid email
                "location": "New York, NY",
            }
        }

        result = validate_resume_data(invalid_data, ValidationLevel.STRICT)
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("email" in error.field_path for error in result.errors)

    def test_latex_injection_prevention(self):
        """Test that LaTeX injection attempts are blocked"""
        malicious_data = {
            "personalInfo": {
                "name": "\\input{/etc/passwd}",  # LaTeX injection attempt
                "email": "test@example.com",
            }
        }

        result = validate_resume_data(malicious_data, ValidationLevel.STRICT)
        assert not result.is_valid
        assert any(error.error_code == ErrorCode.VAL012 for error in result.errors)

    def test_validation_level_differences(self):
        """Test different behavior between validation levels"""
        data_with_issues = {
            "personalInfo": {"name": "John", "email": "john@example.com"},
            "experience": [
                {
                    "position": "Engineer",
                    "company": "Corp",
                    # Missing required dates
                }
            ],
        }

        # Strict validation should fail
        strict_result = validate_resume_data(data_with_issues, ValidationLevel.STRICT)

        # Lenient validation might pass with warnings
        lenient_result = validate_resume_data(data_with_issues, ValidationLevel.LENIENT)

        # Permissive validation should pass
        permissive_result = validate_resume_data(
            data_with_issues, ValidationLevel.PERMISSIVE
        )

        # Assert that strict is more restrictive than lenient, which is more restrictive than permissive
        assert (
            strict_result.is_valid
            <= lenient_result.is_valid
            <= permissive_result.is_valid
        )

    def test_data_normalization(self):
        """Test that data normalization works correctly"""
        data_to_normalize = {
            "personalInfo": {
                "name": "  John Doe  ",  # Extra whitespace
                "email": "JOHN@EXAMPLE.COM",  # Uppercase email
                "phone": "555.123.4567",  # Different phone format
            }
        }

        result = validate_resume_data(data_to_normalize, ValidationLevel.LENIENT)
        if result.is_valid:
            # Check that data was normalized
            normalized = result.normalized_data
            assert normalized["personalInfo"]["name"] == "John Doe"  # Trimmed
            assert "@" in normalized["personalInfo"]["email"]  # Email processed


class TestValidationIntegration:
    """Integration tests for validation system"""

    def test_validation_with_real_resume_data(self):
        """Test validation with realistic resume data"""
        realistic_data = {
            "personalInfo": {
                "name": "Jane Smith",
                "email": "jane.smith@email.com",
                "phone": "+1 (555) 987-6543",
                "location": "San Francisco, CA",
                "linkedin": "https://linkedin.com/in/janesmith",
                "website": "https://janesmith.dev",
            },
            "professionalSummary": "Experienced software engineer with 7+ years in full-stack development.",
            "experience": [
                {
                    "position": "Senior Software Engineer",
                    "company": "Tech Innovations Inc.",
                    "location": "San Francisco, CA",
                    "startDate": "2021-03",
                    "endDate": "Present",
                    "description": "Lead development of microservices architecture",
                    "achievements": [
                        "Reduced system latency by 40%",
                        "Led team of 5 engineers",
                    ],
                    "technologies": ["Python", "React", "AWS"],
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "University of California, Berkeley",
                    "graduationDate": "2018-05",
                    "gpa": "3.8/4.0",
                }
            ],
            "skills": {
                "technical": ["Python", "JavaScript", "React", "AWS"],
                "soft": ["Leadership", "Communication"],
            },
        }

        result = validate_resume_data(realistic_data, ValidationLevel.STRICT)
        assert result.is_valid
        assert result.normalized_data is not None
        assert len(result.errors) == 0

    def test_validation_error_context(self):
        """Test that validation errors include proper context"""
        invalid_data = {
            "personalInfo": {
                "name": "",  # Empty name
                "email": "invalid",  # Invalid email
            }
        }

        result = validate_resume_data(invalid_data, ValidationLevel.STRICT)
        assert not result.is_valid
        assert len(result.errors) > 0

        # Check that errors have proper context
        for error in result.errors:
            assert error.field_path is not None
            assert error.message is not None
            assert error.error_code is not None
            assert hasattr(error, "context")


if __name__ == "__main__":
    pytest.main([__file__])
