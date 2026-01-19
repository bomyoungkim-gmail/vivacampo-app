"""
Livestock Health Assessment Model

Identifies health issues in cattle (bovine) and swine from images.
Detects visual signs of common diseases, injuries, and abnormalities.

Features:
- Skin and coat condition assessment
- Eye and mucous membrane analysis
- Posture and mobility indicators
- Common disease detection
- Lameness detection
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import tensorflow as tf
from .base_model import BaseVisionModel
import structlog

logger = structlog.get_logger()


# =============================================================================
# BOVINE (CATTLE) HEALTH CONDITIONS
# =============================================================================

BOVINE_CONDITIONS = {
    # Healthy states
    "bovine_healthy": {
        "name_pt": "Bovino Saudável",
        "animal": "bovine",
        "category": "healthy",
        "severity": 0,
        "indicators": [
            "Pelagem brilhante e uniforme",
            "Olhos alertas e brilhantes",
            "Mucosas rosadas",
            "Postura normal",
            "Comportamento ativo",
        ],
        "recommendations": [],
    },

    # Respiratory diseases
    "bovine_pneumonia": {
        "name_pt": "Pneumonia Bovina",
        "animal": "bovine",
        "category": "respiratory",
        "severity": 4,
        "indicators": [
            "Respiração acelerada/difícil",
            "Secreção nasal",
            "Tosse",
            "Febre (orelhas quentes)",
            "Apatia",
        ],
        "recommendations": [
            "Isolar animal imediatamente",
            "Chamar veterinário urgente",
            "Manter hidratação",
            "Antibioticoterapia conforme prescrição",
            "Monitorar temperatura",
        ],
    },
    "bovine_ibr": {
        "name_pt": "Rinotraqueíte Infecciosa Bovina (IBR)",
        "animal": "bovine",
        "category": "viral",
        "severity": 4,
        "indicators": [
            "Secreção nasal mucopurulenta",
            "Conjuntivite",
            "Lesões na mucosa nasal",
            "Febre alta",
            "Salivação excessiva",
        ],
        "recommendations": [
            "Isolamento rigoroso",
            "Tratamento de suporte",
            "Verificar status vacinal do rebanho",
            "Notificar veterinário",
        ],
    },

    # Skin diseases
    "bovine_dermatophytosis": {
        "name_pt": "Dermatofitose (Tinha)",
        "animal": "bovine",
        "category": "fungal",
        "severity": 2,
        "indicators": [
            "Lesões circulares sem pelo",
            "Crostas acinzentadas",
            "Coceira moderada",
            "Pele espessada",
        ],
        "recommendations": [
            "Aplicar antifúngico tópico",
            "Melhorar ventilação do ambiente",
            "Separar animais afetados",
            "Desinfetar instalações",
        ],
    },
    "bovine_mange": {
        "name_pt": "Sarna Bovina",
        "animal": "bovine",
        "category": "parasitic",
        "severity": 3,
        "indicators": [
            "Coceira intensa",
            "Perda de pelo em placas",
            "Pele engrossada e enrugada",
            "Crostas e feridas",
            "Inquietação",
        ],
        "recommendations": [
            "Aplicar acaricida (ivermectina)",
            "Tratar todo o lote",
            "Repetir tratamento em 14 dias",
            "Limpar e desinfetar instalações",
        ],
    },
    "bovine_photosensitization": {
        "name_pt": "Fotossensibilização",
        "animal": "bovine",
        "category": "toxic",
        "severity": 3,
        "indicators": [
            "Lesões em áreas despigmentadas",
            "Pele avermelhada/inchada",
            "Descamação",
            "Evita sol",
            "Possível icterícia",
        ],
        "recommendations": [
            "Remover do sol imediatamente",
            "Identificar planta tóxica no pasto",
            "Tratar lesões cutâneas",
            "Avaliar função hepática",
        ],
    },

    # Eye diseases
    "bovine_pinkeye": {
        "name_pt": "Ceratoconjuntivite Infecciosa (Olho Rosa)",
        "animal": "bovine",
        "category": "bacterial",
        "severity": 3,
        "indicators": [
            "Lacrimejamento excessivo",
            "Olho fechado/fotofobia",
            "Córnea opaca/branca",
            "Úlcera corneana",
            "Secreção ocular",
        ],
        "recommendations": [
            "Aplicar colírio/pomada antibiótica",
            "Proteger do sol e poeira",
            "Isolar animais afetados",
            "Controlar moscas",
            "Casos graves: veterinário",
        ],
    },

    # Foot diseases
    "bovine_foot_rot": {
        "name_pt": "Podridão dos Cascos (Foot Rot)",
        "animal": "bovine",
        "category": "bacterial",
        "severity": 3,
        "indicators": [
            "Claudicação severa",
            "Inchaço entre os dedos",
            "Odor fétido",
            "Pele necrosada",
            "Febre",
        ],
        "recommendations": [
            "Limpar e desbridar lesão",
            "Aplicar antibiótico sistêmico",
            "Pedilúvio com sulfato de cobre",
            "Manter em local seco",
            "Casos graves: veterinário",
        ],
    },
    "bovine_digital_dermatitis": {
        "name_pt": "Dermatite Digital (Doença de Mortellaro)",
        "animal": "bovine",
        "category": "bacterial",
        "severity": 3,
        "indicators": [
            "Lesão em forma de morango",
            "Dor ao toque",
            "Claudicação",
            "Odor característico",
            "Lesão na coroa do casco",
        ],
        "recommendations": [
            "Limpeza e curativo local",
            "Antibiótico tópico (oxitetraciclina)",
            "Pedilúvio regular",
            "Melhorar higiene das instalações",
        ],
    },

    # Metabolic diseases
    "bovine_bloat": {
        "name_pt": "Timpanismo (Empanzinamento)",
        "animal": "bovine",
        "category": "metabolic",
        "severity": 5,
        "indicators": [
            "Abdômen distendido (lado esquerdo)",
            "Dificuldade respiratória",
            "Inquietação/dor",
            "Salivação",
            "Não rumina",
        ],
        "recommendations": [
            "EMERGÊNCIA - Chamar veterinário",
            "Manter animal em movimento",
            "Sonda esofágica se disponível",
            "Anti-espumante oral",
            "Casos extremos: trocarização",
        ],
    },
    "bovine_milk_fever": {
        "name_pt": "Febre do Leite (Hipocalcemia)",
        "animal": "bovine",
        "category": "metabolic",
        "severity": 4,
        "indicators": [
            "Vaca recém-parida",
            "Fraqueza/tremores",
            "Decúbito (não levanta)",
            "Orelhas frias",
            "Pupilas dilatadas",
        ],
        "recommendations": [
            "EMERGÊNCIA - Veterinário urgente",
            "Cálcio intravenoso",
            "Manter aquecida",
            "Não forçar levantar",
            "Prevenção: manejo nutricional pré-parto",
        ],
    },

    # Reproductive issues
    "bovine_mastitis": {
        "name_pt": "Mastite",
        "animal": "bovine",
        "category": "bacterial",
        "severity": 3,
        "indicators": [
            "Úbere inchado/quente",
            "Leite alterado (grumos, sangue)",
            "Dor à ordenha",
            "Febre",
            "Quarto afetado endurecido",
        ],
        "recommendations": [
            "Ordenhar quarto afetado frequentemente",
            "Aplicar antibiótico intramamário",
            "CMT para diagnóstico",
            "Melhorar higiene de ordenha",
            "Casos graves: antibiótico sistêmico",
        ],
    },
    "bovine_metritis": {
        "name_pt": "Metrite/Retenção de Placenta",
        "animal": "bovine",
        "category": "reproductive",
        "severity": 4,
        "indicators": [
            "Corrimento vaginal fétido",
            "Febre",
            "Apatia/anorexia",
            "Queda na produção de leite",
            "Placenta pendente (retenção)",
        ],
        "recommendations": [
            "Chamar veterinário",
            "Antibioticoterapia sistêmica",
            "NÃO puxar placenta",
            "Lavagem uterina se indicado",
            "Suporte nutricional",
        ],
    },

    # Parasitic diseases
    "bovine_tick_infestation": {
        "name_pt": "Infestação por Carrapatos",
        "animal": "bovine",
        "category": "parasitic",
        "severity": 2,
        "indicators": [
            "Carrapatos visíveis na pele",
            "Coceira",
            "Anemia (mucosas pálidas)",
            "Perda de peso",
            "Pelos arrepiados",
        ],
        "recommendations": [
            "Aplicar carrapaticida",
            "Rotação de princípios ativos",
            "Tratar todo o rebanho",
            "Manejo de pastagem",
            "Monitorar para tristeza parasitária",
        ],
    },
    "bovine_anaplasmosis": {
        "name_pt": "Anaplasmose (Tristeza Parasitária)",
        "animal": "bovine",
        "category": "parasitic",
        "severity": 4,
        "indicators": [
            "Mucosas pálidas/amareladas",
            "Febre alta",
            "Fraqueza extrema",
            "Urina escura",
            "Anemia severa",
        ],
        "recommendations": [
            "URGENTE - Veterinário",
            "Oxitetraciclina ou imidocarb",
            "Transfusão em casos graves",
            "Controle de carrapatos",
            "Suporte nutricional",
        ],
    },

    # Neurological
    "bovine_rabies_suspect": {
        "name_pt": "Suspeita de Raiva",
        "animal": "bovine",
        "category": "viral",
        "severity": 5,
        "indicators": [
            "Mugido rouco",
            "Salivação excessiva",
            "Dificuldade de deglutição",
            "Paralisia progressiva",
            "Comportamento anormal",
        ],
        "recommendations": [
            "NÃO TOCAR - Risco de zoonose",
            "NOTIFICAR autoridades sanitárias",
            "Isolar animal",
            "Vacinar rebanho",
            "Enviar material para diagnóstico",
        ],
    },
}


# =============================================================================
# SWINE (PIG) HEALTH CONDITIONS
# =============================================================================

SWINE_CONDITIONS = {
    # Healthy states
    "swine_healthy": {
        "name_pt": "Suíno Saudável",
        "animal": "swine",
        "category": "healthy",
        "severity": 0,
        "indicators": [
            "Pele rosada e limpa",
            "Cerdas brilhantes",
            "Olhos alertas",
            "Respiração normal",
            "Comportamento ativo/curioso",
        ],
        "recommendations": [],
    },

    # Respiratory diseases
    "swine_pneumonia": {
        "name_pt": "Pneumonia Suína",
        "animal": "swine",
        "category": "respiratory",
        "severity": 4,
        "indicators": [
            "Tosse seca persistente",
            "Respiração abdominal",
            "Atraso no crescimento",
            "Febre",
            "Apatia",
        ],
        "recommendations": [
            "Melhorar ventilação",
            "Antibioticoterapia",
            "Reduzir densidade",
            "Verificar programa vacinal",
            "Veterinário para casos graves",
        ],
    },
    "swine_prrs": {
        "name_pt": "Síndrome Reprodutiva e Respiratória Suína (PRRS)",
        "animal": "swine",
        "category": "viral",
        "severity": 5,
        "indicators": [
            "Abortos/natimortos",
            "Leitões fracos ao nascer",
            "Problemas respiratórios",
            "Orelhas azuladas (cianose)",
            "Febre",
        ],
        "recommendations": [
            "NOTIFICAR veterinário",
            "Quarentena do lote",
            "Biossegurança rigorosa",
            "Manejo de reposição",
            "Programa vacinal",
        ],
    },
    "swine_influenza": {
        "name_pt": "Influenza Suína",
        "animal": "swine",
        "category": "viral",
        "severity": 3,
        "indicators": [
            "Surto súbito de tosse",
            "Febre alta",
            "Secreção nasal",
            "Apatia",
            "Recuperação rápida (5-7 dias)",
        ],
        "recommendations": [
            "Tratamento de suporte",
            "Manter hidratação",
            "Controlar infecções secundárias",
            "Evitar estresse",
            "Vacinar lotes futuros",
        ],
    },

    # Skin diseases
    "swine_mange": {
        "name_pt": "Sarna Sarcóptica Suína",
        "animal": "swine",
        "category": "parasitic",
        "severity": 3,
        "indicators": [
            "Coceira intensa",
            "Crostas nas orelhas",
            "Pele espessada/enrugada",
            "Perda de cerdas",
            "Lesões generalizadas",
        ],
        "recommendations": [
            "Ivermectina injetável",
            "Tratar todo o plantel",
            "Repetir em 14 dias",
            "Limpeza das instalações",
        ],
    },
    "swine_erysipelas": {
        "name_pt": "Erisipela Suína",
        "animal": "swine",
        "category": "bacterial",
        "severity": 4,
        "indicators": [
            "Manchas vermelhas em diamante na pele",
            "Febre alta (>41°C)",
            "Artrite/claudicação",
            "Apatia",
            "Morte súbita possível",
        ],
        "recommendations": [
            "Penicilina urgente",
            "Vacinar todo o plantel",
            "Isolar afetados",
            "Limpeza e desinfecção",
            "Notificar veterinário",
        ],
    },
    "swine_pityriasis": {
        "name_pt": "Pitiríase Rósea",
        "animal": "swine",
        "category": "dermatological",
        "severity": 1,
        "indicators": [
            "Manchas rosadas circulares",
            "Descamação leve",
            "Sem coceira",
            "Animal normal",
            "Autolimitante",
        ],
        "recommendations": [
            "Geralmente não requer tratamento",
            "Melhorar higiene",
            "Monitorar evolução",
            "Diferencial: tinha, sarna",
        ],
    },

    # Digestive diseases
    "swine_diarrhea": {
        "name_pt": "Diarreia Suína",
        "animal": "swine",
        "category": "digestive",
        "severity": 3,
        "indicators": [
            "Fezes líquidas",
            "Desidratação",
            "Perda de peso",
            "Região perianal suja",
            "Apatia",
        ],
        "recommendations": [
            "Reidratação oral/parenteral",
            "Identificar causa (viral/bacteriana)",
            "Ajustar dieta",
            "Antibiótico se bacteriana",
            "Melhorar higiene",
        ],
    },
    "swine_ped": {
        "name_pt": "Diarreia Epidêmica Suína (PED)",
        "animal": "swine",
        "category": "viral",
        "severity": 5,
        "indicators": [
            "Diarreia aquosa em leitões",
            "Vômito",
            "Alta mortalidade (<7 dias)",
            "Desidratação rápida",
            "Surto explosivo",
        ],
        "recommendations": [
            "EMERGÊNCIA - Veterinário urgente",
            "Biossegurança máxima",
            "Suporte nutricional/hidratação",
            "Feedback para porcas",
            "Notificar autoridades",
        ],
    },

    # Lameness
    "swine_lameness": {
        "name_pt": "Claudicação/Problemas de Casco",
        "animal": "swine",
        "category": "locomotor",
        "severity": 2,
        "indicators": [
            "Mancando",
            "Relutância em andar",
            "Lesões nos cascos",
            "Articulações inchadas",
            "Deitado frequentemente",
        ],
        "recommendations": [
            "Examinar cascos",
            "Melhorar piso das baias",
            "Anti-inflamatório se indicado",
            "Casquear se necessário",
            "Avaliar nutrição (biotina)",
        ],
    },

    # Reproductive
    "swine_mma": {
        "name_pt": "Síndrome MMA (Mastite-Metrite-Agalaxia)",
        "animal": "swine",
        "category": "reproductive",
        "severity": 4,
        "indicators": [
            "Porca recém-parida",
            "Febre",
            "Sem leite (agalaxia)",
            "Corrimento vaginal",
            "Tetos quentes/doloridos",
        ],
        "recommendations": [
            "Ocitocina para estimular leite",
            "Antibiótico sistêmico",
            "Anti-inflamatório",
            "Amamentar leitões manualmente",
            "Veterinário urgente",
        ],
    },

    # Neurological
    "swine_streptococcus": {
        "name_pt": "Meningite Estreptocócica",
        "animal": "swine",
        "category": "bacterial",
        "severity": 4,
        "indicators": [
            "Tremores/convulsões",
            "Andar em círculos",
            "Incoordenação",
            "Paralisia",
            "Febre alta",
        ],
        "recommendations": [
            "Antibiótico imediato (penicilina/ampicilina)",
            "Anti-inflamatório",
            "Isolar afetados",
            "Vacinação preventiva",
            "Veterinário urgente",
        ],
    },
}


# Combine all conditions
LIVESTOCK_CONDITIONS = {**BOVINE_CONDITIONS, **SWINE_CONDITIONS}

CONDITION_CATEGORIES = {
    "healthy": {"name_pt": "Saudável", "color": "green", "priority": 0},
    "dermatological": {"name_pt": "Dermatológico", "color": "yellow", "priority": 1},
    "nutritional": {"name_pt": "Nutricional", "color": "yellow", "priority": 1},
    "parasitic": {"name_pt": "Parasitário", "color": "orange", "priority": 2},
    "digestive": {"name_pt": "Digestivo", "color": "orange", "priority": 2},
    "locomotor": {"name_pt": "Locomotor", "color": "orange", "priority": 2},
    "fungal": {"name_pt": "Fúngico", "color": "orange", "priority": 2},
    "toxic": {"name_pt": "Tóxico", "color": "red", "priority": 3},
    "bacterial": {"name_pt": "Bacteriano", "color": "red", "priority": 3},
    "respiratory": {"name_pt": "Respiratório", "color": "red", "priority": 4},
    "reproductive": {"name_pt": "Reprodutivo", "color": "red", "priority": 4},
    "metabolic": {"name_pt": "Metabólico", "color": "darkred", "priority": 5},
    "viral": {"name_pt": "Viral", "color": "darkred", "priority": 5},
}


class LivestockHealthModel(BaseVisionModel):
    """
    Model for livestock (bovine/swine) health assessment.

    Architecture:
    - Backbone: EfficientNetV2-S
    - Head: Multi-class classification + health score regression

    Input: RGB image 384x384 (larger for detail detection)
    Output:
        - condition_id: str
        - condition_name: str (Portuguese)
        - animal: str (bovine/swine)
        - category: str
        - severity: int (0-5)
        - health_score: float (0-100)
        - confidence: float
        - indicators: List[str]
        - recommendations: List[str]
    """

    def __init__(
        self,
        animal_type: str = "bovine",  # "bovine" or "swine" or "all"
        input_size: Tuple[int, int] = (384, 384),
    ):
        # Filter conditions by animal type
        if animal_type == "bovine":
            conditions = BOVINE_CONDITIONS
        elif animal_type == "swine":
            conditions = SWINE_CONDITIONS
        else:
            conditions = LIVESTOCK_CONDITIONS

        class_names = list(conditions.keys())

        super().__init__(
            model_name=f"livestock_health_{animal_type}",
            input_size=input_size,
            num_classes=len(class_names),
        )
        self._class_names = class_names
        self.animal_type = animal_type
        self._conditions = conditions

    def build_model(self) -> tf.keras.Model:
        """Build classification model with health score regression."""
        inputs = tf.keras.Input(shape=(*self.input_size, 3), name="image_input")

        # Data augmentation
        x = tf.keras.layers.RandomFlip("horizontal")(inputs)
        x = tf.keras.layers.RandomRotation(0.1)(x)
        x = tf.keras.layers.RandomZoom(0.15)(x)
        x = tf.keras.layers.RandomBrightness(0.2)(x)
        x = tf.keras.layers.RandomContrast(0.2)(x)

        # Backbone - EfficientNetV2-S
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
        condition_info = self._conditions.get(condition_id, {})

        category = condition_info.get("category", "unknown")
        category_info = CONDITION_CATEGORIES.get(category, {})

        severity = condition_info.get("severity", 0)

        # Health score
        if health_score_raw is not None:
            if isinstance(health_score_raw, np.ndarray):
                health_score = float(health_score_raw.flatten()[0]) * 100
            else:
                health_score = float(health_score_raw) * 100
        else:
            health_score = 100 - (severity * 20)

        health_score = max(0, min(100, health_score))

        # Alternative diagnoses
        alternatives = []
        for idx, prob in zip(top_indices[1:3], top_probs[1:3]):
            if prob > 0.1:
                alt_id = self._class_names[idx]
                alt_info = self._conditions.get(alt_id, {})
                alternatives.append({
                    "condition_id": alt_id,
                    "condition_name": alt_info.get("name_pt", alt_id),
                    "probability": round(float(prob), 3),
                })

        # Alert level
        if severity >= 5:
            alert_level = "emergency"
            alert_color = "darkred"
        elif severity >= 4:
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
            "animal": condition_info.get("animal", self.animal_type),
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
            "requires_veterinary": severity >= 3,
            "is_emergency": severity >= 5,
            "requires_notification": condition_id in [
                "bovine_rabies_suspect",
                "swine_prrs",
                "swine_ped",
            ],
            "model_version": self.model_name,
        }

    def get_conditions_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all conditions for a specific category."""
        return [
            {"id": k, **v}
            for k, v in self._conditions.items()
            if v.get("category") == category
        ]

    def get_conditions_by_severity(self, min_severity: int) -> List[Dict[str, Any]]:
        """Get all conditions with severity >= min_severity."""
        return [
            {"id": k, **v}
            for k, v in self._conditions.items()
            if v.get("severity", 0) >= min_severity
        ]


class BovineHealthModel(LivestockHealthModel):
    """Specialized model for bovine (cattle) health assessment."""

    def __init__(self, input_size: Tuple[int, int] = (384, 384)):
        super().__init__(animal_type="bovine", input_size=input_size)


class SwineHealthModel(LivestockHealthModel):
    """Specialized model for swine (pig) health assessment."""

    def __init__(self, input_size: Tuple[int, int] = (384, 384)):
        super().__init__(animal_type="swine", input_size=input_size)
