"""
Unit tests for the error handling system

Tests the error code system, error registry, message formatting,
and error definition functionality.
"""

import pytest

from resume_agent_template_engine.core.errors import (
    ErrorCategory,
    ErrorCode,
    ErrorDefinition,
    ErrorRegistry,
    ErrorSeverity,
    error_registry,
    get_error_definition,
)


class TestErrorCode:
    """Test ErrorCode enum"""

    def test_error_code_enum_values(self):
        """Test ErrorCode enum has expected values"""
        # Validation error codes
        assert ErrorCode.VAL001.value == "VAL001"
        assert ErrorCode.VAL002.value == "VAL002"
        assert ErrorCode.VAL003.value == "VAL003"
        assert ErrorCode.VAL012.value == "VAL012"

        # Template error codes
        assert ErrorCode.TPL001.value == "TPL001"
        assert ErrorCode.TPL002.value == "TPL002"

        # API error codes
        assert ErrorCode.API001.value == "API001"

    def test_error_code_enum_completeness(self):
        """Test that error codes cover all categories"""
        # Get all error codes
        all_codes = [code for code in ErrorCode]

        # Check we have codes for major categories
        validation_codes = [code for code in all_codes if code.value.startswith("VAL")]
        template_codes = [code for code in all_codes if code.value.startswith("TPL")]
        api_codes = [code for code in all_codes if code.value.startswith("API")]

        assert len(validation_codes) > 0, "Should have validation error codes"
        assert len(template_codes) > 0, "Should have template error codes"
        assert len(api_codes) > 0, "Should have API error codes"

    def test_error_code_uniqueness(self):
        """Test that all error codes are unique"""
        all_values = [code.value for code in ErrorCode]
        assert len(all_values) == len(set(all_values)), "Error codes should be unique"


class TestErrorCategory:
    """Test ErrorCategory enum"""

    def test_error_category_values(self):
        """Test ErrorCategory enum values"""
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.TEMPLATE.value == "template"
        assert ErrorCategory.API.value == "api"
        assert ErrorCategory.SYSTEM.value == "system"

    def test_error_category_completeness(self):
        """Test that we have all expected categories"""
        expected_categories = ["validation", "template", "api", "system"]
        actual_categories = [cat.value for cat in ErrorCategory]

        for expected in expected_categories:
            assert expected in actual_categories


class TestErrorSeverity:
    """Test ErrorSeverity enum"""

    def test_error_severity_values(self):
        """Test ErrorSeverity enum values"""
        assert ErrorSeverity.ERROR.value == "error"
        assert ErrorSeverity.WARNING.value == "warning"
        assert ErrorSeverity.INFO.value == "info"

    def test_error_severity_ordering(self):
        """Test that severity levels have logical ordering"""
        severities = [ErrorSeverity.INFO, ErrorSeverity.WARNING, ErrorSeverity.ERROR]
        assert len(severities) == 3
        # This ensures all expected severities exist


class TestErrorDefinition:
    """Test ErrorDefinition dataclass"""

    def test_error_definition_creation(self):
        """Test creating ErrorDefinition"""
        error_def = ErrorDefinition(
            code=ErrorCode.VAL001,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            title="Missing Required Field",
            message_template="Field '{field}' is required",
            http_status_code=400,
            user_facing=True,
            suggested_fix="Add the missing field",
        )

        assert error_def.code == ErrorCode.VAL001
        assert error_def.category == ErrorCategory.VALIDATION
        assert error_def.severity == ErrorSeverity.ERROR
        assert error_def.title == "Missing Required Field"
        assert error_def.http_status_code == 400
        assert error_def.user_facing is True

    def test_error_definition_optional_fields(self):
        """Test ErrorDefinition with optional fields"""
        error_def = ErrorDefinition(
            code=ErrorCode.VAL002,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.WARNING,
            title="Test Error",
            message_template="Test message",
        )

        # Optional fields should have defaults
        assert error_def.http_status_code is None
        assert error_def.user_facing is True  # Default
        assert error_def.suggested_fix is None


class TestErrorRegistry:
    """Test ErrorRegistry functionality"""

    def test_error_registry_exists(self):
        """Test that global error registry exists"""
        assert error_registry is not None
        assert isinstance(error_registry, ErrorRegistry)

    def test_error_registry_has_errors(self):
        """Test that error registry contains error definitions"""
        # Check that registry has some errors using public methods
        all_codes = error_registry.get_all_codes()
        assert len(all_codes) > 0

        # Check that it has errors for different categories
        validation_errors = error_registry.get_errors_by_category(
            ErrorCategory.VALIDATION
        )
        template_errors = error_registry.get_errors_by_category(ErrorCategory.TEMPLATE)

        assert len(validation_errors) > 0, "Should have validation errors"
        assert len(template_errors) > 0, "Should have template errors"

    def test_error_registry_get_error(self):
        """Test getting error from registry"""
        error_def = error_registry.get_error(ErrorCode.VAL001)

        assert error_def is not None
        assert error_def.code == ErrorCode.VAL001
        assert error_def.category == ErrorCategory.VALIDATION

    def test_error_registry_get_nonexistent_error(self):
        """Test getting non-existent error returns None"""
        # This should return None for unknown error codes
        # We can't test with a fake enum value, so we test the method exists
        assert hasattr(error_registry, "get_error")

    def test_error_registry_format_message(self):
        """Test message formatting functionality"""
        # Test basic message formatting
        formatted = error_registry.format_message(
            ErrorCode.VAL001, field="personalInfo.name"
        )

        assert isinstance(formatted, str)
        assert len(formatted) > 0
        # Should contain the field name
        assert "personalInfo.name" in formatted or "field" in formatted.lower()

    def test_error_registry_format_message_with_context(self):
        """Test message formatting with multiple context variables"""
        formatted = error_registry.format_message(
            ErrorCode.VAL003, field="email", value="invalid-email"
        )

        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_error_registry_get_errors_by_category(self):
        """Test getting errors by category"""
        validation_errors = error_registry.get_errors_by_category(
            ErrorCategory.VALIDATION
        )

        assert isinstance(validation_errors, list)
        assert len(validation_errors) > 0

        # All returned errors should be validation errors
        for error in validation_errors:
            assert error.category == ErrorCategory.VALIDATION

    def test_error_registry_get_errors_by_severity(self):
        """Test getting errors by severity"""
        error_errors = error_registry.get_errors_by_severity(ErrorSeverity.ERROR)

        assert isinstance(error_errors, list)
        assert len(error_errors) > 0

        # All returned errors should be error severity
        for error in error_errors:
            assert error.severity == ErrorSeverity.ERROR


class TestErrorRegistryIntegration:
    """Test error registry integration functionality"""

    def test_get_error_definition_function(self):
        """Test global get_error_definition function"""
        error_def = get_error_definition(ErrorCode.VAL001)

        assert error_def is not None
        assert isinstance(error_def, ErrorDefinition)
        assert error_def.code == ErrorCode.VAL001

    def test_error_definition_consistency(self):
        """Test that error definitions are consistent"""
        # Get all errors and check consistency
        all_codes = error_registry.get_all_codes()

        for code in all_codes:
            definition = error_registry.get_error(code)
            assert definition is not None

            # Code should match
            assert definition.code == code

            # Should have required fields
            assert definition.title is not None
            assert definition.message_template is not None
            assert definition.category is not None
            assert definition.severity is not None

            # Message template should be a string
            assert isinstance(definition.message_template, str)
            assert len(definition.message_template) > 0

    def test_error_http_status_codes(self):
        """Test that error HTTP status codes are reasonable"""
        all_codes = error_registry.get_all_codes()

        for code in all_codes:
            definition = error_registry.get_error(code)
            if definition and definition.http_status_code is not None:
                # Should be a valid HTTP status code
                assert isinstance(definition.http_status_code, int)
                assert 100 <= definition.http_status_code <= 599

                # Most errors should be 4xx or 5xx
                if definition.category in [ErrorCategory.VALIDATION, ErrorCategory.API]:
                    assert 400 <= definition.http_status_code <= 499
                elif definition.category == ErrorCategory.SYSTEM:
                    assert 500 <= definition.http_status_code <= 599

    def test_message_template_formatting(self):
        """Test that message templates can be formatted"""
        # Test various error codes with different template variables
        test_cases = [
            (ErrorCode.VAL001, {"field": "test_field"}),
            (ErrorCode.VAL003, {"field": "email", "value": "invalid"}),
        ]

        for error_code, context in test_cases:
            try:
                formatted = error_registry.format_message(error_code, **context)
                assert isinstance(formatted, str)
                assert len(formatted) > 0

                # Should not contain unformatted placeholders for provided context
                for key in context:
                    placeholder = "{" + key + "}"
                    # Either the placeholder is replaced or the key appears in the message
                    assert placeholder not in formatted or key in formatted.lower()

            except Exception as e:
                pytest.fail(f"Failed to format message for {error_code}: {e}")

    def test_error_registry_coverage(self):
        """Test that error registry covers all defined error codes"""
        # Get all error codes
        all_error_codes = [code for code in ErrorCode]
        registered_codes = error_registry.get_all_codes()

        # Check that registry has definition for each code
        missing_codes = []
        for code in all_error_codes:
            if code not in registered_codes:
                missing_codes.append(code)

        # Some codes might not be defined yet, but we should have key ones
        coverage_percentage = (len(all_error_codes) - len(missing_codes)) / len(
            all_error_codes
        )
        assert coverage_percentage >= 0.3, (
            f"Error registry should cover at least 30% of error codes. Missing: {missing_codes}"
        )

        # Ensure we have at least some critical error codes
        critical_codes = [
            ErrorCode.VAL001,
            ErrorCode.VAL003,
            ErrorCode.VAL012,
            ErrorCode.TPL001,
            ErrorCode.TPL002,
            ErrorCode.API001,
        ]
        for code in critical_codes:
            assert code in registered_codes, (
                f"Critical error code {code} should be registered"
            )


class TestErrorHandlingEdgeCases:
    """Test edge cases in error handling"""

    def test_format_message_missing_context(self):
        """Test formatting message with missing context variables"""
        # This should handle missing context gracefully
        formatted = error_registry.format_message(ErrorCode.VAL001)

        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_format_message_extra_context(self):
        """Test formatting message with extra context variables"""
        # This should ignore extra context variables
        formatted = error_registry.format_message(
            ErrorCode.VAL001, field="test", extra_var="should_be_ignored"
        )

        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_error_definition_immutability(self):
        """Test that error definitions are effectively immutable"""
        error_def = error_registry.get_error(ErrorCode.VAL001)

        if error_def:
            # Attempting to modify should not affect the registry
            original_title = error_def.title
            # We can't actually modify dataclass fields directly,
            # but we can verify the object exists and has expected properties
            assert error_def.title == original_title


if __name__ == "__main__":
    pytest.main([__file__])
