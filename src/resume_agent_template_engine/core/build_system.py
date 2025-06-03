import os
import subprocess
import concurrent.futures
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import logging
import tempfile
import shutil
import hashlib
import pickle
import time
from dataclasses import dataclass, field
from enum import Enum
import platform
import json
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class BuildStatus(str, Enum):
    """Build status enumeration"""

    PENDING = "pending"
    BUILDING = "building"
    SUCCESS = "success"
    FAILED = "failed"
    CACHED = "cached"


class LatexEngine(str, Enum):
    """Supported LaTeX engines"""

    PDFLATEX = "pdflatex"
    XELATEX = "xelatex"
    LUALATEX = "lualatex"


@dataclass
class BuildRequest:
    """Represents a build request"""

    id: str
    template_path: str
    output_path: str
    latex_content: str
    engine: LatexEngine = LatexEngine.PDFLATEX
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique build ID"""
        content_hash = hashlib.md5(self.latex_content.encode()).hexdigest()[:8]
        timestamp = str(int(time.time()))[-6:]
        return f"build_{content_hash}_{timestamp}"


@dataclass
class BuildResult:
    """Represents a build result"""

    request_id: str
    status: BuildStatus
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    build_time: float = 0.0
    logs: List[str] = field(default_factory=list)
    artifacts: Dict[str, str] = field(default_factory=dict)


class DependencyResolver:
    """Resolves LaTeX package dependencies"""

    def __init__(self):
        """Initialize dependency resolver"""
        self.package_info = self._load_package_info()
        self.system_packages = self._detect_system_packages()

    def _load_package_info(self) -> Dict[str, Dict[str, Any]]:
        """Load package information database"""
        # This would ideally load from a comprehensive package database
        return {
            "geometry": {"description": "Page layout", "conflicts": []},
            "fontenc": {"description": "Font encoding", "conflicts": []},
            "inputenc": {"description": "Input encoding", "conflicts": []},
            "babel": {"description": "Multilingual support", "conflicts": []},
            "hyperref": {
                "description": "Hyperlinks",
                "conflicts": ["url"],
                "load_order": "late",
            },
            "graphicx": {"description": "Graphics inclusion", "conflicts": []},
            "xcolor": {"description": "Color support", "conflicts": ["color"]},
            "enumitem": {"description": "List customization", "conflicts": []},
            "titlesec": {"description": "Section title formatting", "conflicts": []},
            "fancyhdr": {"description": "Header and footer", "conflicts": []},
            "microtype": {"description": "Typography enhancement", "conflicts": []},
            "amsmath": {"description": "AMS math", "conflicts": []},
            "amsfonts": {"description": "AMS fonts", "conflicts": []},
            "amssymb": {"description": "AMS symbols", "conflicts": []},
        }

    def _detect_system_packages(self) -> List[str]:
        """Detect available system packages"""
        available_packages = []

        # Try to detect packages by attempting to compile a test document
        test_packages = list(self.package_info.keys())

        for package in test_packages:
            if self._test_package_availability(package):
                available_packages.append(package)

        return available_packages

    def _test_package_availability(self, package: str) -> bool:
        """Test if a package is available on the system"""
        test_content = f"""
\\documentclass{{article}}
\\usepackage{{{package}}}
\\begin{{document}}
Test
\\end{{document}}
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            tex_file = Path(temp_dir) / "test.tex"

            try:
                with open(tex_file, "w", encoding="utf-8") as f:
                    f.write(test_content)

                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "test.tex"],
                    cwd=temp_dir,
                    capture_output=True,
                    timeout=30,
                )

                return result.returncode == 0

            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False

    def resolve_dependencies(self, packages: List[str]) -> Tuple[List[str], List[str]]:
        """
        Resolve package dependencies and conflicts

        Returns:
            Tuple of (resolved_packages, conflicts)
        """
        resolved = []
        conflicts = []
        late_load = []

        for package in packages:
            if package not in self.package_info:
                resolved.append(package)  # Unknown package, assume it's valid
                continue

            package_info = self.package_info[package]

            # Check for conflicts
            for conflict in package_info.get("conflicts", []):
                if conflict in packages:
                    conflicts.append(f"{package} conflicts with {conflict}")

            # Check load order
            if package_info.get("load_order") == "late":
                late_load.append(package)
            else:
                resolved.append(package)

        # Add late-loading packages at the end
        resolved.extend(late_load)

        return resolved, conflicts

    def get_missing_packages(self, packages: List[str]) -> List[str]:
        """Get list of packages not available on the system"""
        return [pkg for pkg in packages if pkg not in self.system_packages]


class BuildCache:
    """Caches build results to speed up repeated builds"""

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize build cache"""
        self.cache_dir = (
            Path(cache_dir) if cache_dir else Path.home() / ".resume_agent_cache"
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_index = self._load_cache_index()

    def _load_cache_index(self) -> Dict[str, Dict[str, Any]]:
        """Load cache index"""
        index_file = self.cache_dir / "index.json"
        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache index: {e}")

        return {}

    def _save_cache_index(self) -> None:
        """Save cache index"""
        index_file = self.cache_dir / "index.json"
        try:
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(self.cache_index, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")

    def _get_content_hash(self, content: str) -> str:
        """Generate hash for content"""
        return hashlib.sha256(content.encode()).hexdigest()

    def get_cached_result(
        self, latex_content: str, engine: LatexEngine
    ) -> Optional[str]:
        """Get cached build result if available"""
        content_hash = self._get_content_hash(latex_content)
        cache_key = f"{content_hash}_{engine.value}"

        if cache_key in self.cache_index:
            cache_entry = self.cache_index[cache_key]
            cached_file = self.cache_dir / cache_entry["filename"]

            if cached_file.exists():
                return str(cached_file)

        return None

    def cache_result(
        self, latex_content: str, engine: LatexEngine, output_file: str
    ) -> None:
        """Cache a build result"""
        content_hash = self._get_content_hash(latex_content)
        cache_key = f"{content_hash}_{engine.value}"
        cached_filename = f"{cache_key}.pdf"
        cached_file = self.cache_dir / cached_filename

        try:
            shutil.copy2(output_file, cached_file)

            self.cache_index[cache_key] = {
                "filename": cached_filename,
                "created_at": time.time(),
                "engine": engine.value,
                "size": os.path.getsize(output_file),
            }

            self._save_cache_index()
            logger.info(f"Cached build result: {cache_key}")

        except Exception as e:
            logger.error(f"Failed to cache result: {e}")

    def cleanup_old_entries(self, max_age_days: int = 30) -> None:
        """Clean up old cache entries"""
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600

        keys_to_remove = []

        for cache_key, entry in self.cache_index.items():
            if current_time - entry["created_at"] > max_age_seconds:
                cached_file = self.cache_dir / entry["filename"]
                if cached_file.exists():
                    cached_file.unlink()
                keys_to_remove.append(cache_key)

        for key in keys_to_remove:
            del self.cache_index[key]

        self._save_cache_index()
        logger.info(f"Cleaned up {len(keys_to_remove)} old cache entries")


class ParallelBuilder:
    """Handles parallel PDF generation"""

    def __init__(self, max_workers: int = None, cache_dir: Optional[str] = None):
        """
        Initialize parallel builder

        Args:
            max_workers: Maximum number of worker threads
            cache_dir: Directory for build cache
        """
        self.max_workers = max_workers or min(4, (os.cpu_count() or 1) + 1)
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.build_queue: Dict[str, BuildRequest] = {}
        self.results: Dict[str, BuildResult] = {}
        self.cache = BuildCache(cache_dir)
        self.dependency_resolver = DependencyResolver()
        self._lock = threading.Lock()

    def submit_build(self, request: BuildRequest) -> str:
        """Submit a build request"""
        with self._lock:
            self.build_queue[request.id] = request

            # Check cache first
            cached_result = self.cache.get_cached_result(
                request.latex_content, request.engine
            )
            if cached_result:
                result = BuildResult(
                    request_id=request.id,
                    status=BuildStatus.CACHED,
                    output_path=cached_result,
                    build_time=0.0,
                )
                self.results[request.id] = result
                return request.id

            # Submit for building
            future = self.executor.submit(self._build_document, request)
            future.add_done_callback(
                lambda f: self._handle_build_completion(request.id, f)
            )

            return request.id

    def get_build_status(self, request_id: str) -> Optional[BuildResult]:
        """Get build status for a request"""
        return self.results.get(request_id)

    def wait_for_build(
        self, request_id: str, timeout: Optional[float] = None
    ) -> BuildResult:
        """Wait for a build to complete"""
        start_time = time.time()

        while request_id not in self.results:
            if timeout and (time.time() - start_time) > timeout:
                return BuildResult(
                    request_id=request_id,
                    status=BuildStatus.FAILED,
                    error_message="Build timeout",
                )

            time.sleep(0.1)

        return self.results[request_id]

    def _build_document(self, request: BuildRequest) -> BuildResult:
        """Build a single document"""
        start_time = time.time()

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                tex_file = temp_path / "document.tex"

                # Write LaTeX content
                with open(tex_file, "w", encoding="utf-8") as f:
                    f.write(request.latex_content)

                # Build PDF
                success, logs = self._compile_latex(tex_file, request.engine)

                if success:
                    pdf_file = tex_file.with_suffix(".pdf")
                    if pdf_file.exists():
                        # Copy to output location
                        os.makedirs(os.path.dirname(request.output_path), exist_ok=True)
                        shutil.copy2(pdf_file, request.output_path)

                        # Cache the result
                        self.cache.cache_result(
                            request.latex_content, request.engine, request.output_path
                        )

                        build_time = time.time() - start_time
                        return BuildResult(
                            request_id=request.id,
                            status=BuildStatus.SUCCESS,
                            output_path=request.output_path,
                            build_time=build_time,
                            logs=logs,
                        )
                    else:
                        return BuildResult(
                            request_id=request.id,
                            status=BuildStatus.FAILED,
                            error_message="PDF file not generated",
                            logs=logs,
                        )
                else:
                    return BuildResult(
                        request_id=request.id,
                        status=BuildStatus.FAILED,
                        error_message="LaTeX compilation failed",
                        logs=logs,
                    )

        except Exception as e:
            return BuildResult(
                request_id=request.id,
                status=BuildStatus.FAILED,
                error_message=str(e),
                build_time=time.time() - start_time,
            )

    def _compile_latex(
        self, tex_file: Path, engine: LatexEngine
    ) -> Tuple[bool, List[str]]:
        """Compile LaTeX document"""
        logs = []

        try:
            # Run LaTeX compilation (potentially multiple times for references)
            for run in range(2):  # Usually 2 runs are sufficient
                result = subprocess.run(
                    [engine.value, "-interaction=nonstopmode", str(tex_file.name)],
                    cwd=tex_file.parent,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                logs.append(f"Run {run + 1} output:")
                logs.append(result.stdout)
                if result.stderr:
                    logs.append("Errors:")
                    logs.append(result.stderr)

                if result.returncode != 0:
                    return False, logs

            return True, logs

        except subprocess.TimeoutExpired:
            logs.append("LaTeX compilation timed out")
            return False, logs
        except FileNotFoundError:
            logs.append(f"LaTeX engine '{engine.value}' not found")
            return False, logs
        except Exception as e:
            logs.append(f"Compilation error: {e}")
            return False, logs

    def _handle_build_completion(self, request_id: str, future):
        """Handle completion of a build"""
        try:
            result = future.result()
            with self._lock:
                self.results[request_id] = result
        except Exception as e:
            with self._lock:
                self.results[request_id] = BuildResult(
                    request_id=request_id,
                    status=BuildStatus.FAILED,
                    error_message=f"Build execution error: {e}",
                )

    def shutdown(self):
        """Shutdown the parallel builder"""
        self.executor.shutdown(wait=True)


class CrossPlatformBuilder:
    """Cross-platform build system"""

    def __init__(self):
        """Initialize cross-platform builder"""
        self.platform = platform.system().lower()
        self.latex_installations = self._detect_latex_installations()
        self.preferred_engine = self._get_preferred_engine()

    def _detect_latex_installations(self) -> Dict[str, str]:
        """Detect available LaTeX installations"""
        installations = {}

        engines_to_check = ["pdflatex", "xelatex", "lualatex"]

        for engine in engines_to_check:
            try:
                result = subprocess.run(
                    [engine, "--version"], capture_output=True, text=True, timeout=10
                )

                if result.returncode == 0:
                    installations[engine] = shutil.which(engine)

            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        return installations

    def _get_preferred_engine(self) -> LatexEngine:
        """Get preferred LaTeX engine based on platform and availability"""
        if "xelatex" in self.latex_installations:
            return LatexEngine.XELATEX  # Better Unicode support
        elif "pdflatex" in self.latex_installations:
            return LatexEngine.PDFLATEX  # Most compatible
        elif "lualatex" in self.latex_installations:
            return LatexEngine.LUALATEX  # Modern alternative
        else:
            return LatexEngine.PDFLATEX  # Fallback

    def get_build_environment(self) -> Dict[str, str]:
        """Get build environment variables"""
        env = os.environ.copy()

        # Platform-specific adjustments
        if self.platform == "windows":
            # Ensure proper PATH for MiKTeX/TeX Live
            tex_paths = [
                r"C:\Program Files\MiKTeX\miktex\bin\x64",
                r"C:\texlive\2023\bin\win32",
                r"C:\texlive\2022\bin\win32",
            ]

            for tex_path in tex_paths:
                if os.path.exists(tex_path):
                    env["PATH"] = tex_path + os.pathsep + env.get("PATH", "")
                    break

        elif self.platform == "darwin":  # macOS
            # Ensure proper PATH for MacTeX
            mactex_paths = [
                "/usr/local/texlive/2023/bin/universal-darwin",
                "/usr/local/texlive/2022/bin/universal-darwin",
                "/Library/TeX/texbin",
            ]

            for tex_path in mactex_paths:
                if os.path.exists(tex_path):
                    env["PATH"] = tex_path + os.pathsep + env.get("PATH", "")
                    break

        # Set font cache directory
        if "FONTCONFIG_PATH" not in env:
            font_cache_dir = Path.home() / ".fontconfig"
            font_cache_dir.mkdir(exist_ok=True)
            env["FONTCONFIG_PATH"] = str(font_cache_dir)

        return env

    def optimize_for_platform(self, latex_content: str) -> str:
        """Optimize LaTeX content for current platform"""
        # Platform-specific optimizations
        if self.platform == "windows":
            # Ensure proper line endings
            latex_content = latex_content.replace("\n", "\r\n")

        # Font handling optimizations
        if "fontspec" in latex_content and self.preferred_engine in [
            LatexEngine.XELATEX,
            LatexEngine.LUALATEX,
        ]:
            # Add platform-specific font fallbacks
            if self.platform == "windows":
                latex_content = latex_content.replace(
                    "\\setmainfont{", "\\setmainfont[Ligatures=TeX]{"
                )
            elif self.platform == "darwin":
                # macOS font optimizations
                latex_content = latex_content.replace(
                    "\\setmainfont{Times New Roman}", "\\setmainfont{Times}"
                )

        return latex_content
