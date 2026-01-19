from typing import List, Dict
import structlog

logger = structlog.get_logger()

# Signal types by use type
SIGNAL_TYPES = {
    "PASTURE": [
        "PASTURE_FORAGE_RISK",
        "PASTURE_LOCAL_DEGRADATION",
        "PASTURE_RECOVERY_LAG"
    ],
    "CROP": [
        "CROP_STRESS_EARLY",
        "CROP_RECOVERY_LAG"
    ]
}

# Recommended actions by signal type
RECOMMENDED_ACTIONS = {
    "PASTURE_FORAGE_RISK": [
        "Avaliar lotação e considerar rotação de pasto",
        "Considerar suplementação alimentar"
    ],
    "PASTURE_LOCAL_DEGRADATION": [
        "Inspecionar manchas de degradação no campo",
        "Verificar condições do solo e drenagem"
    ],
    "PASTURE_RECOVERY_LAG": [
        "Avaliar tempo de descanso do pasto",
        "Considerar adubação de recuperação"
    ],
    "CROP_STRESS_EARLY": [
        "Verificar sistema de irrigação e estresse hídrico",
        "Inspecionar presença de pragas ou doenças",
        "Avaliar necessidade de adubação"
    ],
    "CROP_RECOVERY_LAG": [
        "Monitorar recuperação da cultura",
        "Avaliar impacto no potencial produtivo"
    ]
}


def determine_signal_type(
    use_type: str,
    features: Dict[str, float],
    change_detection: Dict
) -> str:
    """
    Determine signal type based on use_type and features.
    
    Logic:
    - PASTURE_FORAGE_RISK: Negative slope + drop magnitude
    - PASTURE_LOCAL_DEGRADATION: High heterogeneity + drop
    - PASTURE_RECOVERY_LAG: Long recovery_lag
    - CROP_STRESS_EARLY: Negative slope early in season
    - CROP_RECOVERY_LAG: Long recovery_lag
    """
    if use_type == "PASTURE":
        # Check for forage risk
        if features.get('slope_recent', 0) < -0.01 and features.get('drop_magnitude', 0) > 0.1:
            return "PASTURE_FORAGE_RISK"
        
        # Check for local degradation
        if features.get('heterogeneity', 0) > 0.15 and features.get('drop_magnitude', 0) > 0.1:
            return "PASTURE_LOCAL_DEGRADATION"
        
        # Check for recovery lag
        if features.get('recovery_lag', 0) > 4:
            return "PASTURE_RECOVERY_LAG"
        
        # Default to forage risk
        return "PASTURE_FORAGE_RISK"
    
    elif use_type == "CROP":
        # Check for recovery lag
        if features.get('recovery_lag', 0) > 4:
            return "CROP_RECOVERY_LAG"
        
        # Default to early stress
        return "CROP_STRESS_EARLY"
    
    # Fallback
    return "PASTURE_FORAGE_RISK"


def get_recommended_actions(signal_type: str) -> List[str]:
    """
    Get recommended actions for signal type.
    Each action is ≤120 characters.
    """
    actions = RECOMMENDED_ACTIONS.get(signal_type, [])
    
    # Validate length
    for action in actions:
        if len(action) > 120:
            logger.warning("action_too_long", signal_type=signal_type, action=action)
    
    return actions[:5]  # Max 5 actions
