"""
Health check endpoint.
"""

from fastapi import APIRouter

router = APIRouter(prefix="", tags=["Health"])


@router.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    return {"status": "healthy"}
