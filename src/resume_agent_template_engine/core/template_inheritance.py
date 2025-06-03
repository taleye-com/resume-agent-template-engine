import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
import logging
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
import importlib.util

logger = logging.getLogger(__name__)


class TemplateInheritanceError(Exception):
    """Exception raised for template inheritance errors"""

    pass


class BaseTemplate(ABC):
    """Abstract base template with inheritance support"""

    def __init__(self, data: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        """
        Initialize base template

        Args:
            data: Template data
            config: Template configuration
        """
        self.data = data
        self.config = config or {}
        self.parent_template = None
        self.child_templates = []
        self._setup_inheritance()

    def _setup_inheritance(self) -> None:
        """Setup template inheritance chain"""
        parent_config = self.config.get("extends")
        if parent_config:
            self._load_parent_template(parent_config)

    def _load_parent_template(self, parent_config: Union[str, Dict[str, Any]]) -> None:
        """Load parent template"""
        if isinstance(parent_config, str):
            parent_config = {"template": parent_config}

        parent_name = parent_config.get("template")
        if not parent_name:
            raise TemplateInheritanceError("Parent template name not specified")

        # Load parent template dynamically
        parent_path = self._resolve_parent_path(parent_name)
        self.parent_template = self._instantiate_parent(parent_path, parent_config)

    def _resolve_parent_path(self, parent_name: str) -> Path:
        """Resolve parent template path"""
        # Implementation depends on template discovery mechanism
        current_dir = Path(__file__).parent.parent / "templates"

        # Search in same document type first
        doc_type = getattr(self, "template_type", "unknown")
        if hasattr(doc_type, "value"):
            doc_type = doc_type.value

        parent_path = current_dir / doc_type / parent_name
        if parent_path.exists():
            return parent_path

        # Search in base templates
        base_path = current_dir / "base" / parent_name
        if base_path.exists():
            return base_path

        raise TemplateInheritanceError(f"Parent template not found: {parent_name}")

    def _instantiate_parent(
        self, parent_path: Path, config: Dict[str, Any]
    ) -> "BaseTemplate":
        """Instantiate parent template"""
        helper_file = parent_path / "helper.py"
        if not helper_file.exists():
            raise TemplateInheritanceError(
                f"Parent template helper not found: {helper_file}"
            )

        # Load parent template class
        spec = importlib.util.spec_from_file_location(
            f"{parent_path.name}_helper", helper_file
        )
        helper_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper_module)

        # Find template class
        template_class = None
        for attr_name in dir(helper_module):
            attr = getattr(helper_module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseTemplate)
                and attr != BaseTemplate
            ):
                template_class = attr
                break

        if not template_class:
            raise TemplateInheritanceError(
                f"No valid template class found in {helper_file}"
            )

        # Merge configurations
        parent_config = self.config.copy()
        parent_config.update(config.get("config", {}))

        return template_class(self.data, parent_config)

    def get_inherited_value(self, key: str, default: Any = None) -> Any:
        """Get value with inheritance chain lookup"""
        # Check current template config first
        if key in self.config:
            return self.config[key]

        # Check parent template
        if self.parent_template:
            return self.parent_template.get_inherited_value(key, default)

        return default

    def merge_data(self, additional_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge data with inheritance chain"""
        merged_data = {}

        # Start with parent data if available
        if self.parent_template:
            merged_data = self.parent_template.merge_data({})

        # Add current template data
        merged_data.update(self.data)

        # Add additional data
        merged_data.update(additional_data)

        return merged_data

    @abstractmethod
    def render_blocks(self) -> Dict[str, str]:
        """Render template blocks that can be overridden"""
        pass

    def render(self) -> str:
        """Render complete template with inheritance"""
        blocks = self.render_blocks()

        # If we have a parent, let it handle the main rendering
        if self.parent_template:
            # Override parent blocks with our blocks
            parent_blocks = self.parent_template.render_blocks()
            parent_blocks.update(blocks)
            return self.parent_template._render_with_blocks(parent_blocks)

        # No parent, render directly
        return self._render_with_blocks(blocks)

    @abstractmethod
    def _render_with_blocks(self, blocks: Dict[str, str]) -> str:
        """Render template with provided blocks"""
        pass


class LatexTemplateWithInheritance(BaseTemplate):
    """LaTeX template with inheritance support"""

    def __init__(self, data: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        """Initialize LaTeX template with inheritance"""
        super().__init__(data, config)
        self.template_dir = Path(config.get("template_dir", "."))
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["tex"]),
            block_start_string="\\BLOCK{",
            block_end_string="}",
            variable_start_string="\\VAR{",
            variable_end_string="}",
            comment_start_string="\\#{",
            comment_end_string="}",
        )

    def render_blocks(self) -> Dict[str, str]:
        """Render LaTeX template blocks"""
        blocks = {}

        # Load block definitions from template files
        for tex_file in self.template_dir.glob("*.tex"):
            template_content = tex_file.read_text(encoding="utf-8")

            # Extract blocks using regex or template parsing
            block_matches = self._extract_blocks(template_content)
            for block_name, block_content in block_matches.items():
                rendered_block = self._render_block_content(block_content)
                blocks[block_name] = rendered_block

        return blocks

    def _extract_blocks(self, content: str) -> Dict[str, str]:
        """Extract block definitions from template content"""
        import re

        # Look for block definitions like \BLOCK{blockname}...\ENDBLOCK{blockname}
        pattern = r"\\BLOCK\{([^}]+)\}(.*?)\\ENDBLOCK\{\1\}"
        matches = re.findall(pattern, content, re.DOTALL)

        return {name: content.strip() for name, content in matches}

    def _render_block_content(self, content: str) -> str:
        """Render block content with Jinja2"""
        template = self.jinja_env.from_string(content)
        return template.render(**self.merge_data({}))

    def _render_with_blocks(self, blocks: Dict[str, str]) -> str:
        """Render complete LaTeX template with blocks"""
        main_template_file = self.template_dir / "main.tex"
        if not main_template_file.exists():
            # Fallback to first .tex file
            tex_files = list(self.template_dir.glob("*.tex"))
            if not tex_files:
                raise TemplateInheritanceError(
                    "No .tex files found in template directory"
                )
            main_template_file = tex_files[0]

        main_content = main_template_file.read_text(encoding="utf-8")

        # Replace block placeholders with rendered blocks
        for block_name, block_content in blocks.items():
            placeholder = f"\\PLACEHOLDER{{{block_name}}}"
            main_content = main_content.replace(placeholder, block_content)

        # Render the main template
        template = self.jinja_env.from_string(main_content)
        return template.render(**self.merge_data({}))


class TemplateInheritanceManager:
    """Manages template inheritance relationships"""

    def __init__(self, templates_base_path: str):
        """
        Initialize inheritance manager

        Args:
            templates_base_path: Base path for templates
        """
        self.templates_base_path = Path(templates_base_path)
        self.inheritance_map = {}
        self.dependency_graph = {}
        self._build_inheritance_map()

    def _build_inheritance_map(self) -> None:
        """Build inheritance map from template configurations"""
        if not self.templates_base_path.exists():
            logger.warning(
                f"Templates base path does not exist: {self.templates_base_path}"
            )
            return

        for doc_type_dir in self.templates_base_path.iterdir():
            if not doc_type_dir.is_dir():
                continue

            for template_dir in doc_type_dir.iterdir():
                if not template_dir.is_dir():
                    continue

                template_id = f"{doc_type_dir.name}/{template_dir.name}"
                inheritance_info = self._get_template_inheritance_info(template_dir)

                if inheritance_info:
                    self.inheritance_map[template_id] = inheritance_info
                    self._update_dependency_graph(template_id, inheritance_info)

    def _get_template_inheritance_info(
        self, template_dir: Path
    ) -> Optional[Dict[str, Any]]:
        """Get inheritance information for a template"""
        config_files = [
            template_dir / "template.yaml",
            template_dir / "template.yml",
            template_dir / "config.yaml",
            template_dir / "config.yml",
        ]

        for config_file in config_files:
            if config_file.exists():
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        config = yaml.safe_load(f)

                    if "extends" in config:
                        return {
                            "parent": config["extends"],
                            "config": config,
                            "path": template_dir,
                        }
                except Exception as e:
                    logger.warning(f"Failed to load config from {config_file}: {e}")

        return None

    def _update_dependency_graph(
        self, template_id: str, inheritance_info: Dict[str, Any]
    ) -> None:
        """Update dependency graph with inheritance relationship"""
        parent = inheritance_info["parent"]
        if isinstance(parent, dict):
            parent = parent.get("template", parent.get("name"))

        if template_id not in self.dependency_graph:
            self.dependency_graph[template_id] = {"parents": [], "children": []}

        self.dependency_graph[template_id]["parents"].append(parent)

        if parent not in self.dependency_graph:
            self.dependency_graph[parent] = {"parents": [], "children": []}

        self.dependency_graph[parent]["children"].append(template_id)

    def get_inheritance_chain(self, template_id: str) -> List[str]:
        """Get complete inheritance chain for a template"""
        chain = [template_id]
        current = template_id

        while current in self.dependency_graph:
            parents = self.dependency_graph[current]["parents"]
            if not parents:
                break

            parent = parents[0]  # Take first parent for simplicity
            if parent in chain:  # Circular dependency
                raise TemplateInheritanceError(
                    f"Circular dependency detected: {' -> '.join(chain + [parent])}"
                )

            chain.append(parent)
            current = parent

        return list(reversed(chain))  # Return from base to derived

    def validate_inheritance(self) -> List[str]:
        """Validate inheritance relationships and return any issues"""
        issues = []

        for template_id, inheritance_info in self.inheritance_map.items():
            try:
                chain = self.get_inheritance_chain(template_id)

                # Check if all templates in chain exist
                for chain_template in chain[:-1]:  # Exclude self
                    if not self._template_exists(chain_template):
                        issues.append(
                            f"Template {template_id} extends non-existent template: {chain_template}"
                        )

            except TemplateInheritanceError as e:
                issues.append(f"Inheritance error for {template_id}: {e}")

        return issues

    def _template_exists(self, template_id: str) -> bool:
        """Check if a template exists"""
        if "/" in template_id:
            doc_type, template_name = template_id.split("/", 1)
            template_path = self.templates_base_path / doc_type / template_name
        else:
            # Check in base templates
            template_path = self.templates_base_path / "base" / template_id

        return template_path.exists() and (template_path / "helper.py").exists()

    def get_template_hierarchy(self) -> Dict[str, Any]:
        """Get complete template hierarchy"""
        hierarchy = {}

        # Find root templates (no parents)
        root_templates = []
        for template_id in self.dependency_graph:
            if not self.dependency_graph[template_id]["parents"]:
                root_templates.append(template_id)

        # Build hierarchy tree
        for root in root_templates:
            hierarchy[root] = self._build_hierarchy_subtree(root)

        return hierarchy

    def _build_hierarchy_subtree(self, template_id: str) -> Dict[str, Any]:
        """Build hierarchy subtree for a template"""
        subtree = {"children": {}, "info": self.inheritance_map.get(template_id, {})}

        if template_id in self.dependency_graph:
            for child in self.dependency_graph[template_id]["children"]:
                subtree["children"][child] = self._build_hierarchy_subtree(child)

        return subtree
