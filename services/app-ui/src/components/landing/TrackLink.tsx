'use client'

import Link, { type LinkProps } from 'next/link'
import { trackGoal } from '../../lib/analytics'
import { cn } from '../../lib/utils'

type TrackLinkProps = LinkProps & {
    children: React.ReactNode
    className?: string
    goal?: string
    metadata?: Record<string, string | number | boolean>
    onClick?: () => void
}

export function TrackLink({ goal, metadata, className, onClick, children, ...props }: TrackLinkProps) {
    return (
        <Link
            {...props}
            className={cn(className)}
            onClick={() => {
                if (goal) {
                    trackGoal(goal, metadata)
                }
                onClick?.()
            }}
        >
            {children}
        </Link>
    )
}
