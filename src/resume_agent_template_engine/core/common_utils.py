import os
import re
import shutil
import tempfile
import subprocess
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FileOperations:
    """Common file operations to avoid duplication"""

    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Ensure directory exists, create if not"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def safe_copy(src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """Safely copy file with error handling"""
        try:
            src_path = Path(src)
            dst_path = Path(dst)

            # Ensure destination directory exists
            FileOperations.ensure_directory(dst_path.parent)

            shutil.copy2(src_path, dst_path)
            return True
        except Exception as e:
            logger.error(f"Failed to copy {src} to {dst}: {e}")
            return False

    @staticmethod
    def safe_remove(path: Union[str, Path]) -> bool:
        """Safely remove file with error handling"""
        try:
            path = Path(path)
            if path.exists():
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
            return True
        except Exception as e:
            logger.error(f"Failed to remove {path}: {e}")
            return False

    @staticmethod
    def get_file_hash(file_path: Union[str, Path], algorithm: str = "md5") -> str:
        """Get file hash for caching/comparison"""
        hasher = hashlib.new(algorithm)
        path = Path(file_path)

        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Failed to hash file {file_path}: {e}")
            return ""

    @staticmethod
    def read_file_safe(
        file_path: Union[str, Path], encoding: str = "utf-8"
    ) -> Optional[str]:
        """Safely read file content with error handling"""
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None

    @staticmethod
    def write_file_safe(
        file_path: Union[str, Path], content: str, encoding: str = "utf-8"
    ) -> bool:
        """Safely write file content with error handling"""
        try:
            path = Path(file_path)
            FileOperations.ensure_directory(path.parent)

            with open(path, "w", encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            return False


class SubprocessRunner:
    """Common subprocess operations with DRY principles"""

    @staticmethod
    def run_command(
        command: List[str],
        cwd: Optional[str] = None,
        timeout: float = 60,
        capture_output: bool = True,
    ) -> Dict[str, Any]:
        """Run subprocess command with standardized error handling"""
        result = {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "",
            "error_message": "",
        }

        try:
            process_result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
            )

            result.update(
                {
                    "success": process_result.returncode == 0,
                    "returncode": process_result.returncode,
                    "stdout": process_result.stdout,
                    "stderr": process_result.stderr,
                }
            )

        except subprocess.TimeoutExpired:
            result["error_message"] = f"Command timed out after {timeout} seconds"
        except FileNotFoundError:
            result["error_message"] = f"Command not found: {' '.join(command)}"
        except Exception as e:
            result["error_message"] = f"Command execution failed: {str(e)}"

        return result

    @staticmethod
    def check_command_exists(command: str) -> bool:
        """Check if command exists in PATH"""
        try:
            result = subprocess.run(
                ["which", command] if os.name != "nt" else ["where", command],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def run_latex_compilation(
        tex_file: Union[str, Path],
        engine: str = "pdflatex",
        working_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Standardized LaTeX compilation with error handling"""
        tex_path = Path(tex_file)

        if working_dir is None:
            working_dir = tex_path.parent

        command = [engine, "-interaction=nonstopmode", tex_path.name]

        result = SubprocessRunner.run_command(command, cwd=working_dir, timeout=120)

        # Check for PDF output
        pdf_file = Path(working_dir) / tex_path.with_suffix(".pdf").name
        result["pdf_created"] = pdf_file.exists()
        result["pdf_path"] = str(pdf_file) if result["pdf_created"] else None

        return result


class StringUtils:
    """Common string utilities to avoid duplication"""

    @staticmethod
    def escape_latex_chars(text: str) -> str:
        """Escape special LaTeX characters"""
        escape_map = {
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "^": r"\textasciicircum{}",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "\\": r"\textbackslash{}",
        }

        for char, escaped in escape_map.items():
            text = text.replace(char, escaped)

        return text

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for cross-platform compatibility"""
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip(". ")
        # Limit length
        return sanitized[:255]

    @staticmethod
    def normalize_line_endings(text: str) -> str:
        """Normalize line endings to Unix style"""
        return text.replace("\r\n", "\n").replace("\r", "\n")

    @staticmethod
    def extract_variables_from_template(
        template_content: str, pattern: str = r"\{\{\s*([^}]+)\s*\}\}"
    ) -> List[str]:
        """Extract template variables using regex pattern"""
        return list(set(re.findall(pattern, template_content)))

    @staticmethod
    def format_datetime(
        dt: Optional[datetime] = None, format_str: str = "%B %d, %Y"
    ) -> str:
        """Format datetime with fallback to current time"""
        if dt is None:
            dt = datetime.now()
        return dt.strftime(format_str)

    @staticmethod
    def parse_date_flexible(date_str: str) -> Optional[datetime]:
        """Parse date string with multiple format support"""
        formats = [
            "%Y-%m-%d",
            "%Y-%m",
            "%B %d, %Y",
            "%b %d, %Y",
            "%m/%d/%Y",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None


class DataUtils:
    """Common data manipulation utilities"""

    @staticmethod
    def deep_merge_dicts(
        dict1: Dict[str, Any], dict2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = dict1.copy()

        for key, value in dict2.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = DataUtils.deep_merge_dicts(result[key], value)
            else:
                result[key] = value

        return result

    @staticmethod
    def get_nested_value(
        data: Dict[str, Any], key_path: str, default: Any = None
    ) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = key_path.split(".")
        current = data

        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default

    @staticmethod
    def set_nested_value(data: Dict[str, Any], key_path: str, value: Any) -> None:
        """Set value in nested dictionary using dot notation"""
        keys = key_path.split(".")
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    @staticmethod
    def flatten_dict(
        data: Dict[str, Any], prefix: str = "", separator: str = "."
    ) -> Dict[str, Any]:
        """Flatten nested dictionary"""
        result = {}

        for key, value in data.items():
            new_key = f"{prefix}{separator}{key}" if prefix else key

            if isinstance(value, dict):
                result.update(DataUtils.flatten_dict(value, new_key, separator))
            else:
                result[new_key] = value

        return result

    @staticmethod
    def filter_empty_values(
        data: Dict[str, Any], recursive: bool = True
    ) -> Dict[str, Any]:
        """Remove empty values from dictionary"""
        result = {}

        for key, value in data.items():
            if value is None or value == "" or value == []:
                continue

            if recursive and isinstance(value, dict):
                filtered_value = DataUtils.filter_empty_values(value, recursive)
                if filtered_value:  # Only add if not empty after filtering
                    result[key] = filtered_value
            else:
                result[key] = value

        return result


class CacheUtils:
    """Common caching utilities"""

    @staticmethod
    def generate_cache_key(*args, **kwargs) -> str:
        """Generate consistent cache key from arguments"""
        # Create a string representation of all arguments
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])

        # Hash the combined string
        cache_string = "|".join(key_parts)
        return hashlib.md5(cache_string.encode()).hexdigest()

    @staticmethod
    def is_cache_valid(cache_file: Path, source_file: Path) -> bool:
        """Check if cache file is newer than source file"""
        try:
            return (
                cache_file.exists()
                and cache_file.stat().st_mtime > source_file.stat().st_mtime
            )
        except Exception:
            return False

    @staticmethod
    def cleanup_old_cache_files(cache_dir: Path, max_age_days: int = 30) -> int:
        """Clean up old cache files"""
        import time

        if not cache_dir.exists():
            return 0

        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        cleaned_count = 0

        try:
            for cache_file in cache_dir.iterdir():
                if cache_file.is_file():
                    file_age = current_time - cache_file.stat().st_mtime
                    if file_age > max_age_seconds:
                        cache_file.unlink()
                        cleaned_count += 1
        except Exception as e:
            logger.warning(f"Error cleaning cache files: {e}")

        return cleaned_count


class ConfigUtils:
    """Common configuration utilities"""

    @staticmethod
    def load_yaml_config(
        config_path: Union[str, Path], default: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Load YAML configuration with fallback"""
        import yaml

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
            return default or {}

    @staticmethod
    def save_yaml_config(config: Dict[str, Any], config_path: Union[str, Path]) -> bool:
        """Save configuration to YAML file"""
        import yaml

        try:
            path = Path(config_path)
            FileOperations.ensure_directory(path.parent)

            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save config to {config_path}: {e}")
            return False

    @staticmethod
    def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple configuration dictionaries"""
        result = {}
        for config in configs:
            result = DataUtils.deep_merge_dicts(result, config)
        return result


# Decorator for retry logic
def retry_on_failure(
    max_attempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)
):
    """Decorator to retry function calls on failure"""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            import time

            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )

            raise last_exception

        return wrapper

    return decorator


# Context manager for temporary directories
class TemporaryDirectory:
    """Context manager for temporary directories with cleanup"""

    def __init__(self, prefix: str = "temp_", cleanup: bool = True):
        self.prefix = prefix
        self.cleanup = cleanup
        self.path = None

    def __enter__(self) -> Path:
        self.path = Path(tempfile.mkdtemp(prefix=self.prefix))
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cleanup and self.path and self.path.exists():
            try:
                shutil.rmtree(self.path)
            except Exception as e:
                logger.warning(
                    f"Failed to cleanup temporary directory {self.path}: {e}"
                )
