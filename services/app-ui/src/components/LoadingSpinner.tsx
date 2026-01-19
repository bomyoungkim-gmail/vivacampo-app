import { APP_CONFIG } from '@/lib/config'

interface LoadingSpinnerProps {
    message?: string
    fullScreen?: boolean
    size?: 'sm' | 'md' | 'lg'
}

export function LoadingSpinner({
    message = APP_CONFIG.TEXT.LOADING,
    fullScreen = true,
    size = 'md'
}: LoadingSpinnerProps) {
    const sizeClasses = {
        sm: 'h-4 w-4 border-2',
        md: 'h-8 w-8 border-4',
        lg: 'h-12 w-12 border-4'
    }

    const spinner = (
        <div className="text-center">
            <div
                className={`inline-block animate-spin rounded-full border-solid border-primary-600 border-r-transparent ${sizeClasses[size]}`}
            ></div>
            {message && <p className="mt-2 text-gray-600">{message}</p>}
        </div>
    )

    if (fullScreen) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                {spinner}
            </div>
        )
    }

    return spinner
}
