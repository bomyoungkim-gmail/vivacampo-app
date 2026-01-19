'use client'

import { createContext, useContext, useEffect, useState } from 'react'

type Theme = 'light' | 'dark' | 'system'

interface ThemeContextType {
    theme: Theme
    effectiveTheme: 'light' | 'dark'
    setTheme: (theme: Theme) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
    const [theme, setThemeState] = useState<Theme>('system')
    const [effectiveTheme, setEffectiveTheme] = useState<'light' | 'dark'>('light')

    useEffect(() => {
        // Load theme from localStorage
        const savedTheme = localStorage.getItem('theme') as Theme | null
        if (savedTheme) {
            setThemeState(savedTheme)
        }
    }, [])

    useEffect(() => {
        const updateEffectiveTheme = () => {
            let newEffectiveTheme: 'light' | 'dark' = 'light'

            if (theme === 'system') {
                newEffectiveTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
            } else {
                newEffectiveTheme = theme
            }

            setEffectiveTheme(newEffectiveTheme)

            // Update document class
            if (newEffectiveTheme === 'dark') {
                document.documentElement.classList.add('dark')
            } else {
                document.documentElement.classList.remove('dark')
            }
        }

        updateEffectiveTheme()

        // Listen for system theme changes
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
        const handler = () => {
            if (theme === 'system') {
                updateEffectiveTheme()
            }
        }

        mediaQuery.addEventListener('change', handler)
        return () => mediaQuery.removeEventListener('change', handler)
    }, [theme])

    const setTheme = (newTheme: Theme) => {
        setThemeState(newTheme)
        localStorage.setItem('theme', newTheme)
    }

    return (
        <ThemeContext.Provider value={{ theme, effectiveTheme, setTheme }}>
            {children}
        </ThemeContext.Provider>
    )
}

export function useTheme() {
    const context = useContext(ThemeContext)
    if (context === undefined) {
        throw new Error('useTheme must be used within a ThemeProvider')
    }
    return context
}
