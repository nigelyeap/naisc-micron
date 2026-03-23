"""
Backend package for the AI-Powered Smart Tool Log Parser.

Provides the FastAPI application, SQLite database layer,
and natural language query engine.
"""

from backend.database import Database

__all__ = [
    "Database",
]
