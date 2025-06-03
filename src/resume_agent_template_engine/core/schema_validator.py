import json
import jsonschema
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
from enum import Enum

from .base_validator import (
    BaseValidator,
    ValidationError,
    ValidationSeverity,
    ValidationIssue,
)

logger = logging.getLogger(__name__)


class DocumentSchema(str, Enum):
    """Supported document schemas"""

    RESUME = "resume"
    COVER_LETTER = "cover_letter"


class SchemaValidator(BaseValidator):
    """JSON schema validator for resume and cover letter data"""

    def __init__(self, schemas_path: Optional[str] = None):
        """
        Initialize schema validator

        Args:
            schemas_path: Path to directory containing schema files
        """
        super().__init__()
        self.schemas_path = (
            Path(schemas_path) if schemas_path else Path(__file__).parent / "schemas"
        )
        self._schemas = {}
        self._load_schemas()

    def _load_schemas(self) -> None:
        """Load all JSON schemas from the schemas directory"""
        if not self.schemas_path.exists():
            logger.warning(f"Schemas directory not found: {self.schemas_path}")
            self._create_default_schemas()
            return

        for schema_file in self.schemas_path.glob("*.json"):
            schema_name = schema_file.stem
            try:
                with open(schema_file, "r", encoding="utf-8") as f:
                    self._schemas[schema_name] = json.load(f)
                logger.info(f"Loaded schema: {schema_name}")
            except Exception as e:
                logger.error(f"Failed to load schema {schema_file}: {e}")

    def _create_default_schemas(self) -> None:
        """Create default schemas if directory doesn't exist"""
        self.schemas_path.mkdir(parents=True, exist_ok=True)

        # Resume schema
        resume_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": "Resume Schema",
            "required": ["personalInfo"],
            "properties": {
                "personalInfo": {
                    "type": "object",
                    "required": ["name", "email"],
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "email": {"type": "string", "format": "email"},
                        "phone": {"type": "string"},
                        "address": {"type": "string"},
                        "linkedin": {"type": "string", "format": "uri"},
                        "github": {"type": "string", "format": "uri"},
                        "website": {"type": "string", "format": "uri"},
                    },
                },
                "summary": {"type": "string"},
                "experience": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["company", "position", "startDate"],
                        "properties": {
                            "company": {"type": "string", "minLength": 1},
                            "position": {"type": "string", "minLength": 1},
                            "startDate": {"type": "string"},
                            "endDate": {"type": "string"},
                            "current": {"type": "boolean"},
                            "description": {"type": "string"},
                            "achievements": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                },
                "education": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["institution", "degree"],
                        "properties": {
                            "institution": {"type": "string", "minLength": 1},
                            "degree": {"type": "string", "minLength": 1},
                            "major": {"type": "string"},
                            "graduationDate": {"type": "string"},
                            "gpa": {"type": "number", "minimum": 0, "maximum": 4.0},
                        },
                    },
                },
                "skills": {"type": "array", "items": {"type": "string"}},
                "projects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "description": {"type": "string"},
                            "technologies": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "url": {"type": "string", "format": "uri"},
                        },
                    },
                },
                "certifications": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "issuer"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "issuer": {"type": "string", "minLength": 1},
                            "date": {"type": "string"},
                            "url": {"type": "string", "format": "uri"},
                        },
                    },
                },
            },
        }

        # Cover letter schema
        cover_letter_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": "Cover Letter Schema",
            "required": ["personalInfo", "recipient", "content"],
            "properties": {
                "personalInfo": {
                    "type": "object",
                    "required": ["name", "email"],
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "email": {"type": "string", "format": "email"},
                        "phone": {"type": "string"},
                        "address": {"type": "string"},
                    },
                },
                "recipient": {
                    "type": "object",
                    "required": ["company"],
                    "properties": {
                        "company": {"type": "string", "minLength": 1},
                        "hiringManager": {"type": "string"},
                        "position": {"type": "string"},
                        "address": {"type": "string"},
                    },
                },
                "content": {
                    "type": "object",
                    "required": ["opening", "body", "closing"],
                    "properties": {
                        "opening": {"type": "string", "minLength": 1},
                        "body": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                        },
                        "closing": {"type": "string", "minLength": 1},
                    },
                },
                "date": {"type": "string"},
                "subject": {"type": "string"},
            },
        }

        # Save schemas
        with open(self.schemas_path / "resume.json", "w", encoding="utf-8") as f:
            json.dump(resume_schema, f, indent=2)

        with open(self.schemas_path / "cover_letter.json", "w", encoding="utf-8") as f:
            json.dump(cover_letter_schema, f, indent=2)

        self._schemas = {"resume": resume_schema, "cover_letter": cover_letter_schema}

    def validate(self, data: Dict[str, Any], schema_type: DocumentSchema) -> None:
        """
        Validate data against the specified schema

        Args:
            data: Data to validate
            schema_type: Type of schema to validate against

        Raises:
            ValidationError: If validation fails
        """
        schema_name = schema_type.value

        if schema_name not in self._schemas:
            raise ValidationError(f"Schema '{schema_name}' not found")

        schema = self._schemas[schema_name]

        try:
            jsonschema.validate(data, schema)
        except jsonschema.ValidationError as e:
            errors = [str(e)]
            # Collect all validation errors
            validator = jsonschema.Draft7Validator(schema)
            all_errors = list(validator.iter_errors(data))
            errors.extend(
                [
                    f"{'.'.join(str(p) for p in error.absolute_path)}: {error.message}"
                    for error in all_errors
                ]
            )

            raise ValidationError(
                f"Validation failed for {schema_name} schema", errors=errors
            )

    def validate_partial(
        self,
        data: Dict[str, Any],
        schema_type: DocumentSchema,
        required_only: bool = False,
    ) -> List[str]:
        """
        Validate data and return list of errors without raising exception

        Args:
            data: Data to validate
            schema_type: Type of schema to validate against
            required_only: If True, only validate required fields

        Returns:
            List of validation error messages
        """
        schema_name = schema_type.value

        if schema_name not in self._schemas:
            return [f"Schema '{schema_name}' not found"]

        schema = self._schemas[schema_name].copy()

        if required_only:
            # Create a minimal schema with only required fields
            schema = self._extract_required_schema(schema)

        validator = jsonschema.Draft7Validator(schema)
        errors = []

        for error in validator.iter_errors(data):
            field_path = ".".join(str(p) for p in error.absolute_path)
            if field_path:
                errors.append(f"{field_path}: {error.message}")
            else:
                errors.append(error.message)

        return errors

    def _extract_required_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract a schema with only required fields"""
        required_schema = {
            "$schema": schema.get("$schema"),
            "type": "object",
            "required": schema.get("required", []),
            "properties": {},
        }

        if "required" in schema and "properties" in schema:
            for field in schema["required"]:
                if field in schema["properties"]:
                    required_schema["properties"][field] = schema["properties"][field]

        return required_schema

    def get_schema(self, schema_type: DocumentSchema) -> Dict[str, Any]:
        """Get the full schema for a document type"""
        schema_name = schema_type.value
        return self._schemas.get(schema_name, {})

    def get_required_fields(self, schema_type: DocumentSchema) -> List[str]:
        """Get list of required fields for a schema"""
        schema = self.get_schema(schema_type)
        return schema.get("required", [])
