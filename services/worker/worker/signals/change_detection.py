import numpy as np
from typing import List, Dict, Optional, Tuple
import structlog

logger = structlog.get_logger()


def detect_change_bfast_like(
    observations: List[Dict],
    window_size: int = 4,
    persistence_weeks: int = 3,
    threshold: float = 0.1
) -> Optional[Dict]:
    """
    BFastLike change detection algorithm.
    
    Detects structural breaks in time series by:
    1. Comparing mean of window A vs window B (rolling)
    2. Requiring persistence (change must last N weeks)
    3. Producing break_week + magnitude + confidence
    
    Args:
        observations: List of observations with ndvi_mean
        window_size: Size of comparison windows
        persistence_weeks: Minimum weeks change must persist
        threshold: Minimum magnitude to consider as change
    
    Returns:
        Dict with break_week, magnitude, confidence, or None if no change detected
    """
    if len(observations) < window_size * 2 + persistence_weeks:
        logger.warning("insufficient_data_for_change_detection", count=len(observations))
        return None
    
    ndvi_values = [obs['ndvi_mean'] for obs in observations if obs.get('ndvi_mean')]
    
    if not ndvi_values:
        return None
    
    # Rolling window comparison
    best_break = None
    max_magnitude = 0
    
    for i in range(window_size, len(ndvi_values) - window_size - persistence_weeks):
        # Window A (before)
        window_a = ndvi_values[i - window_size:i]
        mean_a = np.mean(window_a)
        
        # Window B (after)
        window_b = ndvi_values[i:i + window_size]
        mean_b = np.mean(window_b)
        
        # Calculate magnitude
        magnitude = abs(mean_a - mean_b)
        
        if magnitude < threshold:
            continue
        
        # Check persistence
        persistent = True
        for j in range(i, min(i + persistence_weeks, len(ndvi_values) - window_size)):
            future_window = ndvi_values[j:j + window_size]
            future_mean = np.mean(future_window)
            
            # Check if change persists
            if abs(future_mean - mean_b) > threshold:
                persistent = False
                break
        
        if persistent and magnitude > max_magnitude:
            max_magnitude = magnitude
            best_break = {
                'break_week': i,
                'magnitude': float(magnitude),
                'direction': 'decrease' if mean_a > mean_b else 'increase',
                'mean_before': float(mean_a),
                'mean_after': float(mean_b)
            }
    
    if best_break:
        # Calculate confidence based on magnitude and persistence
        confidence = min(max_magnitude / 0.3, 1.0)  # Normalize to 0-1
        best_break['confidence'] = float(confidence)
        
        logger.info("change_detected", break_info=best_break)
        return best_break
    
    return None


def detect_change_simple(
    observations: List[Dict],
    threshold: float = 0.15
) -> Optional[Dict]:
    """
    Simple change point detection (fallback for short history).
    
    Compares recent mean vs historical mean.
    """
    if len(observations) < 6:
        return None
    
    ndvi_values = [obs['ndvi_mean'] for obs in observations if obs.get('ndvi_mean')]
    
    if not ndvi_values:
        return None
    
    # Split into historical (first 2/3) and recent (last 1/3)
    split_point = len(ndvi_values) * 2 // 3
    historical = ndvi_values[:split_point]
    recent = ndvi_values[split_point:]
    
    mean_historical = np.mean(historical)
    mean_recent = np.mean(recent)
    
    magnitude = abs(mean_historical - mean_recent)
    
    if magnitude > threshold:
        return {
            'break_week': split_point,
            'magnitude': float(magnitude),
            'direction': 'decrease' if mean_historical > mean_recent else 'increase',
            'mean_before': float(mean_historical),
            'mean_after': float(mean_recent),
            'confidence': min(magnitude / 0.3, 1.0)
        }
    
    return None


def calculate_change_score(change_detection: Optional[Dict]) -> float:
    """
    Calculate change score from change detection result.
    
    Returns score between 0 and 1.
    """
    if not change_detection:
        return 0.0
    
    # Score based on magnitude and confidence
    magnitude_score = min(change_detection['magnitude'] / 0.3, 1.0)
    confidence = change_detection.get('confidence', 0.5)
    
    # Decrease is worse than increase
    direction_multiplier = 1.2 if change_detection['direction'] == 'decrease' else 0.8
    
    score = magnitude_score * confidence * direction_multiplier
    
    return min(score, 1.0)
