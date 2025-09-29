import argparse
import os
import subprocess
import sys

# Add src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

import uvicorn

from resume_agent_template_engine.api.app import app


def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8501)


def run_ui():
    subprocess.run(
        [
            "streamlit",
            "run",
            "src/resume_agent_template_engine/ui/streamlit_app.py",
            "--server.port",
            "8502",
            "--server.address",
            "0.0.0.0",
            "--browser.gatherUsageStats",
            "false",
        ]
    )


def main():
    parser = argparse.ArgumentParser(description="Run the Resume Agent Template Engine")
    parser.add_argument("--api", action="store_true", help="Run the API server")
    parser.add_argument("--ui", action="store_true", help="Run the UI server")
    parser.add_argument(
        "--all", action="store_true", help="Run both the API and UI servers"
    )
    args = parser.parse_args()

    if args.api:
        run_api()
    elif args.ui:
        run_ui()
    elif args.all:
        run_api()
        run_ui()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
