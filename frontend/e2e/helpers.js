export const DEMO_EMAIL = process.env.E2E_DEMO_EMAIL || 'admin@asternova.demo'
export const DEMO_PASSWORD = process.env.DEMO_PASSWORD || 'AsterNova@2024'

/** Sign in through the real login form and wait for the dashboard to render. */
export async function login(page, email = DEMO_EMAIL, password = DEMO_PASSWORD) {
  await page.goto('/login')
  await page.getByLabel('Email or username').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await page.waitForURL('**/dashboard', { timeout: 30_000 })
  await page.getByText('Total patients').first().waitFor()
}

/** Navigate using the sidebar and wait for the URL to change. */
export async function goTo(page, path) {
  await page.goto(path)
  await page.waitForLoadState('networkidle')
}
