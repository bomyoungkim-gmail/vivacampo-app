# FEAT-0007 — Vision Service (Computer Vision AI)

Date: 2026-01-20
Owner: AI Team, Backend Team
Status: Done

## Goal
Provide AI-powered image analysis for livestock weight estimation, crop disease detection, and animal health assessment using computer vision models.

**User value:** Farmers can instantly assess animal weight, detect crop diseases, and identify livestock health issues by taking a photo with their phone - no veterinary visit required for initial triage.

## Scope
**In scope:**
- **Livestock weight estimation:** Cattle (bovine) and swine weight from photos
- **Crop disease detection:** 7 crops (soybean, corn, coffee, citrus, cotton, sugarcane, pasture)
- **Poultry health:** Chicken and turkey disease detection
- **Bovine health:** Cattle disease and condition detection (respiratory, skin, eyes, feet, metabolic, parasitic)
- **Swine health:** Pig disease and condition detection (respiratory, skin, digestive, locomotor, reproductive)
- Batch analysis (up to 10 images)
- TFLite optimization for edge deployment

**Out of scope:**
- Real-time video analysis
- Drone imagery processing
- Model training in production (offline only)
- Multi-animal detection in single image (1 animal per photo)

## User Stories
- **As a farmer**, I want to estimate cattle weight from a photo, so that I can track growth without a scale.
- **As an agronomist**, I want to identify crop diseases from leaf photos, so that I can recommend treatments quickly.
- **As a farm manager**, I want to assess livestock health remotely, so that I can prioritize veterinary visits.
- **As a poultry farmer**, I want early disease detection, so that I can prevent flock-wide outbreaks.

## UX Notes
**Vision Tab in App:**
- Camera capture or gallery upload
- Analysis type selector (auto-detect or manual)
- Results card with confidence score, severity badge, recommendations
- History of past analyses per farm

**Result Display:**
- Weight estimation: kg value, range (confidence interval), Body Condition Score (1-9)
- Disease detection: Disease name, severity (0-5), treatment recommendations, alternatives
- Health assessment: Health score (0-100), alert level (normal/attention/warning/critical/emergency)

**Alert Levels (color-coded):**
- Normal: Green - no action required
- Attention: Yellow - monitor closely
- Warning: Orange - action recommended
- Critical: Red - immediate action required
- Emergency: Dark red - veterinary emergency

## Contract Changes
**API Endpoints:**
- `POST /v1/vision/analyze` - Generic analysis (file upload + analysis_type)
- `POST /v1/vision/analyze/base64` - Base64 image input (for mobile apps)
- `POST /v1/vision/analyze/batch` - Batch analysis (up to 10 images)
- `POST /v1/vision/cattle/weight` - Cattle weight estimation shortcut
- `POST /v1/vision/swine/weight` - Swine weight estimation shortcut
- `POST /v1/vision/crop/disease` - Crop disease detection shortcut
- `POST /v1/vision/poultry/health` - Poultry health assessment shortcut
- `POST /v1/vision/bovine/health` - Bovine health assessment shortcut
- `POST /v1/vision/swine/health` - Swine health assessment shortcut
- `GET /v1/vision/health` - Service health check
- `GET /v1/vision/models` - Model info
- `GET /v1/vision/crops` - Supported crops list
- `GET /v1/vision/crops/{crop}/diseases` - Diseases for specific crop
- `GET /v1/vision/livestock/bovine/conditions` - Bovine health conditions
- `GET /v1/vision/livestock/swine/conditions` - Swine health conditions

**Analysis Types (enum):**
```
cattle_weight | swine_weight | crop_disease | poultry_health | bovine_health | swine_health | auto
```

**Response Examples:**
```json
// Weight estimation
{
  "success": true,
  "analysis_type": "cattle_weight",
  "result": {
    "animal_type": "bovine",
    "estimated_weight_kg": 485.5,
    "weight_range_kg": [460.0, 510.0],
    "body_condition_score": 6,
    "bcs_description": "Moderately fleshy",
    "confidence": 0.87
  },
  "processing_time_ms": 245.3
}

// Disease detection
{
  "success": true,
  "analysis_type": "crop_disease",
  "result": {
    "disease_id": "soybean_rust",
    "disease_name": "Asian Soybean Rust",
    "crop": "soybean",
    "severity": 3,
    "severity_label": "Moderate",
    "confidence": 0.92,
    "recommendations": [
      "Apply fungicide immediately",
      "Inspect adjacent fields",
      "Consider early harvest if severe"
    ],
    "is_healthy": false,
    "requires_action": true
  }
}

// Health assessment
{
  "success": true,
  "analysis_type": "bovine_health",
  "result": {
    "condition_id": "pinkeye",
    "condition_name": "Infectious Bovine Keratoconjunctivitis",
    "category": "eyes",
    "severity": 2,
    "health_score": 72.5,
    "confidence": 0.89,
    "indicators": ["Eye redness", "Excessive tearing", "Corneal opacity"],
    "recommendations": [
      "Isolate affected animal",
      "Administer antibiotic eye ointment",
      "Provide shade to reduce UV exposure"
    ],
    "alert_level": "warning",
    "requires_veterinary": true,
    "is_emergency": false
  }
}
```

**Domain:**
- Service: `services/vision-service` (standalone FastAPI service)
- Models: TensorFlow/TFLite classifiers in `app/models/`
- Predictor: `app/inference/predictor.py` - unified inference interface

**Data:**
- No database tables (stateless service)
- Model files: `models/` directory (not in repo, downloaded separately)
- Training data: External (PlantVillage, custom datasets)

## Acceptance Criteria
- [x] User can upload image for analysis
- [x] User can send base64 image (mobile-friendly)
- [x] System estimates cattle weight with Body Condition Score
- [x] System estimates swine weight with Body Condition Score
- [x] System detects diseases for 7 crop types
- [x] System assesses poultry health with alert levels
- [x] System assesses bovine health with 20+ conditions
- [x] System assesses swine health with 15+ conditions
- [x] Batch analysis supports up to 10 images
- [x] Processing time <500ms per image (TFLite)
- [x] Confidence scores returned for all predictions
- [x] Treatment recommendations provided for diseases

## Observability
**Logs:**
- `image_analyzed` (analysis_type, processing_time_ms)
- `batch_analyzed` (analysis_type, count, processing_time_ms)
- `analysis_failed` (error, analysis_type)

**Metrics:**
- `vision_requests_total` (counter by analysis_type)
- `vision_processing_seconds` (histogram by analysis_type)
- `vision_confidence_scores` (histogram by analysis_type)

## Testing
**Unit tests:**
- Predictor initialization
- Image preprocessing
- Model output parsing

**Integration tests:**
- End-to-end analysis flow (with test images)
- Batch analysis
- Error handling (invalid image, unsupported format)

**Manual tests:**
- Test with real farm photos
- Compare weight estimates with actual measurements
- Validate disease detection accuracy with agronomist

## Architecture Notes
**Service Independence:**
- Runs as separate Docker container
- Optional GPU support (CUDA for training, CPU/TFLite for inference)
- Stateless - can be scaled horizontally

**Model Management:**
- Models downloaded from cloud storage (not in git)
- TFLite conversion for production (smaller, faster)
- Model versioning in responses

## Status
Done - Deployed 2026-01-25
