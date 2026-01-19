/**
 * Client-Side Rate Limiting Detection and Handling
 *
 * Detects when the backend is rate limiting requests (HTTP 429)
 * and provides user-friendly feedback with retry logic.
 */

import { AxiosError } from 'axios'

interface RateLimitInfo {
    isRateLimited: boolean
    retryAfter: number // seconds
    resetAt: Date | null
}

interface RetryConfig {
    maxRetries: number
    baseDelay: number // ms
    maxDelay: number // ms
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
    maxRetries: 3,
    baseDelay: 1000, // 1 second
    maxDelay: 30000, // 30 seconds
}

/**
 * Parse rate limit information from error response
 */
export function parseRateLimitError(error: unknown): RateLimitInfo {
    if (!isAxiosError(error)) {
        return {
            isRateLimited: false,
            retryAfter: 0,
            resetAt: null,
        }
    }

    const response = error.response

    if (response?.status !== 429) {
        return {
            isRateLimited: false,
            retryAfter: 0,
            resetAt: null,
        }
    }

    // Check Retry-After header (standard)
    const retryAfterHeader = response.headers['retry-after']
    let retryAfter = 60 // Default: 1 minute

    if (retryAfterHeader) {
        // Can be seconds or HTTP date
        const parsed = parseInt(retryAfterHeader, 10)
        if (!isNaN(parsed)) {
            retryAfter = parsed
        } else {
            const date = new Date(retryAfterHeader)
            if (!isNaN(date.getTime())) {
                retryAfter = Math.ceil((date.getTime() - Date.now()) / 1000)
            }
        }
    }

    // Check X-RateLimit-Reset header (common)
    const resetHeader = response.headers['x-ratelimit-reset']
    let resetAt: Date | null = null

    if (resetHeader) {
        const timestamp = parseInt(resetHeader, 10)
        if (!isNaN(timestamp)) {
            // Unix timestamp
            resetAt = new Date(timestamp * 1000)
            retryAfter = Math.ceil((resetAt.getTime() - Date.now()) / 1000)
        }
    }

    return {
        isRateLimited: true,
        retryAfter: Math.max(0, retryAfter),
        resetAt,
    }
}

/**
 * Type guard for Axios errors
 */
function isAxiosError(error: unknown): error is AxiosError {
    return (error as AxiosError).isAxiosError === true
}

/**
 * Format retry time for user display
 */
export function formatRetryTime(seconds: number): string {
    if (seconds < 60) {
        return `${seconds} segundo${seconds !== 1 ? 's' : ''}`
    }

    const minutes = Math.ceil(seconds / 60)
    return `${minutes} minuto${minutes !== 1 ? 's' : ''}`
}

/**
 * Get user-friendly rate limit message
 */
export function getRateLimitMessage(info: RateLimitInfo): string {
    if (!info.isRateLimited) {
        return ''
    }

    const retryTime = formatRetryTime(info.retryAfter)

    return `Você fez muitas requisições. Por favor, aguarde ${retryTime} antes de tentar novamente.`
}

/**
 * Exponential backoff calculator
 */
function calculateBackoff(attempt: number, config: RetryConfig): number {
    const delay = Math.min(
        config.baseDelay * Math.pow(2, attempt),
        config.maxDelay
    )

    // Add jitter (±25%) to avoid thundering herd
    const jitter = delay * 0.25 * (Math.random() - 0.5)

    return Math.floor(delay + jitter)
}

/**
 * Retry a failed request with exponential backoff
 *
 * Usage:
 * ```typescript
 * try {
 *   const data = await retryWithBackoff(() => api.getData())
 * } catch (error) {
 *   // All retries failed
 * }
 * ```
 */
export async function retryWithBackoff<T>(
    fn: () => Promise<T>,
    config: Partial<RetryConfig> = {}
): Promise<T> {
    const retryConfig = { ...DEFAULT_RETRY_CONFIG, ...config }
    let lastError: unknown

    for (let attempt = 0; attempt <= retryConfig.maxRetries; attempt++) {
        try {
            return await fn()
        } catch (error) {
            lastError = error

            // Check if rate limited
            const rateLimitInfo = parseRateLimitError(error)

            if (rateLimitInfo.isRateLimited) {
                // For rate limit errors, wait the specified time
                const waitTime = rateLimitInfo.retryAfter * 1000

                console.warn(
                    `Rate limited. Waiting ${rateLimitInfo.retryAfter}s before retry (attempt ${attempt + 1}/${retryConfig.maxRetries})`
                )

                if (attempt < retryConfig.maxRetries) {
                    await sleep(waitTime)
                    continue
                }
            } else {
                // For other errors, use exponential backoff
                if (attempt < retryConfig.maxRetries) {
                    const backoff = calculateBackoff(attempt, retryConfig)

                    console.warn(
                        `Request failed. Retrying in ${backoff}ms (attempt ${attempt + 1}/${retryConfig.maxRetries})`
                    )

                    await sleep(backoff)
                    continue
                }
            }

            // Max retries reached
            throw lastError
        }
    }

    throw lastError
}

/**
 * Sleep utility
 */
function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * React hook for rate limit handling
 *
 * Usage:
 * ```typescript
 * const { isRateLimited, rateLimitInfo, executeWithRetry } = useRateLimitHandler()
 *
 * const handleSubmit = async () => {
 *   await executeWithRetry(() => api.createFarm(data))
 * }
 *
 * {isRateLimited && (
 *   <div>Rate limited! Retry in {rateLimitInfo?.retryAfter}s</div>
 * )}
 * ```
 */
import { useState, useCallback } from 'react'

export function useRateLimitHandler() {
    const [rateLimitInfo, setRateLimitInfo] = useState<RateLimitInfo | null>(null)

    const executeWithRetry = useCallback(
        async <T,>(fn: () => Promise<T>, config?: Partial<RetryConfig>): Promise<T> => {
            try {
                setRateLimitInfo(null)
                return await retryWithBackoff(fn, config)
            } catch (error) {
                const info = parseRateLimitError(error)
                if (info.isRateLimited) {
                    setRateLimitInfo(info)
                }
                throw error
            }
        },
        []
    )

    const clearRateLimit = useCallback(() => {
        setRateLimitInfo(null)
    }, [])

    return {
        isRateLimited: rateLimitInfo?.isRateLimited || false,
        rateLimitInfo,
        executeWithRetry,
        clearRateLimit,
        rateLimitMessage: rateLimitInfo
            ? getRateLimitMessage(rateLimitInfo)
            : null,
    }
}

/**
 * Simple in-memory rate limiter for client-side prevention
 *
 * Prevents sending too many requests before getting 429 from server.
 *
 * Usage:
 * ```typescript
 * const limiter = new ClientRateLimiter({
 *   maxRequests: 10,
 *   windowMs: 60000 // 10 requests per minute
 * })
 *
 * if (limiter.tryAcquire()) {
 *   await api.call()
 * } else {
 *   console.log('Too many requests, waiting...')
 * }
 * ```
 */
export class ClientRateLimiter {
    private requests: number[] = []
    private maxRequests: number
    private windowMs: number

    constructor(config: { maxRequests: number; windowMs: number }) {
        this.maxRequests = config.maxRequests
        this.windowMs = config.windowMs
    }

    tryAcquire(): boolean {
        const now = Date.now()

        // Remove old requests outside the window
        this.requests = this.requests.filter((time) => now - time < this.windowMs)

        // Check if we can make another request
        if (this.requests.length < this.maxRequests) {
            this.requests.push(now)
            return true
        }

        return false
    }

    reset(): void {
        this.requests = []
    }

    getWaitTime(): number {
        if (this.requests.length < this.maxRequests) {
            return 0
        }

        const oldestRequest = this.requests[0]
        const now = Date.now()
        const waitTime = this.windowMs - (now - oldestRequest)

        return Math.max(0, waitTime)
    }
}
