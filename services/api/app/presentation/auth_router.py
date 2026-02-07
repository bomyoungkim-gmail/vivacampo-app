from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from app.presentation.error_responses import DEFAULT_ERROR_RESPONSES
from app.schemas import (
    OIDCLoginRequest,
    IdentityView,
    WorkspaceListResponse,
    WorkspaceView,
    WorkspaceSwitchRequest,
    SessionTokenResponse
)
from app.presentation.dtos.auth_dtos import (
    AuthResponseDTO,
    ForgotPasswordRequestDTO,
    LoginRequestDTO,
    MessageResponseDTO,
    ResetPasswordRequestDTO,
    SignupRequestDTO,
)
from app.infrastructure.models import Identity, Tenant, Membership
from app.infrastructure.di_container import ApiContainer, get_container
from app.auth.dependencies import get_current_membership, CurrentMembership
from app.auth.utils import validate_oidc_token, create_session_token
from app.config import settings
from app.application.dtos.auth import (
    ForgotPasswordCommand,
    LoginCommand,
    ResetPasswordCommand,
    SignupCommand,
)
import uuid

router = APIRouter(responses=DEFAULT_ERROR_RESPONSES)

@router.post("/auth/oidc/login", response_model=dict)
async def oidc_login(
    request: OIDCLoginRequest,
    container: ApiContainer = Depends(get_container)
):
    """
    OIDC login endpoint.
    - Validates OIDC token
    - Creates identity if doesn't exist
    - If INDIVIDUAL (no memberships), creates PERSONAL tenant + TENANT_ADMIN membership
    - Returns identity + workspaces + access_token
    """
    db = container.db_session()
    # Validate OIDC token
    try:
        token_data = validate_oidc_token(request.id_token, request.provider)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    
    # Find or create identity
    identity = db.query(Identity).filter(
        Identity.provider == request.provider,
        Identity.subject == token_data["subject"]
    ).first()
    
    if not identity:
        identity = db.query(Identity).filter(
            Identity.email == token_data["email"]
        ).first()

    if identity:
        updated = False
        if identity.name != token_data["name"]:
            identity.name = token_data["name"]
            updated = True
        if identity.provider != request.provider or identity.subject != token_data["subject"]:
            conflict = db.query(Identity).filter(
                Identity.provider == request.provider,
                Identity.subject == token_data["subject"],
                Identity.id != identity.id
            ).first()
            if not conflict:
                identity.provider = request.provider
                identity.subject = token_data["subject"]
                updated = True
        if updated:
            db.commit()
            db.refresh(identity)
    else:
        identity = Identity(
            provider=request.provider,
            subject=token_data["subject"],
            email=token_data["email"],
            name=token_data["name"],
            status="ACTIVE"
        )
        db.add(identity)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            identity = db.query(Identity).filter(
                Identity.email == token_data["email"]
            ).first()
            if not identity:
                raise
        if identity:
            db.refresh(identity)
    
    # Check if user has any memberships
    memberships = db.query(Membership).filter(
        Membership.identity_id == identity.id
    ).all()
    
    # If no memberships (INDIVIDUAL), create ENTERPRISE tenant (for Dev/MVP)
    if not memberships:
        # Create COMPANY tenant
        personal_tenant = Tenant(
            type="COMPANY",
            name=f"{identity.name}'s Workspace",
            status="ACTIVE",
            plan="ENTERPRISE",
            quotas={}
        )
        db.add(personal_tenant)
        db.commit()
        db.refresh(personal_tenant)
        
        # Create TENANT_ADMIN membership
        membership = Membership(
            tenant_id=personal_tenant.id,
            identity_id=identity.id,
            role="TENANT_ADMIN",
            status="ACTIVE"
        )
        db.add(membership)
        db.commit()
        db.refresh(membership)
        
        memberships = [membership]
    
    # Build workspaces list
    workspaces = []
    for m in memberships:
        tenant = db.query(Tenant).filter(Tenant.id == m.tenant_id).first()
        if tenant and m.status == "ACTIVE":
            workspaces.append(WorkspaceView(
                tenant_id=tenant.id,
                tenant_type=tenant.type,
                tenant_name=tenant.name,
                membership_id=m.id,
                role=m.role,
                status=m.status
            ))
            
    # Select default workspace for session (Prefer PERSONAL, then first active)
    active_workspaces = [w for w in workspaces if w.status == "ACTIVE"]
    default_workspace = next(
        (w for w in active_workspaces if w.tenant_type == "PERSONAL"),
        active_workspaces[0] if active_workspaces else None
    )
    
    access_token = None
    if default_workspace:
        access_token = create_session_token(
            tenant_id=default_workspace.tenant_id,
            membership_id=default_workspace.membership_id,
            identity_id=identity.id,
            role=default_workspace.role
        )
    
    return {
        "identity": IdentityView.from_orm(identity),
        "workspaces": workspaces,
        "access_token": access_token
    }


def _error_detail(code: str, message: str, details: dict | None = None, trace_id: str | None = None) -> dict:
    payload = {"error": {"code": code, "message": message}}
    if details:
        payload["error"]["details"] = details
    if trace_id:
        payload["error"]["traceId"] = trace_id
    return payload


def _set_auth_cookie(response: Response, token: str | None) -> None:
    if not token:
        return
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.session_token_ttl_minutes * 60,
    )


@router.post("/auth/signup", response_model=AuthResponseDTO, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequestDTO,
    response: Response,
    container: ApiContainer = Depends(get_container),
):
    use_case = container.signup_use_case()
    try:
        command = SignupCommand(**request.model_dump())
        result = await use_case.execute(command=command)
    except ValueError as exc:
        if str(exc) == "EMAIL_ALREADY_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_error_detail("EMAIL_ALREADY_EXISTS", "Email already exists"),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_error_detail("BAD_REQUEST", "Invalid signup request"),
        )

    _set_auth_cookie(response, result.access_token)
    return AuthResponseDTO.from_result(result)


@router.post("/auth/login", response_model=AuthResponseDTO)
async def login(
    request: LoginRequestDTO,
    response: Response,
    container: ApiContainer = Depends(get_container),
):
    use_case = container.login_use_case()
    try:
        command = LoginCommand(**request.model_dump())
        result = await use_case.execute(command=command)
    except ValueError as exc:
        if str(exc) == "INVALID_CREDENTIALS":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=_error_detail("INVALID_CREDENTIALS", "Invalid credentials"),
            )
        if str(exc) == "IDENTITY_INACTIVE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=_error_detail("IDENTITY_INACTIVE", "Identity is inactive"),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_error_detail("BAD_REQUEST", "Invalid login request"),
        )

    _set_auth_cookie(response, result.access_token)
    return AuthResponseDTO.from_result(result)


@router.post("/auth/forgot-password", response_model=MessageResponseDTO)
async def forgot_password(
    request: ForgotPasswordRequestDTO,
    container: ApiContainer = Depends(get_container),
):
    use_case = container.forgot_password_use_case()
    command = ForgotPasswordCommand(**request.model_dump())
    result = await use_case.execute(command=command)
    return MessageResponseDTO.from_result(result)


@router.post("/auth/reset-password", response_model=MessageResponseDTO)
async def reset_password(
    request: ResetPasswordRequestDTO,
    container: ApiContainer = Depends(get_container),
):
    use_case = container.reset_password_use_case()
    try:
        command = ResetPasswordCommand(**request.model_dump())
        result = await use_case.execute(command=command)
    except ValueError as exc:
        if str(exc) == "RESET_TOKEN_EXPIRED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error_detail("RESET_TOKEN_EXPIRED", "Reset token expired"),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_error_detail("RESET_TOKEN_INVALID", "Reset token invalid"),
        )
    return MessageResponseDTO.from_result(result)


@router.post("/auth/workspaces/switch", response_model=SessionTokenResponse)
async def switch_workspace(
    request: WorkspaceSwitchRequest,
    membership: CurrentMembership = Depends(get_current_membership),
    container: ApiContainer = Depends(get_container)
):
    """
    Switch workspace (tenant).
    Returns session token with active_tenant_id + membership_id + role.
    
    """
    db = container.db_session()
    # Find membership for the same identity
    membership = db.query(Membership).filter(
        Membership.tenant_id == request.tenant_id,
        Membership.identity_id == membership.identity_id,
        Membership.status == "ACTIVE"
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found or inactive"
        )
    
    # Create session token
    token = create_session_token(
        tenant_id=membership.tenant_id,
        membership_id=membership.id,
        identity_id=membership.identity_id,
        role=membership.role
    )
    
    return SessionTokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=settings.session_token_ttl_minutes * 60
    )


@router.get("/me")
async def get_current_user():
    """
    Get current user info.
    TODO: Implement with proper auth.
    """
    return {"message": "Not implemented yet"}
