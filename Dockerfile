# Multi-stage Dockerfile for Resume Template Engine
# Optimized for production deployment with 10K+ users support

# Stage 1: Base image with LaTeX and system dependencies
FROM ubuntu:22.04 as base

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # LaTeX dependencies (essential packages only for smaller image)
    texlive-latex-base \
    texlive-latex-extra \
    texlive-latex-recommended \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-xetex \
    lmodern \
    # Python and build tools
    python3.11 \
    python3.11-dev \
    python3-pip \
    # Utilities
    curl \
    wget \
    git \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager (faster than pip)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Verify LaTeX installation
RUN pdflatex --version

# Set working directory
WORKDIR /app

# Stage 2: Dependencies
FROM base as dependencies

# Copy dependency files and source (needed for editable install)
COPY pyproject.toml uv.lock ./
COPY src/ /app/src/

# Install Python dependencies using uv (much faster than pip)
RUN uv sync --frozen --no-dev

# Stage 3: Production application
FROM base as production

# Copy installed dependencies from previous stage
COPY --from=dependencies /app/.venv /app/.venv

# Copy application code
COPY src/ /app/src/
COPY gunicorn.conf.py /app/
COPY .env.example /app/.env

# Create necessary directories
RUN mkdir -p /var/log/resume-api /var/run/resume-api /tmp/resume-temp

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/health || exit 1

# Default command (Gunicorn with optimal settings)
CMD ["gunicorn", "resume_agent_template_engine.api.app:app", \
     "--config", "gunicorn.conf.py", \
     "--bind", "0.0.0.0:8501"]

# Stage 4: Development image (with dev dependencies and tools)
FROM base as development

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install ALL dependencies (including dev)
RUN uv sync --frozen

# Install additional dev tools
RUN apt-get update && apt-get install -y \
    vim \
    nano \
    htop \
    redis-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /var/log/resume-api /var/run/resume-api /tmp/resume-temp

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=development

# Expose port
EXPOSE 8501

# Development command with auto-reload
CMD ["uvicorn", "resume_agent_template_engine.api.app:app", \
     "--host", "0.0.0.0", \
     "--port", "8501", \
     "--reload", \
     "--log-level", "debug"]
