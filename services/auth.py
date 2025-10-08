from __future__ import annotations

import os

from fastapi import Header, HTTPException


API_KEY = os.getenv("API_KEY")


def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API key not configured")
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key