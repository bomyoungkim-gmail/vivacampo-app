/**
 * Application constants
 */

/**
 * Productivity baseline for NDVI average comparison.
 *
 * This value represents the historical average NDVI for healthy crops
 * in the Brazilian agricultural regions. Used to calculate productivity
 * deviation in the Analysis tab.
 *
 * TODO: In the future, this should be fetched from the backend and
 * calibrated per region/crop type. See TASK-INTEL-008 for ML-based
 * productivity predictions.
 *
 * Reference: Based on Sentinel-2 NDVI averages for soybean/corn in
 * Paraná/Mato Grosso regions (2020-2025 growing seasons).
 */
export const PRODUCTIVITY_HISTORICAL_AVG = 0.65

/**
 * Vegetation index thresholds for health classification
 */
export const NDVI_THRESHOLDS = {
  LOW: 0.3,
  MODERATE: 0.5,
  HIGH: 0.7,
} as const

/**
 * Nitrogen deficiency detection thresholds
 * Based on ADR-0008: SRRE Index and Nitrogen Detection
 */
export const NITROGEN_THRESHOLDS = {
  NDVI_HIGH: 0.7,    // High NDVI indicates good biomass
  NDRE_LOW: 0.5,     // Low NDRE indicates nitrogen stress
  RECI_LOW: 1.5,     // Low RECI confirms nitrogen deficiency
} as const

/**
 * Harvest detection threshold for RVI drop
 * Based on ADR-0009: Radar-Based Harvest Detection
 */
export const HARVEST_RVI_DROP_THRESHOLD = 0.3
