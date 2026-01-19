import { AxiosError } from 'axios'
import type { APIError, ValidationError } from './types'
import { APP_CONFIG } from './config'

/**
 * Error Handler Utility
 *
 * Centralizes error handling logic across the application.
 * Provides consistent error messages and logging.
 */

export interface ErrorInfo {
    message: string
    code?: string
    details?: string[]
}

/**
 * Parse API error response
 */
export function parseAPIError(error: unknown): ErrorInfo {
    // Not an error object
    if (!error) {
        return {
            message: APP_CONFIG.TEXT.ERROR_GENERIC,
        }
    }

    // Axios error
    if (isAxiosError(error)) {
        const axiosError = error as AxiosError<APIError>

        // Network error
        if (!axiosError.response) {
            return {
                message: APP_CONFIG.TEXT.ERROR_NETWORK,
                code: 'NETWORK_ERROR',
            }
        }

        // HTTP error codes
        const status = axiosError.response.status
        const detail = axiosError.response.data?.detail

        switch (status) {
            case 401:
                return {
                    message: APP_CONFIG.TEXT.ERROR_UNAUTHORIZED,
                    code: 'UNAUTHORIZED',
                }

            case 403:
                return {
                    message: 'Você não tem permissão para realizar esta ação',
                    code: 'FORBIDDEN',
                }

            case 404:
                return {
                    message: 'Recurso não encontrado',
                    code: 'NOT_FOUND',
                }

            case 422:
                // Validation errors (Pydantic)
                if (Array.isArray(detail)) {
                    const validationErrors = detail as ValidationError[]
                    return {
                        message: 'Dados inválidos',
                        code: 'VALIDATION_ERROR',
                        details: validationErrors.map((e) => e.msg),
                    }
                }
                return {
                    message: typeof detail === 'string' ? detail : 'Dados inválidos',
                    code: 'VALIDATION_ERROR',
                }

            case 429:
                return {
                    message: 'Muitas requisições. Tente novamente em alguns minutos',
                    code: 'RATE_LIMIT',
                }

            case 500:
            case 502:
            case 503:
            case 504:
                return {
                    message: 'Erro no servidor. Tente novamente mais tarde',
                    code: 'SERVER_ERROR',
                }

            default:
                return {
                    message: typeof detail === 'string' ? detail : APP_CONFIG.TEXT.ERROR_GENERIC,
                    code: `HTTP_${status}`,
                }
        }
    }

    // Generic Error object
    if (error instanceof Error) {
        return {
            message: error.message,
            code: 'ERROR',
        }
    }

    // Unknown error
    return {
        message: APP_CONFIG.TEXT.ERROR_GENERIC,
        code: 'UNKNOWN',
    }
}

/**
 * Type guard for Axios errors
 */
function isAxiosError(error: unknown): error is AxiosError {
    return (error as AxiosError).isAxiosError === true
}

/**
 * Format error for display
 */
export function formatErrorMessage(error: ErrorInfo): string {
    let message = error.message

    if (error.details && error.details.length > 0) {
        message += ':\n' + error.details.map((d) => `• ${d}`).join('\n')
    }

    return message
}

/**
 * Log error to console (and external service in production)
 */
export function logError(error: unknown, context?: string) {
    const errorInfo = parseAPIError(error)

    // Console logging
    console.error('[Error]', {
        context,
        message: errorInfo.message,
        code: errorInfo.code,
        details: errorInfo.details,
        originalError: error,
    })

    // TODO: Send to external logging service in production
    if (APP_CONFIG.IS_PRODUCTION) {
        // Example: Sentry.captureException(error)
        // Example: LogRocket.captureException(error)
    }
}

/**
 * Custom hook for error handling
 * Usage in components:
 *
 * const { error, handleError, clearError } = useErrorHandler()
 *
 * try {
 *   await api.call()
 * } catch (err) {
 *   handleError(err, 'Failed to load data')
 * }
 */
import { useState, useCallback } from 'react'

export function useErrorHandler() {
    const [error, setError] = useState<ErrorInfo | null>(null)

    const handleError = useCallback((err: unknown, context?: string) => {
        const errorInfo = parseAPIError(err)
        setError(errorInfo)
        logError(err, context)
    }, [])

    const clearError = useCallback(() => {
        setError(null)
    }, [])

    return {
        error,
        handleError,
        clearError,
    }
}

/**
 * Error boundary helper
 * For use with React Error Boundaries
 */
export function handleGlobalError(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Global Error:', error)
    console.error('Error Info:', errorInfo)

    // Log to external service
    if (APP_CONFIG.IS_PRODUCTION) {
        // Example: Sentry.captureException(error, { extra: errorInfo })
    }
}
