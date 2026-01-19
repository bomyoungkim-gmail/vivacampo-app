"""
Cattle Weight Estimation Model

Uses computer vision to estimate cattle weight from images.
Approach:
1. Detect cattle body using object detection
2. Extract body measurements (length, height, width estimation)
3. Regression model to estimate weight based on visual features

Supports: Bovine (cattle), Swine (pigs)
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from .base_model import BaseVisionModel
import structlog

logger = structlog.get_logger()


# Weight ranges by animal type and breed (kg)
WEIGHT_RANGES = {
    "bovine": {
        "nelore": {"min": 200, "max": 800},
        "angus": {"min": 250, "max": 900},
        "brahman": {"min": 220, "max": 850},
        "generic": {"min": 200, "max": 900},
    },
    "swine": {
        "landrace": {"min": 20, "max": 150},
        "large_white": {"min": 20, "max": 160},
        "generic": {"min": 15, "max": 160},
    },
}

# Body Condition Score descriptions
BCS_DESCRIPTIONS = {
    1: "Muito magro - Costelas, espinha e ossos do quadril muito proeminentes",
    2: "Magro - Costelas facilmente visíveis",
    3: "Magro moderado - Costelas visíveis mas com alguma cobertura",
    4: "Limite inferior ideal - Costelas palpáveis com leve pressão",
    5: "Ideal - Costelas palpáveis, boa cobertura muscular",
    6: "Limite superior ideal - Costelas palpáveis com pressão firme",
    7: "Gordo - Costelas difíceis de palpar",
    8: "Gordo excessivo - Depósitos de gordura visíveis",
    9: "Obeso - Grandes depósitos de gordura",
}


class CattleWeightModel(BaseVisionModel):
    """
    Model for estimating cattle/swine weight and body condition score.

    Architecture:
    - Backbone: EfficientNetV2-S (pretrained on ImageNet)
    - Head: Custom regression head for weight + BCS classification

    Input: RGB image 384x384
    Output:
        - estimated_weight_kg: float
        - weight_range: (min, max)
        - body_condition_score: 1-9
        - confidence: float
    """

    def __init__(
        self,
        animal_type: str = "bovine",
        input_size: Tuple[int, int] = (384, 384),
    ):
        super().__init__(
            model_name=f"cattle_weight_{animal_type}",
            input_size=input_size,
            num_classes=9,  # BCS classes 1-9
        )
        self.animal_type = animal_type
        self._class_names = [f"BCS_{i}" for i in range(1, 10)]

    def build_model(self) -> tf.keras.Model:
        """
        Build EfficientNetV2-based model with dual heads:
        1. Regression head for weight estimation
        2. Classification head for Body Condition Score
        """
        # Input layer
        inputs = tf.keras.Input(shape=(*self.input_size, 3), name="image_input")

        # Data augmentation (only during training)
        x = tf.keras.layers.RandomFlip("horizontal")(inputs)
        x = tf.keras.layers.RandomRotation(0.1)(x)
        x = tf.keras.layers.RandomZoom(0.1)(x)
        x = tf.keras.layers.RandomBrightness(0.2)(x)
        x = tf.keras.layers.RandomContrast(0.2)(x)

        # Backbone: EfficientNetV2-S
        backbone = tf.keras.applications.EfficientNetV2S(
            include_top=False,
            weights="imagenet",
            input_shape=(*self.input_size, 3),
            pooling="avg",
        )

        # Freeze backbone initially (for transfer learning)
        backbone.trainable = False

        features = backbone(x)

        # Shared dense layers
        shared = tf.keras.layers.Dense(512, activation="relu")(features)
        shared = tf.keras.layers.BatchNormalization()(shared)
        shared = tf.keras.layers.Dropout(0.3)(shared)

        shared = tf.keras.layers.Dense(256, activation="relu")(shared)
        shared = tf.keras.layers.BatchNormalization()(shared)
        shared = tf.keras.layers.Dropout(0.2)(shared)

        # Head 1: Weight Regression
        weight_head = tf.keras.layers.Dense(128, activation="relu")(shared)
        weight_head = tf.keras.layers.Dense(64, activation="relu")(weight_head)
        weight_output = tf.keras.layers.Dense(1, activation="linear", name="weight")(
            weight_head
        )

        # Head 2: Body Condition Score Classification
        bcs_head = tf.keras.layers.Dense(128, activation="relu")(shared)
        bcs_head = tf.keras.layers.Dense(64, activation="relu")(bcs_head)
        bcs_output = tf.keras.layers.Dense(9, activation="softmax", name="bcs")(
            bcs_head
        )

        # Head 3: Confidence estimation
        conf_head = tf.keras.layers.Dense(64, activation="relu")(shared)
        conf_output = tf.keras.layers.Dense(1, activation="sigmoid", name="confidence")(
            conf_head
        )

        model = tf.keras.Model(
            inputs=inputs, outputs=[weight_output, bcs_output, conf_output]
        )

        self.model = model
        return model

    def compile_model(self, learning_rate: float = 1e-4) -> None:
        """Compile model with appropriate losses for each head."""
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")

        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
            loss={
                "weight": "mse",
                "bcs": "sparse_categorical_crossentropy",
                "confidence": "binary_crossentropy",
            },
            loss_weights={"weight": 1.0, "bcs": 0.5, "confidence": 0.3},
            metrics={
                "weight": ["mae"],
                "bcs": ["accuracy"],
                "confidence": ["accuracy"],
            },
        )

    def unfreeze_backbone(self, num_layers: int = 50) -> None:
        """Unfreeze top layers of backbone for fine-tuning."""
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")

        # Find backbone layer
        for layer in self.model.layers:
            if isinstance(layer, tf.keras.applications.EfficientNetV2S):
                layer.trainable = True
                # Freeze all but last num_layers
                for l in layer.layers[:-num_layers]:
                    l.trainable = False
                logger.info("backbone_unfrozen", num_trainable_layers=num_layers)
                break

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for EfficientNetV2.
        - Normalize to [0, 1]
        - Apply EfficientNet-specific preprocessing
        """
        # Ensure correct size
        if image.shape[:2] != self.input_size:
            from PIL import Image

            img = Image.fromarray(image)
            img = img.resize(self.input_size, Image.Resampling.LANCZOS)
            image = np.array(img)

        # Normalize to [0, 1]
        image = image.astype(np.float32) / 255.0

        return image

    def postprocess_output(self, output: np.ndarray | List[np.ndarray]) -> Dict[str, Any]:
        """
        Convert model output to human-readable format.

        For multi-output model, output is a list: [weight, bcs_probs, confidence]
        """
        if isinstance(output, list):
            weight_raw = output[0]
            bcs_probs = output[1]
            confidence_raw = output[2]
        else:
            # Single output fallback
            weight_raw = output
            bcs_probs = None
            confidence_raw = 0.5

        # Denormalize weight (model outputs normalized value 0-1)
        weight_range = WEIGHT_RANGES[self.animal_type]["generic"]
        weight_min, weight_max = weight_range["min"], weight_range["max"]

        if isinstance(weight_raw, np.ndarray):
            weight_normalized = float(weight_raw.flatten()[0])
        else:
            weight_normalized = float(weight_raw)

        estimated_weight = weight_min + weight_normalized * (weight_max - weight_min)
        estimated_weight = max(weight_min, min(weight_max, estimated_weight))

        # Calculate confidence interval (±10% typical)
        margin = estimated_weight * 0.10
        weight_range_estimate = (
            round(estimated_weight - margin, 1),
            round(estimated_weight + margin, 1),
        )

        # Body Condition Score
        if bcs_probs is not None:
            bcs_class = int(np.argmax(bcs_probs)) + 1  # 1-indexed
            bcs_confidence = float(np.max(bcs_probs))
        else:
            bcs_class = 5  # Default to ideal
            bcs_confidence = 0.5

        # Overall confidence
        if isinstance(confidence_raw, np.ndarray):
            confidence = float(confidence_raw.flatten()[0])
        else:
            confidence = float(confidence_raw)

        return {
            "animal_type": self.animal_type,
            "estimated_weight_kg": round(estimated_weight, 1),
            "weight_range_kg": weight_range_estimate,
            "body_condition_score": bcs_class,
            "bcs_description": BCS_DESCRIPTIONS.get(bcs_class, ""),
            "bcs_confidence": round(bcs_confidence, 3),
            "confidence": round(confidence, 3),
            "model_version": self.model_name,
        }

    def create_representative_dataset(
        self, sample_images: List[np.ndarray]
    ) -> callable:
        """
        Create representative dataset generator for TFLite quantization.
        """

        def representative_dataset():
            for img in sample_images[:100]:  # Use up to 100 samples
                preprocessed = self.preprocess_image(img)
                yield [np.expand_dims(preprocessed, axis=0).astype(np.float32)]

        return representative_dataset


class SwineWeightModel(CattleWeightModel):
    """Specialized model for swine (pig) weight estimation."""

    def __init__(self, input_size: Tuple[int, int] = (384, 384)):
        super().__init__(animal_type="swine", input_size=input_size)
        self.model_name = "swine_weight"
