"""
API Key Authentication Middleware

Add this BEFORE production deployment.
"""

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
import hashlib
import os
from typing import Optional

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Store hashed API keys (NOT plain text)
# In production: Use database or secure key management service
# Example: Hash of "demo-key-12345"
# hashlib.sha256("demo-key-12345".encode()).hexdigest()
# This is a set of valid key hashes.
VALID_API_KEY_HASHES = {
    # Default demo key hash (demo-key-12345)
    "367fe8933ad8bba8f7ff02c047bcb5c00a4fff3ad6e82fef2bf4ee0c850d7c36", 
}

# Allow loading from env
env_hashes = os.getenv("VALID_API_KEY_HASHES", "")
if env_hashes:
    VALID_API_KEY_HASHES.update(h.strip() for h in env_hashes.split(","))

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """
    Verify API key from request header.
    
    Raises HTTPException if invalid or missing.
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Hash the provided key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Check against valid hashes
    if key_hash not in VALID_API_KEY_HASHES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key
