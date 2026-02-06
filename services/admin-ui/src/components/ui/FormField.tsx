import { HTMLAttributes, ReactNode } from 'react'

export interface FormFieldProps extends HTMLAttributes<HTMLDivElement> {
    label?: string
    error?: string
    helperText?: string
    required?: boolean
    children: ReactNode
}

export function FormField({
    label,
    error,
    helperText,
    required = false,
    children,
    className = '',
    ...props
}: FormFieldProps) {
    const hasError = !!error

    return (
        <div className={`w-full space-y-2 ${className}`} {...props}>
            {label && (
                <label className="text-sm font-medium leading-none">
                    {label}
                    {required && <span className="text-destructive ml-1">*</span>}
                </label>
            )}
            {children}
            {error && (
                <p className="text-sm text-destructive flex items-center gap-1" role="alert">
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
                <p className="text-sm text-muted-foreground">{helperText}</p>
            )}
        </div>
    )
}
