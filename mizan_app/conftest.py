# Pytest root conftest — makes backend modules importable when running
# `pytest tests/test_backend.py` from the mizan_app/ project root.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))
