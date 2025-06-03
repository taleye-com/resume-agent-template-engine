import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable
import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class VariableType(str, Enum):
    """Types of template variables"""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    LIST = "list"
    OBJECT = "object"
    COMPUTED = "computed"


@dataclass
class VariableDefinition:
    """Definition of a template variable"""

    name: str
    var_type: VariableType
    default_value: Any = None
    required: bool = False
    description: str = ""
    validation_pattern: Optional[str] = None
    computed_function: Optional[Callable] = None
    depends_on: List[str] = field(default_factory=list)

    def validate_value(self, value: Any) -> bool:
        """Validate value against variable definition"""
        if value is None:
            return not self.required

        # Type validation
        if self.var_type == VariableType.STRING and not isinstance(value, str):
            return False
        elif self.var_type == VariableType.NUMBER and not isinstance(
            value, (int, float)
        ):
            return False
        elif self.var_type == VariableType.BOOLEAN and not isinstance(value, bool):
            return False
        elif self.var_type == VariableType.LIST and not isinstance(value, list):
            return False
        elif self.var_type == VariableType.OBJECT and not isinstance(value, dict):
            return False

        # Pattern validation for strings
        if self.validation_pattern and isinstance(value, str):
            return bool(re.match(self.validation_pattern, value))

        return True


class SectionConfig:
    """Configuration for template sections"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize section configuration"""
        self.sections = config.get("sections", {})
        self.order = config.get("order", [])
        self.spacing = config.get("spacing", {})
        self.conditional_sections = config.get("conditional", {})

    def get_section_order(self, available_sections: List[str]) -> List[str]:
        """Get ordered list of sections"""
        ordered = []

        # Add sections in specified order
        for section in self.order:
            if section in available_sections:
                ordered.append(section)

        # Add remaining sections
        for section in available_sections:
            if section not in ordered:
                ordered.append(section)

        return ordered

    def get_section_spacing(self, section: str) -> str:
        """Get spacing configuration for section"""
        return self.spacing.get(section, "\\vspace{1em}")

    def should_include_section(self, section: str, data: Dict[str, Any]) -> bool:
        """Check if section should be included based on conditions"""
        if section not in self.conditional_sections:
            return True

        condition = self.conditional_sections[section]
        return self._evaluate_condition(condition, data)

    def _evaluate_condition(self, condition: str, data: Dict[str, Any]) -> bool:
        """Evaluate conditional expression"""
        # Simple condition evaluation (can be extended)
        if "." in condition:
            parts = condition.split(".")
            value = data
            try:
                for part in parts:
                    value = value[part]
                return bool(value)
            except (KeyError, TypeError):
                return False

        return condition in data and bool(data[condition])


class VariableProcessor:
    """Processes template variables with DRY principles"""

    def __init__(self):
        """Initialize variable processor"""
        self.variables: Dict[str, VariableDefinition] = {}
        self.computed_cache: Dict[str, Any] = {}
        self.builtin_functions = self._setup_builtin_functions()

    def _setup_builtin_functions(self) -> Dict[str, Callable]:
        """Setup built-in computed functions"""
        return {
            "format_date": self._format_date,
            "format_phone": self._format_phone,
            "capitalize": self._capitalize,
            "join_list": self._join_list,
            "count_items": self._count_items,
        }

    def register_variable(self, variable: VariableDefinition) -> None:
        """Register a variable definition"""
        self.variables[variable.name] = variable

    def register_variables_from_config(self, config_path: str) -> None:
        """Register variables from YAML config"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            for var_config in config.get("variables", []):
                variable = VariableDefinition(
                    name=var_config["name"],
                    var_type=VariableType(var_config["type"]),
                    default_value=var_config.get("default"),
                    required=var_config.get("required", False),
                    description=var_config.get("description", ""),
                    validation_pattern=var_config.get("pattern"),
                    depends_on=var_config.get("depends_on", []),
                )
                self.register_variable(variable)

        except Exception as e:
            logger.warning(f"Failed to load variables config: {e}")

    def process_variables(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process all variables with dependency resolution"""
        processed_data = data.copy()
        self.computed_cache.clear()

        # Resolve dependencies and compute values
        resolved = set()
        while len(resolved) < len(self.variables):
            progress = False

            for var_name, var_def in self.variables.items():
                if var_name in resolved:
                    continue

                # Check if dependencies are resolved
                if all(
                    dep in resolved or dep in processed_data
                    for dep in var_def.depends_on
                ):
                    value = self._compute_variable_value(
                        var_name, var_def, processed_data
                    )
                    if value is not None:
                        processed_data[var_name] = value
                    resolved.add(var_name)
                    progress = True

            if not progress:
                # Circular dependency or missing data
                unresolved = set(self.variables.keys()) - resolved
                logger.warning(f"Unresolved variables: {unresolved}")
                break

        return processed_data

    def _compute_variable_value(
        self, var_name: str, var_def: VariableDefinition, data: Dict[str, Any]
    ) -> Any:
        """Compute value for a variable"""
        # Check cache first
        if var_name in self.computed_cache:
            return self.computed_cache[var_name]

        # Use existing value if present and valid
        if var_name in data:
            value = data[var_name]
            if var_def.validate_value(value):
                self.computed_cache[var_name] = value
                return value

        # Compute value if it's a computed type
        if var_def.var_type == VariableType.COMPUTED and var_def.computed_function:
            try:
                value = var_def.computed_function(data)
                self.computed_cache[var_name] = value
                return value
            except Exception as e:
                logger.warning(f"Failed to compute variable {var_name}: {e}")

        # Use default value
        if var_def.default_value is not None:
            self.computed_cache[var_name] = var_def.default_value
            return var_def.default_value

        # Required variable missing
        if var_def.required:
            raise ValueError(f"Required variable '{var_name}' is missing")

        return None

    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate data against variable definitions"""
        errors = []

        for var_name, var_def in self.variables.items():
            value = data.get(var_name)

            if not var_def.validate_value(value):
                if value is None and var_def.required:
                    errors.append(f"Required variable '{var_name}' is missing")
                else:
                    errors.append(f"Invalid value for variable '{var_name}': {value}")

        return errors

    # Built-in functions
    def _format_date(self, data: Dict[str, Any]) -> str:
        """Format date string"""
        from ..common_utils import StringUtils

        date_value = data.get("date")
        if not date_value:
            return StringUtils.format_datetime()

        if isinstance(date_value, str):
            parsed_date = StringUtils.parse_date_flexible(date_value)
            if parsed_date:
                return StringUtils.format_datetime(parsed_date)

        return str(date_value)

    def _format_phone(self, data: Dict[str, Any]) -> str:
        """Format phone number"""
        phone = data.get("phone", "")
        if not phone:
            return ""

        # Simple phone formatting
        digits = re.sub(r"\D", "", phone)
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == "1":
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"

        return phone

    def _capitalize(self, data: Dict[str, Any]) -> str:
        """Capitalize text"""
        text = data.get("text", "")
        return text.title()

    def _join_list(self, data: Dict[str, Any]) -> str:
        """Join list items"""
        items = data.get("items", [])
        separator = data.get("separator", ", ")
        return separator.join(str(item) for item in items)

    def _count_items(self, data: Dict[str, Any]) -> int:
        """Count items in list"""
        items = data.get("items", [])
        return len(items) if isinstance(items, list) else 0


class DynamicSpacingSystem:
    """Manages dynamic spacing based on content and layout"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize spacing system"""
        self.config = config or self._get_default_spacing_config()

    def _get_default_spacing_config(self) -> Dict[str, Any]:
        """Get default spacing configuration"""
        return {
            "base_spacing": "1em",
            "section_spacing": "1.5em",
            "item_spacing": "0.5em",
            "paragraph_spacing": "1em",
            "adaptive": {
                "enabled": True,
                "content_length_factor": 0.1,
                "section_count_factor": 0.05,
            },
        }

    def calculate_spacing(self, context: Dict[str, Any]) -> str:
        """Calculate appropriate spacing for context"""
        base_spacing = self.config.get("base_spacing", "1em")

        if not self.config.get("adaptive", {}).get("enabled", False):
            return base_spacing

        # Adaptive spacing based on content
        spacing_factor = 1.0

        # Adjust based on content length
        content_length = context.get("content_length", 0)
        if content_length > 0:
            length_factor = self.config["adaptive"]["content_length_factor"]
            spacing_factor *= 1 + content_length * length_factor

        # Adjust based on section count
        section_count = context.get("section_count", 1)
        count_factor = self.config["adaptive"]["section_count_factor"]
        spacing_factor *= 1 + section_count * count_factor

        # Apply limits
        spacing_factor = max(0.5, min(2.0, spacing_factor))

        # Convert to LaTeX spacing
        if base_spacing.endswith("em"):
            base_value = float(base_spacing[:-2])
            return f"{base_value * spacing_factor:.1f}em"

        return base_spacing

    def get_section_spacing(self, section_name: str, context: Dict[str, Any]) -> str:
        """Get spacing for specific section"""
        section_config = self.config.get("sections", {})
        if section_name in section_config:
            return section_config[section_name]

        return self.calculate_spacing(context)


class TemplateVariableSystem:
    """Unified system for template variables and configuration"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize template variable system"""
        self.variable_processor = VariableProcessor()
        self.spacing_system = DynamicSpacingSystem()
        self.section_configs: Dict[str, SectionConfig] = {}

        if config_path:
            self.load_config(config_path)

    def load_config(self, config_path: str) -> None:
        """Load configuration from file"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # Load variables
            self.variable_processor.register_variables_from_config(config_path)

            # Load spacing config
            if "spacing" in config:
                self.spacing_system = DynamicSpacingSystem(config["spacing"])

            # Load section configs
            for template_id, template_config in config.get("templates", {}).items():
                if "sections" in template_config:
                    self.section_configs[template_id] = SectionConfig(template_config)

        except Exception as e:
            logger.warning(f"Failed to load template config: {e}")

    def process_template_data(
        self, template_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process template data with variables and sections"""
        # Process variables
        processed_data = self.variable_processor.process_variables(data)

        # Add section configuration
        if template_id in self.section_configs:
            section_config = self.section_configs[template_id]
            processed_data["_section_config"] = section_config

        # Add spacing configuration
        processed_data["_spacing_system"] = self.spacing_system

        return processed_data

    def validate_template_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate template data"""
        return self.variable_processor.validate_data(data)

    def get_variable_info(self) -> Dict[str, Any]:
        """Get information about registered variables"""
        return {
            "total_variables": len(self.variable_processor.variables),
            "variables": {
                name: {
                    "type": var_def.var_type.value,
                    "required": var_def.required,
                    "description": var_def.description,
                    "has_default": var_def.default_value is not None,
                }
                for name, var_def in self.variable_processor.variables.items()
            },
        }
