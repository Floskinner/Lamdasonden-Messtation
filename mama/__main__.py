"""Console entry point for the `mama` executable."""

from mama.app import main as run_app


def main():
    """Start the Flask-SocketIO application via the console script."""
    run_app()


if __name__ == "__main__":  # pragma: no cover
    main()
