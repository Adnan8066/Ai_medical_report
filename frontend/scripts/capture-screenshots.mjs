/**
 * Capture README screenshots of the running platform.
 *
 * Usage (with the Django backend and the Vite dev server already running):
 *   node scripts/capture-screenshots.mjs
 *
 * Override the target with E2E_BASE_URL, or set DEMO_EMAIL / DEMO_PASSWORD.
 */
import { chromium } from '@playwright/test'
import { mkdirSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const outputDir = resolve(here, '../../docs/screenshots')
const baseURL = process.env.E2E_BASE_URL || 'http://localhost:5173'
const email = process.env.DEMO_EMAIL || 'admin@asternova.demo'
const password = process.env.DEMO_PASSWORD || 'AsterNova@2024'

const pages = [
  { file: '01-dashboard.png', path: '/dashboard', wait: 4500 },
  { file: '02-patients.png', path: '/patients', wait: 3000 },
  { file: '03-patient-profile.png', path: null, wait: 3000 },
  { file: '04-bed-management.png', path: '/beds', wait: 5000 },
  { file: '05-emergency.png', path: '/emergency', wait: 3500 },
  { file: '06-documents.png', path: '/documents', wait: 3500 },
  { file: '07-ai-assistant.png', path: '/assistant', wait: 2500 },
  { file: '08-analytics.png', path: '/analytics', wait: 4500 },
  { file: '09-navigation.png', path: '/navigation', wait: 3000 },
  { file: '10-blood-bank.png', path: '/blood-bank', wait: 3000 },
  { file: '11-audit-logs.png', path: '/audit', wait: 3000 },
  { file: '12-shift-roster.png', path: '/roster', wait: 3000 },
  { file: '13-settings.png', path: '/settings', wait: 3000 },
  { file: '14-patient-portal.png', path: '/portal', wait: 3500 },
]

mkdirSync(outputDir, { recursive: true })

const browser = await chromium.launch()
const context = await browser.newContext({
  viewport: { width: 1600, height: 1000 },
  deviceScaleFactor: 1,
})
const page = await context.newPage()

await page.goto(`${baseURL}/login`)
await page.getByLabel('Email or username').fill(email)
await page.getByLabel('Password').fill(password)
await page.getByRole('button', { name: 'Sign in' }).click()
await page.waitForURL('**/dashboard')
await page.waitForTimeout(4000)

// The patient profile needs a real id, so open the first patient first.
await page.goto(`${baseURL}/patients`)
await page.waitForTimeout(2500)
await page.getByRole('row').nth(1).click()
await page.waitForURL(/\/patients\/\d+/)
const patientProfileUrl = page.url()

for (const target of pages) {
  await page.goto(target.path ? `${baseURL}${target.path}` : patientProfileUrl)
  await page.waitForTimeout(target.wait)
  await page.screenshot({ path: resolve(outputDir, target.file), fullPage: false })
  console.log('captured', target.file)
}

await browser.close()
console.log(`\nScreenshots written to ${outputDir}`)
