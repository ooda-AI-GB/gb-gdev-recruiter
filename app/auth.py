from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import GDEV_API_TOKEN

security = HTTPBearer()


def require_auth(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != GDEV_API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return credentials.credentials
