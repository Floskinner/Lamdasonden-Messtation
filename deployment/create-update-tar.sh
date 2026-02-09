#!/bin/bash

set -euo pipefail

usage() {
    cat <<'EOF'
Usage: create-update-tar.sh [options]

Options:
  --project-root PATH     Base path containing system/ and application/ directories (default: repo root)
  --application-dir PATH  Directory to package as the application (defaults to project-root/application if it exists, otherwise project root)
  --system-dir PATH       Directory to package as the system folder (default: project-root/system)
  --output, -o PATH       Path for the final updater tarball (default: PROJECT_ROOT/artifacts/mama.tar.gz)
  --python-tar PATH       Optional python tarball to bundle (must be a valid tar file)
  --help, -h              Show this help
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT=""
PYTHON_TAR=""
SYSTEM_DIR=""
APPLICATION_DIR=""

APPLICATION_EXCLUDES=("__pycache__" ".git" ".venv" "MAMA.sqlite" "settings.json" "system" "artifacts" ".ruff_cache" "python312.tar.gz")

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project-root)
            PROJECT_ROOT="$(cd "$2" && pwd)"
            SYSTEM_DIR=""
            APPLICATION_DIR=""
            shift 2
            ;;
        --application-dir)
            APPLICATION_DIR="$(cd "$2" && pwd)"
            shift 2
            ;;
        --system-dir)
            SYSTEM_DIR="$(cd "$2" && pwd)"
            shift 2
            ;;
        --output|-o)
            OUTPUT="$(realpath "$2")"
            shift 2
            ;;
        --python-tar)
            PYTHON_TAR="$(realpath "$2")"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage
            exit 1
            ;;
    esac
done

if [ -z "$SYSTEM_DIR" ]; then
    SYSTEM_DIR="$PROJECT_ROOT/system"
fi

if [ -z "$APPLICATION_DIR" ]; then
    DEFAULT_APPLICATION_DIR="$PROJECT_ROOT/application"
    if [ -d "$DEFAULT_APPLICATION_DIR" ]; then
        APPLICATION_DIR="$DEFAULT_APPLICATION_DIR"
    else
        APPLICATION_DIR="$PROJECT_ROOT"
    fi
fi

if [ -z "$OUTPUT" ]; then
    OUTPUT="$PROJECT_ROOT/artifacts/mama.tar.gz"
fi

if [ ! -d "$SYSTEM_DIR" ]; then
    echo "Missing system directory: $SYSTEM_DIR" >&2
    exit 1
fi

if [ ! -d "$APPLICATION_DIR" ]; then
    echo "Missing application directory: $APPLICATION_DIR" >&2
    exit 1
fi

if [ -n "$PYTHON_TAR" ]; then
    if [ ! -f "$PYTHON_TAR" ]; then
        echo "Python tar not found: $PYTHON_TAR" >&2
        exit 1
    fi
    if ! tar -tf "$PYTHON_TAR" >/dev/null 2>&1; then
        echo "Invalid python tarball (failed to read): $PYTHON_TAR" >&2
        exit 1
    fi
fi

mkdir -p "$(dirname "$OUTPUT")"

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "'$TEMP_DIR'"' EXIT

echo "Packaging system from: $SYSTEM_DIR"
tar -czf "$TEMP_DIR/system.tar.gz" -C "$SYSTEM_DIR" .

echo "Packaging application from: $APPLICATION_DIR"
application_args=(tar -czf "$TEMP_DIR/application.tar.gz")
for pattern in "${APPLICATION_EXCLUDES[@]}"; do
    application_args+=(--exclude="$pattern")
done
application_args+=(-C "$APPLICATION_DIR" .)
"${application_args[@]}"

if [ -n "$PYTHON_TAR" ]; then
    echo "Including python tarball: $PYTHON_TAR"
    cp "$PYTHON_TAR" "$TEMP_DIR/python.tar.gz"
fi

final_args=(tar -czf "$OUTPUT" -C "$TEMP_DIR" system.tar.gz application.tar.gz)
if [ -f "$TEMP_DIR/python.tar.gz" ]; then
    final_args+=(python.tar.gz)
fi
"${final_args[@]}"

echo "Updater archive created: $OUTPUT"
