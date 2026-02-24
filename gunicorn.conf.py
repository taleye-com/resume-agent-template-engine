"""
Gunicorn configuration for high-performance API server.
Optimized to handle 10,000+ concurrent users per node.
"""

import multiprocessing
import os

# Server Socket
bind = "0.0.0.0:8501"
backlog = 2048  # Maximum number of pending connections

# Worker Processes
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000  # Max simultaneous clients per worker
max_requests = 10000  # Restart workers after this many requests (prevent memory leaks)
max_requests_jitter = 1000  # Add randomness to prevent all workers restarting at once
timeout = 120  # Worker timeout in seconds
keepalive = 5  # Keep-alive connections

# Threading
threads = int(os.getenv("GUNICORN_THREADS", 4))  # Threads per worker

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"  # Log to stderr
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process Naming
proc_name = "resume-template-engine"

# Server Mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/key.pem"
# certfile = "/path/to/cert.pem"

# Performance
preload_app = True  # Load application before forking workers
worker_tmp_dir = "/dev/shm"  # Use shared memory for worker temp files (Linux only)

# Hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    print("=" * 60)
    print("Starting Resume Template Engine API Server")
    print(f"Workers: {workers}")
    print(f"Threads per worker: {threads}")
    print(f"Total capacity: ~{workers * worker_connections} concurrent connections")
    print("=" * 60)


def on_reload(server):
    """Called to recycle workers during a reload."""
    print("Reloading workers...")


def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    print(f"Worker {worker.pid} received interrupt signal")


def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    print(f"Worker {worker.pid} aborted")


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass


def post_fork(server, worker):
    """Called after a worker has been forked."""
    print(f"Worker spawned (pid: {worker.pid})")


def pre_exec(server):
    """Called just before a new master process is forked."""
    print("Forking new master process")


def when_ready(server):
    """Called just after the server is started."""
    print("Server is ready to accept connections")


def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    print(f"Worker {worker.pid} exited")


def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    print(f"Number of workers changed from {old_value} to {new_value}")


# Environment-specific configurations
if os.getenv("ENVIRONMENT") == "production":
    # Production settings
    workers = max(workers, 16)  # Minimum 16 workers for production
    worker_connections = 2000
    loglevel = "warning"
elif os.getenv("ENVIRONMENT") == "development":
    # Development settings
    workers = 2
    worker_connections = 100
    loglevel = "debug"
    reload = True  # Auto-reload on code changes
