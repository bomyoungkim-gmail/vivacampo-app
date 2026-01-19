import { test, expect } from '@playwright/test'

test.describe('VivaCampo App UI E2E Tests', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:3002')
    })

    test('should redirect to login page', async ({ page }) => {
        await expect(page).toHaveURL(/.*login/)
        await expect(page.locator('h1')).toContainText('VivaCampo')
    })

    test('should login successfully', async ({ page }) => {
        await page.goto('http://localhost:3002/login')

        // Fill login form
        await page.fill('input[type="email"]', 'test@example.com')
        await page.click('button[type="submit"]')

        // Should redirect to dashboard
        await expect(page).toHaveURL(/.*dashboard/)
        await expect(page.locator('h2')).toContainText('Bem-vindo')
    })

    test('should navigate to farms page', async ({ page }) => {
        // Login first
        await page.goto('http://localhost:3002/login')
        await page.fill('input[type="email"]', 'test@example.com')
        await page.click('button[type="submit"]')

        // Navigate to farms
        await page.click('a[href="/farms"]')
        await expect(page).toHaveURL(/.*farms/)
        await expect(page.locator('h1')).toContainText('Fazendas')
    })

    test('should open create farm modal', async ({ page }) => {
        // Login and navigate
        await page.goto('http://localhost:3002/login')
        await page.fill('input[type="email"]', 'test@example.com')
        await page.click('button[type="submit"]')
        await page.click('a[href="/farms"]')

        // Click create button
        await page.click('button:has-text("Nova Fazenda")')

        // Modal should be visible
        await expect(page.locator('h2:has-text("Nova Fazenda")')).toBeVisible()
    })

    test('should navigate to signals page', async ({ page }) => {
        // Login first
        await page.goto('http://localhost:3002/login')
        await page.fill('input[type="email"]', 'test@example.com')
        await page.click('button[type="submit"]')

        // Navigate to signals
        await page.click('a[href="/signals"]')
        await expect(page).toHaveURL(/.*signals/)
        await expect(page.locator('h1')).toContainText('Sinais')
    })

    test('should filter signals by status', async ({ page }) => {
        // Login and navigate
        await page.goto('http://localhost:3002/login')
        await page.fill('input[type="email"]', 'test@example.com')
        await page.click('button[type="submit"]')
        await page.click('a[href="/signals"]')

        // Click filter button
        await page.click('button:has-text("ACTIVE")')

        // URL should update or filter should be applied
        await expect(page.locator('button:has-text("ACTIVE")')).toHaveClass(/bg-green-600/)
    })

    test('should navigate to AI Assistant', async ({ page }) => {
        // Login first
        await page.goto('http://localhost:3002/login')
        await page.fill('input[type="email"]', 'test@example.com')
        await page.click('button[type="submit"]')

        // Navigate to AI Assistant
        await page.click('a[href="/ai-assistant"]')
        await expect(page).toHaveURL(/.*ai-assistant/)
        await expect(page.locator('h2')).toContainText('AI Assistant')
    })

    test('should logout successfully', async ({ page }) => {
        // Login first
        await page.goto('http://localhost:3002/login')
        await page.fill('input[type="email"]', 'test@example.com')
        await page.click('button[type="submit"]')

        // Click logout
        await page.click('button:has-text("Sair")')

        // Should redirect to login
        await expect(page).toHaveURL(/.*login/)
    })
})

test.describe('VivaCampo Admin UI E2E Tests', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:3001/admin')
    })

    test('should show admin login page', async ({ page }) => {
        await expect(page).toHaveURL(/.*login/)
        await expect(page.locator('h1')).toContainText('Admin Portal')
    })

    test('should login with admin token', async ({ page }) => {
        await page.goto('http://localhost:3001/admin/login')

        // Fill token
        await page.fill('input[type="password"]', 'mock_admin_token_12345')
        await page.click('button[type="submit"]')

        // Should redirect to dashboard
        await expect(page).toHaveURL(/.*dashboard/)
        await expect(page.locator('h2')).toContainText('System Health')
    })

    test('should navigate to tenants page', async ({ page }) => {
        // Login first
        await page.goto('http://localhost:3001/admin/login')
        await page.fill('input[type="password"]', 'mock_admin_token_12345')
        await page.click('button[type="submit"]')

        // Navigate to tenants
        await page.click('a[href="/admin/tenants"]')
        await expect(page).toHaveURL(/.*tenants/)
        await expect(page.locator('h1')).toContainText('Tenant Management')
    })

    test('should navigate to jobs page', async ({ page }) => {
        // Login first
        await page.goto('http://localhost:3001/admin/login')
        await page.fill('input[type="password"]', 'mock_admin_token_12345')
        await page.click('button[type="submit"]')

        // Navigate to jobs
        await page.click('a[href="/admin/jobs"]')
        await expect(page).toHaveURL(/.*jobs/)
        await expect(page.locator('h1')).toContainText('Jobs Monitor')
    })

    test('should navigate to audit log', async ({ page }) => {
        // Login first
        await page.goto('http://localhost:3001/admin/login')
        await page.fill('input[type="password"]', 'mock_admin_token_12345')
        await page.click('button[type="submit"]')

        // Navigate to audit
        await page.click('a[href="/admin/audit"]')
        await expect(page).toHaveURL(/.*audit/)
        await expect(page.locator('h1')).toContainText('Audit Log')
    })
})
