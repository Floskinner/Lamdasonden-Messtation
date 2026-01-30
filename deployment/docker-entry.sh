#!/bin/bash

set -eu
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root" >&2
    exit 1
fi

# Test if /app exists
if [ ! -d "/app" ]; then
    echo "/app directory does not exist. Creating /app directory."
    echo "Mount the application volume to /app and try again."
    exit 1
fi

cd /app

echo "Create and copy python312 tarball"
tar -caf python312.tar.gz -C /opt --exclude-caches --exclude=python312/lib/python.3.12/test python312

echo "Download needed wheels"
mkdir -p wheels
pip3 download -d wheels -r requirements.txt

# Donwload some extra build deps wheels
pip3 download -d wheels hatchling setuptools wheel editables
