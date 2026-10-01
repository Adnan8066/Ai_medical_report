import { expect, test } from '@playwright/test'
import { DEMO_PASSWORD, goTo, login } from './helpers.js'

test.describe('authentication and dashboard', () => {
  test('signs in, shows live KPIs and charts, and signs out', async ({ page }) => {
    await login(page)

    await expect(page.getByText('Total patients')).toBeVisible()
    await expect(page.getByText('Available beds')).toBeVisible()
    await expect(page.getByText('ICU occupancy')).toBeVisible()

    // KPIs come from the seeded database, so they must not be empty.
    const patients = page.locator('text=Total patients').locator('..')
    await expect(patients).not.toBeEmpty()

    await expect(page.locator('.recharts-surface').first()).toBeVisible()

    await page.getByRole('button').filter({ has: page.locator('svg[data-testid="LogoutIcon"]') })
      .first()
      .click()
    await page.waitForURL('**/login')
  })

  test('rejects a wrong password with a friendly message', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Email or username').fill('admin@asternova.demo')
    await page.getByLabel('Password').fill('definitely-wrong')
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page.getByText(/Invalid email/i)).toBeVisible()
  })

  test('protects private routes from anonymous visitors', async ({ page }) => {
    await page.goto('/patients')
    await page.waitForURL('**/login')
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible()
  })

  test('demo account quick-fill populates the form', async ({ page }) => {
    await page.goto('/login')
    await page.getByRole('button', { name: /Hospital Admin/ }).click()
    await expect(page.getByLabel('Email or username')).toHaveValue('admin@asternova.demo')
    await expect(page.getByLabel('Password')).toHaveValue(DEMO_PASSWORD)
  })
})

test.describe('patient journey', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  test('lists patients and opens the full clinical profile', async ({ page }) => {
    await goTo(page, '/patients')
    await expect(page.getByRole('heading', { name: 'Patients' })).toBeVisible()
    await expect(page.getByRole('table')).toBeVisible()

    // Clicking a row opens the complete clinical profile.
    await page.getByRole('row').nth(1).click()
    await page.waitForURL(/\/patients\/\d+/)
    await expect(page.getByText('Patient information')).toBeVisible()
    await expect(page.getByRole('tab', { name: 'Timeline' })).toBeVisible()
    await expect(page.getByText('Record counts')).toBeVisible()
  })

  test('registers a new patient and sees it persist', async ({ page }) => {
    await goTo(page, '/patients')
    const uniqueName = `E2E Patient ${Date.now()}`

    await page.getByRole('button', { name: 'Register patient' }).click()
    await page.getByLabel('Full name').fill(uniqueName)
    await page.getByRole('textbox', { name: 'Phone', exact: true }).fill('+91 9847000000 (demo)')
    await page.getByRole('button', { name: 'Save' }).click()

    // The API accepted it and the dialog closed with a confirmation.
    await expect(page.getByText(/record created/i)).toBeVisible({ timeout: 20_000 })

    // The record is really stored: searching hits the database, not local state.
    await page.getByPlaceholder('Search…').first().fill(uniqueName)
    await expect(page.getByRole('cell', { name: uniqueName })).toBeVisible({ timeout: 20_000 })

    // And the new patient has a working profile page.
    await page.getByRole('row').nth(1).click()
    await page.waitForURL(/\/patients\/\d+/)
    await expect(page.getByText(uniqueName).first()).toBeVisible()
  })

  test('validates a too-short phone number on the server', async ({ page }) => {
    await goTo(page, '/patients')
    await page.getByRole('button', { name: 'Register patient' }).click()
    await page.getByLabel('Full name').fill('E2E Invalid Phone')
    await page.getByRole('textbox', { name: 'Phone', exact: true }).fill('12345')
    await page.getByRole('button', { name: 'Save' }).click()
    await expect(page.getByText(/at least 10 digits/i)).toBeVisible()
  })
})
