import { HTMLAttributes, forwardRef } from 'react'

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
    variant?: 'default' | 'interactive'
    children: React.ReactNode
}

const Card = forwardRef<HTMLDivElement, CardProps>(
    ({ variant = 'default', className = '', children, ...props }, ref) => {
        const baseStyles = 'rounded-lg border border-border bg-card text-card-foreground shadow-sm'

        const variants = {
            default: '',
            interactive: 'interactive-card', // Uses .interactive-card from globals.css
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

Card.displayName = 'Card'

const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
    ({ className = '', ...props }, ref) => (
        <div
            ref={ref}
            className={`flex flex-col space-y-1.5 p-6 ${className}`}
            {...props}
        />
    )
)

CardHeader.displayName = 'CardHeader'

const CardTitle = forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(
    ({ className = '', ...props }, ref) => (
        <h3
            ref={ref}
            className={`text-lg font-semibold leading-none tracking-tight ${className}`}
            {...props}
        />
    )
)

CardTitle.displayName = 'CardTitle'

const CardDescription = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLParagraphElement>>(
    ({ className = '', ...props }, ref) => (
        <p
            ref={ref}
            className={`text-sm text-muted-foreground ${className}`}
            {...props}
        />
    )
)

CardDescription.displayName = 'CardDescription'

const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
    ({ className = '', ...props }, ref) => (
        <div ref={ref} className={`p-6 pt-0 ${className}`} {...props} />
    )
)

CardContent.displayName = 'CardContent'

const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
    ({ className = '', ...props }, ref) => (
        <div
            ref={ref}
            className={`flex items-center p-6 pt-0 ${className}`}
            {...props}
        />
    )
)

CardFooter.displayName = 'CardFooter'

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter }
