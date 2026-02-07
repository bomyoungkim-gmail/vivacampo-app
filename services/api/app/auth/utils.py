from datetime import UTC, datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
from uuid import UUID
from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_session_token(
    tenant_id: UUID,
    membership_id: UUID,
    identity_id: UUID,
    role: str
) -> str:
    """
    Create session token for workspace switch.
    Contains active_tenant_id, membership_id, role.
    """
    expires = datetime.now(UTC) + timedelta(minutes=settings.session_token_ttl_minutes)
    
    payload = {
        "sub": str(identity_id),
        "tenant_id": str(tenant_id),
        "membership_id": str(membership_id),
        "role": role,
        "exp": expires,
        "iss": settings.session_jwt_issuer,
        "aud": settings.session_jwt_audience,
    }
    
    token = jwt.encode(payload, settings.session_jwt_secret, algorithm="HS256")
    return token


def decode_session_token(token: str) -> dict:
    """
    Decode and validate session token.
    Raises JWTError if invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.session_jwt_secret,
            algorithms=["HS256"],
            audience=settings.session_jwt_audience,
            issuer=settings.session_jwt_issuer
        )
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid session token: {str(e)}")


def create_password_reset_token(identity_id: UUID, email: str, ttl_minutes: int = 15) -> str:
    expires = datetime.now(UTC) + timedelta(minutes=ttl_minutes)
    payload = {
        "sub": str(identity_id),
        "email": email,
        "exp": expires,
        "iss": settings.session_jwt_issuer,
        "aud": settings.session_jwt_audience,
        "type": "password_reset",
    }
    return jwt.encode(payload, settings.session_jwt_secret, algorithm="HS256")


def decode_password_reset_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.session_jwt_secret,
            algorithms=["HS256"],
            audience=settings.session_jwt_audience,
            issuer=settings.session_jwt_issuer,
        )
        if payload.get("type") != "password_reset":
            raise ValueError("Invalid reset token type")
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid password reset token: {str(e)}")


def validate_oidc_token(id_token: str, provider: str) -> dict:
    """
    Validate OIDC token from provider.
    In production, this would verify signature with provider's public key.
    For MVP/local, we do basic validation.
    """
    try:
        # In production: fetch JWKS from provider and verify signature
        # For now, decode without verification (LOCAL ONLY)
        if settings.env == "local":
            payload = jwt.decode(
                id_token,
                settings.jwt_secret,
                algorithms=["HS256"],
                options={"verify_signature": False}  # LOCAL ONLY
            )
        else:
            # Production: verify with provider's public key
            payload = jwt.decode(
                id_token,
                settings.jwt_secret,
                algorithms=["RS256"],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer
            )
        
        return {
            "subject": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name", payload.get("email")),
        }
    except JWTError as e:
        raise ValueError(f"Invalid OIDC token: {str(e)}")
