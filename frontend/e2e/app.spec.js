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

    // Revenue must use the readable regional compact form, never the bare
    // "₹6.99 L" shorthand.
    const revenue = page.locator('text=Revenue today').locator('..')
    await expect(revenue).toContainText(/₹[\d.]+\s*(Lakhs|Cr)/)
    await expect(revenue).not.toContainText(/₹[\d.]+\sL\b/)

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
    await page.getByRole('button', { name: 'Create record' }).click()

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
    await page.getByRole('button', { name: 'Create record' }).click()
    await expect(page.getByText(/at least 10 digits/i)).toBeVisible()
  })
})

test.describe('dashboard clinical presentation', () => {
  test('separates critical alerts from non-critical warnings', async ({ page }) => {
    await login(page)

    // Critical emergency cases must never share the amber warning treatment.
    const critical = page.locator('.MuiAlert-colorError').filter({ hasText: /critical emergency/i })
    await expect(critical).toBeVisible()

    // The amber bar carries only review-type notices.
    const warning = page.locator('.MuiAlert-standardWarning')
    if (await warning.count()) {
      await expect(warning.first()).not.toContainText(/critical emergency/i)
    }
  })

  test('keeps the demo disclaimer visible without a sidebar pill', async ({ page }) => {
    await login(page)

    await expect(page.getByText(/not for clinical use/i).first()).toBeVisible()

    // The prominent orange pill is gone: the nav now carries only plain
    // footer text, with no bordered amber chip above the menu items.
    const nav = page.locator('.MuiDrawer-paper').first()
    const chips = nav.locator('.MuiChip-root')
    await expect(chips).toHaveCount(0)
  })

  test('shows pending discharges without contradicting the daily count', async ({ page }) => {
    await login(page)

    const card = page.locator('text=Pending discharges').first()
      .locator('xpath=ancestor::*[contains(@class,"MuiCard-root")]')
    await expect(card).toBeVisible()
    // Wait out the skeleton before reading the values.
    await expect(card.locator('.MuiSkeleton-root')).toHaveCount(0, { timeout: 20_000 })

    // The label renders uppercased by CSS, so match case-insensitively.
    const value = (await card.innerText()).replace(/\s+/g, ' ')
    const pending = Number(value.match(/pending discharges (\d+)/i)?.[1])
    const discharged = Number(value.match(/(\d+) discharged today/i)?.[1])

    expect(Number.isNaN(pending)).toBe(false)
    expect(pending).toBeGreaterThan(0)
    expect(discharged).toBeGreaterThanOrEqual(0)
  })

  test('keeps the pending lab queue proportional to inpatient volume', async ({ page }) => {
    await login(page)

    const read = async (label) => {
      const card = page.locator(`text=${label}`).first()
        .locator('xpath=ancestor::*[contains(@class,"MuiCard-root")]')
      await expect(card.locator('.MuiSkeleton-root')).toHaveCount(0, { timeout: 20_000 })
      const text = (await card.innerText()).replace(/\s+/g, ' ')
      return Number(text.match(/(\d[\d,]*)/)?.[1].replace(/,/g, ''))
    }

    const inpatients = await read('Current inpatients')
    const pendingLabs = await read('Pending lab reports')

    expect(inpatients).toBeGreaterThan(0)
    // A realistic lab backlog stays well under one report per inpatient.
    expect(pendingLabs).toBeLessThan(inpatients)
  })
})
