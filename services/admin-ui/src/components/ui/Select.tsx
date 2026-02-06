import { SelectHTMLAttributes, forwardRef } from 'react'
import { ChevronDown } from 'lucide-react'

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
    error?: string
    helperText?: string
    label?: string
    options: Array<{ value: string | number; label: string; disabled?: boolean }>
    placeholder?: string
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
    ({ error, helperText, label, options, placeholder, className = '', id, ...props }, ref) => {
        const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`
        const hasError = !!error

        const baseStyles = 'flex h-10 w-full rounded-lg border bg-background px-3 py-2 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 appearance-none cursor-pointer'

        const variantStyles = hasError
            ? 'border-destructive focus-visible:ring-destructive'
            : 'border-input'

        return (
            <div className="w-full space-y-2">
                {label && (
                    <label
                        htmlFor={selectId}
                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                    >
                        {label}
                    </label>
                )}
                <div className="relative">
                    <select
                        ref={ref}
                        id={selectId}
                        className={`${baseStyles} ${variantStyles} ${className}`}
                        aria-invalid={hasError}
                        aria-describedby={
                            hasError ? `${selectId}-error` : helperText ? `${selectId}-helper` : undefined
                        }
                        {...props}
                    >
                        {placeholder && (
                            <option value="" disabled>
                                {placeholder}
                            </option>
                        )}
                        {options.map((option) => (
                            <option
                                key={option.value}
                                value={option.value}
                                disabled={option.disabled}
                            >
                                {option.label}
                            </option>
                        ))}
                    </select>
                    <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
                </div>
                {error && (
                    <p
                        id={`${selectId}-error`}
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
                    <p id={`${selectId}-helper`} className="text-sm text-muted-foreground">
                        {helperText}
                    </p>
                )}
            </div>
        )
    }
)

Select.displayName = 'Select'

export { Select }
