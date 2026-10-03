"""Database foundation for HerStyleAI.

This package intentionally contains only database primitives for now. Auth
and user-facing API integration are out of scope for the current foundation.
"""

from .base import Base

__all__ = ["Base"]
