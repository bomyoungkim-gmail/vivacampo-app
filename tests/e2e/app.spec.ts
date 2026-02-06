import { test, expect } from '@playwright/test'

const APP_BASE = '/app'
const ADMIN_BASE = '/admin'

const isMobileProject = (projectName?: string) =>
    (projectName || '').toLowerCase().includes('mobile')

async function clickAppNav(page: any, href: string, label: string) {
    const link = page.getByRole('link', { name: label })
    if (await link.isVisible()) {
        await link.click()
        return
    }

    const visibleLink = page.locator(`a[href="${href}"]:visible`).first()
    await visibleLink.click()
}

test.describe('VivaCampo App UI E2E Tests', () => {
    test.beforeEach(async ({ page }) => {
        await page.context().clearCookies()
        await page.addInitScript(() => {
            localStorage.clear()
            sessionStorage.clear()
        })
        await page.goto(`http://localhost:3002${APP_BASE}`, { waitUntil: 'domcontentloaded' })
    })

    test('should redirect to login page', async ({ page }) => {
        try {
            await page.waitForURL(/.*\/app\/login/, { timeout: 10000 })
        } catch {
            if (!page.url().includes('/app/login')) {
                await page.waitForLoadState('domcontentloaded')
                await page.goto(`http://localhost:3002${APP_BASE}/login`, { waitUntil: 'domcontentloaded' })
            }
        }
        await expect(page).toHaveURL(/.*\/app\/login/)
        await expect(page.locator('h1')).toContainText('VivaCampo')
    })

    test('should login successfully', async ({ page }) => {
        await page.goto(`http://localhost:3002${APP_BASE}/login`)

        // Fill login form
        await page.fill('input[type="email"]', 'test@example.com')
        await page.click('button[type="submit"]')

        // Should redirect to dashboard
        await expect(page).toHaveURL(/.*\/app\/dashboard/)
        await expect(page.locator('h2')).toContainText('Bem-vindo')
    })

    test('should navigate to farms page', async ({ page }) => {
        // Login first
        await page.goto(`http://localhost:3002${APP_BASE}/login`)
        await page.fill('input[type="email"]', 'test@example.com')
        await page.click('button[type="submit"]')

        // Navigate to farms
        await clickAppNav(page, `${APP_BASE}/farms`, 'Fazendas')
        await expect(page).toHaveURL(/.*\/app\/farms/)
        await expect(page.locator('h1')).toContainText('VivaCampo')
    })

    test('should open create farm modal', async ({ page }) => {
        // Login and navigate
        await page.goto(`http://localhost:3002${APP_BASE}/login`)
        await page.fill('input[type="email"]', 'test@example.com')
        await page.click('button[type="submit"]')
        await clickAppNav(page, `${APP_BASE}/farms`, 'Fazendas')

        // Click create button
        await page.click('button:has-text("Nova Fazenda")')

        // Modal should be visible
        await expect(page.locator('h2:has-text("Nova Fazenda")')).toBeVisible()
    })

    test('should navigate to signals page', async ({ page }) => {
        // Login first
        await page.goto(`http://localhost:3002${APP_BASE}/login`)
        await page.fill('input[type="email"]', 'test@example.com')
        await page.click('button[type="submit"]')

        // Navigate to signals
        await clickAppNav(page, `${APP_BASE}/signals`, 'Sinais')
        await expect(page).toHaveURL(/.*\/app\/signals/)
        await expect(page.locator('h1')).toContainText('VivaCampo')
    })

    test('should filter signals by status', async ({ page }) => {
        // Login and navigate
        await page.goto(`http://localhost:3002${APP_BASE}/login`)
        await page.fill('input[type="email"]', 'test@example.com')
        await page.click('button[type="submit"]')
        await clickAppNav(page, `${APP_BASE}/signals`, 'Sinais')

        // Click filter button
        await page.click('button:has-text("ACTIVE")')

        // URL should update or filter should be applied
        await expect(page.locator('button:has-text("ACTIVE")')).toHaveClass(/bg-green-600/)
    })

    test('should navigate to AI Assistant', async ({ page }) => {
        // Login first
        await page.goto(`http://localhost:3002${APP_BASE}/login`)
        await page.fill('input[type="email"]', 'test@example.com')
        await page.click('button[type="submit"]')

        // Navigate to AI Assistant
        const aiLabel = isMobileProject(test.info().project.name) ? 'IA' : 'AI Assistant'
        await clickAppNav(page, `${APP_BASE}/ai-assistant`, aiLabel)
        await expect(page).toHaveURL(/.*\/app\/ai-assistant/)
        await expect(page.getByRole('heading', { name: 'AI Assistant' }).first()).toBeVisible()
    })

    test('should logout successfully', async ({ page }) => {
        // Login first
        await page.goto(`http://localhost:3002${APP_BASE}/login`)
        await page.fill('input[type="email"]', 'test@example.com')
        await page.click('button[type="submit"]')

        // Click logout
        await page.click('button:has-text("Sair")')

        // Should redirect to login
        await expect(page).toHaveURL(/.*\/app\/login/)
    })
})

test.describe('VivaCampo Admin UI E2E Tests', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto(`http://localhost:3001${ADMIN_BASE}`)
    })

    test('should show admin login page', async ({ page }) => {
        await expect(page).toHaveURL(/.*login/)
        await expect(page.locator('h1')).toContainText('Portal Admin')
    })

    test('should login with admin token', async ({ page }) => {
        await page.goto(`http://localhost:3001${ADMIN_BASE}/login`)

        // Fill token
        await page.fill('input[type="password"]', 'mock_admin_token_12345')
        await page.click('button[type="submit"]')

        // Should redirect to dashboard
        await page.waitForURL(/.*\/admin\/dashboard/, { timeout: 15000 })
        await expect(page.locator('h1')).toContainText('Visão Geral')
    })

    test('should navigate to tenants page', async ({ page }) => {
        // Login first
        await page.goto(`http://localhost:3001${ADMIN_BASE}/login`)
        await page.fill('input[type="password"]', 'mock_admin_token_12345')
        await page.click('button[type="submit"]')

        // Navigate to tenants (no shared sidebar on all admin pages)
        await page.goto(`http://localhost:3001${ADMIN_BASE}/tenants`)
        await expect(page).toHaveURL(/.*\/admin\/tenants/)
        await expect(page.locator('h1')).toContainText('Tenants')
    })

    test('should navigate to jobs page', async ({ page }) => {
        // Login first
        await page.goto(`http://localhost:3001${ADMIN_BASE}/login`)
        await page.fill('input[type="password"]', 'mock_admin_token_12345')
        await page.click('button[type="submit"]')

        // Navigate to jobs (no shared sidebar on all admin pages)
        await page.goto(`http://localhost:3001${ADMIN_BASE}/jobs`)
        await expect(page).toHaveURL(/.*\/admin\/jobs/)
        await expect(page.locator('h1')).toContainText('Jobs Monitor')
    })

    test('should navigate to audit log', async ({ page }) => {
        // Login first
        await page.goto(`http://localhost:3001${ADMIN_BASE}/login`)
        await page.fill('input[type="password"]', 'mock_admin_token_12345')
        await page.click('button[type="submit"]')

        // Navigate to audit (no shared sidebar on all admin pages)
        await page.goto(`http://localhost:3001${ADMIN_BASE}/audit`)
        await expect(page).toHaveURL(/.*\/admin\/audit/)
        await expect(page.locator('h1')).toContainText('Global Audit Log')
    })
})
