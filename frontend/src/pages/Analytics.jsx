import { useCallback, useEffect, useState } from 'react'
import { Alert, Box, Chip, Grid, Stack, Typography } from '@mui/material'
import api, { endpoints } from '../services/api.js'
import { ErrorState, Loading, PageHeader, SectionCard, StatCard } from '../components/ui.jsx'
import { Bars, PieBreakdown, TrendArea, TrendLine } from '../charts/Charts.jsx'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import MedicalServicesIcon from '@mui/icons-material/MedicalServices'
import LocalHospitalIcon from '@mui/icons-material/LocalHospital'
import BedIcon from '@mui/icons-material/Bed'

export default function Analytics() {
  const [charts, setCharts] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [days, setDays] = useState(30)
  const [error, setError] = useState(null)

  const load = useCallback(() => {
    setError(null)
    Promise.all([
      api.get(endpoints.charts, { params: { days } }),
      api.get(endpoints.forecast, { params: { days: 7, history: days } }),
    ])
      .then(([chartsResponse, forecastResponse]) => {
        setCharts(chartsResponse.data)
        setForecast(forecastResponse.data)
      })
      .catch((err) => setError(err.friendlyMessage || 'Unable to load analytics.'))
  }, [days])

  useEffect(() => {
    load()
  }, [load])

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!charts || !forecast) return <Loading label="Crunching the numbers…" />

  const estimates = forecast.estimates
  const next = (series) => series?.daily?.[0] ?? 0

  return (
    <Box>
      <PageHeader
        title="Analytics & AI Insights"
        subtitle={`Operational analytics across the last ${days} days, with trend estimates`}
        breadcrumb="Overview"
        actions={
          <Stack direction="row" spacing={1}>
            {[14, 30, 60].map((value) => (
              <Chip
                key={value}
                label={`${value} days`}
                color={days === value ? 'primary' : 'default'}
                onClick={() => setDays(value)}
              />
            ))}
          </Stack>
        }
      />

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <StatCard label="Tomorrow's registrations" value={next(estimates.patient_registrations)} hint={estimates.patient_registrations.unit} icon={<TrendingUpIcon />} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <StatCard label="Tomorrow's OPD visits" value={next(estimates.opd_volume)} hint={estimates.opd_volume.unit} tone="secondary" icon={<MedicalServicesIcon />} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <StatCard label="Tomorrow's emergency load" value={next(estimates.emergency_workload)} hint={estimates.emergency_workload.unit} tone="error" icon={<LocalHospitalIcon />} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <StatCard label="Projected bed occupancy" value={`${estimates.bed_occupancy.projected_rate}%`} hint={`Current ${estimates.bed_occupancy.current_rate}%`} tone="warning" icon={<BedIcon />} />
        </Grid>
      </Grid>

      <SectionCard title="AI operational forecasts" subtitle="Least-squares trend estimates over historical demo activity">
        <Alert severity="warning" sx={{ mb: 2 }}>{forecast.disclaimer}</Alert>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, lg: 6 }}>
            <TrendLine
              title="Patient registrations (history + next 7 days)"
              data={[
                ...estimates.patient_registrations.history.map((value, index) => ({ label: `-${estimates.patient_registrations.history.length - index}d`, history: value })),
                ...estimates.patient_registrations.daily.map((value, index) => ({ label: `+${index + 1}d`, estimate: value })),
              ]}
              lines={[
                { key: 'history', label: 'Actual', colour: '#0f766e' },
                { key: 'estimate', label: 'Estimate', colour: '#d97706' },
              ]}
              height={260}
            />
          </Grid>
          <Grid size={{ xs: 12, lg: 6 }}>
            <TrendLine
              title="Emergency workload (history + next 7 days)"
              data={[
                ...estimates.emergency_workload.history.map((value, index) => ({ label: `-${estimates.emergency_workload.history.length - index}d`, history: value })),
                ...estimates.emergency_workload.daily.map((value, index) => ({ label: `+${index + 1}d`, estimate: value })),
              ]}
              lines={[
                { key: 'history', label: 'Actual', colour: '#1d4ed8' },
                { key: 'estimate', label: 'Estimate', colour: '#dc2626' },
              ]}
              height={260}
            />
          </Grid>
        </Grid>
      </SectionCard>

      <SectionCard title="Pharmacy demand watchlist">
        {estimates.pharmacy_demand.top_low_stock.length ? (
          <Bars
            data={estimates.pharmacy_demand.top_low_stock.map((item) => ({
              name: item.name.length > 26 ? `${item.name.slice(0, 24)}…` : item.name,
              Stock: item.stock,
              'Reorder level': item.reorder_level,
            }))}
            xKey="name"
            bars={[
              { key: 'Stock', label: 'Stock', colour: '#0f766e' },
              { key: 'Reorder level', label: 'Reorder level', colour: '#d97706' },
            ]}
            height={320}
            subtitle={`${estimates.pharmacy_demand.low_stock_items} items at or below the reorder level`}
          />
        ) : (
          <Typography variant="body2" color="text.secondary">No pharmacy items are below the reorder level.</Typography>
        )}
      </SectionCard>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 6 }}>
          <SectionCard title="Patient registration trend">
            <TrendArea data={charts.patient_registration_trend} height={240} />
          </SectionCard>
        </Grid>
        <Grid size={{ xs: 12, lg: 6 }}>
          <SectionCard title="Revenue collected">
            <TrendArea data={charts.revenue_trend} yKey="value" height={240} />
          </SectionCard>
        </Grid>
        <Grid size={{ xs: 12, lg: 6 }}>
          <SectionCard title="Department-wise patient distribution">
            <PieBreakdown
              data={(charts.department_distribution || []).map((row) => ({
                name: row.department__name || 'Unassigned', value: row.total,
              }))}
              height={280}
            />
          </SectionCard>
        </Grid>
        <Grid size={{ xs: 12, lg: 6 }}>
          <SectionCard title="Laboratory workload">
            <Bars
              data={(charts.lab_workload || []).map((row) => ({
                name: (row.test__category || 'other').replaceAll('_', ' '), Tests: row.total,
              }))}
              xKey="name"
              bars={[{ key: 'Tests', label: 'Tests' }]}
              height={280}
            />
          </SectionCard>
        </Grid>
        <Grid size={{ xs: 12, lg: 6 }}>
          <SectionCard title="Appointment status mix">
            <PieBreakdown
              data={(charts.appointment_status || []).map((row) => ({
                name: row.status.replaceAll('_', ' '), value: row.total,
              }))}
              height={280}
            />
          </SectionCard>
        </Grid>
        <Grid size={{ xs: 12, lg: 6 }}>
          <SectionCard title="Admission status mix">
            <PieBreakdown
              data={(charts.admission_status || []).map((row) => ({
                name: row.status.replaceAll('_', ' '), value: row.total,
              }))}
              height={280}
            />
          </SectionCard>
        </Grid>
      </Grid>
    </Box>
  )
}
