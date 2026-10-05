import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, Box, Grid, Skeleton, Chip, Stack, Typography } from '@mui/material'
import PeopleIcon from '@mui/icons-material/People'
import EventIcon from '@mui/icons-material/Event'
import LocalHospitalIcon from '@mui/icons-material/LocalHospital'
import BedIcon from '@mui/icons-material/Bed'
import ScienceIcon from '@mui/icons-material/Science'
import MedicationIcon from '@mui/icons-material/Medication'
import PaidIcon from '@mui/icons-material/Paid'
import ShieldIcon from '@mui/icons-material/Shield'
import api, { endpoints } from '../services/api.js'
import { StatCard, PageHeader, SectionCard, ErrorState } from '../components/ui.jsx'
import { Bars, PieBreakdown, TrendArea, TrendLine } from '../charts/Charts.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { formatCurrencyCompact, formatNumber, formatPercent } from '../utils/format.js'

export default function Dashboard() {
  const { user, hospital } = useAuth()
  const navigate = useNavigate()
  const [kpis, setKpis] = useState(null)
  const [charts, setCharts] = useState(null)
  const [error, setError] = useState(null)

  const load = () => {
    setError(null)
    Promise.all([api.get(endpoints.dashboard), api.get(endpoints.charts, { params: { days: 30 } })])
      .then(([dashboard, chartData]) => {
        setKpis(dashboard.data)
        setCharts(chartData.data)
      })
      .catch((err) => setError(err.friendlyMessage || 'Unable to load the dashboard.'))
  }

  useEffect(() => {
    load()
  }, [])

  if (error) return <ErrorState message={error} onRetry={load} />

  const k = kpis?.kpis || {}
  const label = (value, suffix = '') =>
    kpis ? `${formatNumber(value ?? 0)}${suffix}` : <Skeleton width={60} />
  const money = (value) =>
    kpis ? formatCurrencyCompact(value ?? 0) : <Skeleton width={70} />
  const percent = (value) =>
    kpis ? formatPercent(value ?? 0) : <Skeleton width={50} />
  // Hints must respect the loading state too, otherwise a card briefly pairs a
  // skeleton value with a real "0" and contradicts itself.
  const withHint = (hint) => (kpis ? hint : <Skeleton width={90} />)

  return (
    <Box>
      <PageHeader
        title={`Welcome, ${user?.first_name || user?.full_name || 'user'}`}
        subtitle={`${hospital?.name || 'AsterNova Multispeciality Hospital'} · live operational overview`}
        breadcrumb={user?.role_name}
      />
      <Box
        sx={{
          mb: 2,
          px: 1.5,
          py: 0.75,
          border: '1px solid #e3e8ef',
          borderRadius: 2,
          bgcolor: 'rgba(15, 118, 110, 0.04)',
        }}
      >
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          Demonstration environment — every patient, clinician, invoice and clinical record on this
          platform is fictional. Not for clinical use.
        </Typography>
      </Box>
      {kpis?.clinical ? (
        <Stack spacing={1.25} sx={{ mb: 2 }}>
          {kpis.clinical.critical_emergency > 0 ? (
            <Alert
              severity="error"
              variant="outlined"
              sx={{ bgcolor: 'rgba(185, 28, 28, 0.06)', borderColor: 'rgba(185, 28, 28, 0.28)' }}
            >
              {kpis.clinical.critical_emergency} critical emergency case(s) require immediate
              attention.
            </Alert>
          ) : null}
          {kpis.clinical.surgeries_in_progress > 0 || kpis.clinical.abnormal_lab_flags > 0 ? (
            <Alert
              severity="warning"
              variant="outlined"
              sx={{ bgcolor: 'rgba(180, 83, 9, 0.05)', borderColor: 'rgba(180, 83, 9, 0.25)' }}
            >
              {kpis.clinical.surgeries_in_progress > 0
                ? `${kpis.clinical.surgeries_in_progress} surgery in progress`
                : null}
              {kpis.clinical.surgeries_in_progress > 0 && kpis.clinical.abnormal_lab_flags > 0
                ? ' · '
                : null}
              {kpis.clinical.abnormal_lab_flags > 0
                ? `${kpis.clinical.abnormal_lab_flags} abnormal laboratory flag(s) awaiting review`
                : null}
            </Alert>
          ) : null}
        </Stack>
      ) : null}

      <Grid container spacing={2} sx={{ mb: 1 }}>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Total patients" value={label(k.total_patients)} icon={<PeopleIcon />} tone="neutral" onClick={() => navigate('/patients')} /></Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Today's appointments" value={label(k.todays_appointments)} icon={<EventIcon />} tone="neutral" onClick={() => navigate('/appointments')} /></Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Current inpatients" value={label(k.current_inpatients)} icon={<LocalHospitalIcon />} tone="neutral" onClick={() => navigate('/admissions')} /></Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Emergency visits today" value={label(k.emergency_patients)} icon={<LocalHospitalIcon />} tone="error" onClick={() => navigate('/emergency')} /></Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Available beds" value={`${formatNumber(k.available_beds ?? 0)} / ${formatNumber(k.total_beds ?? 0)}`} hint={withHint(`${formatPercent(k.bed_occupancy_rate)} occupied`)} icon={<BedIcon />} tone="neutral" onClick={() => navigate('/beds')} /></Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="ICU occupancy" value={percent(k.icu_occupancy_rate)} hint={withHint(`${formatNumber(k.icu_occupied ?? 0)} of ${formatNumber(k.icu_total ?? 0)} ICU beds in use`)} icon={<LocalHospitalIcon />} tone="neutral" onClick={() => navigate('/beds')} /></Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Pending lab reports" value={label(k.pending_lab_reports)} hint="Awaiting completion" icon={<ScienceIcon />} tone="warning" onClick={() => navigate('/laboratory')} /></Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Pharmacy alerts" value={label(k.pharmacy_alerts)} hint="Low or out of stock" icon={<MedicationIcon />} tone="warning" onClick={() => navigate('/pharmacy')} /></Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Revenue today" value={money(k.revenue_today)} hint={withHint(`Collected of ${formatCurrencyCompact(k.billed_today ?? 0)} billed`)} icon={<PaidIcon />} tone="success" onClick={() => navigate('/billing')} /></Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Pending bills" value={label(k.pending_bills)} hint="Awaiting payment" icon={<PaidIcon />} tone="warning" onClick={() => navigate('/billing')} /></Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Pending insurance claims" value={label(k.pending_insurance_claims)} hint="Submitted or under review" icon={<ShieldIcon />} tone="neutral" onClick={() => navigate('/insurance')} /></Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Pending discharges" value={label(k.ready_for_discharge)} hint={withHint(`${formatNumber(k.discharges_today ?? 0)} discharged today`)} icon={<LocalHospitalIcon />} tone="warning" onClick={() => navigate('/admissions')} /></Grid>
      </Grid>

      <SectionCard title="Hospital analytics" subtitle="Computed live from the seeded demo database" actions={<Chip size="small" label="Last 30 days" />}>
        <Box sx={{ pt: '16px' }}>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, lg: 6 }}><TrendArea title="Patient registration trend" data={charts?.patient_registration_trend || []} /></Grid>
          <Grid size={{ xs: 12, lg: 6 }}><TrendArea title="OPD visits" data={charts?.opd_trend || []} /></Grid>
          <Grid size={{ xs: 12, lg: 6 }}><TrendArea title="Emergency cases" data={charts?.emergency_trend || []} /></Grid>
          <Grid size={{ xs: 12, lg: 6 }}><TrendLine title="Revenue collected" data={charts?.revenue_trend || []} lines={[{ key: 'value', label: 'Revenue' }]} /></Grid>
          <Grid size={{ xs: 12, lg: 6 }}>
            <Bars
              title="OPD visits by department"
              data={(charts?.opd_by_department || []).map((row) => ({ name: row.department__name || 'Unassigned', total: row.total }))}
              xKey="name"
              bars={[{ key: 'total', label: 'Visits' }]}
              layout="vertical"
              height={320}
            />
          </Grid>
          <Grid size={{ xs: 12, lg: 6 }}>
            <Bars
              title="Bed occupancy by category"
              data={(charts?.bed_occupancy || []).map((row) => ({
                name: row.category.replaceAll('_', ' '), occupied: row.occupied, available: row.available,
              }))}
              xKey="name"
              bars={[
                { key: 'occupied', label: 'Occupied', colour: '#dc2626' },
                { key: 'available', label: 'Available', colour: '#15803d' },
              ]}
              height={320}
            />
          </Grid>
          <Grid size={{ xs: 12, lg: 6 }}>
            <PieBreakdown
              title="Department-wise patient distribution"
              data={(charts?.department_distribution || []).map((row) => ({ name: row.department__name || 'Unassigned', value: row.total }))}
              height={300}
            />
          </Grid>
          <Grid size={{ xs: 12, lg: 6 }}>
            <Bars
              title="Laboratory workload by category"
              data={(charts?.lab_workload || []).map((row) => ({ name: (row.test__category || 'other').replaceAll('_', ' '), total: row.total }))}
              xKey="name"
              bars={[{ key: 'total', label: 'Tests' }]}
              height={300}
            />
          </Grid>
          <Grid size={{ xs: 12, lg: 6 }}>
            <Bars
              title="Pharmacy stock by category"
              data={(charts?.pharmacy_stock || []).map((row) => ({ name: (row.category || 'other').replaceAll('_', ' '), units: row.units || 0 }))}
              xKey="name"
              bars={[{ key: 'units', label: 'Units in stock', colour: '#0f766e' }]}
              layout="vertical"
              height={320}
            />
          </Grid>
        </Grid>
        </Box>
      </SectionCard>
    </Box>
  )
}
