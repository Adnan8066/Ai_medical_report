import { useEffect, useState } from 'react'
import {
  Alert, Box, Button, Checkbox, Chip, Dialog, DialogActions, DialogContent, DialogTitle,
  FormControlLabel, Grid, Stack, Tab, Tabs, Typography,
} from '@mui/material'
import api, { endpoints } from '../services/api.js'
import { DemoNotice, ErrorState, PageHeader, SectionCard } from '../components/ui.jsx'
import ResourcePage from '../components/ResourcePage.jsx'

const ROLE_OPTIONS = [
  'super_admin', 'hospital_admin', 'hod', 'doctor', 'nurse', 'receptionist', 'lab_technician',
  'radiologist', 'pharmacist', 'billing_staff', 'insurance_staff', 'inventory_manager', 'patient',
].map((value) => ({ value, label: value.replaceAll('_', ' ') }))

export function UsersPage() {
  return (
    <Box>
      <DemoNotice>Demo accounts are fictional. The password for every account is set by DEMO_PASSWORD.</DemoNotice>
      <ResourcePage
        config={{
          title: 'Users',
          subtitle: 'Accounts, roles and access',
          module: 'users',
          endpoint: endpoints.users,
          createLabel: 'Create user',
          columns: [
            { key: 'username', label: 'Username' },
            { key: 'full_name', label: 'Name' },
            { key: 'email', label: 'Email' },
            { key: 'role_name', label: 'Role' },
            { key: 'department_name', label: 'Department' },
            { key: 'employee_id', label: 'Employee ID' },
            { key: 'is_active', label: 'Active', render: (row) => (row.is_active ? 'Yes' : 'No') },
            { key: 'last_login', label: 'Last login', render: (row) => String(row.last_login || '—').slice(0, 16).replace('T', ' ') },
          ],
          filters: [{ key: 'role', label: 'Role', options: ROLE_OPTIONS }],
          fields: [
            { name: 'username', label: 'Username', required: true, span: 4 },
            { name: 'email', label: 'Email', required: true, span: 4 },
            { name: 'role', label: 'Role', type: 'select', required: true, span: 4, options: ROLE_OPTIONS },
            { name: 'first_name', label: 'First name', span: 4 },
            { name: 'last_name', label: 'Last name', span: 4 },
            { name: 'employee_id', label: 'Employee ID', span: 4 },
            { name: 'phone', label: 'Phone', span: 4 },
            { name: 'department', label: 'Department (ID)', type: 'number', span: 4 },
            { name: 'designation', label: 'Designation', span: 4 },
            { name: 'password', label: 'Temporary password', type: 'password', span: 6, help: 'Minimum 8 characters' },
            { name: 'is_active', label: 'Active', type: 'select', span: 6, options: [{ value: 'true', label: 'Yes' }, { value: 'false', label: 'No' }] },
          ],
        }}
      />
    </Box>
  )
}

export function RolesPage() {
  const [catalogue, setCatalogue] = useState(null)
  const [roles, setRoles] = useState([])
  const [error, setError] = useState(null)
  const [editing, setEditing] = useState(null)
  const [draft, setDraft] = useState({})
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState(null)

  const load = () => {
    setError(null)
    Promise.all([api.get(endpoints.permissionCatalogue), api.get(endpoints.roles)])
      .then(([catalogueResponse, rolesResponse]) => {
        setCatalogue(catalogueResponse.data)
        setRoles(rolesResponse.data.results || rolesResponse.data)
      })
      .catch((err) => setError(err.friendlyMessage || 'Unable to load roles.'))
  }

  useEffect(() => {
    load()
  }, [])

  const openEditor = (role) => {
    setEditing(role)
    setDraft(JSON.parse(JSON.stringify(role.permissions || {})))
  }

  const toggle = (module, action) => {
    setDraft((current) => {
      const actions = new Set(current[module] || [])
      if (actions.has(action)) actions.delete(action)
      else actions.add(action)
      return { ...current, [module]: [...actions] }
    })
  }

  const save = async () => {
    setBusy(true)
    setMessage(null)
    try {
      await api.patch(`${endpoints.roles}${editing.id}/`, { permissions: draft })
      setMessage({ severity: 'success', text: `Permissions updated for ${editing.name}.` })
      setEditing(null)
      load()
    } catch (err) {
      setMessage({ severity: 'error', text: err.friendlyMessage || 'Unable to save permissions.' })
    } finally {
      setBusy(false)
    }
  }

  if (error) return <ErrorState message={error} onRetry={load} />

  return (
    <Box>
      <PageHeader
        title="Roles & Permissions"
        subtitle="Role-based access control applied to every API endpoint and record"
        breadcrumb="Administration"
      />
      {message ? <Alert severity={message.severity} sx={{ mb: 2 }}>{message.text}</Alert> : null}
      <SectionCard title="Roles">
        <Grid container spacing={2}>
          {roles.map((role) => {
            const modules = Object.keys(role.permissions || {}).length
            return (
              <Grid size={{ xs: 12, sm: 6, lg: 4 }} key={role.code}>
                <Box sx={{ border: '1px solid #e2e8f0', borderRadius: 1.5, p: 2 }}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Typography variant="subtitle2">{role.name}</Typography>
                    <Chip size="small" label={`${role.user_count ?? 0} user(s)`} />
                  </Stack>
                  <Typography variant="caption" color="text.secondary" display="block">
                    {modules} module(s) granted
                  </Typography>
                  <Typography variant="caption" className="mono">{role.code}</Typography>
                  <Box sx={{ mt: 1 }}>
                    <Button size="small" onClick={() => openEditor(role)}>Edit permissions</Button>
                  </Box>
                </Box>
              </Grid>
            )
          })}
        </Grid>
      </SectionCard>

      <Dialog open={Boolean(editing)} onClose={() => setEditing(null)} maxWidth="lg" fullWidth>
        <DialogTitle>Permissions · {editing?.name}</DialogTitle>
        <DialogContent dividers>
          {(catalogue?.modules || []).map((module) => (
            <Stack
              key={module.code}
              direction={{ xs: 'column', md: 'row' }}
              spacing={1}
              sx={{ borderBottom: '1px solid #f1f5f9', py: 0.5, alignItems: { md: 'center' } }}
            >
              <Typography variant="body2" sx={{ minWidth: 240 }}>{module.label}</Typography>
              <Box>
                {(catalogue?.actions || ['view', 'create', 'edit', 'delete']).map((action) => (
                  <FormControlLabel
                    key={action}
                    control={
                      <Checkbox
                        size="small"
                        checked={(draft[module.code] || []).includes(action)}
                        onChange={() => toggle(module.code, action)}
                      />
                    }
                    label={<Typography variant="caption">{action}</Typography>}
                  />
                ))}
              </Box>
            </Stack>
          ))}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditing(null)}>Cancel</Button>
          <Button variant="contained" onClick={save} disabled={busy}>Save permissions</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default function Admin() {
  const [tab, setTab] = useState(0)
  return (
    <Box>
      <Tabs value={tab} onChange={(_, value) => setTab(value)} sx={{ mb: 1 }}>
        <Tab label="Users" />
        <Tab label="Roles & permissions" />
      </Tabs>
      {tab === 0 ? <UsersPage /> : <RolesPage />}
    </Box>
  )
}
