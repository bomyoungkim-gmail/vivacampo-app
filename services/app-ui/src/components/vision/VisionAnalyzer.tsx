'use client';

import React, { useState, useCallback } from 'react';
import { ImageCapture } from './ImageCapture';
import {
  visionService,
  AnalysisType,
  VisionAnalysisResult,
  DiseaseDetectionResult,
  WeightEstimationResult,
  HealthAssessmentResult,
} from '../../services/vision';

interface VisionAnalyzerProps {
  analysisType: AnalysisType;
  onResult?: (result: VisionAnalysisResult) => void;
  onError?: (error: Error) => void;
  title?: string;
  description?: string;
}

const ANALYSIS_CONFIG: Record<AnalysisType, { title: string; description: string; icon: string }> = {
  crop_disease: {
    title: 'Diagnóstico de Doenças em Culturas',
    description: 'Tire uma foto da folha ou planta afetada para identificar possíveis doenças',
    icon: '🌱',
  },
  cattle_weight: {
    title: 'Estimativa de Peso - Bovinos',
    description: 'Tire uma foto lateral do animal para estimar o peso',
    icon: '🐄',
  },
  swine_weight: {
    title: 'Estimativa de Peso - Suínos',
    description: 'Tire uma foto lateral do animal para estimar o peso',
    icon: '🐷',
  },
  bovine_health: {
    title: 'Avaliação de Saúde - Bovinos',
    description: 'Tire uma foto do animal para avaliar possíveis condições de saúde',
    icon: '🐄',
  },
  swine_health: {
    title: 'Avaliação de Saúde - Suínos',
    description: 'Tire uma foto do animal para avaliar possíveis condições de saúde',
    icon: '🐷',
  },
  poultry_health: {
    title: 'Avaliação de Saúde - Aves',
    description: 'Tire uma foto da ave para avaliar possíveis condições de saúde',
    icon: '🐔',
  },
};

export function VisionAnalyzer({
  analysisType,
  onResult,
  onError,
  title,
  description,
}: VisionAnalyzerProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<VisionAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [capturedImage, setCapturedImage] = useState<File | null>(null);

  const config = ANALYSIS_CONFIG[analysisType];

  const handleCapture = useCallback(
    async (file: File) => {
      setCapturedImage(file);
      setIsAnalyzing(true);
      setError(null);
      setResult(null);

      try {
        let analysisResult: VisionAnalysisResult;

        switch (analysisType) {
          case 'crop_disease':
            analysisResult = await visionService.analyzeCropDisease(file);
            break;
          case 'cattle_weight':
            analysisResult = await visionService.estimateCattleWeight(file);
            break;
          case 'swine_weight':
            analysisResult = await visionService.estimateSwineWeight(file);
            break;
          case 'bovine_health':
            analysisResult = await visionService.assessBovineHealth(file);
            break;
          case 'swine_health':
            analysisResult = await visionService.assessSwineHealth(file);
            break;
          case 'poultry_health':
            analysisResult = await visionService.assessPoultryHealth(file);
            break;
          default:
            throw new Error(`Unsupported analysis type: ${analysisType}`);
        }

        setResult(analysisResult);
        onResult?.(analysisResult);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Erro na análise';
        setError(errorMessage);
        onError?.(err instanceof Error ? err : new Error(errorMessage));
      } finally {
        setIsAnalyzing(false);
      }
    },
    [analysisType, onResult, onError]
  );

  const handleReset = useCallback(() => {
    setCapturedImage(null);
    setResult(null);
    setError(null);
  }, []);

  return (
    <div className="flex flex-col w-full max-w-lg mx-auto p-4">
      {/* Header */}
      <div className="mb-4 text-center">
        <div className="text-4xl mb-2">{config.icon}</div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          {title || config.title}
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          {description || config.description}
        </p>
      </div>

      {/* Image Capture */}
      {!result && (
        <ImageCapture
          onCapture={handleCapture}
          placeholder={config.description}
          aspectRatio={analysisType.includes('weight') ? 16 / 9 : 4 / 3}
        />
      )}

      {/* Loading State */}
      {isAnalyzing && (
        <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-center">
          <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-2" />
          <p className="text-blue-700 dark:text-blue-300">Analisando imagem...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
          <p className="text-red-700 dark:text-red-300 text-center">{error}</p>
          <button
            onClick={handleReset}
            className="mt-2 w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Tentar novamente
          </button>
        </div>
      )}

      {/* Results */}
      {result && result.success && (
        <div className="mt-4">
          {/* Show captured image */}
          {capturedImage && (
            <div className="mb-4 rounded-lg overflow-hidden">
              <img
                src={URL.createObjectURL(capturedImage)}
                alt="Analyzed"
                className="w-full h-auto"
              />
            </div>
          )}

          {/* Render appropriate result component */}
          {result.analysisType === 'crop_disease' && (
            <DiseaseResult result={result as DiseaseDetectionResult} />
          )}
          {(result.analysisType === 'cattle_weight' ||
            result.analysisType === 'swine_weight') && (
            <WeightResult result={result as WeightEstimationResult} />
          )}
          {(result.analysisType === 'bovine_health' ||
            result.analysisType === 'swine_health' ||
            result.analysisType === 'poultry_health') && (
            <HealthResult result={result as HealthAssessmentResult} />
          )}

          {/* Reset button */}
          <button
            onClick={handleReset}
            className="mt-4 w-full px-4 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700"
          >
            Nova análise
          </button>
        </div>
      )}
    </div>
  );
}

// Disease Detection Result Component
function DiseaseResult({ result }: { result: DiseaseDetectionResult }) {
  const severityColors = ['green', 'yellow', 'orange', 'red', 'red', 'purple'];
  const severityLabels = ['Nenhuma', 'Muito Leve', 'Leve', 'Moderada', 'Severa', 'Crítica'];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              {result.disease.namePt}
            </h3>
            <p className="text-sm text-gray-500">{result.disease.name}</p>
          </div>
          <div className="text-right">
            <span className="text-2xl font-bold text-green-600">
              {Math.round(result.disease.confidence * 100)}%
            </span>
            <p className="text-xs text-gray-500">Confiança</p>
          </div>
        </div>

        {/* Severity indicator */}
        <div className="mt-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Severidade</span>
            <span
              className={`font-medium text-${severityColors[result.disease.severity]}-600`}
            >
              {severityLabels[result.disease.severity]}
            </span>
          </div>
          <div className="mt-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full bg-${severityColors[result.disease.severity]}-500`}
              style={{ width: `${(result.disease.severity / 5) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {result.recommendations?.length > 0 && (
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h4 className="font-medium text-gray-900 dark:text-white mb-2">
            Recomendações
          </h4>
          <ul className="space-y-2">
            {result.recommendations.map((rec, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400"
              >
                <span className="text-green-500">•</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Alternative diagnoses */}
      {result.alternativeDiagnoses?.length > 0 && (
        <div className="p-4">
          <h4 className="font-medium text-gray-900 dark:text-white mb-2">
            Diagnósticos Alternativos
          </h4>
          <div className="space-y-2">
            {result.alternativeDiagnoses.map((alt, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between text-sm"
              >
                <span className="text-gray-600 dark:text-gray-400">
                  {alt.namePt}
                </span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {Math.round(alt.confidence * 100)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Weight Estimation Result Component
function WeightResult({ result }: { result: WeightEstimationResult }) {
  const bcsDescriptions: Record<number, string> = {
    1: 'Muito magro',
    2: 'Magro',
    3: 'Abaixo do peso',
    4: 'Ligeiramente abaixo',
    5: 'Ideal',
    6: 'Ligeiramente acima',
    7: 'Acima do peso',
    8: 'Gordo',
    9: 'Obeso',
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
      {/* Weight estimation */}
      <div className="p-6 text-center border-b border-gray-200 dark:border-gray-700">
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
          Peso Estimado
        </p>
        <p className="text-4xl font-bold text-gray-900 dark:text-white">
          {result.weight.estimatedKg.toFixed(0)}{' '}
          <span className="text-2xl font-normal">kg</span>
        </p>
        <p className="text-sm text-gray-500 mt-1">
          Faixa: {result.weight.rangeMin.toFixed(0)} -{' '}
          {result.weight.rangeMax.toFixed(0)} kg
        </p>
        <div className="mt-2 text-sm text-gray-600">
          <span className="inline-flex items-center px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-700">
            Confiança: {Math.round(result.weight.confidence * 100)}%
          </span>
        </div>
      </div>

      {/* Body Condition Score */}
      <div className="p-4">
        <h4 className="font-medium text-gray-900 dark:text-white mb-3">
          Escore de Condição Corporal (ECC)
        </h4>

        {/* BCS Scale */}
        <div className="relative">
          <div className="flex justify-between mb-1">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((score) => (
              <span
                key={score}
                className={`text-xs ${
                  score === result.bodyConditionScore.score
                    ? 'font-bold text-green-600'
                    : 'text-gray-400'
                }`}
              >
                {score}
              </span>
            ))}
          </div>
          <div className="h-3 bg-gradient-to-r from-red-400 via-green-400 to-red-400 rounded-full relative">
            <div
              className="absolute w-4 h-4 bg-white border-2 border-green-600 rounded-full -top-0.5 transform -translate-x-1/2"
              style={{
                left: `${((result.bodyConditionScore.score - 1) / 8) * 100}%`,
              }}
            />
          </div>
          <div className="flex justify-between mt-1 text-xs text-gray-500">
            <span>Magro</span>
            <span>Ideal</span>
            <span>Obeso</span>
          </div>
        </div>

        <div className="mt-4 text-center">
          <span className="text-lg font-bold text-gray-900 dark:text-white">
            ECC {result.bodyConditionScore.score}
          </span>
          <span className="text-gray-600 dark:text-gray-400 mx-2">-</span>
          <span className="text-gray-600 dark:text-gray-400">
            {bcsDescriptions[result.bodyConditionScore.score] ||
              result.bodyConditionScore.descriptionPt}
          </span>
        </div>
      </div>
    </div>
  );
}

// Health Assessment Result Component
function HealthResult({ result }: { result: HealthAssessmentResult }) {
  const urgencyConfig: Record<
    string,
    { color: string; bg: string; label: string }
  > = {
    low: { color: 'green', bg: 'bg-green-100', label: 'Baixa' },
    medium: { color: 'yellow', bg: 'bg-yellow-100', label: 'Média' },
    high: { color: 'orange', bg: 'bg-orange-100', label: 'Alta' },
    critical: { color: 'red', bg: 'bg-red-100', label: 'Crítica' },
  };

  const urgency = urgencyConfig[result.urgency] || urgencyConfig.low;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
      {/* Health Score */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Escore de Saúde
            </p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              {result.healthScore}
              <span className="text-lg font-normal text-gray-500">/100</span>
            </p>
          </div>
          <div
            className={`px-3 py-1 rounded-full ${urgency.bg} text-${urgency.color}-700`}
          >
            <span className="text-sm font-medium">
              Urgência: {urgency.label}
            </span>
          </div>
        </div>

        {/* Health bar */}
        <div className="mt-3 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full ${
              result.healthScore >= 80
                ? 'bg-green-500'
                : result.healthScore >= 60
                ? 'bg-yellow-500'
                : result.healthScore >= 40
                ? 'bg-orange-500'
                : 'bg-red-500'
            }`}
            style={{ width: `${result.healthScore}%` }}
          />
        </div>
      </div>

      {/* Detected condition */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h4 className="font-medium text-gray-900 dark:text-white mb-2">
          Condição Detectada
        </h4>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {result.condition.namePt}
            </p>
            <p className="text-sm text-gray-500">{result.condition.category}</p>
          </div>
          <span className="text-xl font-bold text-green-600">
            {Math.round(result.condition.confidence * 100)}%
          </span>
        </div>
      </div>

      {/* Recommendations */}
      {result.recommendations?.length > 0 && (
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h4 className="font-medium text-gray-900 dark:text-white mb-2">
            Recomendações
          </h4>
          <ul className="space-y-2">
            {result.recommendations.map((rec, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400"
              >
                <span className="text-green-500 mt-0.5">✓</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Alternative conditions */}
      {result.alternativeConditions?.length > 0 && (
        <div className="p-4">
          <h4 className="font-medium text-gray-900 dark:text-white mb-2">
            Outras Possibilidades
          </h4>
          <div className="space-y-2">
            {result.alternativeConditions.map((alt, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between text-sm"
              >
                <span className="text-gray-600 dark:text-gray-400">
                  {alt.namePt}
                </span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {Math.round(alt.confidence * 100)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default VisionAnalyzer;
