import { useEffect, useMemo, useState } from 'react'
import {
  Alert, Autocomplete, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Divider,
  FormControl, FormHelperText, Grid, IconButton, InputLabel, MenuItem, Select, Stack,
  Table, TableBody, TableCell, TableHead, TableRow, TextField, Tooltip, Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import CloseIcon from '@mui/icons-material/Close'
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
  const [autocompleteOptions, setAutocompleteOptions] = useState({})

  useEffect(() => {
    if (!formOpen) return undefined
    const lookupFields = (config.fields || []).filter((field) => field.lookup)
    if (!lookupFields.length) return undefined
    const cancelled = { value: false }
    const fetches = lookupFields.map(async (field) => {
      const endpoint = typeof field.lookup === 'string' ? field.lookup : field.lookup.endpoint
      try {
        const { data } = await api.get(endpoint)
        if (cancelled.value) return
        const rows = Array.isArray(data) ? data : data.results || []
        const normalised = rows.map((row) => ({
          id: row.id,
          label: field.lookup?.labelKey
            ? field.lookup.labelKey(row)
            : row.name || row.label || row.title || row.full_name || String(row.id),
          raw: row,
        }))
        setAutocompleteOptions((current) => ({ ...current, [field.name]: normalised }))
      } catch (_error) {
        if (!cancelled.value) {
          setAutocompleteOptions((current) => ({ ...current, [field.name]: [] }))
        }
      }
    })
    return () => {
      cancelled.value = true
    }
  }, [formOpen, config.fields])

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
      if (field.type === 'autocomplete') initial[field.name] = null
    })
    setFormValues(initial)
    setFormError(null)
    setFormOpen(true)
  }

  const openEdit = (row) => {
    setEditing(row)
    const values = {}
    ;(config.fields || []).forEach((field) => {
      if (field.type === 'autocomplete') {
        const lookupId = row[`${field.name}`] ?? row[`${field.name}_id`] ?? null
        values[`${field.name}_id`] = lookupId
        values[field.name] = null
        return
      }
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
        if (field.type === 'autocomplete') {
          const selected = formValues[field.name]
          const id = selected?.id ?? selected?.value ?? null
          if (id !== null && id !== undefined && id !== '') payload[field.name] = id
          return
        }
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

      <Dialog
        open={formOpen}
        onClose={() => setFormOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{ sx: { borderRadius: 2 } }}
      >
        <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ px: 3, pt: 2.5, pb: 1 }}>
          <Box>
            <Typography variant="overline" color="text.secondary" sx={{ display: 'block', lineHeight: 1.6 }}>
              {config.breadcrumb || config.title}
            </Typography>
            <Typography variant="h6" sx={{ lineHeight: 1.25 }}>
              {editing ? `Edit ${config.title.toLowerCase().replace(/^./, (c) => c.toUpperCase())}` : (config.createLabel || `New ${config.title}`)}
            </Typography>
          </Box>
          <IconButton onClick={() => setFormOpen(false)} size="small" aria-label="Close dialog">
            <CloseIcon fontSize="small" />
          </IconButton>
        </Stack>
        <Divider />
        <DialogContent sx={{ pt: 2.5 }}>
          {formError ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              {formError}
            </Alert>
          ) : null}
          {renderFormSections(config.fields || [], formValues, setFormValues, autocompleteOptions)}
        </DialogContent>
        <Divider />
        <DialogActions sx={{ px: 3, py: 1.75, justifyContent: 'flex-end' }}>
          <Button onClick={() => setFormOpen(false)} disabled={saving} sx={{ textTransform: 'none', px: 2.5 }}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={submit}
            disabled={saving}
            sx={{ textTransform: 'none', px: 3, boxShadow: 'none' }}
          >
            {saving ? 'Saving…' : editing ? 'Save changes' : 'Create record'}
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

function labelCase(value) {
  if (!value) return ''
  const upper = { opd: 'OPD', icu: 'ICU', ot: 'OT', hiv: 'HIV', dna: 'DNA', er: 'ER' }
  const key = String(value).toLowerCase()
  if (upper[key]) return upper[key]
  return key
    .split('_')
    .map((part, index) => (index === 0 ? part[0]?.toUpperCase() + part.slice(1) : part))
    .join(' ')
}

function DateField({ field, value, onChange }) {
  const current = value || ''
  const [year, month, day] = current ? current.split('-') : ['', '', '']
  const years = Array.from({ length: 100 }, (_v, index) => `${new Date().getFullYear() - index}`)
  const months = [
    { value: '01', label: 'January' },
    { value: '02', label: 'February' },
    { value: '03', label: 'March' },
    { value: '04', label: 'April' },
    { value: '05', label: 'May' },
    { value: '06', label: 'June' },
    { value: '07', label: 'July' },
    { value: '08', label: 'August' },
    { value: '09', label: 'September' },
    { value: '10', label: 'October' },
    { value: '11', label: 'November' },
    { value: '12', label: 'December' },
  ]
  const daysInMonth = (y, m) => (m ? new Date(Number(y || 0), Number(m), 0).getDate() : 31)
  const dayOptions = Array.from({ length: daysInMonth(year, month) }, (_v, index) => `${index + 1}`)

  const emit = (nextYear, nextMonth, nextDay) => {
    if (!nextYear || !nextMonth || !nextDay) {
      onChange('')
      return
    }
    onChange(`${nextYear}-${nextMonth.padStart(2, '0')}-${nextDay.padStart(2, '0')}`)
  }

  return (
    <FormControl fullWidth size="small" required={field.required} sx={{ minWidth: 0 }}>
      <InputLabel shrink htmlFor={`${field.name}-date`}>{field.label}</InputLabel>
      <Stack direction="row" spacing={1} sx={{ pt: 1, minWidth: 0 }}>
        <Select
          id={`${field.name}-date`}
          notched
          displayEmpty
          value={day}
          onChange={(event) => emit(year, month, event.target.value)}
          renderValue={(selected) => (selected ? selected : <em style={{ color: '#94a3b8', fontStyle: 'normal' }}>DD</em>)}
          sx={{ flex: '1 1 80px', minWidth: 80, '& .MuiSelect-select': { py: 1 } }}
        >
          <MenuItem value=""><em>Day</em></MenuItem>
          {dayOptions.map((d) => <MenuItem key={d} value={d}>{d}</MenuItem>)}
        </Select>
        <Select
          notched
          displayEmpty
          value={month}
          onChange={(event) => emit(year, event.target.value, day)}
          renderValue={(selected) => (selected ? months.find((m) => m.value === selected)?.label : <em style={{ color: '#94a3b8', fontStyle: 'normal' }}>Month</em>)}
          sx={{ flex: '2 1 140px', minWidth: 120, '& .MuiSelect-select': { py: 1 } }}
        >
          <MenuItem value=""><em>Month</em></MenuItem>
          {months.map((m) => <MenuItem key={m.value} value={m.value}>{m.label}</MenuItem>)}
        </Select>
        <Select
          notched
          displayEmpty
          value={year}
          onChange={(event) => emit(event.target.value, month, day)}
          renderValue={(selected) => (selected ? selected : <em style={{ color: '#94a3b8', fontStyle: 'normal' }}>YYYY</em>)}
          sx={{ flex: '1.2 1 100px', minWidth: 100, '& .MuiSelect-select': { py: 1 } }}
        >
          <MenuItem value=""><em>Year</em></MenuItem>
          {years.map((y) => <MenuItem key={y} value={y}>{y}</MenuItem>)}
        </Select>
      </Stack>
      {field.help ? <FormHelperText>{field.help}</FormHelperText> : null}
    </FormControl>
  )
}

function renderFormSection(title, fields, formValues, setFormValues, autocompleteOptions) {
  if (!fields.length) return null
  return (
    <Box sx={{ mb: 3 }}>
      <Typography
        variant="subtitle2"
        sx={{ mb: 1.25, color: 'text.primary', fontWeight: 600 }}
      >
        {title}
      </Typography>
      <Grid container spacing={2}>
        {fields.map((field) => (
          <Grid size={{ xs: 12, sm: Math.min(12, field.span || 6) }} key={field.name} sx={{ minWidth: 0 }}>
            {renderFormField(field, formValues, setFormValues, autocompleteOptions)}
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

function renderFormSections(fields, formValues, setFormValues, autocompleteOptions) {
  const groups = new Map()
  fields.forEach((field) => {
    const sectionTitle = field.section || 'Details'
    if (!groups.has(sectionTitle)) groups.set(sectionTitle, [])
    groups.get(sectionTitle).push(field)
  })
  return Array.from(groups.entries()).map(([title, items]) => (
    <Box key={title}>{renderFormSection(title, items, formValues, setFormValues, autocompleteOptions)}</Box>
  ))
}

function renderFormField(field, formValues, setFormValues, autocompleteOptions) {
  const sharedProps = {
    fullWidth: true,
    size: 'small',
    label: field.label,
    required: field.required,
    InputLabelProps: { shrink: true },
    helperText: field.help,
  }

  if (field.type === 'items') {
    return (
      <ItemsField
        field={field}
        rows={formValues[field.name] || []}
        onChange={(rows) => setFormValues((current) => ({ ...current, [field.name]: rows }))}
      />
    )
  }

  if (field.type === 'autocomplete') {
    const options = autocompleteOptions[field.name] || []
    const currentValue = formValues[field.name] || null
    return (
      <Autocomplete
        options={options}
        value={currentValue}
        isOptionEqualToValue={(option, value) => option?.id === value?.id}
        getOptionLabel={(option) => option?.label || ''}
        onChange={(_event, selected) =>
          setFormValues((current) => ({ ...current, [field.name]: selected }))
        }
        renderInput={(params) => (
          <TextField
            {...params}
            {...sharedProps}
            placeholder={field.placeholder || `Search ${field.label.toLowerCase()}…`}
          />
        )}
      />
    )
  }

  if (field.type === 'select') {
    const value = formValues[field.name] ?? ''
    return (
      <FormControl fullWidth size="small" required={field.required}>
        <InputLabel id={`${field.name}-label`} shrink>{field.label}</InputLabel>
        <Select
          labelId={`${field.name}-label`}
          label={field.label}
          notched
          displayEmpty
          value={value}
          onChange={(event) =>
            setFormValues((current) => ({ ...current, [field.name]: event.target.value }))
          }
        >
          <MenuItem value=""><em>— Select —</em></MenuItem>
          {(field.options || []).map((option) => {
            const optValue = typeof option === 'string' ? option : option.value
            const optLabel = typeof option === 'string' ? labelCase(option) : option.label
            return (
              <MenuItem key={optValue} value={optValue} sx={{ textTransform: 'capitalize' }}>
                {optLabel}
              </MenuItem>
            )
          })}
        </Select>
        {field.help ? <FormHelperText>{field.help}</FormHelperText> : null}
      </FormControl>
    )
  }

  if (field.type === 'date') {
    return (
      <DateField
        field={field}
        value={formValues[field.name] ?? ''}
        onChange={(next) => setFormValues((current) => ({ ...current, [field.name]: next }))}
      />
    )
  }

  if (field.type === 'multiline' || field.multiline) {
    return (
      <TextField
        {...sharedProps}
        multiline
        minRows={field.minRows || 3}
        maxRows={field.maxRows || 8}
        placeholder={field.placeholder}
        value={formValues[field.name] ?? ''}
        onChange={(event) =>
          setFormValues((current) => ({ ...current, [field.name]: event.target.value }))
        }
      />
    )
  }

  return (
    <TextField
      {...sharedProps}
      type="text"
      placeholder={field.placeholder}
      value={formValues[field.name] ?? ''}
      onChange={(event) =>
        setFormValues((current) => ({ ...current, [field.name]: event.target.value }))
      }
    />
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
