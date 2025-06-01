import subprocess
import sys
import os
from threading import Thread
import time


def run_streamlit():
    """Run the Streamlit interface."""
    print("Starting Streamlit interface on http://localhost:8502")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8502"]
    )


def run_api():
    """Run the FastAPI server."""
    print("Starting FastAPI server on http://localhost:8501")
    subprocess.run([sys.executable, "api.py"])


if __name__ == "__main__":
    print("=" * 50)
    print("Starting Resume Builder Application")
    print("=" * 50)

    # Start API server in a separate thread
    api_thread = Thread(target=run_api)
    api_thread.daemon = True
    api_thread.start()

    # Give the API server time to start up
    time.sleep(2)

    print("\nAccess the web application at: http://localhost:8502")
    print("The API documentation is available at: http://localhost:8501/docs")
    print("=" * 50)

    # Run Streamlit in the main thread
    run_streamlit()
