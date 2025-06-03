import os
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
from PIL import Image, ImageOps
import shutil

logger = logging.getLogger(__name__)


class ImageFormat(str, Enum):
    """Supported image formats"""

    PDF = "pdf"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    EPS = "eps"


class ImageProcessor:
    """Fast image processing for LaTeX templates"""

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize image processor"""
        self.cache_dir = (
            Path(cache_dir)
            if cache_dir
            else Path.home() / ".resume_agent_cache" / "images"
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.supported_formats = {".jpg", ".jpeg", ".png", ".pdf", ".eps"}

    def process_image(
        self,
        image_path: str,
        target_format: ImageFormat = ImageFormat.PNG,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
    ) -> str:
        """Process image with caching"""
        image_path = Path(image_path)

        if not image_path.exists():
            raise ValueError(f"Image file not found: {image_path}")

        # Generate cache key
        cache_key = self._generate_cache_key(
            image_path, target_format, max_width, max_height
        )
        cached_file = self.cache_dir / f"{cache_key}.{target_format.value}"

        # Return cached version if exists
        if cached_file.exists():
            return str(cached_file)

        # Process image
        processed_path = self._process_image_file(
            image_path, target_format, max_width, max_height
        )

        # Cache result
        shutil.copy2(processed_path, cached_file)

        return str(cached_file)

    def _generate_cache_key(
        self,
        image_path: Path,
        target_format: ImageFormat,
        max_width: Optional[int],
        max_height: Optional[int],
    ) -> str:
        """Generate cache key for image"""
        from ..common_utils import CacheUtils

        # Include file hash and processing parameters
        file_hash = self._get_file_hash(image_path)
        return CacheUtils.generate_cache_key(
            file_hash, target_format.value, max_width or "none", max_height or "none"
        )

    def _get_file_hash(self, file_path: Path) -> str:
        """Get file hash for caching"""
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()[:16]

    def _process_image_file(
        self,
        image_path: Path,
        target_format: ImageFormat,
        max_width: Optional[int],
        max_height: Optional[int],
    ) -> str:
        """Process individual image file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_file = temp_path / f"processed.{target_format.value}"

            # Handle PDF/EPS files differently
            if image_path.suffix.lower() in [".pdf", ".eps"]:
                return self._convert_vector_image(
                    image_path, output_file, target_format
                )

            # Process raster images
            try:
                with Image.open(image_path) as img:
                    # Convert to RGB if necessary
                    if img.mode in ("RGBA", "LA", "P"):
                        img = img.convert("RGB")

                    # Resize if dimensions specified
                    if max_width or max_height:
                        img = self._resize_image(img, max_width, max_height)

                    # Save in target format
                    if (
                        target_format == ImageFormat.JPG
                        or target_format == ImageFormat.JPEG
                    ):
                        img.save(output_file, "JPEG", quality=90, optimize=True)
                    elif target_format == ImageFormat.PNG:
                        img.save(output_file, "PNG", optimize=True)
                    else:
                        img.save(output_file)

                return str(output_file)

            except Exception as e:
                logger.error(f"Failed to process image {image_path}: {e}")
                # Fallback: copy original if formats compatible
                if image_path.suffix.lower()[1:] == target_format.value:
                    shutil.copy2(image_path, output_file)
                    return str(output_file)
                raise

    def _resize_image(
        self, img: Image.Image, max_width: Optional[int], max_height: Optional[int]
    ) -> Image.Image:
        """Resize image maintaining aspect ratio"""
        current_width, current_height = img.size

        # Calculate target dimensions
        if max_width and max_height:
            # Fit within both constraints
            ratio = min(max_width / current_width, max_height / current_height)
        elif max_width:
            ratio = max_width / current_width
        elif max_height:
            ratio = max_height / current_height
        else:
            return img

        # Only resize if making smaller
        if ratio < 1:
            new_width = int(current_width * ratio)
            new_height = int(current_height * ratio)
            return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return img

    def _convert_vector_image(
        self, input_path: Path, output_path: Path, target_format: ImageFormat
    ) -> str:
        """Convert vector images using external tools"""
        # For PDF/EPS, we typically keep them as-is for LaTeX
        if target_format in [ImageFormat.PDF, ImageFormat.EPS]:
            shutil.copy2(input_path, output_path)
            return str(output_path)

        # Convert to raster format using imagemagick or ghostscript
        try:
            import subprocess

            cmd = [
                "convert",  # ImageMagick
                "-density",
                "300",  # High DPI
                str(input_path),
                str(output_path),
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=30)
            if result.returncode == 0:
                return str(output_path)

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Fallback: copy original
        shutil.copy2(input_path, output_path.with_suffix(input_path.suffix))
        return str(output_path.with_suffix(input_path.suffix))


class LaTeXImageHandler:
    """Handles images specifically for LaTeX templates"""

    def __init__(self, image_processor: ImageProcessor):
        """Initialize LaTeX image handler"""
        self.processor = image_processor

    def prepare_image_for_latex(
        self, image_path: str, latex_engine: str = "pdflatex"
    ) -> str:
        """Prepare image for LaTeX compilation"""
        image_path = Path(image_path)

        # Choose optimal format based on LaTeX engine
        if latex_engine == "pdflatex":
            # pdflatex prefers PDF, PNG, JPG
            if image_path.suffix.lower() in [".eps"]:
                return self.processor.process_image(str(image_path), ImageFormat.PDF)
            elif image_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".pdf"]:
                return str(image_path)  # Use as-is

        elif latex_engine in ["xelatex", "lualatex"]:
            # XeLaTeX/LuaLaTeX handle most formats
            if image_path.suffix.lower() in self.processor.supported_formats:
                return str(image_path)

        # Default: convert to PNG
        return self.processor.process_image(str(image_path), ImageFormat.PNG)

    def generate_includegraphics_command(
        self, image_path: str, options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate LaTeX includegraphics command"""
        options = options or {}

        # Build options string
        option_parts = []

        if "width" in options:
            option_parts.append(f"width={options['width']}")
        if "height" in options:
            option_parts.append(f"height={options['height']}")
        if "scale" in options:
            option_parts.append(f"scale={options['scale']}")
        if "angle" in options:
            option_parts.append(f"angle={options['angle']}")
        if "keepaspectratio" in options and options["keepaspectratio"]:
            option_parts.append("keepaspectratio")

        options_str = ",".join(option_parts)

        # Use relative path for LaTeX
        latex_path = Path(image_path).as_posix()

        if options_str:
            return f"\\includegraphics[{options_str}]{{{latex_path}}}"
        else:
            return f"\\includegraphics{{{latex_path}}}"

    def create_figure_environment(
        self,
        image_path: str,
        caption: Optional[str] = None,
        label: Optional[str] = None,
        position: str = "h",
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create complete LaTeX figure environment"""
        graphics_cmd = self.generate_includegraphics_command(image_path, options)

        figure_parts = [f"\\begin{{figure}}[{position}]", "\\centering", graphics_cmd]

        if caption:
            figure_parts.append(f"\\caption{{{caption}}}")

        if label:
            figure_parts.append(f"\\label{{{label}}}")

        figure_parts.append("\\end{figure}")

        return "\n".join(figure_parts)


class ImageCache:
    """Manages image cache with cleanup"""

    def __init__(self, cache_dir: Path):
        """Initialize image cache"""
        self.cache_dir = cache_dir
        self.index_file = cache_dir / "cache_index.txt"

    def cleanup_old_images(self, max_age_days: int = 30) -> int:
        """Clean up old cached images"""
        import time

        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        cleaned_count = 0

        for image_file in self.cache_dir.glob("*"):
            if image_file.is_file() and image_file != self.index_file:
                file_age = current_time - image_file.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        image_file.unlink()
                        cleaned_count += 1
                    except Exception as e:
                        logger.warning(
                            f"Failed to delete cached image {image_file}: {e}"
                        )

        logger.info(f"Cleaned up {cleaned_count} old cached images")
        return cleaned_count

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information"""
        image_files = list(self.cache_dir.glob("*"))
        total_size = sum(f.stat().st_size for f in image_files if f.is_file())

        return {
            "cache_dir": str(self.cache_dir),
            "total_files": len(image_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_types": {},
        }


class ImageValidator:
    """Validates images for template use"""

    @staticmethod
    def validate_image(image_path: str) -> List[str]:
        """Validate image file"""
        issues = []
        image_path = Path(image_path)

        if not image_path.exists():
            issues.append(f"Image file not found: {image_path}")
            return issues

        # Check file size
        file_size = image_path.stat().st_size
        if file_size > 10 * 1024 * 1024:  # 10MB
            issues.append(f"Image file too large: {file_size / (1024*1024):.1f}MB")

        # Check format
        try:
            with Image.open(image_path) as img:
                # Check dimensions
                width, height = img.size
                if width > 5000 or height > 5000:
                    issues.append(f"Image dimensions too large: {width}x{height}")

                # Check for common issues
                if img.mode == "CMYK":
                    issues.append("CMYK images may not display correctly in PDF")

        except Exception as e:
            issues.append(f"Invalid image file: {e}")

        return issues
