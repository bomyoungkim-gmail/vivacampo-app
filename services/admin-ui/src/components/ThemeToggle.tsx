'use client'

import { useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'

export default function ThemeToggle() {
    const [theme, setTheme] = useState<'light' | 'dark'>('light')
    const [mounted, setMounted] = useState(false)

    useEffect(() => {
        setMounted(true)
        const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light')
        setTheme(initialTheme)
        document.documentElement.classList.toggle('dark', initialTheme === 'dark')
    }, [])

    const toggleTheme = () => {
        const newTheme = theme === 'light' ? 'dark' : 'light'
        setTheme(newTheme)
        localStorage.setItem('theme', newTheme)
        document.documentElement.classList.toggle('dark', newTheme === 'dark')
    }

    // Prevent hydration mismatch
    if (!mounted) {
        return (
            <div className="h-10 w-10 rounded-lg bg-muted/50 animate-pulse" />
        )
    }

    return (
        <button
            onClick={toggleTheme}
            className="rounded-lg p-2 hover:bg-muted transition-colors min-h-touch min-w-touch flex items-center justify-center"
            aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        >
            {theme === 'light' ? (
                <Moon className="h-5 w-5 text-foreground" />
            ) : (
                <Sun className="h-5 w-5 text-foreground" />
            )}
        </button>
    )
}
