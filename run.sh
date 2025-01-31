#!/usr/bin/env sh
#
# Build and run the example Docker image.
#
# Mounts the local project directory to reflect a common development workflow.
#
# The `docker run` command uses the following options:
#
#   --rm                        Remove the container after exiting
#   --volume ./app:/app         Mount the app directory to `/app` so code changes don't require an image rebuild
#   --volume /app/.venv         Mount the virtual environment separately, so the developer's environment doesn't end up in the container
#   --publish 8000:8000         Expose the web server port 8000 to the host
#   $@                          Pass any arguments to the container

# Set the image name and tag
IMAGE_NAME="toxpipe-agent"
IMAGE_TAG="latest"

# Build the Docker image
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -f .build/Dockerfile .

if [ -t 1 ]; then
    INTERACTIVE="-it"
else
    INTERACTIVE=""
fi

# Run the Docker container
docker run \
    --rm \
    --volume ./app:/app \
    --volume /app/.venv \
    --publish 8000:8000 \
    $INTERACTIVE \
    ${IMAGE_NAME}:${IMAGE_TAG} \
    "$@"
