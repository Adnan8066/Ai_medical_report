import {
  Alert, Box, Card, CardContent, Chip, CircularProgress, Divider, Skeleton, Stack,
  Typography, alpha,
} from '@mui/material'
import InboxIcon from '@mui/icons-material/Inbox'
import { TOKENS } from '../theme.js'
import { formatNumber } from '../utils/format.js'

/** Page title block: breadcrumb, heading, context line and page actions. */
export function PageHeader({ title, subtitle, actions, breadcrumb }) {
  return (
    <Stack
      direction={{ xs: 'column', md: 'row' }}
      justifyContent="space-between"
      spacing={2}
      sx={{ mb: 2.5, alignItems: { xs: 'flex-start', md: 'center' } }}
    >
      <Box sx={{ minWidth: 0 }}>
        {breadcrumb ? (
          <Typography
            variant="overline"
            sx={{ display: 'block', color: 'text.secondary', lineHeight: 1.6 }}
          >
            {breadcrumb}
          </Typography>
        ) : null}
        <Typography variant="h5" sx={{ lineHeight: 1.25 }}>
          {title}
        </Typography>
        {subtitle ? (
          <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.25 }}>
            {subtitle}
          </Typography>
        ) : null}
      </Box>
      {actions ? (
        <Stack direction="row" spacing={1} sx={{ flexShrink: 0, alignItems: 'center' }}>
          {actions}
        </Stack>
      ) : null}
    </Stack>
  )
}

// Standard operational metrics share one soft blue tint; green, amber and red
// stay reserved for positive trend/financial values and clinical alerts.
// Tones default to `neutral`, so an omitted tone never reintroduces colour.
const STAT_TONE_COLOURS = {
  neutral: '#0369a1',
  primary: '#0369a1',
  secondary: '#0369a1',
  info: '#0369a1',
  success: '#15803d',
  warning: '#b45309',
  error: '#b91c1c',
}

/** KPI tile with a tinted icon badge, tabular value and optional context. */
export function StatCard({ label, value, hint, icon, tone = 'neutral', onClick, badge }) {
  const toneColour = STAT_TONE_COLOURS[tone] || STAT_TONE_COLOURS.neutral

  const display = typeof value === 'number' ? formatNumber(value) : value

  return (
    <Card
      onClick={onClick}
      sx={{
        height: '100%',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'border-color .15s ease, box-shadow .15s ease',
        '&:hover': onClick
          ? { borderColor: alpha(toneColour, 0.45), boxShadow: '0 4px 12px rgba(15,23,42,.06)' }
          : undefined,
      }}
    >
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={1}>
          <Box sx={{ minWidth: 0 }}>
            <Typography
              variant="overline"
              sx={{ color: 'text.secondary', display: 'block', lineHeight: 1.6 }}
            >
              {label}
            </Typography>
            <Typography
              variant="h5"
              className="numeric"
              sx={{ lineHeight: 1.2, fontSize: '1.5rem', mt: 0.25 }}
            >
              {display}
            </Typography>
            {hint ? (
              <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mt: 0.5 }}>
                {hint}
              </Typography>
            ) : null}
          </Box>
          <Stack alignItems="flex-end" spacing={0.5}>
            {icon ? (
              <Box
                sx={{
                  width: 38,
                  height: 38,
                  borderRadius: 2,
                  display: 'grid',
                  placeItems: 'center',
                  bgcolor: alpha(toneColour, 0.1),
                  color: toneColour,
                  fontSize: 20,
                  flexShrink: 0,
                }}
              >
                {icon}
              </Box>
            ) : null}
            {badge}
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  )
}

const STATUS_TONES = {
  available: 'success', active: 'success', completed: 'success', paid: 'success',
  dispensed: 'success', approved: 'success', settled: 'success', normal: 'success',
  on_duty: 'success', adequate: 'success',
  scheduled: 'info', confirmed: 'info', ordered: 'info', submitted: 'info',
  registered: 'info', in_progress: 'info', processing: 'info', under_review: 'info',
  admitted: 'info', low: 'info', draft: 'neutral',
  waiting: 'warning', pending: 'warning', partially_paid: 'warning', low_stock: 'warning',
  reserved: 'warning', expiring_soon: 'warning', ready_for_discharge: 'warning',
  high: 'warning', abnormal: 'warning', no_show: 'warning', under_treatment: 'warning',
  partially_approved: 'warning', partially_dispensed: 'warning', sample_collected: 'warning',
  critical: 'error', occupied: 'error', rejected: 'error', out_of_stock: 'error',
  expired: 'error', failed: 'error', inactive: 'error',
  cancelled: 'neutral', discharged: 'neutral', maintenance: 'neutral', cleaning: 'neutral',
  unknown: 'neutral', medium: 'info', off_duty: 'neutral', on_leave: 'warning',
}

const TONE_COLOURS = {
  success: '#15803d',
  warning: '#b45309',
  error: '#b91c1c',
  info: '#0369a1',
  neutral: '#475569',
}

const PRIORITY_COLOURS = {
  critical: TONE_COLOURS.error,
  high: TONE_COLOURS.warning,
  medium: TONE_COLOURS.info,
  low: TONE_COLOURS.success,
}

/** Soft tonal status pill - readable without shouting. */
export function StatusChip({ value, label }) {
  const key = String(value || '').toLowerCase()
  const tone = STATUS_TONES[key] || 'neutral'
  const colour = TONE_COLOURS[tone]
  const text = label || key.replaceAll('_', ' ') || '—'
  return (
    <Chip
      size="small"
      label={text}
      sx={{
        bgcolor: alpha(colour, 0.1),
        color: colour,
        border: `1px solid ${alpha(colour, 0.22)}`,
        textTransform: 'capitalize',
        fontWeight: 600,
      }}
    />
  )
}

export function PriorityChip({ value, label }) {
  const colour = PRIORITY_COLOURS[String(value).toLowerCase()] || TONE_COLOURS.neutral
  return (
    <Chip
      size="small"
      label={label || value}
      sx={{
        bgcolor: alpha(colour, 0.12),
        color: colour,
        border: `1px solid ${alpha(colour, 0.25)}`,
        textTransform: 'capitalize',
      }}
    />
  )
}

export function Loading({ label = 'Loading data…' }) {
  return (
    <Stack spacing={1.5} sx={{ py: 3 }}>
      <Stack direction="row" spacing={1.5} alignItems="center">
        <CircularProgress size={16} thickness={5} />
        <Typography variant="body2" color="text.secondary">{label}</Typography>
      </Stack>
      <Skeleton variant="rounded" height={72} />
      <Skeleton variant="rounded" height={180} />
    </Stack>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <Alert
      severity="error"
      sx={{ mb: 2 }}
      action={
        onRetry ? (
          <Chip size="small" label="Retry" onClick={onRetry} sx={{ cursor: 'pointer' }} />
        ) : null
      }
    >
      {message || 'Unable to load data.'}
    </Alert>
  )
}

export function EmptyState({ title = 'Nothing to show yet', description }) {
  return (
    <Box sx={{ textAlign: 'center', py: 7, px: 2 }}>
      <InboxIcon sx={{ fontSize: 40, color: TOKENS.borderStrong, mb: 1 }} />
      <Typography variant="subtitle2">{title}</Typography>
      {description ? (
        <Typography variant="body2" color="text.secondary">{description}</Typography>
      ) : null}
    </Box>
  )
}

/** Card with an optional titled header, used for every content section. */
export function SectionCard({ title, subtitle, actions, children, dense }) {
  return (
    <Card sx={{ mb: 2.5 }}>
      <CardContent sx={dense ? { p: 1.5, '&:last-child': { pb: 1.5 } } : undefined}>
        {title ? (
          <>
            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              justifyContent="space-between"
              spacing={1}
              sx={{ mb: 1.5, alignItems: { sm: 'center' } }}
            >
              <Box>
                <Typography variant="subtitle1">{title}</Typography>
                {subtitle ? (
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    {subtitle}
                  </Typography>
                ) : null}
              </Box>
              {actions ? (
                <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                  {actions}
                </Stack>
              ) : null}
            </Stack>
            <Divider sx={{ mb: 2 }} />
          </>
        ) : null}
        {children}
      </CardContent>
    </Card>
  )
}

/** Label/value pair used across detail panels. */
export function Field({ label, value, mono }) {
  return (
    <Box sx={{ minWidth: 132 }}>
      <Typography
        variant="caption"
        sx={{ color: 'text.secondary', display: 'block', textTransform: 'uppercase', letterSpacing: '.05em', fontSize: '.6875rem', fontWeight: 600 }}
      >
        {label}
      </Typography>
      <Typography variant="body2" className={mono ? 'mono' : undefined} sx={{ mt: 0.25 }}>
        {value === null || value === undefined || value === '' ? '—' : value}
      </Typography>
    </Box>
  )
}

/** Standard "this is fabricated data" notice. */
export function DemoNotice({ children }) {
  return (
    <Alert severity="info" variant="outlined" sx={{ mb: 2, bgcolor: alpha('#0369a1', 0.04) }}>
      {children ||
        'All patients, clinicians, staff, insurers and records in this platform are fictional demo data.'}
    </Alert>
  )
}
