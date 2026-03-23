"""
Entry point -- run the FastAPI server with uvicorn.

Usage:
    python -m backend.run
    # or
    python backend/run.py
"""

import os
import sys

# Ensure the project root is on sys.path so sibling packages resolve
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import uvicorn

from backend.app import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
