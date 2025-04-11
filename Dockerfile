FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set non-interactive mode for apt
ENV DEBIAN_FRONTEND=noninteractive

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && apt-get clean

# Install minimal LaTeX dependencies instead of the full texlive package
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    texlive-base \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-latex-recommended \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies with verbose output
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p output

# Expose the port
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "api.py"] 