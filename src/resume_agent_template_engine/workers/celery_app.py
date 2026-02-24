"""
Celery configuration for background document generation.
Enables queuing and distributed processing of document generation tasks.
"""

import os
from celery import Celery
from kombu import Queue, Exchange

# Redis connection for Celery broker and backend
REDIS_URL = os.getenv(
    "CELERY_BROKER_URL",
    f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/1"
)

# Create Celery app
celery_app = Celery(
    "resume_template_engine",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "resume_agent_template_engine.workers.tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "resume_agent_template_engine.workers.tasks.generate_pdf_task": {
            "queue": "pdf_generation",
            "routing_key": "pdf.generate",
        },
        "resume_agent_template_engine.workers.tasks.generate_latex_task": {
            "queue": "latex_generation",
            "routing_key": "latex.generate",
        },
    },

    # Queue configuration
    task_queues=(
        Queue(
            "pdf_generation",
            Exchange("pdf_generation", type="direct"),
            routing_key="pdf.generate",
            max_priority=10,
        ),
        Queue(
            "latex_generation",
            Exchange("latex_generation", type="direct"),
            routing_key="latex.generate",
            max_priority=10,
        ),
    ),

    # Task execution
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,  # Requeue if worker crashes
    task_track_started=True,  # Track when tasks start

    # Performance settings
    worker_prefetch_multiplier=1,  # Don't prefetch tasks (better for long tasks)
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (prevent memory leaks)
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,  # Persist results to Redis

    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Autodiscover tasks
celery_app.autodiscover_tasks([
    "resume_agent_template_engine.workers"
])
