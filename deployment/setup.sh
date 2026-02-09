#!/bin/bash

set -eu

SKIP_PYTHON=${SKIP_PYTHON:-false}
COPY_PROJECT=${COPY_PROJECT:-true}
FORCE_DOCKER_BUILD=${FORCE_DOCKER_BUILD:-false}

create-python() {
    if [ "$FORCE_DOCKER_BUILD" = true ]; then
        echo "Forcing docker base image rebuild"
        docker buildx build --platform linux/arm/v6 -t docker.floskinner.de/mama:3.12 .
    fi

    if docker image inspect docker.floskinner.de/mama:3.12 >/dev/null 2>&1; then
        echo "Docker base image already exists"
    else
        {
            echo "Pull docker base image"
            docker buildx build --platform linux/arm/v6 -t docker.floskinner.de/mama:3.12 .
        } || {
            echo "Failed to build docker base image"
            echo "Build image manually with"
            docker buildx build --platform linux/arm/v6 -t docker.floskinner.de/mama:3.12 .
        }
    fi

    echo "Get artifacts from docker container"
    docker run -it --rm --platform linux/arm/v6 -v "$(pwd):/app" docker.floskinner.de/mama:3.12

    if [[ -s "python312.tar.gz" && -d "wheels" ]]; then
        echo "Artifacts successfully created"
    else
        echo "Failed to create artifacts"
        exit 1
    fi

    # echo "Copy artifacts to raspberry pi"
    # rsync -avz --progress wheels/ pi@mama.local:~/mama/wheels/
    # rsync -avz --progress python312.tar.gz pi@mama.local:~/mama/
}


copy-project-files() {
    echo "Copy project files to raspberry pi"
    ssh pi@mama.local "mkdir -p ~/mama/"
    rsync -avz --progress --exclude ".git" --exclude "__pycache__" --exclude ".venv" --exclude "MAMA.sqlite" --exclude "settings.json" --exclude "artifacts" . pi@mama.local:~/mama/
}


for arg in "$@"; do
    case "$arg" in
        --skip-python)
            SKIP_PYTHON=true;
            ;;
        --copy-project)
            COPY_PROJECT=true;
            ;;
        --force-docker-build)
            FORCE_DOCKER_BUILD=true;
            ;;
        *)
            echo "Ignoring unknown option: $arg" >&2
            ;;
    esac
done

if [ "$SKIP_PYTHON" = false ]; then
    create-python
else
    echo "Skipping python creation"
fi

if [ "$COPY_PROJECT" = true ]; then
    copy-project-files
else
    echo "Skipping project file copy"
fi


echo "Please run 'on the raspberry pi:'"
echo "  cd ~/mama/"
echo "  ./deployment/install.sh"
