"""
API Schemas for Vision Service

Pydantic models for request/response validation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class AnalysisType(str, Enum):
    CATTLE_WEIGHT = "cattle_weight"
    SWINE_WEIGHT = "swine_weight"
    CROP_DISEASE = "crop_disease"
    POULTRY_HEALTH = "poultry_health"
    BOVINE_HEALTH = "bovine_health"
    SWINE_HEALTH = "swine_health"
    AUTO = "auto"


class AnimalType(str, Enum):
    BOVINE = "bovine"
    SWINE = "swine"
    POULTRY = "poultry"


# ==================== Request Schemas ====================


class ImageAnalysisRequest(BaseModel):
    """Request for image analysis."""

    analysis_type: AnalysisType = Field(
        ...,
        description="Type of analysis to perform",
    )
    image_base64: Optional[str] = Field(
        None,
        description="Base64 encoded image (alternative to file upload)",
    )


class BatchAnalysisRequest(BaseModel):
    """Request for batch image analysis."""

    analysis_type: AnalysisType
    images_base64: List[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of base64 encoded images",
    )


# ==================== Response Schemas ====================


class WeightEstimationResponse(BaseModel):
    """Response for cattle/swine weight estimation."""

    animal_type: str
    estimated_weight_kg: float
    weight_range_kg: tuple[float, float]
    body_condition_score: int = Field(..., ge=1, le=9)
    bcs_description: str
    bcs_confidence: float
    confidence: float
    model_version: str


class DiseaseDetectionResponse(BaseModel):
    """Response for crop disease detection."""

    disease_id: str
    disease_name: str
    crop: str
    severity: int = Field(..., ge=0, le=5)
    severity_label: str
    severity_color: str
    confidence: float
    recommendations: List[str]
    alternatives: List[Dict[str, Any]]
    is_healthy: bool
    requires_action: bool
    model_version: str


class LivestockHealthResponse(BaseModel):
    """Response for livestock (bovine/swine) health assessment."""

    condition_id: str
    condition_name: str
    animal: str
    category: str
    category_name: str
    severity: int = Field(..., ge=0, le=5)
    health_score: float = Field(..., ge=0, le=100)
    confidence: float
    indicators: List[str]
    recommendations: List[str]
    alternatives: List[Dict[str, Any]]
    is_healthy: bool
    alert_level: str
    alert_color: str
    requires_veterinary: bool
    is_emergency: bool
    requires_notification: bool
    model_version: str


class PoultryHealthResponse(BaseModel):
    """Response for poultry health assessment."""

    condition_id: str
    condition_name: str
    animal: str
    category: str
    category_name: str
    severity: int = Field(..., ge=0, le=5)
    health_score: float = Field(..., ge=0, le=100)
    confidence: float
    indicators: List[str]
    recommendations: List[str]
    alternatives: List[Dict[str, Any]]
    is_healthy: bool
    alert_level: str
    alert_color: str
    requires_veterinary: bool
    requires_notification: bool
    model_version: str


class AnalysisResponse(BaseModel):
    """Generic analysis response wrapper."""

    success: bool = True
    analysis_type: str
    result: Dict[str, Any]
    processing_time_ms: Optional[float] = None


class BatchAnalysisResponse(BaseModel):
    """Response for batch analysis."""

    success: bool = True
    analysis_type: str
    results: List[Dict[str, Any]]
    total_count: int
    processing_time_ms: Optional[float] = None


class ModelInfoResponse(BaseModel):
    """Response with model information."""

    cattle_weight: Optional[Dict[str, Any]]
    swine_weight: Optional[Dict[str, Any]]
    crop_disease: Optional[Dict[str, Any]]
    poultry_health: Optional[Dict[str, Any]]
    bovine_health: Optional[Dict[str, Any]]
    swine_health: Optional[Dict[str, Any]]
    use_tflite: bool
    models_dir: str


class SupportedCropsResponse(BaseModel):
    """Response with supported crops list."""

    crops: List[str]


class CropDiseasesResponse(BaseModel):
    """Response with diseases for a specific crop."""

    crop: str
    diseases: List[Dict[str, Any]]


class LivestockConditionsResponse(BaseModel):
    """Response with livestock health conditions."""

    animal: str
    conditions: List[Dict[str, Any]]


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    service: str = "vision-service"
    version: str = "1.0.0"
    models_loaded: Dict[str, bool]


class ErrorResponse(BaseModel):
    """Error response."""

    success: bool = False
    error: str
    detail: Optional[str] = None
