"""Storage layer for MyLLMTradingAgents."""

from .base import Storage
from .sqlite_store import SQLiteStorage

__all__ = [
    "Storage",
    "SQLiteStorage",
]


def create_storage(db_path: str = "arena.db") -> Storage:
    """Create storage instance."""
    return SQLiteStorage(db_path)
