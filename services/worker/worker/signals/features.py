import numpy as np
from typing import List, Dict
import structlog

logger = structlog.get_logger()


def extract_features(observations: List[Dict]) -> Dict[str, float]:
    """
    Extract features from observations for signal scoring.
    
    Features:
    - slope_recent: Linear regression slope of last 4 weeks
    - drop_magnitude: Maximum drop from baseline
    - cumulative_anomaly: Sum of negative anomalies
    - recovery_lag: Weeks since baseline crossing
    - heterogeneity: NDVI standard deviation
    - stability: Temporal variance
    """
    if len(observations) < 4:
        logger.warning("insufficient_observations_for_features", count=len(observations))
        return {}
    
    # Extract values
    ndvi_values = [obs['ndvi_mean'] for obs in observations if obs.get('ndvi_mean')]
    ndvi_std_values = [obs['ndvi_std'] for obs in observations if obs.get('ndvi_std')]
    anomaly_values = [obs['anomaly'] for obs in observations if obs.get('anomaly')]
    baseline_values = [obs['baseline'] for obs in observations if obs.get('baseline')]
    
    if not ndvi_values:
        return {}
    
    # Calculate features
    features = {}
    
    # 1. Slope recent (last 4 weeks)
    if len(ndvi_values) >= 4:
        recent_values = ndvi_values[-4:]
        x = np.arange(len(recent_values))
        slope, _ = np.polyfit(x, recent_values, 1)
        features['slope_recent'] = float(slope)
    
    # 2. Drop magnitude (vs baseline)
    if baseline_values and ndvi_values:
        avg_baseline = np.mean(baseline_values)
        min_ndvi = np.min(ndvi_values)
        features['drop_magnitude'] = float(avg_baseline - min_ndvi)
    
    # 3. Cumulative anomaly (sum of negative anomalies)
    if anomaly_values:
        negative_anomalies = [a for a in anomaly_values if a < 0]
        features['cumulative_anomaly'] = float(sum(negative_anomalies))
    
    # 4. Recovery lag (weeks since last baseline crossing)
    if baseline_values and ndvi_values:
        avg_baseline = np.mean(baseline_values)
        recovery_lag = 0
        for i in range(len(ndvi_values) - 1, -1, -1):
            if ndvi_values[i] >= avg_baseline:
                break
            recovery_lag += 1
        features['recovery_lag'] = recovery_lag
    
    # 5. Heterogeneity (average NDVI std)
    if ndvi_std_values:
        features['heterogeneity'] = float(np.mean(ndvi_std_values))
    
    # 6. Stability (temporal variance)
    if len(ndvi_values) >= 4:
        features['stability'] = float(np.var(ndvi_values))
    
    logger.info("features_extracted", features=features)
    return features


def calculate_rule_score(features: Dict[str, float], use_type: str) -> float:
    """
    Calculate rule-based score using heuristics.
    Returns score between 0 and 1.
    """
    score = 0.0
    
    # Negative slope is bad
    if features.get('slope_recent', 0) < -0.01:
        score += 0.2
    
    # Large drop from baseline is bad
    if features.get('drop_magnitude', 0) > 0.15:
        score += 0.3
    
    # Cumulative negative anomaly is bad
    if features.get('cumulative_anomaly', 0) < -0.5:
        score += 0.2
    
    # Long recovery lag is bad
    if features.get('recovery_lag', 0) > 4:
        score += 0.2
    
    # High heterogeneity might indicate issues
    if features.get('heterogeneity', 0) > 0.15:
        score += 0.1
    
    return min(score, 1.0)


def calculate_ml_score(features: Dict[str, float]) -> float:
    """
    Calculate ML-based score using logistic regression.
    For MVP, uses fixed beta coefficients.
    
    score = 1 / (1 + exp(-(β0 + β1*x1 + β2*x2 + ...)))
    """
    # Fixed beta coefficients (calibrated for MVP)
    beta = {
        'intercept': -2.0,
        'slope_recent': -5.0,
        'drop_magnitude': 3.0,
        'cumulative_anomaly': -2.0,
        'recovery_lag': 0.1,
        'heterogeneity': 1.5,
        'stability': 0.5
    }
    
    # Calculate linear combination
    z = beta['intercept']
    for feature, value in features.items():
        if feature in beta:
            z += beta[feature] * value
    
    # Logistic function
    ml_score = 1 / (1 + np.exp(-z))
    
    return float(ml_score)


def calculate_final_score(
    rule_score: float,
    change_score: float,
    ml_score: float
) -> float:
    """
    Calculate final score as weighted combination.
    
    final_score = 0.4 * rule_score + 0.3 * change_score + 0.3 * ml_score
    """
    final_score = 0.4 * rule_score + 0.3 * change_score + 0.3 * ml_score
    return min(max(final_score, 0.0), 1.0)


def determine_severity(score: float) -> str:
    """Determine severity from score"""
    if score >= 0.8:
        return "HIGH"
    elif score >= 0.65:
        return "MEDIUM"
    else:
        return "LOW"


def determine_confidence(
    score: float,
    valid_pixel_ratio: float,
    history_weeks: int
) -> str:
    """
    Determine confidence based on score, data quality, and history.
    """
    confidence_score = score
    
    # Adjust for data quality
    if valid_pixel_ratio < 0.5:
        confidence_score *= 0.7
    elif valid_pixel_ratio < 0.7:
        confidence_score *= 0.85
    
    # Adjust for history length
    if history_weeks < 12:
        confidence_score *= 0.8
    
    if confidence_score >= 0.75:
        return "HIGH"
    elif confidence_score >= 0.5:
        return "MEDIUM"
    else:
        return "LOW"
