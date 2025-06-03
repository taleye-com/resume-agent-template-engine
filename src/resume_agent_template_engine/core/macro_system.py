import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import logging
from dataclasses import dataclass
from enum import Enum
import yaml

logger = logging.getLogger(__name__)


class MacroType(str, Enum):
    """Types of LaTeX macros"""

    COMMAND = "command"
    ENVIRONMENT = "environment"
    COUNTER = "counter"
    LENGTH = "length"


@dataclass
class MacroDefinition:
    """Definition of a LaTeX macro"""

    name: str
    macro_type: MacroType
    definition: str
    parameters: int = 0
    optional_params: int = 0
    description: str = ""
    category: str = "general"
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class MacroRegistry:
    """Registry for managing custom LaTeX macros"""

    def __init__(self):
        """Initialize macro registry"""
        self.macros: Dict[str, MacroDefinition] = {}
        self.categories: Dict[str, List[str]] = {}
        self.dependencies: Dict[str, List[str]] = {}
        self._load_builtin_macros()

    def _load_builtin_macros(self) -> None:
        """Load built-in macros for resume templates"""
        builtin_macros = [
            MacroDefinition(
                name="resumeSection",
                macro_type=MacroType.COMMAND,
                definition=r"\newcommand{\resumeSection}[1]{\section*{#1}\vspace{-0.3em}\hrule\vspace{0.5em}}",
                parameters=1,
                description="Create a resume section with underline",
                category="resume",
            ),
            MacroDefinition(
                name="resumeItem",
                macro_type=MacroType.COMMAND,
                definition=r"\newcommand{\resumeItem}[2]{\item \textbf{#1}: #2}",
                parameters=2,
                description="Create a resume item with bold label",
                category="resume",
            ),
            MacroDefinition(
                name="contactInfo",
                macro_type=MacroType.COMMAND,
                definition=r"\newcommand{\contactInfo}[4]{\begin{center}#1 \\ #2 \\ #3 \\ #4\end{center}}",
                parameters=4,
                description="Format contact information in center",
                category="resume",
            ),
            MacroDefinition(
                name="skillCategory",
                macro_type=MacroType.COMMAND,
                definition=r"\newcommand{\skillCategory}[2]{\textbf{#1:} #2\\}",
                parameters=2,
                description="Format skill category with colon",
                category="resume",
            ),
            MacroDefinition(
                name="dateRange",
                macro_type=MacroType.COMMAND,
                definition=r"\newcommand{\dateRange}[2]{\hfill \textit{#1 -- #2}}",
                parameters=2,
                description="Format date range aligned to right",
                category="resume",
            ),
            MacroDefinition(
                name="experienceItem",
                macro_type=MacroType.ENVIRONMENT,
                definition=r"""
\newenvironment{experienceItem}[3]
{\noindent\textbf{#1} \hfill \textit{#2} \\ \textit{#3} \vspace{0.5em}
\begin{itemize}[leftmargin=1em]}
{\end{itemize}\vspace{0.5em}}""",
                parameters=3,
                description="Environment for experience items with company, dates, and position",
                category="resume",
                dependencies=["enumitem"],
            ),
            MacroDefinition(
                name="educationItem",
                macro_type=MacroType.COMMAND,
                definition=r"\newcommand{\educationItem}[4]{\textbf{#1} \hfill \textit{#2} \\ \textit{#3} \hfill GPA: #4 \\[0.5em]}",
                parameters=4,
                description="Format education item with institution, dates, degree, and GPA",
                category="resume",
            ),
            MacroDefinition(
                name="projectItem",
                macro_type=MacroType.ENVIRONMENT,
                definition=r"""
\newenvironment{projectItem}[2]
{\noindent\textbf{#1} \hfill \textit{#2}
\begin{itemize}[leftmargin=1em]}
{\end{itemize}\vspace{0.5em}}""",
                parameters=2,
                description="Environment for project items with name and technologies",
                category="resume",
                dependencies=["enumitem"],
            ),
            MacroDefinition(
                name="coverLetterHeader",
                macro_type=MacroType.COMMAND,
                definition=r"\newcommand{\coverLetterHeader}[2]{\begin{flushright}#1\\#2\end{flushright}\vspace{1em}}",
                parameters=2,
                description="Format cover letter header with name and date",
                category="cover_letter",
            ),
            MacroDefinition(
                name="recipientAddress",
                macro_type=MacroType.COMMAND,
                definition=r"\newcommand{\recipientAddress}[3]{#1\\#2\\#3\vspace{1em}}",
                parameters=3,
                description="Format recipient address block",
                category="cover_letter",
            ),
        ]

        for macro in builtin_macros:
            self.register_macro(macro)

    def register_macro(self, macro: MacroDefinition) -> None:
        """Register a macro in the registry"""
        self.macros[macro.name] = macro

        # Update categories
        if macro.category not in self.categories:
            self.categories[macro.category] = []
        if macro.name not in self.categories[macro.category]:
            self.categories[macro.category].append(macro.name)

        # Update dependencies
        if macro.dependencies:
            self.dependencies[macro.name] = macro.dependencies

    def get_macro(self, name: str) -> Optional[MacroDefinition]:
        """Get macro by name"""
        return self.macros.get(name)

    def get_macros_by_category(self, category: str) -> List[MacroDefinition]:
        """Get all macros in a category"""
        macro_names = self.categories.get(category, [])
        return [self.macros[name] for name in macro_names if name in self.macros]

    def get_all_dependencies(self, macro_names: List[str]) -> List[str]:
        """Get all dependencies for a list of macros"""
        all_deps = set()

        def collect_deps(name: str):
            if name in self.dependencies:
                for dep in self.dependencies[name]:
                    if dep not in all_deps:
                        all_deps.add(dep)
                        collect_deps(dep)  # Recursive dependency resolution

        for name in macro_names:
            collect_deps(name)

        return list(all_deps)

    def validate_macro_definition(self, definition: str) -> Tuple[bool, List[str]]:
        """Validate a macro definition for security and correctness"""
        issues = []

        # Security checks
        security_patterns = [
            (r"\\write18", "Shell execution detected"),
            (r"\\immediate\\write18", "Immediate shell execution detected"),
            (r"\\input\s*\|", "Pipe input detected"),
            (r"\\openin", "File reading detected"),
            (r"\\openout", "File writing detected"),
            (r"\\catcode", "Category code modification detected"),
        ]

        for pattern, message in security_patterns:
            if re.search(pattern, definition):
                issues.append(f"Security issue: {message}")

        # Syntax checks
        if not definition.strip():
            issues.append("Empty macro definition")

        # Check for balanced braces
        brace_count = definition.count("{") - definition.count("}")
        if brace_count != 0:
            issues.append(f"Unbalanced braces (difference: {brace_count})")

        # Check for proper newcommand structure
        if "\\newcommand" in definition:
            if not re.search(r"\\newcommand\s*\{\\[^}]+\}", definition):
                issues.append("Invalid \\newcommand structure")

        if "\\newenvironment" in definition:
            if not re.search(r"\\newenvironment\s*\{[^}]+\}", definition):
                issues.append("Invalid \\newenvironment structure")

        return len(issues) == 0, issues

    def export_macros(
        self, macro_names: List[str] = None, include_dependencies: bool = True
    ) -> str:
        """Export macros as LaTeX code"""
        if macro_names is None:
            macro_names = list(self.macros.keys())

        if include_dependencies:
            # Get all dependencies
            all_deps = self.get_all_dependencies(macro_names)
            # Add package imports for dependencies
            package_imports = []
            for dep in all_deps:
                if dep not in [
                    "amsmath",
                    "amsfonts",
                ]:  # Skip commonly included packages
                    package_imports.append(f"\\usepackage{{{dep}}}")
        else:
            package_imports = []

        latex_code = []

        if package_imports:
            latex_code.append("% Package dependencies")
            latex_code.extend(package_imports)
            latex_code.append("")

        latex_code.append("% Custom macro definitions")

        for name in macro_names:
            if name in self.macros:
                macro = self.macros[name]
                latex_code.append(f"% {macro.description}")
                if macro.category:
                    latex_code.append(f"% Category: {macro.category}")
                latex_code.append(macro.definition)
                latex_code.append("")

        return "\n".join(latex_code)


class MacroProcessor:
    """Processes macros in template content"""

    def __init__(self, registry: MacroRegistry):
        """Initialize macro processor"""
        self.registry = registry

    def extract_macro_usage(self, content: str) -> List[str]:
        """Extract macro names used in content"""
        used_macros = set()

        # Find custom commands
        command_pattern = r"\\([a-zA-Z]+)(?:\[[^\]]*\])?(?:\{[^}]*\})*"
        commands = re.findall(command_pattern, content)

        for cmd in commands:
            if cmd in self.registry.macros:
                used_macros.add(cmd)

        # Find custom environments
        env_pattern = r"\\begin\{([^}]+)\}"
        environments = re.findall(env_pattern, content)

        for env in environments:
            if env in self.registry.macros:
                used_macros.add(env)

        return list(used_macros)

    def generate_macro_preamble(self, content: str) -> str:
        """Generate macro preamble for template content"""
        used_macros = self.extract_macro_usage(content)
        return self.registry.export_macros(used_macros, include_dependencies=True)

    def validate_macro_usage(self, content: str) -> List[str]:
        """Validate macro usage in content"""
        issues = []
        used_macros = self.extract_macro_usage(content)

        for macro_name in used_macros:
            macro = self.registry.get_macro(macro_name)
            if not macro:
                issues.append(f"Unknown macro: {macro_name}")
                continue

            # Count usage and check parameter count
            if macro.macro_type == MacroType.COMMAND:
                pattern = rf"\\{macro_name}(?:\[[^\]]*\])?(\{{[^}}]*\}})*"
                matches = re.findall(pattern, content)

                for match in matches:
                    param_count = len([m for m in match if m])
                    if param_count != macro.parameters:
                        issues.append(
                            f"Macro {macro_name} expects {macro.parameters} parameters, got {param_count}"
                        )

        return issues


class MacroLibrary:
    """Library of reusable macro collections"""

    def __init__(self, library_path: Optional[str] = None):
        """Initialize macro library"""
        self.library_path = (
            Path(library_path)
            if library_path
            else Path(__file__).parent / "macro_library"
        )
        self.collections: Dict[str, Dict[str, MacroDefinition]] = {}
        self._load_collections()

    def _load_collections(self) -> None:
        """Load macro collections from library directory"""
        if not self.library_path.exists():
            self.library_path.mkdir(parents=True, exist_ok=True)
            self._create_default_collections()

        for collection_file in self.library_path.glob("*.yaml"):
            collection_name = collection_file.stem
            try:
                with open(collection_file, "r", encoding="utf-8") as f:
                    collection_data = yaml.safe_load(f)

                self.collections[collection_name] = {}
                for macro_data in collection_data.get("macros", []):
                    macro = MacroDefinition(**macro_data)
                    self.collections[collection_name][macro.name] = macro

                logger.info(f"Loaded macro collection: {collection_name}")

            except Exception as e:
                logger.error(f"Failed to load macro collection {collection_file}: {e}")

    def _create_default_collections(self) -> None:
        """Create default macro collections"""
        resume_collection = {
            "name": "Resume Macros",
            "description": "Standard macros for resume templates",
            "macros": [
                {
                    "name": "resumeSection",
                    "macro_type": "command",
                    "definition": r"\newcommand{\resumeSection}[1]{\section*{#1}\vspace{-0.3em}\hrule\vspace{0.5em}}",
                    "parameters": 1,
                    "description": "Create a resume section with underline",
                    "category": "resume",
                },
                {
                    "name": "experienceEntry",
                    "macro_type": "command",
                    "definition": r"\newcommand{\experienceEntry}[4]{\noindent\textbf{#1} \hfill \textit{#2} \\ \textit{#3} \\ #4 \vspace{0.5em}}",
                    "parameters": 4,
                    "description": "Format experience entry with company, dates, position, description",
                    "category": "resume",
                },
            ],
        }

        cover_letter_collection = {
            "name": "Cover Letter Macros",
            "description": "Standard macros for cover letter templates",
            "macros": [
                {
                    "name": "letterHeader",
                    "macro_type": "command",
                    "definition": r"\newcommand{\letterHeader}[3]{\begin{flushright}#1\\#2\\#3\end{flushright}\vspace{1em}}",
                    "parameters": 3,
                    "description": "Format letter header with name, address, date",
                    "category": "cover_letter",
                },
                {
                    "name": "salutation",
                    "macro_type": "command",
                    "definition": r"\newcommand{\salutation}[1]{Dear #1,\vspace{1em}}",
                    "parameters": 1,
                    "description": "Format salutation",
                    "category": "cover_letter",
                },
            ],
        }

        # Save collections
        collections = [
            ("resume", resume_collection),
            ("cover_letter", cover_letter_collection),
        ]

        for name, collection in collections:
            collection_file = self.library_path / f"{name}.yaml"
            with open(collection_file, "w", encoding="utf-8") as f:
                yaml.dump(collection, f, default_flow_style=False, sort_keys=False)

    def get_collection(self, name: str) -> Dict[str, MacroDefinition]:
        """Get macro collection by name"""
        return self.collections.get(name, {})

    def list_collections(self) -> List[str]:
        """List available collections"""
        return list(self.collections.keys())

    def install_collection(self, collection_name: str, registry: MacroRegistry) -> None:
        """Install a collection into a macro registry"""
        if collection_name not in self.collections:
            raise ValueError(f"Collection '{collection_name}' not found")

        for macro in self.collections[collection_name].values():
            registry.register_macro(macro)

    def create_collection(
        self, name: str, macros: List[MacroDefinition], description: str = ""
    ) -> None:
        """Create a new macro collection"""
        collection_data = {
            "name": name.title() + " Macros",
            "description": description or f"Custom macro collection: {name}",
            "macros": [
                {
                    "name": macro.name,
                    "macro_type": macro.macro_type.value,
                    "definition": macro.definition,
                    "parameters": macro.parameters,
                    "optional_params": macro.optional_params,
                    "description": macro.description,
                    "category": macro.category,
                    "dependencies": macro.dependencies,
                }
                for macro in macros
            ],
        }

        collection_file = self.library_path / f"{name}.yaml"
        with open(collection_file, "w", encoding="utf-8") as f:
            yaml.dump(collection_data, f, default_flow_style=False, sort_keys=False)

        # Load into memory
        self.collections[name] = {macro.name: macro for macro in macros}
