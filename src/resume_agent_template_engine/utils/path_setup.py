"""
Path setup utility for Resume Agent Template Engine.

This module ensures that the package can be imported correctly regardless of
where the script is run from.
"""

import sys
import os
from pathlib import Path


def setup_package_path():
    """
    Add the src directory to Python path to enable package imports.

    This function should be called at the beginning of any script that needs
    to import from resume_agent_template_engine package.
    """
    # Get the current file's directory
    current_file = Path(__file__).resolve()

    # Navigate to the src directory
    # From utils/path_setup.py -> utils -> resume_agent_template_engine -> src
    src_dir = current_file.parent.parent.parent

    # Add to path if not already there
    src_path = str(src_dir)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    return src_path


def get_project_root():
    """Get the project root directory."""
    current_file = Path(__file__).resolve()
    # From utils/path_setup.py -> utils -> resume_agent_template_engine -> src -> project_root
    return current_file.parent.parent.parent.parent


def get_src_directory():
    """Get the src directory."""
    current_file = Path(__file__).resolve()
    # From utils/path_setup.py -> utils -> resume_agent_template_engine -> src
    return current_file.parent.parent.parent


# Automatically setup path when this module is imported
setup_package_path()
