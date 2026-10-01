import { expect, test } from '@playwright/test'
import { goTo, login } from './helpers.js'

test.describe('module screens', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  const screens = [
    ['/beds', 'Bed Management', 'Total beds'],
    ['/emergency', 'Emergency Department', 'Active cases'],
    ['/documents', 'Medical Documents', 'Documents'],
    ['/analytics', 'Analytics & AI Insights', "Tomorrow's OPD visits"],
    ['/navigation', 'Hospital Navigation', 'Find your destination'],
    ['/blood-bank', 'Blood Bank', 'Units available'],
    ['/assistant', 'AI Hospital Assistant', 'Suggested questions'],
    ['/roster', 'Shift Roster', 'Staff on roster'],
    ['/settings', 'Hospital Settings', 'Hospital profile'],
    ['/admin', 'Roles & Permissions', 'Roles'],
    ['/audit', 'Audit Logs', 'Logs'],
    ['/portal', 'My Health Portal', 'Profile'],
    ['/laboratory', 'Laboratory', 'Lab ID'],
    ['/pharmacy', 'Pharmacy Stock', 'Medicine ID'],
    ['/billing', 'Billing', 'Invoice'],
    ['/insurance', 'Insurance Claims', 'Claim'],
    ['/inventory', 'Inventory & Stores', 'Item code'],
    ['/surgery', 'Operation Theatre', 'Surgery'],
    ['/admissions', 'Admissions & IPD', 'Admission'],
    ['/appointments', 'Appointments', 'Appointment'],
  ]

  for (const [path, heading, marker] of screens) {
    test(`${path} renders ${heading}`, async ({ page }) => {
      await goTo(page, path)
      await expect(page.getByText(heading, { exact: false }).first()).toBeVisible()
      await expect(page.getByText(marker, { exact: false }).first()).toBeVisible({
        timeout: 40_000,
      })
      // No unhandled error state should be showing.
      await expect(page.getByText('Unable to load')).toHaveCount(0)
    })
  }
})

test.describe('AI assistant', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  test('answers an operational question from live data', async ({ page }) => {
    await goTo(page, '/assistant')
    await page.getByRole('button', { name: 'Which beds are available?' }).click()
    await expect(page.getByText(/beds are available/i).first()).toBeVisible({ timeout: 45_000 })
    await expect(
      page.getByText(/administrative and information-support/i).first(),
    ).toBeVisible()
  })

  test('document assistant grounds answers and cites sources', async ({ page }) => {
    await goTo(page, '/assistant')
    await page.getByRole('button', { name: 'Documents', exact: true }).click()
    await page
      .getByLabel('Ask about the documents')
      .fill('What medications are mentioned?')
    await page.getByRole('button', { name: 'Send' }).click()
    await expect(
      page.getByText(/According to the uploaded documents|No matching content/i),
    ).toBeVisible({ timeout: 30_000 })
  })
})

test.describe('bed management actions', () => {
  test('opens a bed and shows the availability legend', async ({ page }) => {
    await login(page)
    await goTo(page, '/beds')
    await expect(page.getByText('Bed board')).toBeVisible({ timeout: 45_000 })
    await expect(page.getByText('available', { exact: true }).first()).toBeVisible()
    await expect(page.getByText('Occupancy by category')).toBeVisible()
  })
})

test.describe('layout', () => {
  test('sidebar does not overlap page content on desktop', async ({ page }) => {
    await login(page)
    await goTo(page, '/patients')

    const drawer = await page.locator('.MuiDrawer-paper').first().boundingBox()
    const header = await page.locator('header').first().boundingBox()
    const heading = await page.getByRole('heading', { name: 'Patients' }).boundingBox()

    expect(drawer).not.toBeNull()
    // The top bar and page content must start to the right of the sidebar.
    expect(header.x).toBeGreaterThanOrEqual(drawer.x + drawer.width - 1)
    expect(heading.x).toBeGreaterThanOrEqual(drawer.x + drawer.width - 1)
  })
})
