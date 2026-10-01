import { useMemo, useState } from 'react'
import { Box, Chip, MenuItem, Stack, TextField } from '@mui/material'
import { endpoints } from '../services/api.js'
import useResource from '../hooks/useResource.js'
import DataTable from '../components/DataTable.jsx'
import { DemoNotice, PageHeader, SectionCard, StatusChip } from '../components/ui.jsx'

const SEVERITY_COLOURS = { info: 'default', warning: 'warning', critical: 'error' }

export default function AuditLogs() {
  const [search, setSearch] = useState('')
  const [module, setModule] = useState('')
  const [severity, setSeverity] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const params = useMemo(
    () => ({
      search,
      module,
      severity,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    }),
    [search, module, severity, dateFrom, dateTo],
  )

  const resource = useResource(endpoints.auditLogs, { params, pageSize: 50 })

  return (
    <Box>
      <PageHeader
        title="Audit Logs"
        subtitle="Append-only record of who did what, when and to which object"
        breadcrumb="Intelligence"
      />
      <DemoNotice>
        Audit entries never store clinical payloads — only the action, the affected object reference and
        request context.
      </DemoNotice>
      <SectionCard>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} sx={{ mb: 2 }}>
          <TextField
            size="small" type="date" label="From" InputLabelProps={{ shrink: true }}
            value={dateFrom} onChange={(event) => setDateFrom(event.target.value)}
          />
          <TextField
            size="small" type="date" label="To" InputLabelProps={{ shrink: true }}
            value={dateTo} onChange={(event) => setDateTo(event.target.value)}
          />
          <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center' }}>
            {['info', 'warning', 'critical'].map((value) => (
              <Chip
                key={value}
                size="small"
                label={value}
                color={SEVERITY_COLOURS[value]}
                variant={severity === value ? 'filled' : 'outlined'}
                onClick={() => setSeverity(severity === value ? '' : value)}
              />
            ))}
          </Stack>
          <TextField
            select size="small" label="Module" value={module}
            onChange={(event) => setModule(event.target.value)} sx={{ minWidth: 180 }}
          >
            <MenuItem value="">All</MenuItem>
            {['users', 'patients', 'doctors', 'appointments', 'opd', 'emergency', 'admissions', 'beds',
              'laboratory', 'radiology', 'pharmacy', 'surgery', 'bloodbank', 'documents', 'billing',
              'insurance', 'inventory', 'staff', 'notifications', 'ai', 'audit'].map((value) => (
              <MenuItem key={value} value={value}>{value}</MenuItem>
            ))}
          </TextField>
        </Stack>

        <DataTable
          dense
          columns={[
            { key: 'created_at', label: 'When', render: (row) => String(row.created_at).slice(0, 19).replace('T', ' ') },
            { key: 'username', label: 'User' },
            { key: 'role', label: 'Role' },
            { key: 'action', label: 'Action' },
            { key: 'module', label: 'Module' },
            { key: 'object_type', label: 'Object' },
            { key: 'object_id', label: 'Object ID' },
            { key: 'severity', label: 'Severity', render: (row) => <StatusChip value={row.severity === 'critical' ? 'critical' : row.severity} label={row.severity} /> },
            { key: 'ip_address', label: 'IP' },
          ]}
          rows={resource.rows}
          loading={resource.loading}
          error={resource.error}
          onRetry={resource.reload}
          count={resource.count}
          page={resource.page}
          onPageChange={resource.setPage}
          pageSize={50}
          search={search}
          onSearchChange={setSearch}
        />
      </SectionCard>
    </Box>
  )
}
