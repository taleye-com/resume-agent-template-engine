import os
import subprocess
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class FontEngine(str, Enum):
    """Font engines for LaTeX"""

    PDFLATEX = "pdflatex"
    XELATEX = "xelatex"
    LUALATEX = "lualatex"


@dataclass
class FontDefinition:
    """Definition of a font"""

    name: str
    family: str  # serif, sans, mono
    file_path: Optional[str] = None
    system_name: Optional[str] = None
    latex_package: Optional[str] = None
    engine_support: List[FontEngine] = None
    features: List[str] = None

    def __post_init__(self):
        if self.engine_support is None:
            self.engine_support = [
                FontEngine.PDFLATEX,
                FontEngine.XELATEX,
                FontEngine.LUALATEX,
            ]
        if self.features is None:
            self.features = []


class FontManager:
    """Manages fonts for LaTeX compilation"""

    def __init__(self):
        """Initialize font manager"""
        self.platform = platform.system().lower()
        self.system_fonts = self._detect_system_fonts()
        self.latex_fonts = self._get_latex_fonts()
        self.font_cache = {}

    def _detect_system_fonts(self) -> Dict[str, FontDefinition]:
        """Detect available system fonts"""
        fonts = {}

        # Common fonts across platforms
        common_fonts = [
            FontDefinition("Times New Roman", "serif", system_name="Times New Roman"),
            FontDefinition("Arial", "sans", system_name="Arial"),
            FontDefinition("Helvetica", "sans", system_name="Helvetica"),
            FontDefinition("Courier New", "mono", system_name="Courier New"),
            FontDefinition("Georgia", "serif", system_name="Georgia"),
        ]

        # Platform-specific fonts
        if self.platform == "darwin":  # macOS
            macos_fonts = [
                FontDefinition("SF Pro", "sans", system_name="SF Pro"),
                FontDefinition("Menlo", "mono", system_name="Menlo"),
                FontDefinition("Avenir", "sans", system_name="Avenir"),
            ]
            common_fonts.extend(macos_fonts)

        elif self.platform == "windows":
            windows_fonts = [
                FontDefinition("Segoe UI", "sans", system_name="Segoe UI"),
                FontDefinition("Consolas", "mono", system_name="Consolas"),
                FontDefinition("Calibri", "sans", system_name="Calibri"),
            ]
            common_fonts.extend(windows_fonts)

        elif self.platform == "linux":
            linux_fonts = [
                FontDefinition(
                    "Liberation Serif", "serif", system_name="Liberation Serif"
                ),
                FontDefinition(
                    "Liberation Sans", "sans", system_name="Liberation Sans"
                ),
                FontDefinition(
                    "Liberation Mono", "mono", system_name="Liberation Mono"
                ),
            ]
            common_fonts.extend(linux_fonts)

        for font in common_fonts:
            if self._is_font_available(font):
                fonts[font.name] = font

        return fonts

    def _get_latex_fonts(self) -> Dict[str, FontDefinition]:
        """Get LaTeX package-based fonts"""
        return {
            "Latin Modern": FontDefinition(
                "Latin Modern",
                "serif",
                latex_package="lmodern",
                engine_support=[
                    FontEngine.PDFLATEX,
                    FontEngine.XELATEX,
                    FontEngine.LUALATEX,
                ],
            ),
            "Computer Modern": FontDefinition(
                "Computer Modern", "serif", engine_support=[FontEngine.PDFLATEX]
            ),
            "TeX Gyre Termes": FontDefinition(
                "TeX Gyre Termes",
                "serif",
                latex_package="tgtermes",
                engine_support=[
                    FontEngine.PDFLATEX,
                    FontEngine.XELATEX,
                    FontEngine.LUALATEX,
                ],
            ),
            "TeX Gyre Heros": FontDefinition(
                "TeX Gyre Heros",
                "sans",
                latex_package="tgheros",
                engine_support=[
                    FontEngine.PDFLATEX,
                    FontEngine.XELATEX,
                    FontEngine.LUALATEX,
                ],
            ),
            "TeX Gyre Cursor": FontDefinition(
                "TeX Gyre Cursor",
                "mono",
                latex_package="tgcursor",
                engine_support=[
                    FontEngine.PDFLATEX,
                    FontEngine.XELATEX,
                    FontEngine.LUALATEX,
                ],
            ),
            "Source Sans Pro": FontDefinition(
                "Source Sans Pro",
                "sans",
                latex_package="sourcesanspro",
                engine_support=[
                    FontEngine.PDFLATEX,
                    FontEngine.XELATEX,
                    FontEngine.LUALATEX,
                ],
            ),
            "Source Code Pro": FontDefinition(
                "Source Code Pro",
                "mono",
                latex_package="sourcecodepro",
                engine_support=[
                    FontEngine.PDFLATEX,
                    FontEngine.XELATEX,
                    FontEngine.LUALATEX,
                ],
            ),
        }

    def _is_font_available(self, font: FontDefinition) -> bool:
        """Check if a font is available on the system"""
        if font.system_name:
            return self._check_system_font(font.system_name)
        elif font.latex_package:
            return self._check_latex_package(font.latex_package)
        return False

    def _check_system_font(self, font_name: str) -> bool:
        """Check if system font is available"""
        try:
            if self.platform == "darwin":
                # Use system_profiler on macOS
                result = subprocess.run(
                    ["fc-list", ":", "family"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                return font_name.lower() in result.stdout.lower()

            elif self.platform in ["linux", "windows"]:
                # Use fc-list on Linux/Windows with fontconfig
                result = subprocess.run(
                    ["fc-list", ":", "family"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                return font_name.lower() in result.stdout.lower()

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return False

    def _check_latex_package(self, package_name: str) -> bool:
        """Check if LaTeX package is available"""
        try:
            test_content = f"""
\\documentclass{{article}}
\\usepackage{{{package_name}}}
\\begin{{document}}
Test
\\end{{document}}
"""

            import tempfile

            with tempfile.TemporaryDirectory() as temp_dir:
                tex_file = Path(temp_dir) / "test.tex"
                with open(tex_file, "w") as f:
                    f.write(test_content)

                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "test.tex"],
                    cwd=temp_dir,
                    capture_output=True,
                    timeout=30,
                )
                return result.returncode == 0

        except Exception:
            return False

    def get_available_fonts(
        self, family: Optional[str] = None, engine: Optional[FontEngine] = None
    ) -> List[FontDefinition]:
        """Get available fonts filtered by family and engine"""
        all_fonts = {**self.system_fonts, **self.latex_fonts}
        fonts = []

        for font in all_fonts.values():
            # Filter by family
            if family and font.family != family:
                continue

            # Filter by engine support
            if engine and engine not in font.engine_support:
                continue

            fonts.append(font)

        return fonts

    def get_font_config(self, font_name: str, engine: FontEngine) -> Optional[str]:
        """Get LaTeX configuration for a font"""
        # Check system fonts first
        if font_name in self.system_fonts:
            font = self.system_fonts[font_name]
            return self._generate_font_config(font, engine)

        # Check LaTeX fonts
        if font_name in self.latex_fonts:
            font = self.latex_fonts[font_name]
            return self._generate_font_config(font, engine)

        return None

    def _generate_font_config(self, font: FontDefinition, engine: FontEngine) -> str:
        """Generate LaTeX font configuration"""
        if engine == FontEngine.PDFLATEX:
            if font.latex_package:
                return f"\\usepackage{{{font.latex_package}}}"
            else:
                # Use default fonts for pdflatex
                return ""

        elif engine in [FontEngine.XELATEX, FontEngine.LUALATEX]:
            if font.system_name:
                if font.family == "serif":
                    return f"\\setmainfont{{{font.system_name}}}"
                elif font.family == "sans":
                    return f"\\setsansfont{{{font.system_name}}}"
                elif font.family == "mono":
                    return f"\\setmonofont{{{font.system_name}}}"
            elif font.latex_package:
                return f"\\usepackage{{{font.latex_package}}}"

        return ""

    def generate_font_preamble(
        self, font_config: Dict[str, str], engine: FontEngine
    ) -> str:
        """Generate complete font preamble"""
        preamble_parts = []

        # Add fontspec for XeLaTeX/LuaLaTeX
        if engine in [FontEngine.XELATEX, FontEngine.LUALATEX]:
            preamble_parts.append("\\usepackage{fontspec}")

        # Add font configurations
        for font_type, font_name in font_config.items():
            config = self.get_font_config(font_name, engine)
            if config:
                preamble_parts.append(config)

        return "\n".join(preamble_parts)

    def optimize_for_engine(
        self, font_config: Dict[str, str], engine: FontEngine
    ) -> Dict[str, str]:
        """Optimize font configuration for specific engine"""
        optimized = {}

        for font_type, font_name in font_config.items():
            # Get available fonts for this engine
            available = self.get_available_fonts(engine=engine)
            available_names = [f.name for f in available]

            if font_name in available_names:
                optimized[font_type] = font_name
            else:
                # Find fallback
                fallback = self._find_fallback_font(font_name, engine)
                if fallback:
                    optimized[font_type] = fallback.name
                    logger.info(f"Using fallback font {fallback.name} for {font_name}")

        return optimized

    def _find_fallback_font(
        self, requested_font: str, engine: FontEngine
    ) -> Optional[FontDefinition]:
        """Find fallback font for requested font"""
        # Try to determine font family from requested font
        family = self._guess_font_family(requested_font)

        # Get available fonts for this family and engine
        available = self.get_available_fonts(family=family, engine=engine)

        if available:
            # Return first available font in family
            return available[0]

        # Fallback to any available font
        all_available = self.get_available_fonts(engine=engine)
        return all_available[0] if all_available else None

    def _guess_font_family(self, font_name: str) -> str:
        """Guess font family from font name"""
        font_lower = font_name.lower()

        serif_keywords = ["times", "georgia", "garamond", "serif", "book"]
        mono_keywords = ["courier", "mono", "code", "console", "terminal"]

        if any(keyword in font_lower for keyword in mono_keywords):
            return "mono"
        elif any(keyword in font_lower for keyword in serif_keywords):
            return "serif"
        else:
            return "sans"

    def get_font_recommendations(
        self, engine: FontEngine, use_case: str = "resume"
    ) -> Dict[str, str]:
        """Get font recommendations for specific use case"""
        recommendations = {
            "resume": {
                "serif": ["TeX Gyre Termes", "Times New Roman", "Georgia"],
                "sans": ["TeX Gyre Heros", "Helvetica", "Arial", "Calibri"],
                "mono": ["TeX Gyre Cursor", "Courier New", "Consolas"],
            },
            "cover_letter": {
                "serif": ["TeX Gyre Termes", "Times New Roman", "Georgia"],
                "sans": ["Source Sans Pro", "Helvetica", "Arial"],
                "mono": ["Source Code Pro", "Courier New"],
            },
        }

        use_case_fonts = recommendations.get(use_case, recommendations["resume"])
        result = {}

        for family, font_list in use_case_fonts.items():
            for font_name in font_list:
                available = self.get_available_fonts(family=family, engine=engine)
                available_names = [f.name for f in available]

                if font_name in available_names:
                    result[family] = font_name
                    break

        return result


class FontConfigGenerator:
    """Generates font configurations for templates"""

    def __init__(self, font_manager: FontManager):
        """Initialize font config generator"""
        self.font_manager = font_manager

    def generate_template_fonts(
        self, template_config: Dict[str, Any], engine: FontEngine
    ) -> str:
        """Generate font configuration for template"""
        font_config = template_config.get("fonts", {})

        # Use recommendations if no specific fonts configured
        if not font_config:
            template_type = template_config.get("type", "resume")
            font_config = self.font_manager.get_font_recommendations(
                engine, template_type
            )

        # Optimize for engine
        optimized_config = self.font_manager.optimize_for_engine(font_config, engine)

        # Generate preamble
        return self.font_manager.generate_font_preamble(optimized_config, engine)

    def validate_font_config(
        self, font_config: Dict[str, str], engine: FontEngine
    ) -> List[str]:
        """Validate font configuration"""
        issues = []

        for font_type, font_name in font_config.items():
            config = self.font_manager.get_font_config(font_name, engine)
            if not config:
                issues.append(f"Font '{font_name}' not available for {engine.value}")

        return issues
