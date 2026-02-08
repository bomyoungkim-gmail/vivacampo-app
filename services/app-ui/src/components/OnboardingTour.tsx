'use client'

import React, { useEffect, useMemo, useState, useRef } from 'react'
import { useUser } from '../stores/useUserStore'
import { X } from 'lucide-react'
import { trackGoal } from '../lib/analytics'

const TOUR_STORAGE_PREFIX = 'tour-completed'

function getTourKey(userId: string) {
  return `${TOUR_STORAGE_PREFIX}:${userId}`
}

type TourStep = {
  title: string
  description: string
}

const STEPS: TourStep[] = [
  {
    title: 'Command Center (⌘K / Ctrl+K)',
    description: 'Abra o Command Center e digite comandos como “Ver chuva” ou “NDVI da semana”.',
  },
  {
    title: 'Field Dock',
    description: 'Use o Dock para alternar ferramentas rápidas no mapa: camadas, medições e atalhos.',
  },
]

export default function OnboardingTour() {
  const user = useUser()
  const [open, setOpen] = useState(false)
  const [stepIndex, setStepIndex] = useState(0)
  const stepStartRef = useRef<number | null>(null)

  const storageKey = useMemo(() => {
    if (!user?.id) return null
    return getTourKey(user.id)
  }, [user?.id])

  useEffect(() => {
    if (!storageKey || typeof window === 'undefined') return
    const completed = window.localStorage.getItem(storageKey)
    if (!completed) {
      setOpen(true)
      setStepIndex(0)
      stepStartRef.current = performance.now()
      trackGoal('onboarding_step', {
        step_id: 'command-center',
        action: 'started',
        time_spent: 0,
      })
    }
  }, [storageKey])

  if (!open || !storageKey) return null

  const step = STEPS[stepIndex]
  const isLastStep = stepIndex === STEPS.length - 1

  const completeTour = () => {
    window.localStorage.setItem(storageKey, 'true')
    setOpen(false)
    trackGoal('onboarding_step', {
      step_id: stepIndex === 0 ? 'command-center' : 'field-dock',
      action: 'completed',
      time_spent: stepStartRef.current
        ? Number(((performance.now() - stepStartRef.current) / 1000).toFixed(2))
        : 0,
    })
  }

  const skipTour = () => {
    window.localStorage.setItem(storageKey, 'true')
    setOpen(false)
    trackGoal('onboarding_step', {
      step_id: stepIndex === 0 ? 'command-center' : 'field-dock',
      action: 'skipped',
      time_spent: stepStartRef.current
        ? Number(((performance.now() - stepStartRef.current) / 1000).toFixed(2))
        : 0,
    })
  }

  return (
    <div className="fixed inset-0 z-[var(--z-modal)] flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-950/95 p-6 text-white shadow-2xl">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Onboarding</p>
            <h2 className="mt-2 text-xl font-semibold">{step.title}</h2>
          </div>
          <button
            type="button"
            onClick={completeTour}
            className="rounded-full p-1 text-slate-300 transition-colors hover:text-white"
            aria-label="Fechar tour"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <p className="mt-3 text-sm text-slate-200">{step.description}</p>

        <div className="mt-5 flex items-center justify-between">
          <p className="text-xs text-slate-400">
            Passo {stepIndex + 1} de {STEPS.length}
          </p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={skipTour}
              className="rounded-lg border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 transition-colors hover:border-slate-500"
            >
              Pular
            </button>
            <button
              type="button"
              onClick={() => {
                if (isLastStep) {
                  completeTour()
                } else {
                  trackGoal('onboarding_step', {
                    step_id: 'command-center',
                    action: 'completed',
                    time_spent: stepStartRef.current
                      ? Number(((performance.now() - stepStartRef.current) / 1000).toFixed(2))
                      : 0,
                  })
                  trackGoal('onboarding_step', {
                    step_id: 'field-dock',
                    action: 'started',
                    time_spent: 0,
                  })
                  stepStartRef.current = performance.now()
                  setStepIndex((prev) => prev + 1)
                }
              }}
              className="rounded-lg bg-emerald-500 px-3 py-2 text-xs font-semibold text-slate-950 transition-colors hover:bg-emerald-400"
            >
              {isLastStep ? 'Concluir' : 'Próximo'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
