import { InputHTMLAttributes, forwardRef } from 'react'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
    error?: string
    helperText?: string
    label?: string
}

const Input = forwardRef<HTMLInputElement, InputProps>(
    ({ error, helperText, label, className = '', id, ...props }, ref) => {
        const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`
        const hasError = !!error

        const baseStyles = 'flex h-10 w-full rounded-lg border bg-background px-3 py-2 text-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50'

        const variantStyles = hasError
            ? 'border-destructive focus-visible:ring-destructive'
            : 'border-input'

        return (
            <div className="w-full space-y-2">
                {label && (
                    <label
                        htmlFor={inputId}
                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                    >
                        {label}
                    </label>
                )}
                <input
                    ref={ref}
                    id={inputId}
                    className={`${baseStyles} ${variantStyles} ${className}`}
                    aria-invalid={hasError}
                    aria-describedby={
                        hasError ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined
                    }
                    {...props}
                />
                {error && (
                    <p
                        id={`${inputId}-error`}
                        className="text-sm text-destructive flex items-center gap-1"
                        role="alert"
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="14"
                            height="14"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        >
                            <circle cx="12" cy="12" r="10" />
                            <line x1="12" y1="8" x2="12" y2="12" />
                            <line x1="12" y1="16" x2="12.01" y2="16" />
                        </svg>
                        {error}
                    </p>
                )}
                {!error && helperText && (
                    <p id={`${inputId}-helper`} className="text-sm text-muted-foreground">
                        {helperText}
                    </p>
                )}
            </div>
        )
    }
)

Input.displayName = 'Input'

export { Input }
