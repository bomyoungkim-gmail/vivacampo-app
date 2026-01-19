"""
Poultry Health Assessment Model

Identifies health issues in poultry (chickens, turkeys) from images.
Detects visual signs of common diseases and abnormalities.

Features:
- Plumage condition assessment
- Comb and wattle color analysis
- Posture and behavior indicators
- Common disease detection
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import tensorflow as tf
from .base_model import BaseVisionModel
import structlog

logger = structlog.get_logger()


# Health condition catalog
POULTRY_CONDITIONS = {
    # Healthy states
    "healthy_chicken": {
        "name_pt": "Ave Saudável",
        "animal": "chicken",
        "category": "healthy",
        "severity": 0,
        "indicators": ["Plumagem brilhante", "Crista vermelha viva", "Postura ativa"],
        "recommendations": [],
    },
    "healthy_turkey": {
        "name_pt": "Peru Saudável",
        "animal": "turkey",
        "category": "healthy",
        "severity": 0,
        "indicators": ["Plumagem completa", "Carúncula vermelha", "Comportamento normal"],
        "recommendations": [],
    },
    # Respiratory diseases
    "infectious_bronchitis": {
        "name_pt": "Bronquite Infecciosa",
        "animal": "chicken",
        "category": "respiratory",
        "severity": 4,
        "indicators": [
            "Respiração difícil",
            "Secreção nasal",
            "Olhos lacrimejantes",
            "Queda na postura",
        ],
        "recommendations": [
            "Isolar aves afetadas imediatamente",
            "Consultar veterinário",
            "Melhorar ventilação do galpão",
            "Verificar programa de vacinação",
        ],
    },
    "newcastle_disease": {
        "name_pt": "Doença de Newcastle",
        "animal": "chicken",
        "category": "viral",
        "severity": 5,
        "indicators": [
            "Dificuldade respiratória",
            "Diarreia esverdeada",
            "Torção do pescoço",
            "Paralisia das asas",
        ],
        "recommendations": [
            "NOTIFICAR autoridades sanitárias",
            "Quarentena total do lote",
            "Não movimentar aves",
            "Biossegurança rigorosa",
        ],
    },
    "avian_influenza_suspect": {
        "name_pt": "Suspeita de Influenza Aviária",
        "animal": "chicken",
        "category": "viral",
        "severity": 5,
        "indicators": [
            "Morte súbita",
            "Edema facial",
            "Crista e barbela cianóticas",
            "Hemorragias nas pernas",
        ],
        "recommendations": [
            "NOTIFICAR MAPA imediatamente",
            "NÃO movimentar aves ou materiais",
            "Restringir acesso ao local",
            "Aguardar orientação oficial",
        ],
    },
    # Parasitic conditions
    "mites_lice": {
        "name_pt": "Infestação por Ácaros/Piolhos",
        "animal": "chicken",
        "category": "parasitic",
        "severity": 2,
        "indicators": [
            "Coceira excessiva",
            "Perda de penas",
            "Pele irritada",
            "Queda na produção",
        ],
        "recommendations": [
            "Aplicar acaricida/inseticida aprovado",
            "Limpar e desinfetar instalações",
            "Tratar todas as aves do lote",
            "Repetir tratamento em 10-14 dias",
        ],
    },
    "coccidiosis": {
        "name_pt": "Coccidiose",
        "animal": "chicken",
        "category": "parasitic",
        "severity": 3,
        "indicators": [
            "Diarreia sanguinolenta",
            "Penas arrepiadas",
            "Apatia",
            "Cama úmida",
        ],
        "recommendations": [
            "Administrar coccidiostático",
            "Melhorar manejo da cama",
            "Verificar programa de prevenção",
            "Reduzir densidade se necessário",
        ],
    },
    # Nutritional deficiencies
    "vitamin_deficiency": {
        "name_pt": "Deficiência Nutricional",
        "animal": "chicken",
        "category": "nutritional",
        "severity": 2,
        "indicators": [
            "Penas opacas ou quebradiças",
            "Crescimento retardado",
            "Deformidades ósseas",
            "Fraqueza nas pernas",
        ],
        "recommendations": [
            "Revisar formulação da ração",
            "Suplementar vitaminas",
            "Verificar qualidade dos ingredientes",
            "Consultar nutricionista animal",
        ],
    },
    # Skin and feather conditions
    "feather_pecking": {
        "name_pt": "Bicagem de Penas",
        "animal": "chicken",
        "category": "behavioral",
        "severity": 2,
        "indicators": [
            "Áreas sem penas",
            "Ferimentos na pele",
            "Comportamento agressivo",
            "Estresse no lote",
        ],
        "recommendations": [
            "Reduzir densidade populacional",
            "Melhorar enriquecimento ambiental",
            "Verificar intensidade luminosa",
            "Ajustar nutrição (proteína/fibra)",
        ],
    },
    "bumblefoot": {
        "name_pt": "Pododermatite",
        "animal": "chicken",
        "category": "bacterial",
        "severity": 3,
        "indicators": [
            "Inchaço nos pés",
            "Lesões plantares",
            "Claudicação",
            "Relutância em andar",
        ],
        "recommendations": [
            "Tratar ferimentos individualmente",
            "Melhorar condição da cama",
            "Verificar poleiros",
            "Antibiótico se necessário (veterinário)",
        ],
    },
    # Digestive issues
    "crop_impaction": {
        "name_pt": "Compactação de Papo",
        "animal": "chicken",
        "category": "digestive",
        "severity": 3,
        "indicators": [
            "Papo aumentado e duro",
            "Dificuldade para comer",
            "Perda de peso",
            "Regurgitação",
        ],
        "recommendations": [
            "Massagear papo gentilmente",
            "Oferecer água morna",
            "Jejum temporário",
            "Veterinário se não resolver",
        ],
    },
    # Eye conditions
    "eye_infection": {
        "name_pt": "Infecção Ocular",
        "animal": "chicken",
        "category": "bacterial",
        "severity": 3,
        "indicators": [
            "Olhos fechados ou inchados",
            "Secreção ocular",
            "Fotofobia",
            "Dificuldade de alimentação",
        ],
        "recommendations": [
            "Limpar olhos com solução salina",
            "Aplicar colírio antibiótico",
            "Isolar ave afetada",
            "Investigar causa (amônia, doença)",
        ],
    },
}

CONDITION_CATEGORIES = {
    "healthy": {"name_pt": "Saudável", "color": "green", "priority": 0},
    "nutritional": {"name_pt": "Nutricional", "color": "yellow", "priority": 1},
    "behavioral": {"name_pt": "Comportamental", "color": "orange", "priority": 2},
    "parasitic": {"name_pt": "Parasitário", "color": "orange", "priority": 3},
    "bacterial": {"name_pt": "Bacteriano", "color": "red", "priority": 4},
    "respiratory": {"name_pt": "Respiratório", "color": "red", "priority": 4},
    "digestive": {"name_pt": "Digestivo", "color": "orange", "priority": 3},
    "viral": {"name_pt": "Viral", "color": "darkred", "priority": 5},
}


class PoultryHealthModel(BaseVisionModel):
    """
    Model for poultry health assessment.

    Architecture:
    - Backbone: EfficientNetV2-S
    - Head: Multi-class classification + health score regression

    Input: RGB image 224x224
    Output:
        - condition_id: str
        - condition_name: str (Portuguese)
        - category: str
        - severity: int (0-5)
        - health_score: float (0-100)
        - confidence: float
        - indicators: List[str]
        - recommendations: List[str]
    """

    def __init__(
        self,
        input_size: Tuple[int, int] = (224, 224),
    ):
        class_names = list(POULTRY_CONDITIONS.keys())

        super().__init__(
            model_name="poultry_health",
            input_size=input_size,
            num_classes=len(class_names),
        )
        self._class_names = class_names

    def build_model(self) -> tf.keras.Model:
        """Build classification model with health score regression."""
        inputs = tf.keras.Input(shape=(*self.input_size, 3), name="image_input")

        # Data augmentation
        x = tf.keras.layers.RandomFlip("horizontal")(inputs)
        x = tf.keras.layers.RandomRotation(0.1)(x)
        x = tf.keras.layers.RandomZoom(0.1)(x)
        x = tf.keras.layers.RandomBrightness(0.15)(x)
        x = tf.keras.layers.RandomContrast(0.15)(x)

        # Backbone
        backbone = tf.keras.applications.EfficientNetV2S(
            include_top=False,
            weights="imagenet",
            input_shape=(*self.input_size, 3),
            pooling="avg",
        )
        backbone.trainable = False

        features = backbone(x)

        # Shared layers
        shared = tf.keras.layers.Dense(512, activation="relu")(features)
        shared = tf.keras.layers.BatchNormalization()(shared)
        shared = tf.keras.layers.Dropout(0.4)(shared)

        shared = tf.keras.layers.Dense(256, activation="relu")(shared)
        shared = tf.keras.layers.BatchNormalization()(shared)
        shared = tf.keras.layers.Dropout(0.3)(shared)

        # Head 1: Condition classification
        condition_output = tf.keras.layers.Dense(
            self.num_classes, activation="softmax", name="condition"
        )(shared)

        # Head 2: Health score regression (0-100)
        health_head = tf.keras.layers.Dense(64, activation="relu")(shared)
        health_output = tf.keras.layers.Dense(
            1, activation="sigmoid", name="health_score"
        )(health_head)

        model = tf.keras.Model(
            inputs=inputs, outputs=[condition_output, health_output]
        )

        self.model = model
        return model

    def compile_model(self, learning_rate: float = 1e-4) -> None:
        """Compile model with appropriate losses."""
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")

        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
            loss={
                "condition": "sparse_categorical_crossentropy",
                "health_score": "mse",
            },
            loss_weights={"condition": 1.0, "health_score": 0.5},
            metrics={
                "condition": ["accuracy"],
                "health_score": ["mae"],
            },
        )

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for model input."""
        if image.shape[:2] != self.input_size:
            from PIL import Image as PILImage

            img = PILImage.fromarray(image)
            img = img.resize(self.input_size, PILImage.Resampling.LANCZOS)
            image = np.array(img)

        image = image.astype(np.float32) / 255.0
        return image

    def postprocess_output(self, output: np.ndarray | List[np.ndarray]) -> Dict[str, Any]:
        """Convert model output to health assessment."""
        if isinstance(output, list):
            condition_probs = output[0]
            health_score_raw = output[1]
        else:
            condition_probs = output
            health_score_raw = None

        # Get top predictions
        top_indices = np.argsort(condition_probs)[::-1][:3]
        top_probs = condition_probs[top_indices]

        primary_idx = top_indices[0]
        primary_prob = float(top_probs[0])

        condition_id = self._class_names[primary_idx]
        condition_info = POULTRY_CONDITIONS.get(condition_id, {})

        category = condition_info.get("category", "unknown")
        category_info = CONDITION_CATEGORIES.get(category, {})

        severity = condition_info.get("severity", 0)

        # Health score (0-100, higher is better)
        if health_score_raw is not None:
            if isinstance(health_score_raw, np.ndarray):
                health_score = float(health_score_raw.flatten()[0]) * 100
            else:
                health_score = float(health_score_raw) * 100
        else:
            # Estimate from severity
            health_score = 100 - (severity * 20)

        health_score = max(0, min(100, health_score))

        # Alternative diagnoses
        alternatives = []
        for idx, prob in zip(top_indices[1:3], top_probs[1:3]):
            if prob > 0.1:
                alt_id = self._class_names[idx]
                alt_info = POULTRY_CONDITIONS.get(alt_id, {})
                alternatives.append({
                    "condition_id": alt_id,
                    "condition_name": alt_info.get("name_pt", alt_id),
                    "probability": round(float(prob), 3),
                })

        # Determine alert level
        if severity >= 4:
            alert_level = "critical"
            alert_color = "red"
        elif severity >= 3:
            alert_level = "warning"
            alert_color = "orange"
        elif severity >= 1:
            alert_level = "attention"
            alert_color = "yellow"
        else:
            alert_level = "normal"
            alert_color = "green"

        return {
            "condition_id": condition_id,
            "condition_name": condition_info.get("name_pt", condition_id),
            "animal": condition_info.get("animal", "chicken"),
            "category": category,
            "category_name": category_info.get("name_pt", category),
            "severity": severity,
            "health_score": round(health_score, 1),
            "confidence": round(primary_prob, 3),
            "indicators": condition_info.get("indicators", []),
            "recommendations": condition_info.get("recommendations", []),
            "alternatives": alternatives,
            "is_healthy": severity == 0,
            "alert_level": alert_level,
            "alert_color": alert_color,
            "requires_veterinary": severity >= 4,
            "requires_notification": severity >= 5,
            "model_version": self.model_name,
        }

    def get_conditions_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all conditions for a specific category."""
        return [
            {"id": k, **v}
            for k, v in POULTRY_CONDITIONS.items()
            if v.get("category") == category
        ]
