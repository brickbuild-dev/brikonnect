"""
Database type compatibility layer.

Provides types that work with both PostgreSQL and SQLite for testing.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import String, Text, TypeDecorator
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.types import CHAR, JSON


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    
    Uses PostgreSQL's UUID type when available, otherwise uses CHAR(36).
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class JSONBCompatible(TypeDecorator):
    """Platform-independent JSONB type.
    
    Uses PostgreSQL's JSONB when available, otherwise uses JSON.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.JSONB())
        else:
            return dialect.type_descriptor(JSON())


class ArrayOfStrings(TypeDecorator):
    """Platform-independent array of strings.
    
    Uses PostgreSQL's ARRAY(Text) when available, otherwise uses JSON.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.ARRAY(Text))
        else:
            return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        # For SQLite, store as JSON array
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        return value


class INETCompatible(TypeDecorator):
    """Platform-independent INET type.
    
    Uses PostgreSQL's INET when available, otherwise uses String.
    """
    impl = String(45)  # Max length for IPv6
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.INET())
        else:
            return dialect.type_descriptor(String(45))
