import { useCallback, useEffect, useState } from 'react'
import {
  Box, Button, Chip, Grid, Stack, TextField, Typography,
} from '@mui/material'
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft'
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import api, { endpoints } from '../services/api.js'
import {
  DemoNotice, ErrorState, Loading, PageHeader, SectionCard, StatCard, StatusChip,
} from '../components/ui.jsx'
import GroupsIcon from '@mui/icons-material/Groups'
import LocalHospitalIcon from '@mui/icons-material/LocalHospital'
import BadgeIcon from '@mui/icons-material/Badge'
import ScheduleIcon from '@mui/icons-material/Schedule'

const todayIso = () => new Date().toISOString().slice(0, 10)

export default function ShiftRoster() {
  const [date, setDate] = useState(todayIso())
  const [roster, setRoster] = useState(null)
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback((target) => {
    setError(null)
    Promise.all([
      api.get(`${endpoints.shiftAssignments}roster/`, { params: { date: target } }),
      api.get(`${endpoints.staff}summary/`),
    ])
      .then(([rosterResponse, summaryResponse]) => {
        setRoster(rosterResponse.data)
        setSummary(summaryResponse.data)
      })
      .catch((err) => setError(err.friendlyMessage || 'Unable to load the shift roster.'))
  }, [])

  useEffect(() => {
    load(date)
  }, [load, date])

  const shiftDay = (offset) => {
    const next = new Date(date)
    next.setDate(next.getDate() + offset)
    setDate(next.toISOString().slice(0, 10))
  }

  const markStatus = async (assignment, status) => {
    try {
      await api.patch(`${endpoints.shiftAssignments}${assignment.id}/`, { status })
      load(date)
    } catch (err) {
      window.alert(err.friendlyMessage || 'Unable to update the roster entry.')
    }
  }

  if (error) return <ErrorState message={error} onRetry={() => load(date)} />
  if (!roster) return <Loading label="Loading the roster…" />

  const totalAssigned = roster.shifts.reduce((sum, group) => sum + group.count, 0)

  return (
    <Box>
      <PageHeader
        title="Shift Roster"
        subtitle="Who is on duty, in which department and for which shift"
        breadcrumb="People"
        actions={
          <Stack direction="row" spacing={1} alignItems="center">
            <Button size="small" startIcon={<ChevronLeftIcon />} onClick={() => shiftDay(-1)}>
              Previous
            </Button>
            <TextField
              size="small" type="date" value={date}
              InputLabelProps={{ shrink: true }}
              onChange={(event) => setDate(event.target.value)}
            />
            <Button size="small" endIcon={<ChevronRightIcon />} onClick={() => shiftDay(1)}>
              Next
            </Button>
          </Stack>
        }
      />
      <DemoNotice>Roster entries are fictional demo assignments.</DemoNotice>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <StatCard label="Staff on roster" value={totalAssigned} hint={roster.date} icon={<GroupsIcon />} />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <StatCard label="Workforce" value={summary?.total ?? '—'} hint={`${summary?.active ?? 0} active`} icon={<LocalHospitalIcon />} tone="secondary" />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <StatCard label="On duty now" value={summary?.on_duty ?? 0} icon={<BadgeIcon />} tone="success" />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <StatCard label="Shift patterns" value={roster.shifts.length} icon={<ScheduleIcon />} tone="info" />
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        {roster.shifts.map((group) => (
          <Grid size={{ xs: 12, lg: 6 }} key={group.shift.id}>
            <SectionCard
              title={`${group.shift.name} shift`}
              subtitle={`${String(group.shift.start_time).slice(0, 5)} – ${String(group.shift.end_time).slice(0, 5)} · ${group.count} staff`}
              actions={
                <Chip
                  size="small"
                  label={group.shift.is_emergency_shift ? 'Emergency cover' : `${group.shift.duration_hours}h`}
                  color={group.shift.is_emergency_shift ? 'error' : 'default'}
                />
              }
            >
              {group.assignments.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  Nobody is rostered on this shift for {roster.date}.
                </Typography>
              ) : (
                <Stack spacing={1} sx={{ maxHeight: 380, overflowY: 'auto' }}>
                  {group.assignments.map((assignment) => (
                    <Box
                      key={assignment.id}
                      sx={{
                        border: '1px solid #e2e8f0', borderRadius: 1.5, p: 1.25,
                        display: 'flex', flexWrap: 'wrap', gap: 1.5, alignItems: 'center',
                      }}
                    >
                      <Box sx={{ minWidth: 170 }}>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {assignment.staff_name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {assignment.employee_id} · {assignment.staff_role}
                        </Typography>
                      </Box>
                      <Typography variant="body2" sx={{ minWidth: 150 }}>
                        {assignment.department_name || 'Unassigned'}
                      </Typography>
                      <Chip size="small" variant="outlined" label={assignment.ward || '—'} />
                      <StatusChip value={assignment.status} label={assignment.status_label} />
                      <Stack direction="row" spacing={0.5}>
                        <Button size="small" onClick={() => markStatus(assignment, 'in_progress')}>
                          On duty
                        </Button>
                        <Button size="small" onClick={() => markStatus(assignment, 'completed')}>
                          Complete
                        </Button>
                      </Stack>
                    </Box>
                  ))}
                </Stack>
              )}
            </SectionCard>
          </Grid>
        ))}
      </Grid>

      {summary?.by_role?.length ? (
        <SectionCard title="Workforce by role">
          <Stack direction="row" gap={1} flexWrap="wrap">
            {summary.by_role.map((row) => (
              <Chip key={row.role} label={`${row.label}: ${row.total}`} />
            ))}
          </Stack>
        </SectionCard>
      ) : null}
    </Box>
  )
}
