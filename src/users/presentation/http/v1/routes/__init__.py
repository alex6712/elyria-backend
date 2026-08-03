from fastapi import APIRouter

from .auth import router as _auth_router

users_v1_router = APIRouter(prefix="/v1")
"""TODO: docstring"""

users_v1_router.include_router(_auth_router)

__all__ = ["users_v1_router"]
