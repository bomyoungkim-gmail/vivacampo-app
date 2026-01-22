/**
 * VivaCampo Vision Service Types
 * Shared types for vision analysis across web and mobile platforms.
 */

// Analysis types supported by the vision service
export type AnalysisType =
  | 'crop_disease'
  | 'cattle_weight'
  | 'swine_weight'
  | 'bovine_health'
  | 'swine_health'
  | 'poultry_health';

// Base prediction result
export interface PredictionResult {
  success: boolean;
  analysisType: AnalysisType;
  timestamp: string;
  processingTimeMs: number;
  offline: boolean;
  error?: string;
}

// Disease detection result
export interface DiseaseDetectionResult extends PredictionResult {
  analysisType: 'crop_disease';
  disease: {
    id: string;
    name: string;
    namePt: string;
    confidence: number;
    severity: number; // 0-5
    category: string;
  };
  recommendations: string[];
  alternativeDiagnoses: Array<{
    id: string;
    name: string;
    namePt: string;
    confidence: number;
  }>;
}

// Weight estimation result
export interface WeightEstimationResult extends PredictionResult {
  analysisType: 'cattle_weight' | 'swine_weight';
  weight: {
    estimatedKg: number;
    rangeMin: number;
    rangeMax: number;
    confidence: number;
  };
  bodyConditionScore: {
    score: number; // 1-9
    description: string;
    descriptionPt: string;
  };
}

// Health assessment result
export interface HealthAssessmentResult extends PredictionResult {
  analysisType: 'bovine_health' | 'swine_health' | 'poultry_health';
  healthScore: number; // 0-100
  condition: {
    id: string;
    name: string;
    namePt: string;
    confidence: number;
    category: string;
    severity: string;
  };
  recommendations: string[];
  urgency: 'low' | 'medium' | 'high' | 'critical';
  alternativeConditions: Array<{
    id: string;
    name: string;
    namePt: string;
    confidence: number;
  }>;
}

// Union type for all results
export type VisionAnalysisResult =
  | DiseaseDetectionResult
  | WeightEstimationResult
  | HealthAssessmentResult;

// Model info for management
export interface ModelInfo {
  id: string;
  name: string;
  version: string;
  analysisType: AnalysisType;
  sizeBytes: number;
  quantization: 'none' | 'dynamic' | 'float16' | 'int8';
  downloaded: boolean;
  lastUpdated?: string;
}

// Download progress
export interface DownloadProgress {
  modelId: string;
  progress: number; // 0-100
  bytesDownloaded: number;
  totalBytes: number;
  status: 'pending' | 'downloading' | 'completed' | 'error';
  error?: string;
}

// Vision service configuration
export interface VisionServiceConfig {
  apiBaseUrl: string;
  preferOffline: boolean;
  offlineModelsDir?: string;
  maxImageSize: number; // pixels
  compressionQuality: number; // 0-1
}

// Analysis request
export interface AnalysisRequest {
  image: File | Blob | string; // File, Blob, or base64
  analysisType: AnalysisType;
  options?: {
    topK?: number;
    confidenceThreshold?: number;
    includeAlternatives?: boolean;
  };
}
