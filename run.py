import subprocess
import sys
import os
from threading import Thread

def run_streamlit():
    """Run the Streamlit interface."""
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8502"])

def run_api():
    """Run the FastAPI server."""
    subprocess.run([sys.executable, "api.py"])

if __name__ == "__main__":
    # Start API server in a separate thread
    api_thread = Thread(target=run_api)
    api_thread.daemon = True
    api_thread.start()
    
    # Run Streamlit in the main thread
    run_streamlit() 