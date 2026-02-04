import os
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import logging

security = HTTPBasic()
logger = logging.getLogger(__name__)

# Load credentials from environment
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")

print(f"[AUTH] Loaded Username: {repr(ADMIN_USERNAME)}")
print(f"[AUTH] Loaded Password: {repr(ADMIN_PASSWORD)}")


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Verify admin credentials using HTTP Basic Auth."""
    
    print(f"[AUTH] Login attempt - Username: {repr(credentials.username)}, Password: {repr(credentials.password)}")
    print(f"[AUTH] Expected - Username: {repr(ADMIN_USERNAME)}, Password: {repr(ADMIN_PASSWORD)}")
    
    # Simple string comparison
    if credentials.username == ADMIN_USERNAME and credentials.password == ADMIN_PASSWORD:
        logger.info(f"Admin login successful: {credentials.username}")
        return credentials.username
    
    logger.warning(f"Failed login attempt for username: {credentials.username}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Basic"},
    )
