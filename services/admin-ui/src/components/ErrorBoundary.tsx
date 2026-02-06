'use client'

import { Component, ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'
import { Button } from './ui/Button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from './ui/Card'

interface ErrorBoundaryProps {
    children: ReactNode
    fallback?: (error: Error, resetError: () => void) => ReactNode
}

interface ErrorBoundaryState {
    hasError: boolean
    error: Error | null
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props)
        this.state = { hasError: false, error: null }
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        return { hasError: true, error }
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        // Log to console in development
        if (process.env.NODE_ENV === 'development') {
            console.error('ErrorBoundary caught an error:', error, errorInfo)
        }

        // TODO: Send to error tracking service (Sentry, etc.)
        // logErrorToService(error, errorInfo)
    }

    resetError = () => {
        this.setState({ hasError: false, error: null })
    }

    render() {
        if (this.state.hasError && this.state.error) {
            // Use custom fallback if provided
            if (this.props.fallback) {
                return this.props.fallback(this.state.error, this.resetError)
            }

            // Default fallback UI
            return (
                <div className="flex items-center justify-center min-h-[400px] p-4">
                    <Card className="max-w-lg w-full">
                        <CardHeader>
                            <div className="flex items-center gap-3">
                                <div className="rounded-full bg-destructive/10 p-3">
                                    <AlertTriangle className="h-6 w-6 text-destructive" />
                                </div>
                                <CardTitle>Algo deu errado</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <p className="text-sm text-muted-foreground">
                                Ocorreu um erro inesperado ao carregar este componente.
                            </p>
                            {process.env.NODE_ENV === 'development' && (
                                <div className="rounded-lg bg-muted p-4 overflow-auto">
                                    <p className="text-xs font-mono text-destructive">
                                        {this.state.error.message}
                                    </p>
                                    {this.state.error.stack && (
                                        <pre className="text-xs font-mono text-muted-foreground mt-2 overflow-x-auto">
                                            {this.state.error.stack}
                                        </pre>
                                    )}
                                </div>
                            )}
                        </CardContent>
                        <CardFooter className="flex gap-2">
                            <Button onClick={this.resetError} variant="outline">
                                Tentar novamente
                            </Button>
                            <Button onClick={() => window.location.reload()} variant="primary">
                                Recarregar página
                            </Button>
                        </CardFooter>
                    </Card>
                </div>
            )
        }

        return this.props.children
    }
}
