/**
 * Shared display formatters.
 *
 * Centralising these keeps dates, money and statuses consistent across every
 * module, which is what makes a data-heavy product look deliberate rather than
 * assembled screen by screen.
 */

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function toDate(value) {
  if (!value) return null
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

/** 2026-09-27 -> 27 Sep 2026 */
export function formatDate(value) {
  const date = toDate(value)
  if (!date) return '—'
  return `${String(date.getDate()).padStart(2, '0')} ${MONTHS[date.getMonth()]} ${date.getFullYear()}`
}

/** ISO timestamp -> 27 Sep 2026, 14:35 */
export function formatDateTime(value, { seconds = false } = {}) {
  const date = toDate(value)
  if (!date) return '—'
  const time = `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  const suffix = seconds ? `:${String(date.getSeconds()).padStart(2, '0')}` : ''
  return `${formatDate(date)}, ${time}${suffix}`
}

/** 14:35 from a time string or ISO timestamp. */
export function formatTime(value) {
  if (typeof value === 'string' && /^\d{2}:\d{2}/.test(value)) return value.slice(0, 5)
  const date = toDate(value)
  if (!date) return '—'
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

/** 58035.6 -> ₹58,035.60 (Indian digit grouping, two decimals). */
export function formatCurrency(value, { symbol = '₹', decimals = 2 } = {}) {
  const amount = Number(value)
  if (value === null || value === undefined || Number.isNaN(amount)) return '—'
  return `${symbol}${amount.toLocaleString('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}`
}

/** Compact money for KPI cards: ₹5.8L / ₹1.2Cr. */
export function formatCurrencyCompact(value, symbol = '₹') {
  const amount = Number(value)
  if (value === null || value === undefined || Number.isNaN(amount)) return '—'
  if (Math.abs(amount) >= 1e7) return `${symbol}${(amount / 1e7).toFixed(2)} Cr`
  if (Math.abs(amount) >= 1e5) return `${symbol}${(amount / 1e5).toFixed(2)} L`
  return formatCurrency(amount, { symbol, decimals: 0 })
}

export function formatNumber(value, decimals = 0) {
  const amount = Number(value)
  if (value === null || value === undefined || Number.isNaN(amount)) return '—'
  return amount.toLocaleString('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

export function formatPercent(value, decimals = 0) {
  const amount = Number(value)
  if (value === null || value === undefined || Number.isNaN(amount)) return '—'
  return `${amount.toFixed(decimals)}%`
}

/** snake_case / SCREAMING to Sentence case. */
export function titleCase(value) {
  if (value === null || value === undefined) return '—'
  return String(value)
    .replaceAll('_', ' ')
    .toLowerCase()
    .replace(/\b[a-z]/g, (letter) => letter.toUpperCase())
}

export function truncate(value, length = 48) {
  if (value === null || value === undefined) return '—'
  const text = String(value)
  return text.length > length ? `${text.slice(0, length - 1)}…` : text
}

/** Whole years and months since a date, e.g. "18 y 4 m". */
export function formatDuration(fromDate, toDateValue = new Date()) {
  const start = toDate(fromDate)
  const end = toDate(toDateValue)
  if (!start || !end) return '—'
  let years = end.getFullYear() - start.getFullYear()
  let months = end.getMonth() - start.getMonth()
  if (end.getDate() < start.getDate()) months -= 1
  if (months < 0) {
    years -= 1
    months += 12
  }
  return `${years} y ${months} m`
}

/** Differences in days, for length-of-stay style values. */
export function formatDays(value) {
  const days = Number(value)
  if (value === null || value === undefined || Number.isNaN(days)) return '—'
  return days === 1 ? '1 day' : `${days} days`
}
