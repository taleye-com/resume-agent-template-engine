"""
Unit tests for the schema generator system

Tests the SchemaGenerator class and its methods for generating JSON schemas,
examples, and YAML conversion functionality.
"""

import pytest

from resume_agent_template_engine.api.schema_generator import SchemaGenerator
from resume_agent_template_engine.core.base import DocumentType


class TestSchemaGenerator:
    """Test SchemaGenerator basic functionality"""

    def test_schema_generator_class_exists(self):
        """Test that SchemaGenerator class exists and can be instantiated"""
        generator = SchemaGenerator()
        assert generator is not None

    def test_schema_generator_static_methods(self):
        """Test that key static methods exist"""
        assert hasattr(SchemaGenerator, "generate_resume_schema")
        assert hasattr(SchemaGenerator, "generate_cover_letter_schema")
        assert hasattr(SchemaGenerator, "generate_resume_example")
        assert hasattr(SchemaGenerator, "generate_cover_letter_example")
        assert hasattr(SchemaGenerator, "get_schema_for_document_type")


class TestResumeSchemaGeneration:
    """Test resume schema generation"""

    def test_generate_resume_schema(self):
        """Test generating resume schema"""
        schema = SchemaGenerator.generate_resume_schema()

        # Basic schema structure
        assert isinstance(schema, dict)
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

        # Required fields
        assert "personalInfo" in schema["required"]

        # Key properties exist
        properties = schema["properties"]
        assert "personalInfo" in properties
        assert "experience" in properties
        assert "education" in properties
        assert "skills" in properties

    def test_resume_schema_personal_info(self):
        """Test personal info section of resume schema"""
        schema = SchemaGenerator.generate_resume_schema()
        personal_info = schema["properties"]["personalInfo"]

        assert personal_info["type"] == "object"
        assert "name" in personal_info["required"]
        assert "email" in personal_info["required"]

        # Check key properties
        properties = personal_info["properties"]
        assert "name" in properties
        assert "email" in properties
        assert "phone" in properties
        assert "location" in properties

        # Check email format validation
        assert properties["email"]["format"] == "email"

    def test_resume_schema_experience_section(self):
        """Test experience section of resume schema"""
        schema = SchemaGenerator.generate_resume_schema()
        experience = schema["properties"]["experience"]

        assert experience["type"] == "array"
        assert "items" in experience

        # Check experience item structure
        exp_item = experience["items"]
        assert exp_item["type"] == "object"
        assert "position" in exp_item["required"]
        assert "company" in exp_item["required"]
        assert "startDate" in exp_item["required"]

        # Check date pattern validation
        start_date = exp_item["properties"]["startDate"]
        assert "pattern" in start_date

    def test_resume_schema_skills_section(self):
        """Test skills section of resume schema"""
        schema = SchemaGenerator.generate_resume_schema()
        skills = schema["properties"]["skills"]

        assert skills["type"] == "object"
        properties = skills["properties"]

        # Check skill categories
        assert "technical" in properties
        assert "soft" in properties
        assert "languages" in properties
        assert "frameworks" in properties
        assert "tools" in properties

        # All skill categories should be arrays
        for skill_type in properties.values():
            assert skill_type["type"] == "array"
            assert skill_type["items"]["type"] == "string"


class TestCoverLetterSchemaGeneration:
    """Test cover letter schema generation"""

    def test_generate_cover_letter_schema(self):
        """Test generating cover letter schema"""
        schema = SchemaGenerator.generate_cover_letter_schema()

        # Basic schema structure
        assert isinstance(schema, dict)
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

        # Required fields
        assert "personalInfo" in schema["required"]
        assert "body" in schema["required"]

        # Key properties exist
        properties = schema["properties"]
        assert "personalInfo" in properties
        assert "recipient" in properties
        assert "body" in properties
        assert "date" in properties

    def test_cover_letter_recipient_section(self):
        """Test recipient section of cover letter schema"""
        schema = SchemaGenerator.generate_cover_letter_schema()
        recipient = schema["properties"]["recipient"]

        assert recipient["type"] == "object"
        properties = recipient["properties"]

        # Check recipient properties
        assert "name" in properties
        assert "company" in properties
        assert "address" in properties
        assert "city" in properties
        assert "state" in properties

        # Check address can be string or array
        address = properties["address"]
        assert address["type"] == ["string", "array"]

    def test_cover_letter_body_section(self):
        """Test body section of cover letter schema"""
        schema = SchemaGenerator.generate_cover_letter_schema()
        body = schema["properties"]["body"]

        # Body can be string or array of strings
        assert body["type"] == ["string", "array"]
        assert body["items"]["type"] == "string"


class TestExampleGeneration:
    """Test example data generation"""

    def test_generate_resume_example(self):
        """Test generating resume example"""
        example = SchemaGenerator.generate_resume_example()

        # Basic structure
        assert isinstance(example, dict)
        assert "personalInfo" in example
        assert "experience" in example
        assert "education" in example
        assert "skills" in example

        # Personal info has required fields
        personal_info = example["personalInfo"]
        assert "name" in personal_info
        assert "email" in personal_info
        assert personal_info["name"] == "John Doe"
        assert "@" in personal_info["email"]

        # Experience is array with entries
        assert isinstance(example["experience"], list)
        assert len(example["experience"]) > 0

        # First experience entry has required fields
        exp = example["experience"][0]
        assert "position" in exp
        assert "company" in exp
        assert "startDate" in exp

    def test_generate_cover_letter_example(self):
        """Test generating cover letter example"""
        example = SchemaGenerator.generate_cover_letter_example()

        # Basic structure
        assert isinstance(example, dict)
        assert "personalInfo" in example
        assert "recipient" in example
        assert "body" in example

        # Personal info has required fields
        personal_info = example["personalInfo"]
        assert "name" in personal_info
        assert "email" in personal_info

        # Recipient has company info
        recipient = example["recipient"]
        assert "name" in recipient
        assert "company" in recipient

        # Body is array of paragraphs
        assert isinstance(example["body"], list)
        assert len(example["body"]) > 0

    def test_example_data_validity(self):
        """Test that generated examples are valid according to schemas"""
        # This is a basic validation - in a real scenario you'd use jsonschema
        resume_schema = SchemaGenerator.generate_resume_schema()
        resume_example = SchemaGenerator.generate_resume_example()

        # Check required fields are present
        required_fields = resume_schema["required"]
        for field in required_fields:
            assert field in resume_example

        # Check personal info required fields
        personal_required = resume_schema["properties"]["personalInfo"]["required"]
        personal_example = resume_example["personalInfo"]
        for field in personal_required:
            assert field in personal_example


class TestSchemaForDocumentType:
    """Test get_schema_for_document_type method"""

    def test_get_schema_for_resume(self):
        """Test getting schema for resume document type"""
        result = SchemaGenerator.get_schema_for_document_type(DocumentType.RESUME)

        assert isinstance(result, dict)
        assert "schema" in result
        assert "json_example" in result
        assert "yaml_example" in result

        # Check schema is valid
        schema = result["schema"]
        assert schema["type"] == "object"
        assert "personalInfo" in schema["properties"]

        # Check example is valid
        example = result["json_example"]
        assert "personalInfo" in example

        # Check YAML example is string
        yaml_example = result["yaml_example"]
        assert isinstance(yaml_example, str)
        assert "personalInfo:" in yaml_example

    def test_get_schema_for_cover_letter(self):
        """Test getting schema for cover letter document type"""
        result = SchemaGenerator.get_schema_for_document_type(DocumentType.COVER_LETTER)

        assert isinstance(result, dict)
        assert "schema" in result
        assert "json_example" in result
        assert "yaml_example" in result

        # Check schema is valid
        schema = result["schema"]
        assert schema["type"] == "object"
        assert "personalInfo" in schema["properties"]
        assert "body" in schema["properties"]

        # Check example is valid
        example = result["json_example"]
        assert "personalInfo" in example
        assert "body" in example

    def test_get_schema_invalid_document_type(self):
        """Test getting schema for invalid document type"""
        with pytest.raises(ValueError) as exc_info:
            SchemaGenerator.get_schema_for_document_type("invalid_type")

        assert "Unsupported document type" in str(exc_info.value)


class TestYAMLConversion:
    """Test YAML conversion functionality"""

    def test_dict_to_yaml_basic(self):
        """Test basic dictionary to YAML conversion"""
        test_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "skills": ["Python", "JavaScript"],
        }

        yaml_result = SchemaGenerator._dict_to_yaml(test_data)

        assert isinstance(yaml_result, str)
        assert "name:" in yaml_result
        assert "John Doe" in yaml_result
        assert "email:" in yaml_result
        assert "skills:" in yaml_result

    def test_dict_to_basic_yaml_fallback(self):
        """Test basic YAML conversion fallback when yaml module unavailable"""
        test_data = {
            "personalInfo": {"name": "John Doe", "email": "john@example.com"},
            "skills": ["Python", "JavaScript"],
        }

        yaml_result = SchemaGenerator._dict_to_basic_yaml(test_data)

        assert isinstance(yaml_result, str)
        assert "personalInfo:" in yaml_result
        assert "name: John Doe" in yaml_result
        assert "skills:" in yaml_result
        assert "- Python" in yaml_result

    def test_yaml_conversion_nested_objects(self):
        """Test YAML conversion with nested objects"""
        test_data = {
            "personalInfo": {
                "name": "John Doe",
                "contact": {"email": "john@example.com", "phone": "555-1234"},
            }
        }

        yaml_result = SchemaGenerator._dict_to_basic_yaml(test_data)

        assert "personalInfo:" in yaml_result
        assert "contact:" in yaml_result
        assert "email: john@example.com" in yaml_result

    def test_yaml_conversion_arrays_of_objects(self):
        """Test YAML conversion with arrays of objects"""
        test_data = {
            "experience": [
                {"position": "Software Engineer", "company": "Tech Corp"},
                {"position": "Developer", "company": "Web Co"},
            ]
        }

        yaml_result = SchemaGenerator._dict_to_basic_yaml(test_data)

        assert "experience:" in yaml_result
        assert "position: Software Engineer" in yaml_result
        assert "company: Tech Corp" in yaml_result


class TestSchemaGeneratorIntegration:
    """Integration tests for schema generator"""

    def test_schema_generation_consistency(self):
        """Test that schemas and examples are consistent"""
        # Get full schema data for resume
        result = SchemaGenerator.get_schema_for_document_type(DocumentType.RESUME)
        schema = result["schema"]
        example = result["json_example"]

        # Check that example contains all required fields from schema
        required_fields = schema.get("required", [])
        for field in required_fields:
            assert field in example, f"Required field '{field}' missing from example"

        # Check personal info requirements
        if "personalInfo" in schema["properties"]:
            personal_required = schema["properties"]["personalInfo"].get("required", [])
            personal_example = example.get("personalInfo", {})
            for field in personal_required:
                assert field in personal_example, (
                    f"Required personal info field '{field}' missing"
                )

    def test_multiple_document_types(self):
        """Test that both document types work correctly"""
        resume_result = SchemaGenerator.get_schema_for_document_type(
            DocumentType.RESUME
        )
        cover_letter_result = SchemaGenerator.get_schema_for_document_type(
            DocumentType.COVER_LETTER
        )

        # Both should have the same structure
        for result in [resume_result, cover_letter_result]:
            assert "schema" in result
            assert "json_example" in result
            assert "yaml_example" in result

        # But different content
        assert resume_result["schema"] != cover_letter_result["schema"]
        assert resume_result["json_example"] != cover_letter_result["json_example"]

    def test_yaml_json_consistency(self):
        """Test that YAML and JSON examples represent the same data"""
        result = SchemaGenerator.get_schema_for_document_type(DocumentType.RESUME)
        json_example = result["json_example"]
        yaml_example = result["yaml_example"]

        # Basic checks that YAML contains key data from JSON
        assert json_example["personalInfo"]["name"] in yaml_example
        assert json_example["personalInfo"]["email"] in yaml_example

        # Check that major sections are present
        assert "personalInfo:" in yaml_example
        assert "experience:" in yaml_example
        assert "education:" in yaml_example


if __name__ == "__main__":
    pytest.main([__file__])
