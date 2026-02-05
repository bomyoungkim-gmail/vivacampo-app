import { HTMLAttributes, forwardRef } from 'react'

export interface BadgeProps extends HTMLAttributes<HTMLDivElement> {
    variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'secondary'
    children: React.ReactNode
}

const Badge = forwardRef<HTMLDivElement, BadgeProps>(
    ({ variant = 'default', className = '', children, ...props }, ref) => {
        const baseStyles = 'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2'

        const variants = {
            default: 'bg-primary/10 text-primary dark:bg-primary/20',
            success: 'bg-primary/10 text-primary dark:bg-primary/20',
            warning: 'bg-chart-3/10 text-chart-3 dark:bg-chart-3/20',
            error: 'bg-destructive/10 text-destructive dark:bg-destructive/20',
            info: 'bg-chart-2/10 text-chart-2 dark:bg-chart-2/20',
            secondary: 'bg-muted text-muted-foreground',
        }

        return (
            <div
                ref={ref}
                className={`${baseStyles} ${variants[variant]} ${className}`}
                {...props}
            >
                {children}
            </div>
        )
    }
)

Badge.displayName = 'Badge'

export { Badge }
