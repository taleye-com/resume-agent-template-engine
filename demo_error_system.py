#!/usr/bin/env python3
"""
Demo script showcasing the new standardized error registry and format system
"""

import json
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from resume_agent_template_engine.core.errors import (
    ErrorCode, ErrorCategory, ErrorSeverity, error_registry
)
from resume_agent_template_engine.core.exceptions import (
    ValidationException, TemplateNotFoundException, APIException,
    create_validation_error, create_template_error, create_api_error
)
from resume_agent_template_engine.core.responses import (
    ErrorResponse, ResponseFormatter, create_error_response
)


def demo_error_registry():
    """Demo the centralized error registry"""
    print("=== Error Registry Demo ===\n")

    print("📋 Available Error Categories:")
    for category in ErrorCategory:
        errors = error_registry.get_errors_by_category(category)
        print(f"  {category.value}: {len(errors)} errors")

    print(f"\n🔢 Total Error Codes: {len(error_registry.get_all_codes())}")

    print("\n📊 Error Codes by Severity:")
    for severity in ErrorSeverity:
        errors = error_registry.get_errors_by_severity(severity)
        print(f"  {severity.value}: {len(errors)} errors")

    print("\n🔍 Sample Error Definitions:")
    sample_codes = [ErrorCode.VAL001, ErrorCode.TPL001, ErrorCode.API001, ErrorCode.SYS001]

    for code in sample_codes:
        error_def = error_registry.get_error(code)
        print(f"\n  {code.value}:")
        print(f"    Title: {error_def.title}")
        print(f"    Category: {error_def.category.value}")
        print(f"    Severity: {error_def.severity.value}")
        print(f"    HTTP Status: {error_def.http_status_code}")
        print(f"    Message: {error_def.message_template}")
        if error_def.suggested_fix:
            print(f"    Fix: {error_def.suggested_fix}")


def demo_error_formatting():
    """Demo error message formatting with context"""
    print("\n=== Error Message Formatting Demo ===\n")

    test_cases = [
        (ErrorCode.VAL001, {"field": "name", "section": "personalInfo"}),
        (ErrorCode.VAL003, {"email": "invalid-email"}),
        (ErrorCode.VAL006, {"date": "2023-13-45"}),
        (ErrorCode.TPL001, {"template": "nonexistent", "document_type": "resume", "available_templates": "classic, modern"}),
        (ErrorCode.API003, {"parameter": "format", "value": "docx"}),
    ]

    for error_code, context in test_cases:
        formatted_message = error_registry.format_message(error_code, **context)
        error_def = error_registry.get_error(error_code)

        print(f"🔸 {error_code.value} ({error_def.title}):")
        print(f"   Template: {error_def.message_template}")
        print(f"   Context: {context}")
        print(f"   Result: {formatted_message}")
        print()


def demo_exception_hierarchy():
    """Demo the custom exception hierarchy"""
    print("=== Exception Hierarchy Demo ===\n")

    print("🏗️ Creating Different Exception Types:\n")

    # Validation Exception
    try:
        raise ValidationException(
            ErrorCode.VAL003,
            field_path="personalInfo.email",
            field_value="invalid-email"
        )
    except ValidationException as e:
        print("📧 Validation Exception:")
        print(f"   Code: {e.error_code}")
        print(f"   Field: {e.field_path}")
        print(f"   Message: {e.formatted_message}")
        print(f"   Severity: {e.severity.value}")
        print(f"   HTTP Status: {e.http_status_code}")
        print()

    # Template Exception
    try:
        raise TemplateNotFoundException(
            template_name="nonexistent",
            document_type="resume",
            available_templates=["classic", "modern"]
        )
    except TemplateNotFoundException as e:
        print("📄 Template Exception:")
        print(f"   Code: {e.error_code}")
        print(f"   Template: {e.template_name}")
        print(f"   Document Type: {e.document_type}")
        print(f"   Message: {e.formatted_message}")
        print()

    # API Exception
    try:
        raise create_api_error(
            ErrorCode.API003,
            endpoint="/generate",
            method="POST",
            parameter="format",
            value="invalid"
        )
    except APIException as e:
        print("🌐 API Exception:")
        print(f"   Code: {e.error_code}")
        print(f"   Endpoint: {e.endpoint}")
        print(f"   Method: {e.method}")
        print(f"   Message: {e.formatted_message}")
        print()


def demo_response_formatting():
    """Demo standardized response formatting"""
    print("=== Response Formatting Demo ===\n")

    print("📤 Error Response Formats:\n")

    # Simple error response
    error_response = create_error_response(
        ErrorCode.VAL001,
        field="name",
        section="personalInfo"
    )
    print("1. Simple Error Response:")
    print(json.dumps(error_response, indent=2))
    print()

    # Exception-based response
    try:
        raise ValidationException(
            ErrorCode.VAL006,
            field_path="experience[0].startDate",
            context={"date": "invalid-date"}
        )
    except ValidationException as e:
        response = ResponseFormatter.format_error_response(e)
        print("2. Exception-based Response:")
        print(json.dumps(response, indent=2))
        print()

    # Multiple validation errors (simulated)
    print("3. Multiple Validation Errors Response:")
    multi_error_response = {
        "is_valid": False,
        "request_id": "req_12345",
        "timestamp": "2024-01-15T10:30:00Z",
        "errors": [
            {
                "code": "VAL001",
                "category": "validation",
                "severity": "error",
                "field": "personalInfo.name",
                "message": "Required field 'personalInfo.name' is missing from personalInfo",
                "suggested_fix": "Add the required field to your data"
            },
            {
                "code": "VAL003",
                "category": "validation",
                "severity": "error",
                "field": "personalInfo.email",
                "message": "Email 'invalid-email' is not in valid format",
                "suggested_fix": "Use format like 'user@domain.com'"
            }
        ],
        "warnings": [],
        "metadata": {
            "validation_level": "lenient",
            "total_issues": 2
        }
    }
    print(json.dumps(multi_error_response, indent=2))
    print()


def demo_api_integration():
    """Demo how the error system integrates with API responses"""
    print("=== API Integration Demo ===\n")

    print("🔌 API Error Response Examples:\n")

    # Simulate different API scenarios
    scenarios = [
        {
            "name": "Invalid Template",
            "exception": TemplateNotFoundException(
                template_name="nonexistent",
                document_type="resume",
                available_templates=["classic", "modern"]
            )
        },
        {
            "name": "Missing Required Field",
            "exception": ValidationException(
                ErrorCode.VAL001,
                field_path="personalInfo.name",
                context={"field": "name", "section": "personalInfo"}
            )
        },
        {
            "name": "Invalid Request Parameter",
            "exception": create_api_error(
                ErrorCode.API003,
                parameter="format",
                value="docx",
                endpoint="/generate"
            )
        }
    ]

    for scenario in scenarios:
        print(f"📋 Scenario: {scenario['name']}")
        response = ResponseFormatter.format_error_response(scenario['exception'])
        print(f"   HTTP Status: {scenario['exception'].http_status_code}")
        print(f"   Error Code: {scenario['exception'].error_code}")
        print(f"   Message: {scenario['exception'].formatted_message}")
        print(f"   User Facing: {scenario['exception'].is_user_facing}")
        print()


def demo_error_correlation():
    """Demo error correlation and tracking"""
    print("=== Error Correlation Demo ===\n")

    print("🔗 Request ID Correlation:\n")

    request_id = "req_demo_12345"

    # Simulate multiple related errors in a request
    try:
        # First validation error
        raise ValidationException(
            ErrorCode.VAL001,
            field_path="personalInfo.name",
            request_id=request_id
        )
    except ValidationException as e1:
        print("Error 1:")
        print(f"   Request ID: {e1.request_id}")
        print(f"   Timestamp: {e1.timestamp}")
        print(f"   Field: {e1.field_path}")
        print()

        try:
            # Second related error
            raise ValidationException(
                ErrorCode.VAL003,
                field_path="personalInfo.email",
                request_id=request_id
            )
        except ValidationException as e2:
            print("Error 2 (Same Request):")
            print(f"   Request ID: {e2.request_id}")
            print(f"   Timestamp: {e2.timestamp}")
            print(f"   Field: {e2.field_path}")
            print()

            print("✅ Both errors share the same request ID for correlation!")


def demo_backwards_compatibility():
    """Demo backwards compatibility with existing error handling"""
    print("\n=== Backwards Compatibility Demo ===\n")

    print("🔄 Old vs New Error Handling:\n")

    # Simulate old-style error
    from resume_agent_template_engine.core.validation import ValidationError

    # Old way (still works)
    old_error = ValidationError(
        field_path="personalInfo.email",
        error_code=ErrorCode.VAL003,  # Now uses error codes
        message="Email format is invalid",
        severity=ErrorSeverity.ERROR
    )

    print("Old ValidationError (enhanced):")
    print(f"   Field: {old_error.field_path}")
    print(f"   Code: {old_error.error_code}")
    print(f"   Message: {old_error.message}")
    print(f"   Severity: {old_error.severity}")
    print(f"   Error Type (compat): {old_error.error_type}")  # Backward compatibility
    print()

    # New way (recommended)
    new_error = ValidationError.create(
        field_path="personalInfo.email",
        error_code=ErrorCode.VAL003,
        email="invalid-email"
    )

    print("New ValidationError (recommended):")
    print(f"   Field: {new_error.field_path}")
    print(f"   Code: {new_error.error_code}")
    print(f"   Message: {new_error.message}")
    print(f"   Severity: {new_error.severity}")
    print(f"   Suggested Fix: {new_error.suggested_fix}")


if __name__ == "__main__":
    print("Resume Compiler: Standardized Error Registry & Format System Demo\n")
    print("=" * 80 + "\n")

    try:
        demo_error_registry()
        demo_error_formatting()
        demo_exception_hierarchy()
        demo_response_formatting()
        demo_api_integration()
        demo_error_correlation()
        demo_backwards_compatibility()

        print("\n" + "=" * 80)
        print("✨ ERROR SYSTEM FEATURES SUMMARY:")
        print()
        print("🎯 CENTRALIZED ERROR REGISTRY:")
        print("   • Unique error codes with consistent categorization")
        print("   • Standardized message templates with context variables")
        print("   • Severity levels and HTTP status code mapping")
        print("   • Suggested fixes and documentation URLs")
        print()
        print("🏗️ CUSTOM EXCEPTION HIERARCHY:")
        print("   • Type-safe exceptions with automatic message formatting")
        print("   • Request ID correlation for debugging")
        print("   • Context-aware error information")
        print("   • User-facing vs internal error classification")
        print()
        print("📤 STANDARDIZED RESPONSE FORMAT:")
        print("   • Consistent JSON structure across all API endpoints")
        print("   • Detailed error information with field paths")
        print("   • Multiple error aggregation support")
        print("   • Metadata and debugging information")
        print()
        print("🔌 API INTEGRATION:")
        print("   • Global exception handlers for consistent responses")
        print("   • Automatic HTTP status code mapping")
        print("   • Request correlation and error tracking")
        print("   • Debug information control")
        print()
        print("🔄 BACKWARDS COMPATIBILITY:")
        print("   • Existing ValidationError enhanced with error codes")
        print("   • Gradual migration path for legacy code")
        print("   • Compatible with existing API contracts")
        print()
        print("=" * 80)

    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)