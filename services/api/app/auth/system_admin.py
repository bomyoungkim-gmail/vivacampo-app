"""
System Admin authentication dependency.
Verifies SYSTEM_ADMIN token.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.config import settings
import structlog

logger = structlog.get_logger()
security = HTTPBearer()


def get_current_system_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Verify SYSTEM_ADMIN token.
    
    Token should be issued with:
    - issuer: SYSTEM_ADMIN_ISSUER
    - audience: SYSTEM_ADMIN_AUDIENCE
    - claim: role=SYSTEM_ADMIN
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            issuer=settings.system_admin_issuer,
            audience=settings.system_admin_audience
        )
        
        role = payload.get("role")
        if role != "SYSTEM_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="SYSTEM_ADMIN role required"
            )
        
        return payload
    
    except JWTError as e:
        logger.warning("system_admin_auth_failed", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid SYSTEM_ADMIN token"
        )
