#!/bin/bash

# Check for required commands
for cmd in docker docker-compose curl; do
    if ! command -v $cmd &> /dev/null; then
        echo "Error: $cmd is required but not installed."
        exit 1
    fi
done

# Enable BuildKit for better build performance
export DOCKER_BUILDKIT=1

# Add verbose output
echo "Building Docker image with verbose output..."

# Step 1: Build the image separately first
echo "Step 1: Building the Docker image..."
docker build --progress=plain -t resume-template-engine .

# Check if build was successful
if [ $? -ne 0 ]; then
    echo "Build failed. Please check the error messages above."
    exit 1
fi

echo "Image built successfully!"

# Step 2: Start the container
echo "Step 2: Starting the container..."
docker compose up -d

# Check if container started
if [ $? -ne 0 ]; then
    echo "Failed to start the container. Please check the error messages above."
    exit 1
fi

echo "Container started successfully!"

# Step 3: Show container status
echo "Step 3: Checking container status..."
docker compose ps

# Step 4: Wait for the API to be ready
echo "Step 4: Waiting for API to be ready..."
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if curl -s http://localhost:8501/docs > /dev/null; then
        echo "API is ready!"
        break
    fi
    echo "Waiting for API to be ready... (attempt $attempt/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "API failed to start within the expected time."
    echo "Check the logs with: docker compose logs -f"
    exit 1
fi

echo "Build and deployment completed successfully!"
echo "API documentation is available at: http://localhost:8501/docs"
echo "You can check logs with: docker compose logs -f" 