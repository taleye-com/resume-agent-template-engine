"""
Resume Agent Template Engine

A template engine for generating professional resumes and cover letters.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path to fix import issues
# This ensures the package can be imported from anywhere
current_file = Path(__file__).resolve()
src_dir = current_file.parent.parent  # Go up to src/ directory
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

__version__ = "0.1.0"
__author__ = "Resume Agent Template Engine Team"

from .core import TemplateEngine, DocumentType, OutputFormat

__all__ = ["TemplateEngine", "DocumentType", "OutputFormat"]
