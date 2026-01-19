"""
Vision API Routes

FastAPI endpoints for image analysis.
"""

import base64
import time
from typing import Any, Dict, List
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
import structlog

from app.inference.predictor import get_predictor
from app.api.schemas import (
    AnalysisType,
    AnalysisResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    CropDiseasesResponse,
    ErrorResponse,
    HealthCheckResponse,
    LivestockConditionsResponse,
    ModelInfoResponse,
    SupportedCropsResponse,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/v1/vision", tags=["vision"])


# ==================== Health & Info ====================


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Check service health and model status."""
    predictor = get_predictor()
    info = predictor.get_model_info()

    return HealthCheckResponse(
        status="healthy",
        service="vision-service",
        version="1.0.0",
        models_loaded={
            "cattle_weight": info.get("cattle_weight") is not None,
            "swine_weight": info.get("swine_weight") is not None,
            "crop_disease": info.get("crop_disease") is not None,
            "poultry_health": info.get("poultry_health") is not None,
            "bovine_health": info.get("bovine_health") is not None,
            "swine_health": info.get("swine_health") is not None,
        },
    )


@router.get("/models", response_model=ModelInfoResponse)
async def get_models_info():
    """Get information about loaded models."""
    predictor = get_predictor()
    return predictor.get_model_info()


@router.get("/crops", response_model=SupportedCropsResponse)
async def get_supported_crops():
    """Get list of supported crops for disease detection."""
    predictor = get_predictor()
    return SupportedCropsResponse(crops=predictor.get_supported_crops())


@router.get("/crops/{crop}/diseases", response_model=CropDiseasesResponse)
async def get_crop_diseases(crop: str):
    """Get all diseases for a specific crop."""
    predictor = get_predictor()
    diseases = predictor.get_diseases_by_crop(crop)

    if not diseases:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No diseases found for crop: {crop}",
        )

    return CropDiseasesResponse(crop=crop, diseases=diseases)


@router.get("/livestock/bovine/conditions", response_model=LivestockConditionsResponse)
async def get_bovine_conditions():
    """Get all health conditions for bovine (cattle)."""
    predictor = get_predictor()
    conditions = predictor.get_bovine_conditions()
    return LivestockConditionsResponse(animal="bovine", conditions=conditions)


@router.get("/livestock/swine/conditions", response_model=LivestockConditionsResponse)
async def get_swine_conditions():
    """Get all health conditions for swine (pigs)."""
    predictor = get_predictor()
    conditions = predictor.get_swine_conditions()
    return LivestockConditionsResponse(animal="swine", conditions=conditions)


# ==================== Image Analysis ====================


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    analysis_type: AnalysisType = Form(...),
):
    """
    Analyze an uploaded image.

    - **file**: Image file (JPEG, PNG)
    - **analysis_type**: Type of analysis to perform
        - cattle_weight: Estimate cattle weight
        - swine_weight: Estimate swine weight
        - crop_disease: Detect crop diseases
        - poultry_health: Assess poultry health
        - bovine_health: Assess cattle health/diseases
        - swine_health: Assess swine health/diseases
        - auto: Auto-detect content type
    """
    start_time = time.perf_counter()

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload an image (JPEG, PNG).",
        )

    try:
        # Read image bytes
        image_bytes = await file.read()

        # Run analysis
        predictor = get_predictor()
        result = predictor.analyze_image(image_bytes, analysis_type.value)

        processing_time = (time.perf_counter() - start_time) * 1000

        logger.info(
            "image_analyzed",
            analysis_type=analysis_type.value,
            processing_time_ms=round(processing_time, 2),
        )

        return AnalysisResponse(
            success=True,
            analysis_type=analysis_type.value,
            result=result,
            processing_time_ms=round(processing_time, 2),
        )

    except Exception as e:
        logger.error("analysis_failed", error=str(e), analysis_type=analysis_type.value)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


@router.post("/analyze/base64", response_model=AnalysisResponse)
async def analyze_image_base64(
    image_base64: str,
    analysis_type: AnalysisType,
):
    """
    Analyze a base64 encoded image.

    Useful for mobile apps that need to send images as JSON.
    """
    start_time = time.perf_counter()

    try:
        # Decode base64
        image_bytes = base64.b64decode(image_base64)

        # Run analysis
        predictor = get_predictor()
        result = predictor.analyze_image(image_bytes, analysis_type.value)

        processing_time = (time.perf_counter() - start_time) * 1000

        return AnalysisResponse(
            success=True,
            analysis_type=analysis_type.value,
            result=result,
            processing_time_ms=round(processing_time, 2),
        )

    except Exception as e:
        logger.error("analysis_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


@router.post("/analyze/batch", response_model=BatchAnalysisResponse)
async def analyze_batch(request: BatchAnalysisRequest):
    """
    Analyze multiple images in a batch.

    Maximum 10 images per request.
    """
    start_time = time.perf_counter()

    try:
        # Decode all images
        images = [base64.b64decode(img) for img in request.images_base64]

        # Run batch analysis
        predictor = get_predictor()
        results = predictor.predict_batch(images, request.analysis_type.value)

        processing_time = (time.perf_counter() - start_time) * 1000

        logger.info(
            "batch_analyzed",
            analysis_type=request.analysis_type.value,
            count=len(images),
            processing_time_ms=round(processing_time, 2),
        )

        return BatchAnalysisResponse(
            success=True,
            analysis_type=request.analysis_type.value,
            results=results,
            total_count=len(results),
            processing_time_ms=round(processing_time, 2),
        )

    except Exception as e:
        logger.error("batch_analysis_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch analysis failed: {str(e)}",
        )


# ==================== Specialized Endpoints ====================


@router.post("/cattle/weight", response_model=AnalysisResponse)
async def estimate_cattle_weight(file: UploadFile = File(...)):
    """
    Estimate cattle (bovine) weight from image.

    Returns:
    - Estimated weight in kg
    - Weight range (confidence interval)
    - Body Condition Score (1-9)
    """
    return await analyze_image(file, AnalysisType.CATTLE_WEIGHT)


@router.post("/swine/weight", response_model=AnalysisResponse)
async def estimate_swine_weight(file: UploadFile = File(...)):
    """
    Estimate swine (pig) weight from image.

    Returns:
    - Estimated weight in kg
    - Weight range (confidence interval)
    - Body Condition Score (1-9)
    """
    return await analyze_image(file, AnalysisType.SWINE_WEIGHT)


@router.post("/crop/disease", response_model=AnalysisResponse)
async def detect_crop_disease(file: UploadFile = File(...)):
    """
    Detect crop disease from leaf/plant image.

    Supports: Soybean, Corn, Coffee, Citrus, Cotton, Sugarcane, Pasture

    Returns:
    - Disease identification
    - Severity level (0-5)
    - Treatment recommendations
    - Alternative diagnoses
    """
    return await analyze_image(file, AnalysisType.CROP_DISEASE)


@router.post("/poultry/health", response_model=AnalysisResponse)
async def assess_poultry_health(file: UploadFile = File(...)):
    """
    Assess poultry health from image.

    Detects common diseases and conditions in chickens and turkeys.

    Returns:
    - Health condition identification
    - Health score (0-100)
    - Severity level
    - Recommended actions
    - Alert level (normal/attention/warning/critical)
    """
    return await analyze_image(file, AnalysisType.POULTRY_HEALTH)


@router.post("/bovine/health", response_model=AnalysisResponse)
async def assess_bovine_health(file: UploadFile = File(...)):
    """
    Assess bovine (cattle) health from image.

    Detects common diseases and conditions including:
    - Respiratory: Pneumonia, IBR
    - Skin: Dermatophytosis, Mange, Photosensitization
    - Eyes: Pinkeye (Keratoconjunctivitis)
    - Feet: Foot rot, Digital dermatitis
    - Metabolic: Bloat, Milk fever
    - Reproductive: Mastitis, Metritis
    - Parasitic: Ticks, Anaplasmosis
    - Neurological: Rabies (suspected)

    Returns:
    - Health condition identification
    - Health score (0-100)
    - Severity level (0-5)
    - Visual indicators
    - Treatment recommendations
    - Alert level (normal/attention/warning/critical/emergency)
    """
    return await analyze_image(file, AnalysisType.BOVINE_HEALTH)


@router.post("/swine/health", response_model=AnalysisResponse)
async def assess_swine_health(file: UploadFile = File(...)):
    """
    Assess swine (pig) health from image.

    Detects common diseases and conditions including:
    - Respiratory: Pneumonia, PRRS, Influenza
    - Skin: Mange, Erysipelas, Pityriasis
    - Digestive: Diarrhea, PED
    - Locomotor: Lameness, foot problems
    - Reproductive: MMA syndrome
    - Neurological: Streptococcal meningitis

    Returns:
    - Health condition identification
    - Health score (0-100)
    - Severity level (0-5)
    - Visual indicators
    - Treatment recommendations
    - Alert level (normal/attention/warning/critical/emergency)
    """
    return await analyze_image(file, AnalysisType.SWINE_HEALTH)


# ==================== Error Handlers ====================


@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error=exc.detail,
        ).model_dump(),
    )
