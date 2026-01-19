"""
Crop Disease Detection Model

Identifies diseases in crops from leaf/plant images.
Trained on PlantVillage + PlantDoc datasets with additional
Brazilian crop diseases.

Supports: Soybean, Corn, Cotton, Coffee, Sugarcane, Citrus, etc.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import tensorflow as tf
from .base_model import BaseVisionModel
import structlog

logger = structlog.get_logger()


# Disease categories with Portuguese translations and severity
DISEASE_CATALOG = {
    # Soybean diseases
    "soybean_healthy": {
        "name_pt": "Soja Saudável",
        "crop": "soybean",
        "severity": 0,
        "recommendations": [],
    },
    "soybean_rust": {
        "name_pt": "Ferrugem Asiática da Soja",
        "crop": "soybean",
        "severity": 4,
        "recommendations": [
            "Aplicar fungicida imediatamente",
            "Monitorar áreas vizinhas",
            "Considerar cultivares resistentes na próxima safra",
        ],
    },
    "soybean_bacterial_blight": {
        "name_pt": "Crestamento Bacteriano",
        "crop": "soybean",
        "severity": 3,
        "recommendations": [
            "Evitar trabalho no campo com plantas molhadas",
            "Usar sementes certificadas",
            "Rotação de culturas",
        ],
    },
    "soybean_target_spot": {
        "name_pt": "Mancha Alvo",
        "crop": "soybean",
        "severity": 3,
        "recommendations": [
            "Aplicar fungicida preventivo",
            "Manter espaçamento adequado",
            "Eliminar restos culturais",
        ],
    },
    # Corn diseases
    "corn_healthy": {
        "name_pt": "Milho Saudável",
        "crop": "corn",
        "severity": 0,
        "recommendations": [],
    },
    "corn_cercospora_leaf_spot": {
        "name_pt": "Cercosporiose",
        "crop": "corn",
        "severity": 2,
        "recommendations": [
            "Aplicar fungicida se necessário",
            "Usar híbridos tolerantes",
            "Rotação de culturas",
        ],
    },
    "corn_common_rust": {
        "name_pt": "Ferrugem Comum do Milho",
        "crop": "corn",
        "severity": 3,
        "recommendations": [
            "Aplicar fungicida em casos severos",
            "Plantar híbridos resistentes",
            "Monitorar condições climáticas",
        ],
    },
    "corn_northern_leaf_blight": {
        "name_pt": "Helmintosporiose",
        "crop": "corn",
        "severity": 3,
        "recommendations": [
            "Fungicida preventivo em áreas de risco",
            "Eliminar restos de cultura",
            "Usar híbridos resistentes",
        ],
    },
    # Coffee diseases
    "coffee_healthy": {
        "name_pt": "Café Saudável",
        "crop": "coffee",
        "severity": 0,
        "recommendations": [],
    },
    "coffee_leaf_rust": {
        "name_pt": "Ferrugem do Cafeeiro",
        "crop": "coffee",
        "severity": 4,
        "recommendations": [
            "Aplicar fungicida cúprico",
            "Podar ramos afetados",
            "Considerar variedades resistentes",
        ],
    },
    "coffee_cercospora": {
        "name_pt": "Cercosporiose do Café",
        "crop": "coffee",
        "severity": 2,
        "recommendations": [
            "Adubação equilibrada",
            "Irrigação adequada",
            "Fungicida se necessário",
        ],
    },
    # Citrus diseases
    "citrus_healthy": {
        "name_pt": "Citros Saudável",
        "crop": "citrus",
        "severity": 0,
        "recommendations": [],
    },
    "citrus_greening": {
        "name_pt": "Greening (HLB)",
        "crop": "citrus",
        "severity": 5,
        "recommendations": [
            "ERRADICAR planta infectada imediatamente",
            "Controlar psilídeo vetor",
            "Notificar autoridades fitossanitárias",
            "Inspecionar plantas vizinhas",
        ],
    },
    "citrus_canker": {
        "name_pt": "Cancro Cítrico",
        "crop": "citrus",
        "severity": 4,
        "recommendations": [
            "Podar e destruir partes afetadas",
            "Aplicar cobre preventivo",
            "Desinfetar ferramentas",
        ],
    },
    # Sugarcane
    "sugarcane_healthy": {
        "name_pt": "Cana Saudável",
        "crop": "sugarcane",
        "severity": 0,
        "recommendations": [],
    },
    "sugarcane_mosaic": {
        "name_pt": "Mosaico da Cana",
        "crop": "sugarcane",
        "severity": 3,
        "recommendations": [
            "Usar mudas sadias certificadas",
            "Eliminar plantas infectadas",
            "Controlar pulgões vetores",
        ],
    },
    "sugarcane_orange_rust": {
        "name_pt": "Ferrugem Alaranjada",
        "crop": "sugarcane",
        "severity": 4,
        "recommendations": [
            "Aplicar fungicida sistêmico",
            "Usar variedades resistentes",
            "Monitoramento constante",
        ],
    },
    # Cotton
    "cotton_healthy": {
        "name_pt": "Algodão Saudável",
        "crop": "cotton",
        "severity": 0,
        "recommendations": [],
    },
    "cotton_bacterial_blight": {
        "name_pt": "Mancha Angular do Algodoeiro",
        "crop": "cotton",
        "severity": 3,
        "recommendations": [
            "Usar sementes tratadas",
            "Rotação de culturas",
            "Destruir restos culturais",
        ],
    },
    "cotton_target_spot": {
        "name_pt": "Mancha Alvo do Algodão",
        "crop": "cotton",
        "severity": 3,
        "recommendations": [
            "Fungicida preventivo",
            "Espaçamento adequado",
            "Evitar excesso de nitrogênio",
        ],
    },
    # Pasture
    "pasture_healthy": {
        "name_pt": "Pastagem Saudável",
        "crop": "pasture",
        "severity": 0,
        "recommendations": [],
    },
    "pasture_spittlebug_damage": {
        "name_pt": "Dano de Cigarrinha das Pastagens",
        "crop": "pasture",
        "severity": 3,
        "recommendations": [
            "Controle biológico com Metarhizium",
            "Manejo do pastejo",
            "Diversificação de forrageiras",
        ],
    },
}

SEVERITY_LABELS = {
    0: ("Saudável", "green"),
    1: ("Muito Leve", "lime"),
    2: ("Leve", "yellow"),
    3: ("Moderado", "orange"),
    4: ("Severo", "red"),
    5: ("Crítico", "darkred"),
}


class CropDiseaseModel(BaseVisionModel):
    """
    Model for crop disease classification.

    Architecture:
    - Backbone: EfficientNetV2-S or ConvNeXt-Tiny
    - Head: Multi-class classification

    Input: RGB image 224x224
    Output:
        - disease_id: str
        - disease_name: str (Portuguese)
        - crop: str
        - severity: int (0-5)
        - confidence: float
        - recommendations: List[str]
    """

    def __init__(
        self,
        input_size: Tuple[int, int] = (224, 224),
        use_convnext: bool = False,
    ):
        # Get class names from catalog
        class_names = list(DISEASE_CATALOG.keys())

        super().__init__(
            model_name="crop_disease",
            input_size=input_size,
            num_classes=len(class_names),
        )
        self._class_names = class_names
        self.use_convnext = use_convnext

    def build_model(self) -> tf.keras.Model:
        """
        Build classification model with EfficientNetV2 or ConvNeXt backbone.
        """
        inputs = tf.keras.Input(shape=(*self.input_size, 3), name="image_input")

        # Data augmentation
        x = tf.keras.layers.RandomFlip("horizontal")(inputs)
        x = tf.keras.layers.RandomRotation(0.15)(x)
        x = tf.keras.layers.RandomZoom(0.15)(x)
        x = tf.keras.layers.RandomBrightness(0.2)(x)
        x = tf.keras.layers.RandomContrast(0.2)(x)

        # Backbone
        if self.use_convnext:
            # ConvNeXt for potentially better accuracy
            backbone = tf.keras.applications.ConvNeXtTiny(
                include_top=False,
                weights="imagenet",
                input_shape=(*self.input_size, 3),
                pooling="avg",
            )
        else:
            # EfficientNetV2 for better mobile performance
            backbone = tf.keras.applications.EfficientNetV2S(
                include_top=False,
                weights="imagenet",
                input_shape=(*self.input_size, 3),
                pooling="avg",
            )

        backbone.trainable = False
        features = backbone(x)

        # Classification head
        x = tf.keras.layers.Dense(512, activation="relu")(features)
        x = tf.keras.layers.BatchNormalization()(x)
        x = tf.keras.layers.Dropout(0.4)(x)

        x = tf.keras.layers.Dense(256, activation="relu")(x)
        x = tf.keras.layers.BatchNormalization()(x)
        x = tf.keras.layers.Dropout(0.3)(x)

        # Output: disease classification
        outputs = tf.keras.layers.Dense(
            self.num_classes, activation="softmax", name="disease_class"
        )(x)

        model = tf.keras.Model(inputs=inputs, outputs=outputs)
        self.model = model
        return model

    def compile_model(self, learning_rate: float = 1e-4) -> None:
        """Compile model with categorical crossentropy."""
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")

        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy", tf.keras.metrics.TopKCategoricalAccuracy(k=3)],
        )

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for EfficientNetV2/ConvNeXt."""
        if image.shape[:2] != self.input_size:
            from PIL import Image as PILImage

            img = PILImage.fromarray(image)
            img = img.resize(self.input_size, PILImage.Resampling.LANCZOS)
            image = np.array(img)

        # Normalize to [0, 1]
        image = image.astype(np.float32) / 255.0
        return image

    def postprocess_output(self, output: np.ndarray) -> Dict[str, Any]:
        """Convert model output to disease information."""
        # Get top predictions
        top_indices = np.argsort(output)[::-1][:3]
        top_probs = output[top_indices]

        # Primary prediction
        primary_idx = top_indices[0]
        primary_prob = float(top_probs[0])

        disease_id = self._class_names[primary_idx]
        disease_info = DISEASE_CATALOG.get(disease_id, {})

        severity = disease_info.get("severity", 0)
        severity_label, severity_color = SEVERITY_LABELS.get(severity, ("Desconhecido", "gray"))

        # Secondary predictions (differential diagnosis)
        alternatives = []
        for idx, prob in zip(top_indices[1:3], top_probs[1:3]):
            if prob > 0.1:  # Only include if >10% probability
                alt_id = self._class_names[idx]
                alt_info = DISEASE_CATALOG.get(alt_id, {})
                alternatives.append({
                    "disease_id": alt_id,
                    "disease_name": alt_info.get("name_pt", alt_id),
                    "probability": round(float(prob), 3),
                })

        return {
            "disease_id": disease_id,
            "disease_name": disease_info.get("name_pt", disease_id),
            "crop": disease_info.get("crop", "unknown"),
            "severity": severity,
            "severity_label": severity_label,
            "severity_color": severity_color,
            "confidence": round(primary_prob, 3),
            "recommendations": disease_info.get("recommendations", []),
            "alternatives": alternatives,
            "is_healthy": severity == 0,
            "requires_action": severity >= 3,
            "model_version": self.model_name,
        }

    def get_diseases_by_crop(self, crop: str) -> List[Dict[str, Any]]:
        """Get all diseases for a specific crop."""
        return [
            {"id": k, **v}
            for k, v in DISEASE_CATALOG.items()
            if v.get("crop") == crop
        ]

    def get_supported_crops(self) -> List[str]:
        """Get list of supported crops."""
        return list(set(v.get("crop") for v in DISEASE_CATALOG.values()))
