# Add this directory to sys.path so that intra-backend imports
# (e.g. `from classifier import classify` inside api.py) resolve correctly
# when the package is loaded via `uvicorn backend.api:app` from the project root.
import sys
from pathlib import Path

_backend_dir = str(Path(__file__).parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
