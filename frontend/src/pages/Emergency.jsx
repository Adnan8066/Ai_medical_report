import { useCallback, useEffect, useState } from 'react'
import {
  Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Grid, MenuItem,
  Stack, TextField, Typography,
} from '@mui/material'
import api, { endpoints } from '../services/api.js'
import {
  DemoNotice, ErrorState, Field, Loading, PageHeader, PriorityChip, SectionCard, StatCard, StatusChip,
} from '../components/ui.jsx'
import { TrendArea } from '../charts/Charts.jsx'
import AmbulanceIcon from '@mui/icons-material/LocalHospital'
import FavoriteIcon from '@mui/icons-material/Favorite'
import TimerIcon from '@mui/icons-material/Timer'
import MeetingRoomIcon from '@mui/icons-material/MeetingRoom'

export default function Emergency() {
  const [board, setBoard] = useState(null)
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(null)
  const [busy, setBusy] = useState(false)
  const [statusValue, setStatusValue] = useState('')
  const [priorityValue, setPriorityValue] = useState('')

  const load = useCallback(() => {
    setError(null)
    Promise.all([api.get(`${endpoints.emergency}board/`), api.get(`${endpoints.emergency}stats/`)])
      .then(([boardResponse, statsResponse]) => {
        setBoard(boardResponse.data)
        setStats(statsResponse.data)
      })
      .catch((err) => setError(err.friendlyMessage || 'Unable to load the emergency board.'))
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const updateStatus = async () => {
    if (!selected || !statusValue) return
    setBusy(true)
    try {
      await api.patch(`${endpoints.emergency}${selected.id}/`, {
        status: statusValue,
        priority: priorityValue || selected.priority,
      })
      setSelected(null)
      setStatusValue('')
      setPriorityValue('')
      load()
    } catch (err) {
      window.alert(err.friendlyMessage || 'Unable to update the case.')
    } finally {
      setBusy(false)
    }
  }

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!board || !stats) return <Loading label="Loading emergency department…" />

  return (
    <Box>
      <PageHeader
        title="Emergency Department"
        subtitle={`Live triage board · generated ${String(board.generated_at).slice(0, 16).replace('T', ' ')}`}
        breadcrumb="Clinical"
      />
      <DemoNotice>All emergency cases are fictional demo records.</DemoNotice>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Active cases" value={board.active_count} icon={<AmbulanceIcon />} tone="error" /></Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Critical today" value={stats.critical} hint={`${stats.high} high priority`} icon={<FavoriteIcon />} tone="error" /></Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="Average wait" value={`${board.average_wait_minutes} min`} hint={`Longest ${board.longest_wait_minutes} min`} icon={<TimerIcon />} tone="warning" /></Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}><StatCard label="In treatment" value={stats.in_treatment} hint={`${stats.admitted} admitted today`} icon={<MeetingRoomIcon />} tone="info" /></Grid>
      </Grid>

      <SectionCard title="Emergency cases (last 14 days)">
        <TrendArea
          data={(stats.trend || []).map((row) => ({
            label: String(row.arrival_time__date).slice(5),
            total: row.total,
          }))}
          height={220}
        />
      </SectionCard>

      {['critical', 'high', 'medium', 'low'].map((priority) => {
        const group = board.by_priority?.[priority]
        if (!group) return null
        return (
          <SectionCard
            key={priority}
            title={`${group.label} priority`}
            subtitle={`${group.count} active case(s)`}
          >
            {group.cases.length === 0 ? (
              <Typography variant="body2" color="text.secondary">No active cases in this priority band.</Typography>
            ) : (
              <Stack spacing={1}>
                {group.cases.map((item) => (
                  <Box
                    key={item.id}
                    sx={{
                      display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center',
                      border: '1px solid #e2e8f0', borderLeft: `4px solid ${priority === 'critical' ? '#dc2626' : priority === 'high' ? '#d97706' : priority === 'medium' ? '#0284c7' : '#15803d'}`,
                      borderRadius: 1.5, p: 1.5,
                    }}
                  >
                    <Box sx={{ minWidth: 150 }}>
                      <Typography variant="subtitle2">{item.patient_name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {item.case_id} · {item.patient_code} · {item.patient_age ?? '—'}y {item.patient_gender}
                      </Typography>
                    </Box>
                    <Field label="Arrival" value={String(item.arrival_time).slice(11, 16)} />
                    <Field label="Waiting" value={`${item.waiting_minutes} min`} />
                    <Field label="Doctor" value={item.doctor_name} />
                    <Field label="Nurse" value={item.nurse_name} />
                    <Field label="Bed" value={item.bed_number} />
                    <Field label="Complaint" value={item.chief_complaint} />
                    <PriorityChip value={item.priority} label={item.priority_label} />
                    <StatusChip value={item.status} label={item.status_label} />
                    <Button
                      size="small"
                      onClick={() => {
                        setSelected(item)
                        setStatusValue(item.status)
                        setPriorityValue(item.priority)
                      }}
                    >
                      Update
                    </Button>
                  </Box>
                ))}
              </Stack>
            )}
          </SectionCard>
        )
      })}

      <Dialog open={Boolean(selected)} onClose={() => setSelected(null)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selected?.case_id} · {selected?.patient_name}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Stack direction="row" gap={2} flexWrap="wrap">
              <Field label="Priority" value={<PriorityChip value={selected?.priority} label={selected?.priority_label} />} />
              <Field label="Vitals" value={selected?.vitals_summary} />
              <Field label="Disposition" value={selected?.disposition} />
            </Stack>
            <TextField select size="small" label="Status" value={statusValue} onChange={(event) => setStatusValue(event.target.value)}>
              {['waiting', 'triaged', 'in_treatment', 'observation', 'admitted', 'discharged', 'referred', 'transferred'].map((value) => (
                <MenuItem key={value} value={value}>{value.replaceAll('_', ' ')}</MenuItem>
              ))}
            </TextField>
            <TextField
              select size="small" label="Priority" value={priorityValue}
              onChange={(event) => setPriorityValue(event.target.value)}
            >
              {['critical', 'high', 'medium', 'low'].map((value) => (
                <MenuItem key={value} value={value}>{value}</MenuItem>
              ))}
            </TextField>
            <Chip size="small" label="Clinical detail editing is available from the full case form" />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelected(null)}>Cancel</Button>
          <Button variant="contained" disabled={busy} onClick={updateStatus}>Save status</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
