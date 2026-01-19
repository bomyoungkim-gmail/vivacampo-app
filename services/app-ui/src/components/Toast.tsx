'use client'

import { useEffect } from 'react'
import type { ErrorInfo } from '@/lib/errorHandler'

interface ToastProps {
    error: ErrorInfo | null
    onClose: () => void
    duration?: number
}

export function ErrorToast({ error, onClose, duration = 5000 }: ToastProps) {
    useEffect(() => {
        if (error && duration > 0) {
            const timer = setTimeout(onClose, duration)
            return () => clearTimeout(timer)
        }
    }, [error, duration, onClose])

    if (!error) return null

    const hasDetails = error.details && error.details.length > 0

    return (
        <div className="fixed bottom-4 right-4 z-50 max-w-md animate-slide-in">
            <div className="rounded-lg bg-red-50 p-4 shadow-lg ring-1 ring-red-200">
                <div className="flex">
                    <div className="flex-shrink-0">
                        <svg
                            className="h-5 w-5 text-red-400"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                        >
                            <path
                                fillRule="evenodd"
                                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                                clipRule="evenodd"
                            />
                        </svg>
                    </div>
                    <div className="ml-3 flex-1">
                        <h3 className="text-sm font-medium text-red-800">
                            {error.message}
                        </h3>
                        {hasDetails && (
                            <div className="mt-2 text-sm text-red-700">
                                <ul className="list-inside list-disc space-y-1">
                                    {error.details!.map((detail, index) => (
                                        <li key={index}>{detail}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                        {error.code && (
                            <p className="mt-1 text-xs text-red-600">
                                Código: {error.code}
                            </p>
                        )}
                    </div>
                    <div className="ml-4 flex-shrink-0">
                        <button
                            onClick={onClose}
                            className="inline-flex rounded-md bg-red-50 text-red-500 hover:text-red-600 focus:outline-none focus:ring-2 focus:ring-red-400 focus:ring-offset-2 focus:ring-offset-red-50"
                        >
                            <span className="sr-only">Fechar</span>
                            <svg
                                className="h-5 w-5"
                                viewBox="0 0 20 20"
                                fill="currentColor"
                            >
                                <path
                                    fillRule="evenodd"
                                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                                    clipRule="evenodd"
                                />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}

interface SuccessToastProps {
    message: string | null
    onClose: () => void
    duration?: number
}

export function SuccessToast({ message, onClose, duration = 3000 }: SuccessToastProps) {
    useEffect(() => {
        if (message && duration > 0) {
            const timer = setTimeout(onClose, duration)
            return () => clearTimeout(timer)
        }
    }, [message, duration, onClose])

    if (!message) return null

    return (
        <div className="fixed bottom-4 right-4 z-50 max-w-md animate-slide-in">
            <div className="rounded-lg bg-green-50 p-4 shadow-lg ring-1 ring-green-200">
                <div className="flex">
                    <div className="flex-shrink-0">
                        <svg
                            className="h-5 w-5 text-green-400"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                        >
                            <path
                                fillRule="evenodd"
                                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                clipRule="evenodd"
                            />
                        </svg>
                    </div>
                    <div className="ml-3 flex-1">
                        <p className="text-sm font-medium text-green-800">{message}</p>
                    </div>
                    <div className="ml-4 flex-shrink-0">
                        <button
                            onClick={onClose}
                            className="inline-flex rounded-md bg-green-50 text-green-500 hover:text-green-600 focus:outline-none focus:ring-2 focus:ring-green-400 focus:ring-offset-2 focus:ring-offset-green-50"
                        >
                            <span className="sr-only">Fechar</span>
                            <svg
                                className="h-5 w-5"
                                viewBox="0 0 20 20"
                                fill="currentColor"
                            >
                                <path
                                    fillRule="evenodd"
                                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                                    clipRule="evenodd"
                                />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
