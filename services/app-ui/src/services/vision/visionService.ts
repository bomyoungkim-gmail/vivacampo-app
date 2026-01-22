/**
 * VivaCampo Vision Service
 * Handles image analysis for crop diseases and livestock assessment.
 * Supports both online (API) and offline (TFLite) inference.
 */

import {
  AnalysisType,
  AnalysisRequest,
  VisionAnalysisResult,
  DiseaseDetectionResult,
  WeightEstimationResult,
  HealthAssessmentResult,
  ModelInfo,
  DownloadProgress,
  VisionServiceConfig,
} from './types';

// Default configuration
const DEFAULT_CONFIG: VisionServiceConfig = {
  apiBaseUrl: process.env.NEXT_PUBLIC_VISION_API_URL || 'http://localhost:8090',
  preferOffline: false,
  maxImageSize: 1024,
  compressionQuality: 0.85,
};

class VisionService {
  private config: VisionServiceConfig;
  private offlineModels: Map<AnalysisType, boolean> = new Map();

  constructor(config: Partial<VisionServiceConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Update service configuration
   */
  updateConfig(config: Partial<VisionServiceConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Check if offline inference is available for a given analysis type
   */
  isOfflineAvailable(analysisType: AnalysisType): boolean {
    return this.offlineModels.get(analysisType) || false;
  }

  /**
   * Analyze an image using the appropriate method (offline or online)
   */
  async analyze(request: AnalysisRequest): Promise<VisionAnalysisResult> {
    const startTime = Date.now();

    try {
      // Prepare image
      const imageData = await this.prepareImage(request.image);

      // Try offline first if preferred and available
      if (this.config.preferOffline && this.isOfflineAvailable(request.analysisType)) {
        try {
          return await this.analyzeOffline(imageData, request);
        } catch (offlineError) {
          console.warn('Offline analysis failed, falling back to API:', offlineError);
        }
      }

      // Use online API
      return await this.analyzeOnline(imageData, request);
    } catch (error) {
      const processingTime = Date.now() - startTime;
      return this.createErrorResult(request.analysisType, error, processingTime);
    }
  }

  /**
   * Analyze crop disease from plant/leaf image
   */
  async analyzeCropDisease(image: File | Blob | string): Promise<DiseaseDetectionResult> {
    const result = await this.analyze({
      image,
      analysisType: 'crop_disease',
      options: { includeAlternatives: true },
    });
    return result as DiseaseDetectionResult;
  }

  /**
   * Estimate cattle weight from image
   */
  async estimateCattleWeight(image: File | Blob | string): Promise<WeightEstimationResult> {
    const result = await this.analyze({
      image,
      analysisType: 'cattle_weight',
    });
    return result as WeightEstimationResult;
  }

  /**
   * Estimate swine weight from image
   */
  async estimateSwineWeight(image: File | Blob | string): Promise<WeightEstimationResult> {
    const result = await this.analyze({
      image,
      analysisType: 'swine_weight',
    });
    return result as WeightEstimationResult;
  }

  /**
   * Assess bovine health from image
   */
  async assessBovineHealth(image: File | Blob | string): Promise<HealthAssessmentResult> {
    const result = await this.analyze({
      image,
      analysisType: 'bovine_health',
      options: { includeAlternatives: true },
    });
    return result as HealthAssessmentResult;
  }

  /**
   * Assess swine health from image
   */
  async assessSwineHealth(image: File | Blob | string): Promise<HealthAssessmentResult> {
    const result = await this.analyze({
      image,
      analysisType: 'swine_health',
      options: { includeAlternatives: true },
    });
    return result as HealthAssessmentResult;
  }

  /**
   * Assess poultry health from image
   */
  async assessPoultryHealth(image: File | Blob | string): Promise<HealthAssessmentResult> {
    const result = await this.analyze({
      image,
      analysisType: 'poultry_health',
      options: { includeAlternatives: true },
    });
    return result as HealthAssessmentResult;
  }

  /**
   * Get list of available models
   */
  async getAvailableModels(): Promise<ModelInfo[]> {
    try {
      const response = await fetch(`${this.config.apiBaseUrl}/v1/vision/models`);
      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to get available models:', error);
      return [];
    }
  }

  /**
   * Download a model for offline use (for React Native / mobile)
   * This is a placeholder - actual implementation depends on platform
   */
  async downloadModel(
    modelId: string,
    onProgress?: (progress: DownloadProgress) => void
  ): Promise<boolean> {
    // Web doesn't support local model storage
    // This would be implemented in React Native using react-native-fs
    console.warn('Model download is only supported on mobile platforms');
    return false;
  }

  /**
   * Delete a downloaded model
   */
  async deleteModel(modelId: string): Promise<boolean> {
    console.warn('Model deletion is only supported on mobile platforms');
    return false;
  }

  // Private methods

  private async prepareImage(image: File | Blob | string): Promise<Blob> {
    let blob: Blob;

    if (typeof image === 'string') {
      // Base64 string
      const response = await fetch(image);
      blob = await response.blob();
    } else {
      blob = image;
    }

    // Resize if needed
    return await this.resizeImage(blob);
  }

  private async resizeImage(blob: Blob): Promise<Blob> {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        const maxSize = this.config.maxImageSize;

        // Check if resize is needed
        if (img.width <= maxSize && img.height <= maxSize) {
          resolve(blob);
          return;
        }

        // Calculate new dimensions
        let width = img.width;
        let height = img.height;

        if (width > height) {
          if (width > maxSize) {
            height = (height * maxSize) / width;
            width = maxSize;
          }
        } else {
          if (height > maxSize) {
            width = (width * maxSize) / height;
            height = maxSize;
          }
        }

        // Create canvas and resize
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;

        const ctx = canvas.getContext('2d');
        if (!ctx) {
          reject(new Error('Failed to get canvas context'));
          return;
        }

        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob(
          (resizedBlob) => {
            if (resizedBlob) {
              resolve(resizedBlob);
            } else {
              reject(new Error('Failed to resize image'));
            }
          },
          'image/jpeg',
          this.config.compressionQuality
        );
      };

      img.onerror = () => reject(new Error('Failed to load image'));
      img.src = URL.createObjectURL(blob);
    });
  }

  private async analyzeOnline(
    imageData: Blob,
    request: AnalysisRequest
  ): Promise<VisionAnalysisResult> {
    const startTime = Date.now();

    const formData = new FormData();
    formData.append('file', imageData, 'image.jpg');

    // Map analysis type to API endpoint
    const endpointMap: Record<AnalysisType, string> = {
      crop_disease: '/v1/vision/crop/disease',
      cattle_weight: '/v1/vision/cattle/weight',
      swine_weight: '/v1/vision/swine/weight',
      bovine_health: '/v1/vision/bovine/health',
      swine_health: '/v1/vision/swine/health',
      poultry_health: '/v1/vision/poultry/health',
    };

    const endpoint = endpointMap[request.analysisType];

    const response = await fetch(`${this.config.apiBaseUrl}${endpoint}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API error: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    const processingTime = Date.now() - startTime;

    return this.transformApiResponse(data, request.analysisType, processingTime, false);
  }

  private async analyzeOffline(
    imageData: Blob,
    request: AnalysisRequest
  ): Promise<VisionAnalysisResult> {
    // Placeholder for TFLite inference
    // This would be implemented using @mediapipe/tasks-vision or similar
    throw new Error('Offline inference not implemented for web');
  }

  private transformApiResponse(
    data: Record<string, unknown>,
    analysisType: AnalysisType,
    processingTimeMs: number,
    offline: boolean
  ): VisionAnalysisResult {
    const baseResult = {
      success: true,
      analysisType,
      timestamp: new Date().toISOString(),
      processingTimeMs,
      offline,
    };

    switch (analysisType) {
      case 'crop_disease':
        return {
          ...baseResult,
          disease: data.disease as DiseaseDetectionResult['disease'],
          recommendations: data.recommendations as string[],
          alternativeDiagnoses: data.alternatives as DiseaseDetectionResult['alternativeDiagnoses'],
        } as DiseaseDetectionResult;

      case 'cattle_weight':
      case 'swine_weight':
        return {
          ...baseResult,
          weight: data.weight as WeightEstimationResult['weight'],
          bodyConditionScore: data.body_condition_score as WeightEstimationResult['bodyConditionScore'],
        } as WeightEstimationResult;

      case 'bovine_health':
      case 'swine_health':
      case 'poultry_health':
        return {
          ...baseResult,
          healthScore: data.health_score as number,
          condition: data.condition as HealthAssessmentResult['condition'],
          recommendations: data.recommendations as string[],
          urgency: data.urgency as HealthAssessmentResult['urgency'],
          alternativeConditions: data.alternatives as HealthAssessmentResult['alternativeConditions'],
        } as HealthAssessmentResult;

      default:
        throw new Error(`Unknown analysis type: ${analysisType}`);
    }
  }

  private createErrorResult(
    analysisType: AnalysisType,
    error: unknown,
    processingTimeMs: number
  ): VisionAnalysisResult {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';

    return {
      success: false,
      analysisType,
      timestamp: new Date().toISOString(),
      processingTimeMs,
      offline: false,
      error: errorMessage,
    } as VisionAnalysisResult;
  }
}

// Export singleton instance
export const visionService = new VisionService();

// Export class for custom instances
export { VisionService };
