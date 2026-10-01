import { useCallback, useEffect, useState } from 'react'
import {
  Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Grid, MenuItem,
  Stack, TextField, Tooltip, Typography,
} from '@mui/material'
import api, { endpoints } from '../services/api.js'
import { DemoNotice, ErrorState, Loading, PageHeader, SectionCard, StatCard } from '../components/ui.jsx'
import { Bars } from '../charts/Charts.jsx'
import BedIcon from '@mui/icons-material/Bed'
import PersonIcon from '@mui/icons-material/Person'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import BookmarkIcon from '@mui/icons-material/Bookmark'
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart'

const COLOURS = {
  available: '#15803d',
  occupied: '#dc2626',
  reserved: '#d97706',
  maintenance: '#64748b',
  cleaning: '#0891b2',
}

export default function Beds() {
  const [stats, setStats] = useState(null)
  const [board, setBoard] = useState([])
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState({ category: '', status: '' })
  const [selected, setSelected] = useState(null)
  const [patients, setPatients] = useState([])
  const [patientId, setPatientId] = useState('')
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    setError(null)
    Promise.all([api.get(`${endpoints.beds}stats/`), api.get(`${endpoints.beds}board/`)])
      .then(([statsResponse, boardResponse]) => {
        setStats(statsResponse.data)
        setBoard(boardResponse.data.wards || [])
      })
      .catch((err) => setError(err.friendlyMessage || 'Unable to load the bed board.'))
  }, [])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    api
      .get(endpoints.patients, { params: { admission_status: 'not_admitted', page_size: 100 } })
      .then(({ data }) => setPatients(data.results || []))
      .catch(() => undefined)
  }, [])

  const act = async (action, payload) => {
    if (!selected) return
    setBusy(true)
    try {
      await api.post(`${endpoints.beds}${selected.id}/${action}/`, payload || {})
      setSelected(null)
      setPatientId('')
      load()
    } catch (err) {
      window.alert(err.response?.data?.detail || err.friendlyMessage || 'Action failed.')
    } finally {
      setBusy(false)
    }
  }

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!stats) return <Loading label="Loading bed occupancy…" />

  const matches = (bed) =>
    (!filters.category || bed.category === filters.category) &&
    (!filters.status || bed.status === filters.status)

  return (
    <Box>
      <PageHeader
        title="Bed Management"
        subtitle="Live occupancy across all wards, categories and maintenance states"
        breadcrumb="Clinical"
      />
      <DemoNotice>Bed assignments shown here are fictional demo allocations.</DemoNotice>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid size={{ xs: 12, sm: 6, lg: 2.4 }}><StatCard label="Total beds" value={stats.total} icon={<BedIcon />} /></Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 2.4 }}><StatCard label="Occupied" value={stats.occupied} hint={`${stats.occupancy_rate}% occupancy`} tone="error" icon={<PersonIcon />} /></Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 2.4 }}><StatCard label="Available" value={stats.available} tone="success" icon={<CheckCircleIcon />} /></Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 2.4 }}><StatCard label="Reserved" value={stats.reserved} tone="warning" icon={<BookmarkIcon />} /></Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 2.4 }}><StatCard label="ICU occupancy" value={`${stats.icu.occupancy_rate}%`} hint={`${stats.icu.available} of ${stats.icu.total} free`} tone="info" icon={<MonitorHeartIcon />} /></Grid>
      </Grid>

      <SectionCard title="Occupancy by category">
        <Bars
          data={(stats.by_category || []).map((row) => ({
            name: row.label, Occupied: row.occupied, Available: row.available,
            Reserved: row.reserved, Maintenance: row.maintenance,
          }))}
          xKey="name"
          bars={[
            { key: 'Occupied', label: 'Occupied', colour: '#dc2626' },
            { key: 'Available', label: 'Available', colour: '#15803d' },
            { key: 'Reserved', label: 'Reserved', colour: '#d97706' },
            { key: 'Maintenance', label: 'Maintenance', colour: '#64748b' },
          ]}
          height={300}
        />
      </SectionCard>

      <SectionCard
        title="Bed board"
        subtitle="Click a bed to assign a patient, release it or change its status"
        actions={
          <Stack direction="row" spacing={1}>
            <TextField
              select size="small" label="Category" value={filters.category}
              onChange={(event) => setFilters({ ...filters, category: event.target.value })}
              sx={{ minWidth: 170 }}
            >
              <MenuItem value="">All</MenuItem>
              {['general', 'semi_private', 'private', 'icu', 'emergency', 'pediatric', 'maternity', 'isolation'].map((value) => (
                <MenuItem key={value} value={value}>{value.replaceAll('_', ' ')}</MenuItem>
              ))}
            </TextField>
            <TextField
              select size="small" label="Status" value={filters.status}
              onChange={(event) => setFilters({ ...filters, status: event.target.value })}
              sx={{ minWidth: 150 }}
            >
              <MenuItem value="">All</MenuItem>
              {['available', 'occupied', 'reserved', 'maintenance', 'cleaning'].map((value) => (
                <MenuItem key={value} value={value}>{value}</MenuItem>
              ))}
            </TextField>
          </Stack>
        }
      >
        <Stack direction="row" spacing={1.5} sx={{ mb: 2, flexWrap: 'wrap', gap: 1 }}>
          {Object.entries(COLOURS).map(([status, colour]) => (
            <Chip
              key={status}
              size="small"
              label={status}
              sx={{ bgcolor: colour, color: '#fff', textTransform: 'capitalize' }}
            />
          ))}
        </Stack>

        {board.map((group) => {
          const beds = (group.beds || []).filter(matches)
          if (!beds.length) return null
          return (
            <Box key={group.ward.id ?? 'unassigned'} sx={{ mb: 2.5 }}>
              <Typography variant="subtitle2">
                {group.ward.name} <Typography component="span" variant="caption" color="text.secondary">
                  {group.ward.code} · {beds.length} bed(s)
                </Typography>
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.8, mt: 1 }}>
                {beds.map((bed) => (
                  <Tooltip
                    key={bed.id}
                    title={`${bed.bed_number} · ${bed.category_label} · ${bed.status_label}${bed.patient_name ? ` · ${bed.patient_name}` : ''}`}
                  >
                    <Box
                      onClick={() => setSelected(bed)}
                      sx={{
                        width: 78, p: 0.8, borderRadius: 1.5, cursor: 'pointer',
                        border: '1px solid #e2e8f0', borderLeft: `4px solid ${COLOURS[bed.status] || '#94a3b8'}`,
                        bgcolor: bed.status === 'occupied' ? '#fef2f2' : '#f8fafc',
                        '&:hover': { boxShadow: 2 },
                      }}
                    >
                      <Typography variant="caption" sx={{ fontWeight: 600, display: 'block' }}>
                        {bed.bed_number}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" noWrap>
                        {bed.patient_name || bed.status}
                      </Typography>
                    </Box>
                  </Tooltip>
                ))}
              </Box>
            </Box>
          )
        })}
      </SectionCard>

      <Dialog open={Boolean(selected)} onClose={() => setSelected(null)} maxWidth="xs" fullWidth>
        <DialogTitle>
          Bed {selected?.bed_number}
          <Typography variant="caption" display="block" color="text.secondary">
            {selected?.ward_name} · {selected?.category_label} · {selected?.status_label}
            {selected?.patient_name ? ` · ${selected.patient_name} (${selected.patient_code})` : ''}
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              select size="small" label="Assign patient" value={patientId}
              onChange={(event) => setPatientId(event.target.value)}
              helperText="Only patients not currently admitted are listed"
            >
              <MenuItem value="">—</MenuItem>
              {patients.map((patient) => (
                <MenuItem key={patient.id} value={patient.id}>
                  {patient.patient_id} · {patient.name}
                </MenuItem>
              ))}
            </TextField>
            <Button
              variant="contained"
              disabled={!patientId || busy}
              onClick={() => act('assign', { patient: Number(patientId) })}
            >
              Assign patient
            </Button>
            <Button color="warning" disabled={busy} onClick={() => act('release')}>
              Release / send for cleaning
            </Button>
            <Button color="inherit" disabled={busy} onClick={() => act('set_status', { status: 'maintenance' })}>
              Mark under maintenance
            </Button>
            <Button color="success" disabled={busy} onClick={() => act('set_status', { status: 'available' })}>
              Mark available
            </Button>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelected(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
