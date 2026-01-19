"""
Vision Predictor

Unified interface for running inference across all vision models.
Handles model loading, preprocessing, and result formatting.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import structlog

from app.config import settings
from app.models import (
    CattleWeightModel,
    CropDiseaseModel,
    PoultryHealthModel,
    BovineHealthModel,
    SwineHealthModel,
)

logger = structlog.get_logger()


class VisionPredictor:
    """
    Unified predictor for all vision models.

    Supports both Keras and TFLite inference modes.
    TFLite is preferred for production (faster, smaller memory footprint).
    """

    def __init__(
        self,
        models_dir: Optional[Path] = None,
        use_tflite: bool = True,
        lazy_load: bool = True,
    ):
        """
        Initialize predictor.

        Args:
            models_dir: Directory containing model files
            use_tflite: Use TFLite models for inference (recommended)
            lazy_load: Load models on first use instead of at init
        """
        self.models_dir = models_dir or settings.models_dir
        self.use_tflite = use_tflite
        self.lazy_load = lazy_load

        # Model instances (lazy loaded)
        self._cattle_weight: Optional[CattleWeightModel] = None
        self._swine_weight: Optional[CattleWeightModel] = None
        self._crop_disease: Optional[CropDiseaseModel] = None
        self._poultry_health: Optional[PoultryHealthModel] = None
        self._bovine_health: Optional[BovineHealthModel] = None
        self._swine_health: Optional[SwineHealthModel] = None

        # Load models immediately if not lazy
        if not lazy_load:
            self._load_all_models()

    def _load_all_models(self) -> None:
        """Load all models."""
        self._get_cattle_weight_model()
        self._get_swine_weight_model()
        self._get_crop_disease_model()
        self._get_poultry_health_model()
        self._get_bovine_health_model()
        self._get_swine_health_model()

    def _get_cattle_weight_model(self) -> CattleWeightModel:
        """Get or create cattle weight model."""
        if self._cattle_weight is None:
            self._cattle_weight = CattleWeightModel(animal_type="bovine")
            model_path = self.models_dir / "cattle_weight_dynamic.tflite"

            if self.use_tflite and model_path.exists():
                self._cattle_weight.load_tflite(model_path)
                logger.info("loaded_tflite_model", model="cattle_weight")
            else:
                # Build model for inference without pretrained weights
                self._cattle_weight.build_model()
                logger.info("built_keras_model", model="cattle_weight")

        return self._cattle_weight

    def _get_swine_weight_model(self) -> CattleWeightModel:
        """Get or create swine weight model."""
        if self._swine_weight is None:
            self._swine_weight = CattleWeightModel(animal_type="swine")
            model_path = self.models_dir / "swine_weight_dynamic.tflite"

            if self.use_tflite and model_path.exists():
                self._swine_weight.load_tflite(model_path)
                logger.info("loaded_tflite_model", model="swine_weight")
            else:
                self._swine_weight.build_model()
                logger.info("built_keras_model", model="swine_weight")

        return self._swine_weight

    def _get_crop_disease_model(self) -> CropDiseaseModel:
        """Get or create crop disease model."""
        if self._crop_disease is None:
            self._crop_disease = CropDiseaseModel()
            model_path = self.models_dir / "crop_disease_dynamic.tflite"

            if self.use_tflite and model_path.exists():
                self._crop_disease.load_tflite(model_path)
                logger.info("loaded_tflite_model", model="crop_disease")
            else:
                self._crop_disease.build_model()
                logger.info("built_keras_model", model="crop_disease")

        return self._crop_disease

    def _get_poultry_health_model(self) -> PoultryHealthModel:
        """Get or create poultry health model."""
        if self._poultry_health is None:
            self._poultry_health = PoultryHealthModel()
            model_path = self.models_dir / "poultry_health_dynamic.tflite"

            if self.use_tflite and model_path.exists():
                self._poultry_health.load_tflite(model_path)
                logger.info("loaded_tflite_model", model="poultry_health")
            else:
                self._poultry_health.build_model()
                logger.info("built_keras_model", model="poultry_health")

        return self._poultry_health

    def _get_bovine_health_model(self) -> BovineHealthModel:
        """Get or create bovine health model."""
        if self._bovine_health is None:
            self._bovine_health = BovineHealthModel()
            model_path = self.models_dir / "bovine_health_dynamic.tflite"

            if self.use_tflite and model_path.exists():
                self._bovine_health.load_tflite(model_path)
                logger.info("loaded_tflite_model", model="bovine_health")
            else:
                self._bovine_health.build_model()
                logger.info("built_keras_model", model="bovine_health")

        return self._bovine_health

    def _get_swine_health_model(self) -> SwineHealthModel:
        """Get or create swine health model."""
        if self._swine_health is None:
            self._swine_health = SwineHealthModel()
            model_path = self.models_dir / "swine_health_dynamic.tflite"

            if self.use_tflite and model_path.exists():
                self._swine_health.load_tflite(model_path)
                logger.info("loaded_tflite_model", model="swine_health")
            else:
                self._swine_health.build_model()
                logger.info("built_keras_model", model="swine_health")

        return self._swine_health

    # ==================== PUBLIC API ====================

    def predict_cattle_weight(
        self,
        image: Union[np.ndarray, bytes, str, Path],
    ) -> Dict[str, Any]:
        """
        Estimate cattle (bovine) weight from image.

        Args:
            image: Image as numpy array, bytes, or file path

        Returns:
            Dict with weight estimation and body condition score
        """
        model = self._get_cattle_weight_model()
        img_array = self._load_image(image, model.input_size)

        if self.use_tflite and model.tflite_interpreter:
            return model.predict_tflite(img_array)
        else:
            return model.predict(img_array)

    def predict_swine_weight(
        self,
        image: Union[np.ndarray, bytes, str, Path],
    ) -> Dict[str, Any]:
        """
        Estimate swine (pig) weight from image.

        Args:
            image: Image as numpy array, bytes, or file path

        Returns:
            Dict with weight estimation and body condition score
        """
        model = self._get_swine_weight_model()
        img_array = self._load_image(image, model.input_size)

        if self.use_tflite and model.tflite_interpreter:
            return model.predict_tflite(img_array)
        else:
            return model.predict(img_array)

    def predict_crop_disease(
        self,
        image: Union[np.ndarray, bytes, str, Path],
    ) -> Dict[str, Any]:
        """
        Detect crop disease from leaf/plant image.

        Args:
            image: Image as numpy array, bytes, or file path

        Returns:
            Dict with disease identification, severity, and recommendations
        """
        model = self._get_crop_disease_model()
        img_array = self._load_image(image, model.input_size)

        if self.use_tflite and model.tflite_interpreter:
            return model.predict_tflite(img_array)
        else:
            return model.predict(img_array)

    def predict_poultry_health(
        self,
        image: Union[np.ndarray, bytes, str, Path],
    ) -> Dict[str, Any]:
        """
        Assess poultry health from image.

        Args:
            image: Image as numpy array, bytes, or file path

        Returns:
            Dict with health condition, score, and recommendations
        """
        model = self._get_poultry_health_model()
        img_array = self._load_image(image, model.input_size)

        if self.use_tflite and model.tflite_interpreter:
            return model.predict_tflite(img_array)
        else:
            return model.predict(img_array)

    def predict_bovine_health(
        self,
        image: Union[np.ndarray, bytes, str, Path],
    ) -> Dict[str, Any]:
        """
        Assess bovine (cattle) health from image.

        Detects common diseases: pneumonia, mastitis, foot rot, tick infestation,
        skin conditions, eye diseases, metabolic disorders, etc.

        Args:
            image: Image as numpy array, bytes, or file path

        Returns:
            Dict with health condition, severity, indicators, and recommendations
        """
        model = self._get_bovine_health_model()
        img_array = self._load_image(image, model.input_size)

        if self.use_tflite and model.tflite_interpreter:
            return model.predict_tflite(img_array)
        else:
            return model.predict(img_array)

    def predict_swine_health(
        self,
        image: Union[np.ndarray, bytes, str, Path],
    ) -> Dict[str, Any]:
        """
        Assess swine (pig) health from image.

        Detects common diseases: pneumonia, PRRS, erysipelas, mange,
        diarrhea, lameness, reproductive issues, etc.

        Args:
            image: Image as numpy array, bytes, or file path

        Returns:
            Dict with health condition, severity, indicators, and recommendations
        """
        model = self._get_swine_health_model()
        img_array = self._load_image(image, model.input_size)

        if self.use_tflite and model.tflite_interpreter:
            return model.predict_tflite(img_array)
        else:
            return model.predict(img_array)

    def predict_batch(
        self,
        images: List[Union[np.ndarray, bytes, str, Path]],
        model_type: str,
    ) -> List[Dict[str, Any]]:
        """
        Run batch inference.

        Args:
            images: List of images
            model_type: One of the supported analysis types

        Returns:
            List of prediction results
        """
        model_map = {
            "cattle_weight": self._get_cattle_weight_model,
            "swine_weight": self._get_swine_weight_model,
            "crop_disease": self._get_crop_disease_model,
            "poultry_health": self._get_poultry_health_model,
            "bovine_health": self._get_bovine_health_model,
            "swine_health": self._get_swine_health_model,
        }

        if model_type not in model_map:
            raise ValueError(f"Unknown model type: {model_type}")

        model = model_map[model_type]()
        img_arrays = [self._load_image(img, model.input_size) for img in images]

        # Batch inference only works with Keras models
        if self.use_tflite and model.tflite_interpreter:
            # Run sequentially for TFLite
            return [model.predict_tflite(img) for img in img_arrays]
        else:
            return model.predict_batch(img_arrays)

    def analyze_image(
        self,
        image: Union[np.ndarray, bytes, str, Path],
        analysis_type: str,
    ) -> Dict[str, Any]:
        """
        Generic analysis endpoint.

        Args:
            image: Image to analyze
            analysis_type: One of:
                - "cattle_weight": Estimate cattle weight
                - "swine_weight": Estimate swine weight
                - "crop_disease": Detect crop diseases
                - "poultry_health": Assess poultry health
                - "bovine_health": Assess cattle health/diseases
                - "swine_health": Assess swine health/diseases
                - "auto" (try to detect image content)

        Returns:
            Analysis results
        """
        if analysis_type == "cattle_weight":
            return self.predict_cattle_weight(image)
        elif analysis_type == "swine_weight":
            return self.predict_swine_weight(image)
        elif analysis_type == "crop_disease":
            return self.predict_crop_disease(image)
        elif analysis_type == "poultry_health":
            return self.predict_poultry_health(image)
        elif analysis_type == "bovine_health":
            return self.predict_bovine_health(image)
        elif analysis_type == "swine_health":
            return self.predict_swine_health(image)
        elif analysis_type == "auto":
            # TODO: Implement auto-detection of image content
            # For now, default to crop disease
            return self.predict_crop_disease(image)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        return {
            "cattle_weight": self._cattle_weight.get_model_info() if self._cattle_weight else None,
            "swine_weight": self._swine_weight.get_model_info() if self._swine_weight else None,
            "crop_disease": self._crop_disease.get_model_info() if self._crop_disease else None,
            "poultry_health": self._poultry_health.get_model_info() if self._poultry_health else None,
            "bovine_health": self._bovine_health.get_model_info() if self._bovine_health else None,
            "swine_health": self._swine_health.get_model_info() if self._swine_health else None,
            "use_tflite": self.use_tflite,
            "models_dir": str(self.models_dir),
        }

    def get_supported_crops(self) -> List[str]:
        """Get list of supported crops for disease detection."""
        model = self._get_crop_disease_model()
        return model.get_supported_crops()

    def get_diseases_by_crop(self, crop: str) -> List[Dict[str, Any]]:
        """Get all diseases for a specific crop."""
        model = self._get_crop_disease_model()
        return model.get_diseases_by_crop(crop)

    def get_bovine_conditions(self) -> List[Dict[str, Any]]:
        """Get all bovine health conditions."""
        model = self._get_bovine_health_model()
        return [{"id": k, **v} for k, v in model._conditions.items()]

    def get_swine_conditions(self) -> List[Dict[str, Any]]:
        """Get all swine health conditions."""
        model = self._get_swine_health_model()
        return [{"id": k, **v} for k, v in model._conditions.items()]

    # ==================== PRIVATE METHODS ====================

    def _load_image(
        self,
        image: Union[np.ndarray, bytes, str, Path],
        target_size: tuple,
    ) -> np.ndarray:
        """Load and resize image from various sources."""
        from PIL import Image

        if isinstance(image, np.ndarray):
            img_array = image
        elif isinstance(image, bytes):
            from io import BytesIO
            img = Image.open(BytesIO(image)).convert("RGB")
            img_array = np.array(img)
        elif isinstance(image, (str, Path)):
            img = Image.open(image).convert("RGB")
            img_array = np.array(img)
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")

        # Resize if needed
        if img_array.shape[:2] != target_size:
            img = Image.fromarray(img_array)
            img = img.resize((target_size[1], target_size[0]), Image.Resampling.LANCZOS)
            img_array = np.array(img)

        return img_array


# Singleton instance for API use
_predictor: Optional[VisionPredictor] = None


def get_predictor() -> VisionPredictor:
    """Get or create singleton predictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = VisionPredictor()
    return _predictor
