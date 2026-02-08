'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { AnalysisType } from '../../services/vision';

interface AnalysisOption {
  type: AnalysisType;
  title: string;
  description: string;
  icon: string;
  color: string;
}

const ANALYSIS_OPTIONS: AnalysisOption[] = [
  {
    type: 'crop_disease',
    title: 'Doenças em Plantas',
    description: 'Identifique doenças em soja, milho, café e outras culturas',
    icon: '🌿',
    color: 'bg-green-500',
  },
  {
    type: 'cattle_weight',
    title: 'Peso de Bovinos',
    description: 'Estime o peso de gado bovino a partir de uma foto',
    icon: '🐄',
    color: 'bg-amber-500',
  },
  {
    type: 'swine_weight',
    title: 'Peso de Suínos',
    description: 'Estime o peso de suínos a partir de uma foto',
    icon: '🐷',
    color: 'bg-pink-500',
  },
  {
    type: 'bovine_health',
    title: 'Saúde de Bovinos',
    description: 'Avalie condições de saúde em gado bovino',
    icon: '🏥',
    color: 'bg-blue-500',
  },
  {
    type: 'swine_health',
    title: 'Saúde de Suínos',
    description: 'Avalie condições de saúde em suínos',
    icon: '💊',
    color: 'bg-purple-500',
  },
  {
    type: 'poultry_health',
    title: 'Saúde de Aves',
    description: 'Avalie condições de saúde em aves de corte e postura',
    icon: '🐔',
    color: 'bg-orange-500',
  },
];

export default function VisionPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="inline-flex min-h-touch min-w-touch items-center justify-center p-2 -ml-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Link>
            <div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                Análise por Imagem
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Diagnóstico inteligente usando visão computacional
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        {/* Info banner */}
        <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <div className="flex items-start gap-3">
            <div className="text-2xl">📸</div>
            <div>
              <h3 className="font-medium text-blue-900 dark:text-blue-100">
                Como funciona
              </h3>
              <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                Tire uma foto ou selecione da galeria. Nossa IA analisará a imagem
                e fornecerá diagnósticos e recomendações em segundos.
              </p>
            </div>
          </div>
        </div>

        {/* Analysis options grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {ANALYSIS_OPTIONS.map((option) => (
            <Link
              key={option.type}
              href={`/vision/${option.type}`}
              className="block bg-white dark:bg-gray-800 rounded-xl shadow-sm hover:shadow-md transition-shadow overflow-hidden group"
            >
              <div className={`h-2 ${option.color}`} />
              <div className="p-4">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-3xl">{option.icon}</span>
                  <h3 className="font-semibold text-gray-900 dark:text-white group-hover:text-green-600 dark:group-hover:text-green-400 transition-colors">
                    {option.title}
                  </h3>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {option.description}
                </p>
                <div className="mt-3 flex items-center text-green-600 dark:text-green-400 text-sm font-medium">
                  Iniciar análise
                  <svg className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </Link>
          ))}
        </div>

        {/* Offline mode info */}
        <div className="mt-8 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
          <div className="flex items-start gap-3">
            <div className="text-xl">📶</div>
            <div>
              <h3 className="font-medium text-gray-900 dark:text-white">
                Modo Offline
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Os modelos de análise podem funcionar sem internet quando
                baixados previamente. Ideal para uso no campo.
              </p>
              <button
                disabled
                className="mt-2 inline-flex min-h-touch items-center text-sm text-gray-500 dark:text-gray-500 cursor-not-allowed"
              >
                Gerenciar modelos offline (em breve)
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
