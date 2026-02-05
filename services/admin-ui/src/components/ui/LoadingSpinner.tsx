import { HTMLAttributes } from 'react'
import { Loader2 } from 'lucide-react'

export interface LoadingSpinnerProps extends HTMLAttributes<HTMLDivElement> {
    size?: 'sm' | 'md' | 'lg'
    label?: string
}

export function LoadingSpinner({ size = 'md', label, className = '', ...props }: LoadingSpinnerProps) {
    const sizes = {
        sm: 'h-4 w-4',
        md: 'h-8 w-8',
        lg: 'h-12 w-12',
    }

    return (
        <div
            className={`flex flex-col items-center justify-center gap-2 ${className}`}
            role="status"
            aria-label={label || 'Loading'}
            {...props}
        >
            <Loader2 className={`${sizes[size]} animate-spin text-primary`} />
            {label && (
                <p className="text-sm text-muted-foreground">{label}</p>
            )}
        </div>
    )
}
