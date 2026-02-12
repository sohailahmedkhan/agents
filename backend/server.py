"""ASGI entrypoint module.

Allows running the backend with `uvicorn server:app` while delegating app
creation to `app.main`.
"""
from app.main import app
