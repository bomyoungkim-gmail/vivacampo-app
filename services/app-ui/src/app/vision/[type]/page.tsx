'use client';

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { VisionAnalyzer } from '../../../components/vision';
import { AnalysisType, VisionAnalysisResult } from '../../../services/vision';

const VALID_TYPES: AnalysisType[] = [
  'crop_disease',
  'cattle_weight',
  'swine_weight',
  'bovine_health',
  'swine_health',
  'poultry_health',
];

const TYPE_TITLES: Record<AnalysisType, string> = {
  crop_disease: 'Doenças em Plantas',
  cattle_weight: 'Peso de Bovinos',
  swine_weight: 'Peso de Suínos',
  bovine_health: 'Saúde de Bovinos',
  swine_health: 'Saúde de Suínos',
  poultry_health: 'Saúde de Aves',
};

export default function VisionAnalysisPage() {
  const params = useParams();
  const router = useRouter();
  const type = params.type as string;

  // Validate type
  if (!VALID_TYPES.includes(type as AnalysisType)) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center p-8">
          <div className="text-6xl mb-4">❌</div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
            Tipo de análise inválido
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            O tipo de análise &quot;{type}&quot; não é reconhecido.
          </p>
          <Link
            href="/vision"
            className="inline-flex min-h-touch items-center justify-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            Voltar para análises
          </Link>
        </div>
      </div>
    );
  }

  const analysisType = type as AnalysisType;
  const title = TYPE_TITLES[analysisType];

  const handleResult = (result: VisionAnalysisResult) => {
    console.log('Analysis result:', result);
    // Could save to history, send to API, etc.
  };

  const handleError = (error: Error) => {
    console.error('Analysis error:', error);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm sticky top-0 z-10">
        <div className="max-w-lg mx-auto px-4 py-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.back()}
              className="inline-flex min-h-touch min-w-touch items-center justify-center p-2 -ml-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <h1 className="text-lg font-bold text-gray-900 dark:text-white">
              {title}
            </h1>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="pb-8">
        <VisionAnalyzer
          analysisType={analysisType}
          onResult={handleResult}
          onError={handleError}
        />
      </main>
    </div>
  );
}
