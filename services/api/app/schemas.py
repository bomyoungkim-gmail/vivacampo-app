from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator
from typing import Literal, Optional, List
from uuid import UUID
from datetime import datetime
import bleach


# ============
# Auth Schemas
# ============

class OIDCLoginRequest(BaseModel):
    provider: Literal["cognito", "google", "microsoft", "local"]
    id_token: str
    
    @field_validator("provider", mode="before")
    def validate_provider(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v


class IdentityView(BaseModel):
    id: UUID
    email: str
    name: str
    status: str
    
    model_config = ConfigDict(from_attributes=True)


class WorkspaceView(BaseModel):
    tenant_id: UUID
    tenant_type: Literal["COMPANY", "PERSONAL"]
    tenant_name: str
    membership_id: UUID
    role: Literal["TENANT_ADMIN", "OPERATOR", "VIEWER"]
    status: Literal["ACTIVE", "INVITED", "SUSPENDED"]


class WorkspaceListResponse(BaseModel):
    items: List[WorkspaceView]


class WorkspaceSwitchRequest(BaseModel):
    tenant_id: UUID


class SessionTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


# ============
# Farm Schemas
# ============

class FarmCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    timezone: str = "America/Sao_Paulo"
    
    @field_validator("name")
    def sanitize_name(cls, v):
        return bleach.clean(v, tags=[], strip=True)


class FarmView(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    timezone: str
    aoi_count: int = 0
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============
# AOI Schemas
# ============

class AOICreate(BaseModel):
    farm_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    use_type: Literal["PASTURE", "CROP", "TIMBER"]
    geom: dict  # GeoJSON MultiPolygon
    
    @field_validator("name")
    def sanitize_name(cls, v):
        return bleach.clean(v, tags=[], strip=True)
    
    @field_validator("geom")
    def validate_geojson(cls, v):
        if v.get('type') != 'MultiPolygon':
            raise ValueError("Geometry must be MultiPolygon")
        # Additional validation can be added here
        return v


class AOIView(BaseModel):
    id: UUID
    tenant_id: UUID
    farm_id: UUID
    name: str
    use_type: str
    status: str
    area_ha: float
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============
# Signal Schemas
# ============

class OpportunitySignalView(BaseModel):
    id: UUID
    aoi_id: UUID
    aoi_name: Optional[str] = None
    year: int = Field(..., ge=2000, le=2100)
    week: int = Field(..., ge=1, le=53)
    signal_type: str
    status: Literal["OPEN", "ACK", "RESOLVED", "DISMISSED"]
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    confidence: Literal["LOW", "MEDIUM", "HIGH"]
    score: float = Field(..., ge=0.0, le=1.0)
    model_version: str
    change_method: str
    evidence_json: dict
    recommended_actions: List[str] = Field(..., max_length=5)
    created_at: datetime
    
    @field_validator("recommended_actions")
    def validate_actions(cls, v):
        for action in v:
            if len(action) > 120:
                raise ValueError("Action must be ≤120 chars")
        return v
    
    @field_validator("evidence_json")
    def validate_evidence(cls, v):
        required = ['window_weeks', 'baseline_ref', 'valid_pixel_ratio_summary', 'change_detection']
        for key in required:
            if key not in v:
                raise ValueError(f"Missing required evidence field: {key}")
        return v
    
    model_config = ConfigDict(from_attributes=True)


class SignalFeedbackCreate(BaseModel):
    label: Literal["TRUE_POSITIVE", "FALSE_POSITIVE", "NOT_SURE"]
    root_cause: Optional[str] = Field(None, max_length=200)
    note: Optional[str] = Field(None, max_length=500)


# Consolidating AOI Schemas here
class AOICreate(BaseModel):
    farm_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    use_type: Literal["PASTURE", "CROP", "TIMBER"]
    geometry: str  # WKT from frontend
    
    @field_validator("name")
    def sanitize_name(cls, v):
        return bleach.clean(v, tags=[], strip=True)


class AOIView(BaseModel):
    id: UUID
    tenant_id: Optional[UUID] = None  # Optional or default
    farm_id: UUID
    name: str
    use_type: str
    status: str
    area_ha: float
    geometry: str # Added geometry field
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AOIPatch(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    use_type: Optional[Literal["PASTURE", "CROP", "TIMBER"]] = None
    status: Optional[Literal["ACTIVE", "ARCHIVED"]] = None
    geometry: Optional[str] = None  # WKT or GeoJSON string


class BackfillRequest(BaseModel):
    from_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    to_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    cadence: Literal["weekly"] = "weekly"


# Job Schemas
class JobView(BaseModel):
    id: UUID
    aoi_id: Optional[UUID]
    job_type: str
    status: str
    payload: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class JobRunView(BaseModel):
    id: UUID
    job_id: UUID
    attempt: int
    status: str
    metrics: Optional[dict] = None
    error: Optional[dict] = None
    started_at: datetime
    finished_at: Optional[datetime] = None


# Tenant Admin Schemas
class InviteMemberRequest(BaseModel):
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    name: str = Field(..., min_length=1, max_length=100)
    role: Literal["TENANT_ADMIN", "OPERATOR", "VIEWER"]


class MembershipView(BaseModel):
    id: UUID
    identity_id: UUID
    email: str
    name: str
    role: str
    status: str
    created_at: datetime


class MembershipRolePatch(BaseModel):
    role: Literal["TENANT_ADMIN", "OPERATOR", "VIEWER"]


class MembershipStatusPatch(BaseModel):
    status: Literal["ACTIVE", "SUSPENDED"]


class TenantSettingsView(BaseModel):
    tier: str
    min_valid_pixel_ratio: float
    alert_thresholds: dict


class TenantSettingsPatch(BaseModel):
    min_valid_pixel_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)
    alert_thresholds: Optional[dict] = None


class AuditLogView(BaseModel):
    id: UUID
    action: str
    resource_type: str
    resource_id: Optional[str]
    changes: Optional[dict]
    metadata: Optional[dict]
    created_at: datetime


# System Admin Schemas
class TenantView(BaseModel):
    id: UUID
    name: str
    type: str
    status: str
    created_at: datetime


class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: Literal["COMPANY", "PERSONAL"]


class TenantPatch(BaseModel):
    status: Literal["ACTIVE", "SUSPENDED"]


class SystemJobView(BaseModel):
    id: UUID
    tenant_id: UUID
    aoi_id: Optional[UUID]
    aoi_name: Optional[str] = None
    farm_name: Optional[str] = None
    job_type: str
    job_key: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DLQMessageView(BaseModel):
    message_id: str
    body: dict
    receive_count: int
    first_received: datetime


# ============
# Copilot Schemas
# ============

class CopilotThreadCreate(BaseModel):
    aoi_id: Optional[UUID] = None
    signal_id: Optional[UUID] = None


class CopilotMessageCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class CopilotApprovalDecision(BaseModel):
    decision: Literal["APPROVED", "REJECTED"]
    note: Optional[str] = Field(None, max_length=500)


# ============
# Error Schema
# ============

class ErrorResponse(BaseModel):
    error: dict
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input",
                    "details": {},
                    "traceId": "abc123",
                }
            }
        }
    )
