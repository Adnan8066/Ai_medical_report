import { useCallback, useEffect, useState } from 'react'
import { Alert, Box, Grid, Tab, Tabs, Typography } from '@mui/material'
import api, { endpoints } from '../services/api.js'
import useResource from '../hooks/useResource.js'
import DataTable from '../components/DataTable.jsx'
import {
  DemoNotice, ErrorState, Loading, PageHeader, SectionCard, StatCard, StatusChip,
} from '../components/ui.jsx'
import BloodtypeIcon from '@mui/icons-material/Bloodtype'
import BookmarkIcon from '@mui/icons-material/Bookmark'
import WarningIcon from '@mui/icons-material/Warning'
import ScienceIcon from '@mui/icons-material/Science'

export default function BloodBank() {
  const [tab, setTab] = useState(0)
  const [dashboard, setDashboard] = useState(null)
  const [error, setError] = useState(null)

  const reload = useCallback(() => {
    setError(null)
    api
      .get(`${endpoints.bloodStock}dashboard/`)
      .then(({ data }) => setDashboard(data))
      .catch((err) => setError(err.friendlyMessage || 'Unable to load the blood bank.'))
  }, [])

  useEffect(() => {
    reload()
  }, [reload])

  const donations = useResource(endpoints.donations, { auto: tab === 1 })
  const issues = useResource(endpoints.bloodIssues, { auto: tab === 2 })

  if (error) return <ErrorState message={error} onRetry={reload} />
  if (!dashboard) return <Loading label="Loading blood bank inventory…" />

  const summary = dashboard.summary

  return (
    <Box>
      <PageHeader
        title="Blood Bank"
        subtitle="Stock levels, donations and issue records"
        breadcrumb="Diagnostics & Pharmacy"
      />
      <DemoNotice>{dashboard.notice}</DemoNotice>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <StatCard label="Units available" value={summary.total_available} icon={<BloodtypeIcon />} tone="error" />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <StatCard label="Units reserved" value={summary.total_reserved} icon={<BookmarkIcon />} tone="warning" />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <StatCard
            label="Groups in critical stock"
            value={summary.critical_groups.length}
            hint={summary.critical_groups.join(', ') || 'All groups adequately stocked'}
            icon={<WarningIcon />}
            tone={summary.critical_groups.length ? 'error' : 'success'}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <StatCard
            label="Units collected (30 days)"
            value={dashboard.donations.units_collected}
            hint={`${dashboard.donations.last_30_days} donation(s) · ${dashboard.issues.units_issued} units issued`}
            icon={<ScienceIcon />}
            tone="secondary"
          />
        </Grid>
      </Grid>

      <SectionCard title="Blood group availability">
        <Grid container spacing={2}>
          {dashboard.stock.map((item) => {
            const total = item.units_available + item.units_reserved
            return (
              <Grid size={{ xs: 6, sm: 4, md: 3, lg: 1.5 }} key={item.blood_group}>
                <Box
                  sx={{
                    border: '1px solid #e2e8f0',
                    borderRadius: 2,
                    p: 1.5,
                    textAlign: 'center',
                    borderTop: `4px solid ${item.status === 'adequate' ? '#15803d' : item.status === 'low' ? '#d97706' : '#dc2626'}`,
                  }}
                >
                  <Typography variant="h6">{item.blood_group}</Typography>
                  <Typography variant="h5" sx={{ lineHeight: 1.1 }}>{item.units_available}</Typography>
                  <Typography variant="caption" color="text.secondary">available</Typography>
                  <Typography variant="caption" display="block" color="text.secondary">
                    {item.units_reserved} reserved · {total} total
                  </Typography>
                  <StatusChip value={item.status} label={item.status.replaceAll('_', ' ')} />
                </Box>
              </Grid>
            )
          })}
        </Grid>
      </SectionCard>

      <SectionCard>
        <Tabs value={tab} onChange={(_, value) => setTab(value)}>
          <Tab label="Donation records" />
          <Tab label="Issue records" />
          <Tab label="Compatibility reference" />
        </Tabs>
        <Box sx={{ pt: 2 }}>
          {tab === 0 ? (
            <DataTable
              columns={[
                { key: 'donation_id', label: 'Donation' },
                { key: 'donor_name', label: 'Donor' },
                { key: 'blood_group', label: 'Group' },
                { key: 'units', label: 'Units' },
                { key: 'donation_date', label: 'Date' },
                { key: 'donor_age', label: 'Age' },
                { key: 'camp_location', label: 'Location' },
                { key: 'screening', label: 'Screening', render: (row) => <StatusChip value={row.screening === 'passed' ? 'available' : row.screening} label={row.screening_label} /> },
                { key: 'hemoglobin', label: 'Hb' },
              ]}
              rows={donations.rows}
              loading={donations.loading}
              error={donations.error}
              onRetry={donations.reload}
              count={donations.count}
              page={donations.page}
              onPageChange={donations.setPage}
            />
          ) : null}
          {tab === 1 ? (
            <DataTable
              columns={[
                { key: 'issue_id', label: 'Issue' },
                { key: 'blood_group', label: 'Group' },
                { key: 'units', label: 'Units' },
                { key: 'patient_name', label: 'Patient' },
                { key: 'ward', label: 'Ward' },
                { key: 'reason', label: 'Reason' },
                { key: 'crossmatch_id', label: 'Crossmatch' },
                { key: 'requested_at', label: 'Requested', render: (row) => String(row.requested_at).slice(0, 16).replace('T', ' ') },
                { key: 'status', label: 'Status', render: (row) => <StatusChip value={row.status} label={row.status_label} /> },
              ]}
              rows={issues.rows}
              loading={issues.loading}
              error={issues.error}
              onRetry={issues.reload}
              count={issues.count}
              page={issues.page}
              onPageChange={issues.setPage}
            />
          ) : null}
          {tab === 2 ? (
            <Alert severity="info">
              Compatibility mapping is provided by the API at
              <code> /api/blood-bank/stock/compatible/</code> for use by the issue form. Clinical
              cross-matching decisions always remain with the blood bank team.
            </Alert>
          ) : null}
        </Box>
      </SectionCard>
    </Box>
  )
}
