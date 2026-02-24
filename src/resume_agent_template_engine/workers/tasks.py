"""
Celery tasks for background document generation.
Handles heavy PDF compilation without blocking API requests.
"""

import logging
import tempfile
import os
from typing import Dict, Any
from celery import Task

from resume_agent_template_engine.workers.celery_app import celery_app
from resume_agent_template_engine.core.template_engine import TemplateEngine

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task with callbacks for monitoring."""

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info(f"Task {task_id} completed successfully")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error(f"Task {task_id} failed: {exc}")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(f"Task {task_id} retrying: {exc}")


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="resume_agent_template_engine.workers.tasks.generate_pdf_task",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    track_started=True
)
def generate_pdf_task(
    self,
    document_type: str,
    template_name: str,
    data: Dict[str, Any],
    spacing: str = "normal",
    output_format: str = "pdf"
) -> Dict[str, Any]:
    """
    Background task for PDF generation.

    Args:
        document_type: Type of document (resume/cover_letter)
        template_name: Template to use
        data: Document data
        spacing: Layout spacing mode
        output_format: Output format (pdf/latex)

    Returns:
        Dictionary with file_path and metadata
    """
    try:
        logger.info(
            f"Starting PDF generation task {self.request.id}: "
            f"{document_type}/{template_name}"
        )

        # Update task state
        self.update_state(
            state="PROCESSING",
            meta={
                "status": "Generating document...",
                "progress": 10
            }
        )

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False,
            dir="/tmp"
        ) as tmp_file:
            output_path = tmp_file.name

        try:
            # Initialize template engine (synchronous)
            engine = TemplateEngine(enable_cache=False)  # Workers don't need cache

            self.update_state(
                state="PROCESSING",
                meta={
                    "status": "Compiling LaTeX...",
                    "progress": 30
                }
            )

            # Add spacing to data
            data_with_spacing = data.copy()
            data_with_spacing["spacing_mode"] = spacing

            # Generate PDF (synchronous)
            result_path = engine.export_to_pdf(
                document_type,
                template_name,
                data_with_spacing,
                output_path
            )

            self.update_state(
                state="PROCESSING",
                meta={
                    "status": "Finalizing...",
                    "progress": 90
                }
            )

            # Get file size
            file_size = os.path.getsize(result_path)

            # Get person name for filename
            person_name = (
                data.get("personalInfo", {})
                .get("name", "document")
                .replace(" ", "_")
            )

            logger.info(
                f"PDF generation task {self.request.id} completed: "
                f"{file_size} bytes"
            )

            return {
                "status": "SUCCESS",
                "file_path": result_path,
                "file_size": file_size,
                "filename": f"{document_type}_{person_name}.pdf",
                "document_type": document_type,
                "template": template_name,
                "task_id": self.request.id
            }

        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(output_path):
                os.remove(output_path)
            raise

    except Exception as exc:
        logger.error(f"PDF generation task {self.request.id} failed: {exc}")

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="resume_agent_template_engine.workers.tasks.generate_latex_task",
    max_retries=2,
    acks_late=True
)
def generate_latex_task(
    self,
    document_type: str,
    template_name: str,
    data: Dict[str, Any],
    spacing: str = "normal"
) -> Dict[str, Any]:
    """
    Background task for LaTeX generation (no PDF compilation).

    Faster alternative when only LaTeX source is needed.

    Returns:
        Dictionary with LaTeX content and metadata
    """
    try:
        logger.info(
            f"Starting LaTeX generation task {self.request.id}: "
            f"{document_type}/{template_name}"
        )

        # Initialize template engine
        engine = TemplateEngine(enable_cache=False)

        # Add spacing to data
        data_with_spacing = data.copy()
        data_with_spacing["spacing_mode"] = spacing

        # Generate LaTeX
        latex_content = engine.render_document(
            document_type,
            template_name,
            data_with_spacing,
            output_format="latex"
        )

        logger.info(
            f"LaTeX generation task {self.request.id} completed: "
            f"{len(latex_content)} characters"
        )

        return {
            "status": "SUCCESS",
            "latex_content": latex_content,
            "content_length": len(latex_content),
            "document_type": document_type,
            "template": template_name,
            "task_id": self.request.id
        }

    except Exception as exc:
        logger.error(f"LaTeX generation task {self.request.id} failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="resume_agent_template_engine.workers.tasks.batch_generate_task"
)
def batch_generate_task(
    self,
    document_requests: list[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Batch generation task for multiple documents.

    Args:
        document_requests: List of document generation requests

    Returns:
        Dictionary with results for each document
    """
    logger.info(
        f"Starting batch generation task {self.request.id}: "
        f"{len(document_requests)} documents"
    )

    results = []
    failed = []

    for idx, request in enumerate(document_requests):
        try:
            self.update_state(
                state="PROCESSING",
                meta={
                    "status": f"Processing document {idx + 1}/{len(document_requests)}",
                    "progress": int((idx / len(document_requests)) * 100)
                }
            )

            # Submit subtask
            result = generate_pdf_task.delay(
                document_type=request["document_type"],
                template_name=request["template"],
                data=request["data"],
                spacing=request.get("spacing", "normal")
            )

            results.append({
                "index": idx,
                "task_id": result.id,
                "status": "SUBMITTED"
            })

        except Exception as e:
            logger.error(f"Failed to submit document {idx}: {e}")
            failed.append({
                "index": idx,
                "error": str(e)
            })

    return {
        "status": "SUCCESS",
        "total": len(document_requests),
        "submitted": len(results),
        "failed": len(failed),
        "results": results,
        "failures": failed,
        "task_id": self.request.id
    }


@celery_app.task(name="resume_agent_template_engine.workers.tasks.cleanup_old_files")
def cleanup_old_files():
    """
    Periodic task to clean up old temporary files.

    Run this task every hour to prevent disk space issues.
    """
    import time
    from pathlib import Path

    logger.info("Starting cleanup of old temporary files")

    tmp_dir = Path("/tmp")
    current_time = time.time()
    cutoff_time = current_time - (3600 * 2)  # 2 hours old

    cleaned = 0
    errors = 0

    try:
        # Find old PDF files
        for pdf_file in tmp_dir.glob("tmp*.pdf"):
            try:
                if pdf_file.stat().st_mtime < cutoff_time:
                    pdf_file.unlink()
                    cleaned += 1
            except Exception as e:
                logger.error(f"Failed to delete {pdf_file}: {e}")
                errors += 1

        logger.info(
            f"Cleanup completed: {cleaned} files deleted, {errors} errors"
        )

        return {
            "status": "SUCCESS",
            "cleaned": cleaned,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        return {
            "status": "FAILED",
            "error": str(e)
        }
