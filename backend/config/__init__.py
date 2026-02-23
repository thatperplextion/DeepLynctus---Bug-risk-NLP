"""
Configuration Module for DeepLynctus Backend

Centralizes configuration management, database connections, and settings.
Provides a single point of configuration for the entire backend application.
"""

from .database import get_database, close_database, ensure_indexes, Collections

# Export all configuration utilities for easy importing
__all__ = [
    "get_database",
    "close_database", 
    "ensure_indexes",
    "Collections"
]
