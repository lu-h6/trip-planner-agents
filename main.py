"""Development entrypoint for starting the backend from the repository root."""

import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.cli import main


if __name__ == "__main__":
    main()
