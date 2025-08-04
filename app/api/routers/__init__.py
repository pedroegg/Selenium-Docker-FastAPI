"""Expose APIRouter instances so `main.py` can import them easily."""

from .browser import router as browser_router

__all__ = ["browser_router"]
