# Adattatore Vercel Serverless: espone l'istanza ASGI `app` di FastAPI.
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app  # noqa: E402

__all__ = ["app"]
