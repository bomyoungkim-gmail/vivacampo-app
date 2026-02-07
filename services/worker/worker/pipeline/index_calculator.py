"""
Vegetation and radar indices calculator.
Independent of provider - operates on numpy arrays.
"""
from __future__ import annotations

import numpy as np


class IndexCalculator:
    """Calculates vegetation and radar indices from numpy arrays."""

    @staticmethod
    def ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """NDVI = (NIR - Red) / (NIR + Red)"""
        denom = nir + red
        denom = np.where(denom == 0, 0.0001, denom)
        return np.clip((nir - red) / denom, -1, 1)

    @staticmethod
    def ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """NDWI = (Green - NIR) / (Green + NIR)"""
        denom = green + nir
        denom = np.where(denom == 0, 0.0001, denom)
        return np.clip((green - nir) / denom, -1, 1)

    @staticmethod
    def ndmi(nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
        """NDMI = (NIR - SWIR) / (NIR + SWIR)"""
        denom = nir + swir
        denom = np.where(denom == 0, 0.0001, denom)
        return np.clip((nir - swir) / denom, -1, 1)

    @staticmethod
    def savi(red: np.ndarray, nir: np.ndarray, L: float = 0.5) -> np.ndarray:
        """SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L)"""
        denom = nir + red + L
        denom = np.where(denom == 0, 0.0001, denom)
        return np.clip(((nir - red) / denom) * (1 + L), -1, 1)

    @staticmethod
    def rvi(vv: np.ndarray, vh: np.ndarray) -> np.ndarray:
        """RVI = 4 * VH / (VV + VH). Range: 0-1."""
        denominator = vv + vh
        denominator = np.where(denominator == 0, 0.0001, denominator)
        return np.clip(4 * vh / denominator, 0, 1)

    @staticmethod
    def radar_ratio(vv: np.ndarray, vh: np.ndarray) -> np.ndarray:
        """VH/VV Ratio"""
        vv = np.where(vv == 0, 0.0001, vv)
        return vh / vv

    @staticmethod
    def mask_clouds(data_array: np.ndarray, scl_array: np.ndarray) -> np.ndarray:
        """
        Mask clouds using Sentinel-2 Scene Classification Layer (SCL).
        Invalid pixels: 0=NoData, 1=Saturated, 3=CloudShadow, 8=CloudMedium,
        9=CloudHigh, 10=Cirrus.
        """
        if data_array.shape[-2:] != scl_array.shape[-2:]:
            target_h, target_w = data_array.shape[-2:]
            scl_h, scl_w = scl_array.shape[-2:]

            scale_h = target_h / scl_h
            scale_w = target_w / scl_w

            y_coords = np.arange(target_h) / scale_h
            x_coords = np.arange(target_w) / scale_w

            y_indices = np.clip(np.round(y_coords).astype(int), 0, scl_h - 1)
            x_indices = np.clip(np.round(x_coords).astype(int), 0, scl_w - 1)

            scl_array = scl_array[y_indices[:, None], x_indices]

        invalid_pixels = np.isin(scl_array, [0, 1, 3, 8, 9, 10])
        return np.where(invalid_pixels, np.nan, data_array)
