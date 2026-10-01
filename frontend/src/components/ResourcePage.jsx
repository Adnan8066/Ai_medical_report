import { useMemo, useState } from 'react'
import {
  Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Divider,
  Grid, IconButton, MenuItem, Stack, Table, TableBody, TableCell, TableHead, TableRow,
  TextField, Tooltip, Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import { useNavigate } from 'react-router-dom'
import DataTable from './DataTable.jsx'
import api from '../services/api.js'
import useResource from '../hooks/useResource.js'
import { Field, PageHeader, SectionCard } from './ui.jsx'
import { useAuth } from '../context/AuthContext.jsx'

/**
 * Generic list + create/edit screen driven by a configuration object.
 *
 * A module only has to describe its columns, filters and form fields; the
 * component provides search, pagination, CRUD dialogs, permission checks and
 * the standard loading/empty/error states.
 */
export default function ResourcePage({ config }) {
  const { user, can } = useAuth()
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [filterValues, setFilterValues] = useState({})
  const [pageSize, setPageSize] = useState(25)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [detail, setDetail] = useState(null)
  const [formValues, setFormValues] = useState({})
  const [formError, setFormError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)
  const [actionBusy, setActionBusy] = useState(null)

  const params = useMemo(() => {
    const next = { ...(config.baseParams || {}) }
    if (search) next.search = search
    Object.entries(filterValues).forEach(([key, value]) => {
      if (value) next[key] = value
    })
    return next
  }, [search, filterValues, config.baseParams])

  const resource = useResource(config.endpoint, { params, pageSize })
  const module = config.module

  const openCreate = () => {
    setEditing(null)
    const initial = { ...(config.defaultValues || {}) }
    ;(config.fields || []).forEach((field) => {
      if (field.type === 'items' && !initial[field.name]) initial[field.name] = []
    })
    setFormValues(initial)
    setFormError(null)
    setFormOpen(true)
  }

  const openEdit = (row) => {
    setEditing(row)
    const values = {}
    ;(config.fields || []).forEach((field) => {
      values[field.name] = row[field.name] ?? ''
    })
    ;(config.fields || []).forEach((field) => {
      if (field.type === 'items') {
        values[field.name] = (row[field.name] || []).map((item) => ({ ...item }))
      }
    })
    setFormValues(values)
    setFormError(null)
    setFormOpen(true)
  }

  const submit = async () => {
    setSaving(true)
    setFormError(null)
    try {
      const payload = {}
      ;(config.fields || []).forEach((field) => {
        const value = formValues[field.name]
        if (field.type === 'items') {
          const rows = (value || []).filter((item) =>
            Object.values(item).some((entry) => entry !== '' && entry !== null && entry !== undefined),
          )
          if (rows.length) payload[field.name] = rows
          return
        }
        if (value !== '' && value !== undefined && value !== null) payload[field.name] = value
      })
      if (editing) await resource.update(editing.id, payload)
      else await resource.create(payload)
      setMessage({
        severity: 'success',
        text: editing
          ? `${config.title} record updated.`
          : `${config.title} record created.`,
      })
      setFormOpen(false)
    } catch (error) {
      const details = error.response?.data?.errors
      setFormError(
        details && Object.keys(details).length
          ? Object.entries(details).map(([key, value]) => `${key}: ${value}`).join(' • ')
          : error.friendlyMessage || 'Unable to save the record.',
      )
    } finally {
      setSaving(false)
    }
  }

  const remove = async (row) => {
    if (!window.confirm('Delete this record? This cannot be undone.')) return
    try {
      await resource.remove(row.id)
    } catch (error) {
      window.alert(error.friendlyMessage || 'Unable to delete the record.')
    }
  }

  const runRowAction = async (action, row) => {
    if (action.confirm && !window.confirm(action.confirm)) return
    setActionBusy(`${action.label}-${row.id}`)
    try {
      const endpoint =
        typeof action.endpoint === 'function' ? action.endpoint(row) : action.endpoint
      const payload = typeof action.payload === 'function' ? action.payload(row) : action.payload
      if (payload === null) {
        setActionBusy(null)
        return
      }
      const { data } =
        action.method === 'patch'
          ? await api.patch(endpoint, payload || {})
          : await api.post(endpoint, payload || {})
      const detail = action.successMessage
        ? action.successMessage(row, data)
        : `${action.label} completed.`
      setMessage({ severity: 'success', text: detail })
      await resource.reload()
    } catch (error) {
      setMessage({
        severity: 'error',
        text: error.friendlyMessage || `${action.label} failed.`,
      })
    } finally {
      setActionBusy(null)
    }
  }

  const canCreate = config.canCreate !== false && can(module, 'create')
  const canEdit = config.canEdit !== false && can(module, 'edit')

  return (
    <Box>
      <PageHeader
        title={config.title}
        subtitle={config.subtitle}
        breadcrumb={config.breadcrumb}
        actions={
          canCreate ? (
            <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
              {config.createLabel || 'New record'}
            </Button>
          ) : null
        }
      />
      {message ? (
        <Alert severity={message.severity} sx={{ mb: 2 }} onClose={() => setMessage(null)}>
          {message.text}
        </Alert>
      ) : null}
      {config.notice ? <Alert severity="info" sx={{ mb: 2 }}>{config.notice}</Alert> : null}
      <SectionCard>
        <DataTable
          columns={config.columns}
          rows={resource.rows}
          loading={resource.loading}
          error={resource.error}
          onRetry={resource.reload}
          count={resource.count}
          page={resource.page}
          numPages={resource.numPages}
          pageSize={pageSize}
          onPageChange={resource.setPage}
          onPageSizeChange={setPageSize}
          search={search}
          onSearchChange={setSearch}
          filters={config.filters || []}
          filterValues={filterValues}
          onFilterChange={(key, value) =>
            setFilterValues((current) => ({ ...current, [key]: value }))
          }
          onEdit={canEdit ? openEdit : undefined}
          onDelete={canEdit && config.canDelete ? remove : undefined}
          onView={config.detailFields ? (row) => setDetail(row) : undefined}
          onRowClick={config.rowLink ? (row) => navigate(config.rowLink(row)) : undefined}
          rowActions={
            canEdit
              ? (config.rowActions || []).map((action) => ({
                  ...action,
                  isDisabled: (row) =>
                    Boolean(actionBusy) ||
                    (action.isDisabled ? action.isDisabled(row) : false),
                }))
              : []
          }
          onRowAction={runRowAction}
        />
      </SectionCard>

      <Dialog open={formOpen} onClose={() => setFormOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{editing ? `Edit ${config.title}` : config.createLabel || `New ${config.title}`}</DialogTitle>
        <Divider />
        <DialogContent>
          {formError ? (
            <Box sx={{ mb: 2, color: 'error.main', typography: 'body2' }}>{formError}</Box>
          ) : null}
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            {(config.fields || []).map((field) => (
              <Grid size={{ xs: 12, sm: field.span || 6 }} key={field.name}>
                {field.type === 'items' ? (
                  <ItemsField
                    field={field}
                    rows={formValues[field.name] || []}
                    onChange={(rows) =>
                      setFormValues((current) => ({ ...current, [field.name]: rows }))
                    }
                  />
                ) : field.type === 'select' ? (
                  <TextField
                    select
                    fullWidth
                    size="small"
                    label={field.label}
                    required={field.required}
                    value={formValues[field.name] ?? ''}
                    onChange={(event) =>
                      setFormValues((current) => ({ ...current, [field.name]: event.target.value }))
                    }
                    helperText={field.help}
                  >
                    <MenuItem value="">—</MenuItem>
                    {(field.options || []).map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </TextField>
                ) : (
                  <TextField
                    fullWidth
                    size="small"
                    label={field.label}
                    required={field.required}
                    type={field.type || 'text'}
                    multiline={field.multiline}
                    minRows={field.multiline ? 2 : undefined}
                    InputLabelProps={field.type === 'date' ? { shrink: true } : undefined}
                    value={formValues[field.name] ?? ''}
                    onChange={(event) =>
                      setFormValues((current) => ({ ...current, [field.name]: event.target.value }))
                    }
                    helperText={field.help}
                  />
                )}
              </Grid>
            ))}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFormOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={submit} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(detail)} onClose={() => setDetail(null)} maxWidth="md" fullWidth>
        <DialogTitle>{config.title} detail</DialogTitle>
        <Divider />
        <DialogContent>
          {detail ? (
            <Stack direction="row" flexWrap="wrap" gap={2} sx={{ pt: 1 }}>
              {(config.detailFields || []).map((field) => (
                <Field
                  key={field.name}
                  label={field.label}
                  value={field.render ? field.render(detail) : detail[field.name]}
                />
              ))}
            </Stack>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetail(null)}>Close</Button>
          {canEdit ? (
            <Button
              variant="contained"
              onClick={() => {
                const row = detail
                setDetail(null)
                openEdit(row)
              }}
            >
              Edit
            </Button>
          ) : null}
        </DialogActions>
      </Dialog>
      {user ? null : null}
    </Box>
  )
}

/**
 * Repeatable line items (invoice lines, prescription lines, PO lines).
 *
 * `field.itemFields` describes each column; `field.itemDefaults` seeds a new
 * row so the add button always produces a valid starting point.
 */
function ItemsField({ field, rows, onChange }) {
  const columns = field.itemFields || []

  const addRow = () => onChange([...rows, { ...(field.itemDefaults || {}) }])
  const removeRow = (index) => onChange(rows.filter((_, position) => position !== index))
  const setCell = (index, name, value) =>
    onChange(rows.map((row, position) => (position === index ? { ...row, [name]: value } : row)))

  return (
    <Box sx={{ border: '1px solid #e2e8f0', borderRadius: 1.5, p: 1.5 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
        <Box>
          <Typography variant="subtitle2">{field.label}</Typography>
          {field.help ? (
            <Typography variant="caption" color="text.secondary">{field.help}</Typography>
          ) : null}
        </Box>
        <Button size="small" startIcon={<AddIcon />} onClick={addRow}>
          {field.addLabel || 'Add line'}
        </Button>
      </Stack>

      {rows.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          {field.emptyText || 'No lines added yet.'}
        </Typography>
      ) : (
        <Box sx={{ overflowX: 'auto' }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                {columns.map((column) => (
                  <TableCell key={column.name}>{column.label}</TableCell>
                ))}
                <TableCell align="right">Remove</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((row, index) => (
                <TableRow key={index}>
                  {columns.map((column) => (
                    <TableCell key={column.name} sx={{ minWidth: column.width || 120 }}>
                      {column.type === 'select' ? (
                        <TextField
                          select fullWidth size="small" value={row[column.name] ?? ''}
                          onChange={(event) => setCell(index, column.name, event.target.value)}
                        >
                          <MenuItem value="">—</MenuItem>
                          {(column.options || []).map((option) => (
                            <MenuItem
                              key={typeof option === 'string' ? option : option.value}
                              value={typeof option === 'string' ? option : option.value}
                            >
                              {typeof option === 'string' ? option : option.label}
                            </MenuItem>
                          ))}
                        </TextField>
                      ) : (
                        <TextField
                          fullWidth size="small"
                          type={column.type === 'number' ? 'number' : 'text'}
                          value={row[column.name] ?? ''}
                          onChange={(event) => setCell(index, column.name, event.target.value)}
                        />
                      )}
                    </TableCell>
                  ))}
                  <TableCell align="right">
                    <Tooltip title="Remove line">
                      <IconButton size="small" color="error" onClick={() => removeRow(index)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Box>
      )}
    </Box>
  )
}
