import { test, expect } from '@playwright/test'

const breakpoints = [
    { label: 'iphone-se', width: 320, height: 568 },
    { label: 'iphone-12', width: 375, height: 812 },
    { label: 'iphone-14-pro-max', width: 414, height: 896 },
    { label: 'ipad', width: 768, height: 1024 },
    { label: 'desktop', width: 1024, height: 768 },
    { label: 'desktop-lg', width: 1440, height: 900 },
]

test.describe('Mobile responsiveness checks', () => {
    test('landing page meets core mobile constraints', async ({ page }) => {
        const isWebkitProject = test
            .info()
            .project.name.toLowerCase()
            .includes('safari')
        for (const bp of breakpoints) {
            await page.setViewportSize({ width: bp.width, height: bp.height })
            await page.goto('/', { waitUntil: 'domcontentloaded' })

            const result = await page.evaluate(() => {
                const root = document.documentElement
                const horizontalScroll =
                    root.scrollWidth > root.clientWidth + 1

                const bodyFontSize = Number.parseFloat(
                    getComputedStyle(document.body).fontSize || '0'
                )

                const htmlStyle = getComputedStyle(document.documentElement)
                const bodyStyle = getComputedStyle(document.body)

                const candidates = Array.from(
                    document.querySelectorAll<HTMLElement>(
                        'a[href], button, [role="button"], input, select, textarea'
                    )
                )

                const offenders: Array<{
                    tag: string
                    text: string
                    width: number
                    height: number
                }> = []

                for (const el of candidates) {
                    const style = getComputedStyle(el)
                    if (
                        style.display === 'none' ||
                        style.visibility === 'hidden' ||
                        style.pointerEvents === 'none'
                    ) {
                        continue
                    }
                    const rect = el.getBoundingClientRect()
                    if (rect.width === 0 || rect.height === 0) continue

                    if (rect.width < 44 || rect.height < 44) {
                        offenders.push({
                            tag: el.tagName.toLowerCase(),
                            text: (el.textContent || '').trim().slice(0, 40),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                        })
                    }
                }

                return {
                    horizontalScroll,
                    bodyFontSize,
                    scrollBehavior: htmlStyle.scrollBehavior,
                    touchAction: bodyStyle.touchAction,
                    overscrollBehaviorY: bodyStyle.overscrollBehaviorY,
                    offenders: offenders.slice(0, 8),
                    offendersCount: offenders.length,
                }
            })

            expect(
                result.horizontalScroll,
                `Horizontal scroll detected at ${bp.label} (${bp.width}x${bp.height})`
            ).toBe(false)

            expect(
                result.bodyFontSize,
                `Body font size below 16px at ${bp.label} (${bp.width}x${bp.height})`
            ).toBeGreaterThanOrEqual(16)

            expect(
                result.scrollBehavior,
                `scroll-behavior not smooth at ${bp.label} (${bp.width}x${bp.height})`
            ).toBe('smooth')

            expect(
                result.touchAction,
                `touch-action not manipulation at ${bp.label} (${bp.width}x${bp.height})`
            ).toBe('manipulation')

            if (!isWebkitProject || result.overscrollBehaviorY !== undefined) {
                expect(
                    result.overscrollBehaviorY,
                    `overscroll-behavior-y not contain at ${bp.label} (${bp.width}x${bp.height})`
                ).toBe('contain')
            }

            expect(
                result.offendersCount,
                `Touch targets below 44x44 at ${bp.label} (${bp.width}x${bp.height}): ${JSON.stringify(
                    result.offenders
                )}`
            ).toBe(0)
        }
    })
})
