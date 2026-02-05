import { HTMLAttributes } from 'react'

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
    variant?: 'default' | 'text' | 'circular' | 'rectangular'
}

export function Skeleton({ variant = 'default', className = '', ...props }: SkeletonProps) {
    const baseStyles = 'animate-pulse bg-muted'

    const variants = {
        default: 'rounded-md',
        text: 'h-4 w-full rounded',
        circular: 'rounded-full',
        rectangular: 'rounded-none',
    }

    return (
        <div
            className={`${baseStyles} ${variants[variant]} ${className}`}
            aria-live="polite"
            aria-busy="true"
            {...props}
        />
    )
}

// Preset skeleton components for common use cases
export function SkeletonCard() {
    return (
        <div className="rounded-lg border border-border bg-card p-4 shadow-sm space-y-4">
            <Skeleton className="h-6 w-3/4" />
            <Skeleton variant="text" />
            <Skeleton variant="text" />
            <Skeleton variant="text" className="w-2/3" />
        </div>
    )
}

export function SkeletonTable() {
    return (
        <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
        </div>
    )
}
