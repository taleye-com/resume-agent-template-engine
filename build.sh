#!/bin/bash

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

echo "You can check logs with: docker compose logs -f"
echo "API should be available at: http://localhost:8501/docs" 