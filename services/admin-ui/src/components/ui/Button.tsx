import { ButtonHTMLAttributes, forwardRef } from 'react'
import { Loader2 } from 'lucide-react'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'destructive' | 'outline' | 'ghost'
    size?: 'sm' | 'md' | 'lg'
    loading?: boolean
    children: React.ReactNode
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    ({ variant = 'primary', size = 'md', loading = false, disabled, className = '', children, ...props }, ref) => {
        const baseStyles = 'inline-flex items-center justify-center rounded-lg font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer'

        const variants = {
            primary: 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm',
            secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
            destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90 shadow-sm',
            outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
            ghost: 'hover:bg-accent hover:text-accent-foreground',
        }

        const sizes = {
            sm: 'h-9 px-3 text-sm',
            md: 'h-10 px-4 text-sm',
            lg: 'h-11 px-6 text-base',
        }

        const isDisabled = disabled || loading

        return (
            <button
                ref={ref}
                className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
                disabled={isDisabled}
                aria-disabled={isDisabled}
                {...props}
            >
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {children}
            </button>
        )
    }
)

Button.displayName = 'Button'

export { Button }
