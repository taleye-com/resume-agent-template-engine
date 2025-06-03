#!/usr/bin/env python3

import sys
import os
import traceback
import json

# Add src to path like run.py does
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

print("=== Debug Import Test ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Python paths:")
for i, path in enumerate(sys.path):
    print(f"  {i}: {path}")

print("\n=== Testing import ===")
try:
    from resume_agent_template_engine.core.template_engine import TemplateEngine, DocumentType, OutputFormat
    print("✅ Successfully imported TemplateEngine")
    
    engine = TemplateEngine()
    print("✅ Successfully created TemplateEngine instance")
    
    templates = engine.get_available_templates()
    print(f"✅ Available templates: {templates}")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    traceback.print_exc()

print("\n=== Testing API import ===")
try:
    from resume_agent_template_engine.api.app import app
    print("✅ Successfully imported FastAPI app")
except Exception as e:
    print(f"❌ API import failed: {e}")
    traceback.print_exc()

print("\n=== Testing sample data ===")
try:
    sample_data = {
        "personalInfo": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "123-456-7890"
        },
        "experience": []
    }
    
    engine = TemplateEngine()
    available_templates = engine.get_available_templates()
    print(f"Available templates: {available_templates}")
    
    if "resume" in available_templates and available_templates["resume"]:
        template_name = available_templates["resume"][0]
        print(f"Testing with template: {template_name}")
        
        # Test template creation
        template = engine.create_template("resume", template_name, sample_data)
        print("✅ Template created successfully")
        
except Exception as e:
    print(f"❌ Template test failed: {e}")
    traceback.print_exc() 