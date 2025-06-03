import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
from enum import Enum
import tempfile
import shutil
import importlib.util

from .base_validator import BaseValidator, ValidationSeverity, ValidationIssue

logger = logging.getLogger(__name__)


class TemplateValidator(BaseValidator):
    """Comprehensive template validation system"""

    def __init__(self, latex_engine: str = "pdflatex"):
        """
        Initialize template validator

        Args:
            latex_engine: LaTeX engine to use for compilation tests
        """
        super().__init__()
        self.latex_engine = latex_engine
        self.required_latex_packages = {
            "geometry",
            "fontenc",
            "inputenc",
            "babel",
            "amsmath",
            "amsfonts",
            "amssymb",
            "graphicx",
            "xcolor",
            "hyperref",
            "enumitem",
            "titlesec",
        }
        self.security_patterns = [
            r"\\write18",  # Shell escape
            r"\\immediate\\write18",  # Immediate shell escape
            r"\\input\s*\|",  # Pipe input
            r"\\openin\s*\\",  # File reading
            r"\\openout\s*\\",  # File writing
        ]

    def validate(
        self, template_path: str, sample_data: Optional[Dict[str, Any]] = None
    ) -> List[ValidationIssue]:
        """
        Implementation of abstract validate method from BaseValidator

        Args:
            template_path: Path to template directory
            sample_data: Sample data for testing template rendering

        Returns:
            List of validation issues
        """
        return self.validate_template(template_path, sample_data)

    def validate_template(
        self, template_path: str, sample_data: Optional[Dict[str, Any]] = None
    ) -> List[ValidationIssue]:
        """
        Perform comprehensive template validation

        Args:
            template_path: Path to template directory
            sample_data: Sample data for testing template rendering

        Returns:
            List of validation issues
        """
        issues = []
        template_dir = Path(template_path)

        if not template_dir.exists():
            issues.append(
                ValidationIssue(
                    ValidationSeverity.ERROR,
                    f"Template directory does not exist: {template_path}",
                )
            )
            return issues

        # Validate directory structure
        issues.extend(self._validate_directory_structure(template_dir))

        # Validate helper.py file
        helper_file = template_dir / "helper.py"
        if helper_file.exists():
            issues.extend(self._validate_helper_file(helper_file))

        # Validate LaTeX files
        for tex_file in template_dir.glob("*.tex"):
            issues.extend(self._validate_latex_file(tex_file))

        # Test template compilation if sample data provided
        if sample_data and helper_file.exists():
            issues.extend(self._test_template_compilation(template_dir, sample_data))

        return issues

    def _validate_directory_structure(
        self, template_dir: Path
    ) -> List[ValidationIssue]:
        """Validate template directory structure"""
        issues = []

        # Check for required files
        helper_file = template_dir / "helper.py"
        if not helper_file.exists():
            issues.append(
                ValidationIssue(
                    ValidationSeverity.ERROR,
                    "Missing required helper.py file",
                    str(template_dir),
                )
            )

        # Check for LaTeX files
        tex_files = list(template_dir.glob("*.tex"))
        if not tex_files:
            issues.append(
                ValidationIssue(
                    ValidationSeverity.ERROR,
                    "No LaTeX (.tex) files found",
                    str(template_dir),
                )
            )

        # Check for README or documentation
        doc_files = list(template_dir.glob("README*")) + list(template_dir.glob("*.md"))
        if not doc_files:
            issues.append(
                ValidationIssue(
                    ValidationSeverity.WARNING,
                    "No documentation (README) file found",
                    str(template_dir),
                )
            )

        # Check for template metadata
        metadata_files = list(template_dir.glob("template.yaml")) + list(
            template_dir.glob("metadata.json")
        )
        if not metadata_files:
            issues.append(
                ValidationIssue(
                    ValidationSeverity.INFO,
                    "No template metadata file found (template.yaml or metadata.json)",
                    str(template_dir),
                )
            )

        return issues

    def _validate_helper_file(self, helper_file: Path) -> List[ValidationIssue]:
        """Validate helper.py file structure and content"""
        issues = []

        try:
            with open(helper_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for required class definition
            if not re.search(
                r"class\s+\w+Template\s*\([^)]*TemplateInterface[^)]*\):", content
            ):
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.ERROR,
                        "No template class inheriting from TemplateInterface found",
                        str(helper_file),
                    )
                )

            # Check for required methods
            required_methods = ["validate_data", "render", "export_to_pdf"]
            for method in required_methods:
                if not re.search(rf"def\s+{method}\s*\(", content):
                    issues.append(
                        ValidationIssue(
                            ValidationSeverity.ERROR,
                            f"Missing required method: {method}",
                            str(helper_file),
                        )
                    )

            # Check for required properties
            required_properties = ["required_fields", "template_type"]
            for prop in required_properties:
                if not re.search(rf"def\s+{prop}\s*\(", content) and not re.search(
                    rf"{prop}\s*=", content
                ):
                    issues.append(
                        ValidationIssue(
                            ValidationSeverity.ERROR,
                            f"Missing required property: {prop}",
                            str(helper_file),
                        )
                    )

            # Check for security issues
            for line_num, line in enumerate(content.split("\n"), 1):
                if "eval(" in line or "exec(" in line:
                    issues.append(
                        ValidationIssue(
                            ValidationSeverity.WARNING,
                            "Use of eval() or exec() detected - potential security risk",
                            str(helper_file),
                            line_num,
                        )
                    )

                if "__import__" in line:
                    issues.append(
                        ValidationIssue(
                            ValidationSeverity.WARNING,
                            "Use of __import__ detected - potential security risk",
                            str(helper_file),
                            line_num,
                        )
                    )

        except Exception as e:
            issues.append(
                ValidationIssue(
                    ValidationSeverity.ERROR,
                    f"Failed to read helper.py: {e}",
                    str(helper_file),
                )
            )

        return issues

    def _validate_latex_file(self, tex_file: Path) -> List[ValidationIssue]:
        """Validate LaTeX file content and structure"""
        issues = []

        try:
            with open(tex_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for document class
            if not re.search(r"\\documentclass", content):
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.ERROR,
                        "No \\documentclass declaration found",
                        str(tex_file),
                    )
                )

            # Check for document environment
            if "\\begin{document}" not in content:
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.ERROR,
                        "No \\begin{document} found",
                        str(tex_file),
                    )
                )

            if "\\end{document}" not in content:
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.ERROR,
                        "No \\end{document} found",
                        str(tex_file),
                    )
                )

            # Check for package usage
            packages_used = re.findall(
                r"\\usepackage(?:\[[^\]]*\])?\{([^}]+)\}", content
            )
            missing_packages = self.required_latex_packages - set(packages_used)

            if missing_packages:
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.WARNING,
                        f"Recommended packages not found: {', '.join(missing_packages)}",
                        str(tex_file),
                    )
                )

            # Check for security issues
            for line_num, line in enumerate(content.split("\n"), 1):
                for pattern in self.security_patterns:
                    if re.search(pattern, line):
                        issues.append(
                            ValidationIssue(
                                ValidationSeverity.ERROR,
                                f"Security risk detected: {pattern}",
                                str(tex_file),
                                line_num,
                            )
                        )

            # Check for template variables
            variables = re.findall(r"\{\{\s*([^}]+)\s*\}\}", content)
            if not variables:
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.WARNING,
                        "No template variables ({{ variable }}) found",
                        str(tex_file),
                    )
                )

            # Check for undefined references
            undefined_refs = re.findall(r"\\ref\{([^}]+)\}", content)
            defined_labels = re.findall(r"\\label\{([^}]+)\}", content)

            for ref in undefined_refs:
                if ref not in defined_labels:
                    issues.append(
                        ValidationIssue(
                            ValidationSeverity.WARNING,
                            f"Undefined reference: {ref}",
                            str(tex_file),
                        )
                    )

        except Exception as e:
            issues.append(
                ValidationIssue(
                    ValidationSeverity.ERROR,
                    f"Failed to read LaTeX file: {e}",
                    str(tex_file),
                )
            )

        return issues

    def _test_template_compilation(
        self, template_dir: Path, sample_data: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Test template compilation with sample data"""
        issues = []

        try:
            # Import template class dynamically
            import sys

            sys.path.insert(0, str(template_dir.parent))

            spec = importlib.util.spec_from_file_location(
                f"{template_dir.name}_helper", template_dir / "helper.py"
            )
            helper_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(helper_module)

            # Find template class
            template_class = None
            for attr_name in dir(helper_module):
                attr = getattr(helper_module, attr_name)
                if (
                    isinstance(attr, type)
                    and hasattr(attr, "render")
                    and hasattr(attr, "export_to_pdf")
                ):
                    template_class = attr
                    break

            if not template_class:
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.ERROR,
                        "No valid template class found in helper.py",
                        str(template_dir / "helper.py"),
                    )
                )
                return issues

            # Test template instantiation
            try:
                template_instance = template_class(sample_data)
            except Exception as e:
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.ERROR,
                        f"Failed to instantiate template: {e}",
                        str(template_dir / "helper.py"),
                    )
                )
                return issues

            # Test template rendering
            try:
                rendered_content = template_instance.render()
                if not rendered_content.strip():
                    issues.append(
                        ValidationIssue(
                            ValidationSeverity.ERROR,
                            "Template rendering produced empty content",
                            str(template_dir / "helper.py"),
                        )
                    )
            except Exception as e:
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.ERROR,
                        f"Template rendering failed: {e}",
                        str(template_dir / "helper.py"),
                    )
                )
                return issues

            # Test PDF compilation
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    output_path = os.path.join(temp_dir, "test.pdf")
                    template_instance.export_to_pdf(output_path)

                    if not os.path.exists(output_path):
                        issues.append(
                            ValidationIssue(
                                ValidationSeverity.ERROR,
                                "PDF compilation did not produce output file",
                                str(template_dir),
                            )
                        )
                    elif os.path.getsize(output_path) == 0:
                        issues.append(
                            ValidationIssue(
                                ValidationSeverity.ERROR,
                                "PDF compilation produced empty file",
                                str(template_dir),
                            )
                        )
                except Exception as e:
                    issues.append(
                        ValidationIssue(
                            ValidationSeverity.ERROR,
                            f"PDF compilation failed: {e}",
                            str(template_dir),
                        )
                    )

        except Exception as e:
            issues.append(
                ValidationIssue(
                    ValidationSeverity.ERROR,
                    f"Template compilation test failed: {e}",
                    str(template_dir),
                )
            )

        return issues

    def validate_latex_installation(self) -> List[ValidationIssue]:
        """Validate LaTeX installation and required packages"""
        issues = []

        # Check if LaTeX engine is available
        try:
            result = subprocess.run(
                [self.latex_engine, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.ERROR,
                        f"LaTeX engine '{self.latex_engine}' not working properly",
                    )
                )
        except FileNotFoundError:
            issues.append(
                ValidationIssue(
                    ValidationSeverity.ERROR,
                    f"LaTeX engine '{self.latex_engine}' not found",
                )
            )
        except subprocess.TimeoutExpired:
            issues.append(
                ValidationIssue(
                    ValidationSeverity.WARNING,
                    f"LaTeX engine '{self.latex_engine}' response timeout",
                )
            )

        # Test package availability
        test_packages = ["geometry", "fontenc", "hyperref", "xcolor"]
        for package in test_packages:
            if not self._test_latex_package(package):
                issues.append(
                    ValidationIssue(
                        ValidationSeverity.WARNING,
                        f"LaTeX package '{package}' may not be available",
                    )
                )

        return issues

    def _test_latex_package(self, package_name: str) -> bool:
        """Test if a LaTeX package is available"""
        test_content = f"""
\\documentclass{{article}}
\\usepackage{{{package_name}}}
\\begin{{document}}
Test
\\end{{document}}
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            tex_file = os.path.join(temp_dir, "test.tex")

            try:
                with open(tex_file, "w", encoding="utf-8") as f:
                    f.write(test_content)

                result = subprocess.run(
                    [self.latex_engine, "-interaction=nonstopmode", "test.tex"],
                    cwd=temp_dir,
                    capture_output=True,
                    timeout=30,
                )

                return result.returncode == 0

            except Exception:
                return False
