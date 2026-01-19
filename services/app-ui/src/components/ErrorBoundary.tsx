'use client'

import React, { Component, ReactNode } from 'react'
import { handleGlobalError } from '@/lib/errorHandler'

interface Props {
    children: ReactNode
    fallback?: ReactNode
}

interface State {
    hasError: boolean
    error: Error | null
    errorInfo: React.ErrorInfo | null
}

/**
 * Error Boundary Component
 *
 * Catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI.
 *
 * Usage:
 * ```tsx
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 * ```
 *
 * With custom fallback:
 * ```tsx
 * <ErrorBoundary fallback={<CustomErrorUI />}>
 *   <YourComponent />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props)
        this.state = {
            hasError: false,
            error: null,
            errorInfo: null,
        }
    }

    static getDerivedStateFromError(error: Error): Partial<State> {
        // Update state so the next render will show the fallback UI
        return {
            hasError: true,
            error,
        }
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        // Log error to error reporting service
        handleGlobalError(error, errorInfo)

        // Update state with error info
        this.setState({
            errorInfo,
        })
    }

    handleReset = () => {
        this.setState({
            hasError: false,
            error: null,
            errorInfo: null,
        })
    }

    render() {
        if (this.state.hasError) {
            // Custom fallback UI
            if (this.props.fallback) {
                return this.props.fallback
            }

            // Default fallback UI
            return (
                <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
                    <div className="w-full max-w-md">
                        <div className="rounded-lg bg-white p-8 shadow-lg">
                            {/* Error Icon */}
                            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
                                <svg
                                    className="h-6 w-6 text-red-600"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                                    />
                                </svg>
                            </div>

                            {/* Error Message */}
                            <div className="mt-4 text-center">
                                <h3 className="text-lg font-medium text-gray-900">
                                    Algo deu errado
                                </h3>
                                <p className="mt-2 text-sm text-gray-600">
                                    Ocorreu um erro inesperado. Por favor, tente novamente.
                                </p>

                                {/* Show error details in development */}
                                {process.env.NODE_ENV === 'development' && this.state.error && (
                                    <div className="mt-4 rounded-lg bg-red-50 p-4 text-left">
                                        <p className="text-xs font-mono text-red-800">
                                            {this.state.error.toString()}
                                        </p>
                                        {this.state.errorInfo && (
                                            <details className="mt-2">
                                                <summary className="cursor-pointer text-xs font-semibold text-red-700">
                                                    Stack Trace
                                                </summary>
                                                <pre className="mt-2 max-h-40 overflow-auto text-xs text-red-700">
                                                    {this.state.errorInfo.componentStack}
                                                </pre>
                                            </details>
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* Action Buttons */}
                            <div className="mt-6 flex flex-col gap-3">
                                <button
                                    onClick={this.handleReset}
                                    className="w-full rounded-md bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                                >
                                    Tentar Novamente
                                </button>
                                <button
                                    onClick={() => (window.location.href = '/')}
                                    className="w-full rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                                >
                                    Voltar ao Início
                                </button>
                            </div>

                            {/* Support Info */}
                            <p className="mt-4 text-center text-xs text-gray-500">
                                Se o problema persistir, entre em contato com o suporte.
                            </p>
                        </div>
                    </div>
                </div>
            )
        }

        return this.props.children
    }
}

/**
 * HOC to wrap components with Error Boundary
 *
 * Usage:
 * ```tsx
 * export default withErrorBoundary(MyComponent)
 * ```
 */
export function withErrorBoundary<P extends object>(
    Component: React.ComponentType<P>,
    fallback?: ReactNode
) {
    return function WithErrorBoundaryWrapper(props: P) {
        return (
            <ErrorBoundary fallback={fallback}>
                <Component {...props} />
            </ErrorBoundary>
        )
    }
}
