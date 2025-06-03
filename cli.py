#!/usr/bin/env python3
"""
Resume CLI Runner

Simple script to run the Resume Agent Template Engine CLI from the project root.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).parent.resolve()
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Import and run the CLI
from resume_agent_template_engine.cli import main

if __name__ == "__main__":
    main() 