# Deploying the Resume Template Engine with Docker

This guide explains how to deploy the Resume Template Engine using Docker and Docker Compose.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Deployment Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/taleye-com/resume-agent-template-engine
   cd resume-agent-template-engine
   ```

2. **Build and start the Docker containers**

   ```bash
   docker-compose up -d
   ```

   This command will:
   - Build the Docker image from the Dockerfile
   - Start the container
   - Map port 8501 from the container to port 8501 on your host
   - Mount the output directory for persistence

3. **Verify the API is running**

   ```bash
   curl http://localhost:8501/health
   ```

   You should receive a JSON response: `{"status":"healthy"}`

## Using the API

- **API Documentation**: Access the Swagger UI by opening `http://localhost:8501/docs` in your browser
- **Generate a Resume**: Send a POST request to `http://localhost:8501/generate` with the appropriate JSON data
- **List Templates**: Send a GET request to `http://localhost:8501/templates`

## Maintenance

- **View logs**:

  ```bash
  docker-compose logs -f
  ```

- **Restart the service**:

  ```bash
  docker-compose restart
  ```

- **Stop the service**:

  ```bash
  docker-compose down
  ```

- **Update to a new version**:

  ```bash
  git pull
  docker-compose down
  docker-compose up -d --build
  ```

## Customization

- **Change the port**: Edit the `docker-compose.yml` file and modify the ports section from `"8501:8501"` to `"<your-port>:8501"`
- **Modify environment variables**: Add environment variables in the `environment` section of `docker-compose.yml`

## Troubleshooting

- **Check container status**:

  ```bash
  docker-compose ps
  ```

- **Inspect container logs**:

  ```bash
  docker-compose logs -f resume-api
  ```

- **Access container shell**:

  ```bash
  docker-compose exec resume-api /bin/bash
  ``` 