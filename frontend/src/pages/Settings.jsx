import { useEffect, useState } from 'react'
import {
  Alert, Box, Button, Chip, Grid, Stack, TextField, Typography,
} from '@mui/material'
import SaveIcon from '@mui/icons-material/Save'
import api, { endpoints } from '../services/api.js'
import { useAuth } from '../context/AuthContext.jsx'
import { DemoNotice, Field, Loading, PageHeader, SectionCard } from '../components/ui.jsx'

const FIELDS = [
  ['name', 'Hospital name', 8],
  ['hospital_type', 'Hospital type', 4],
  ['registration_number', 'Registration number', 4],
  ['established_year', 'Established year', 4],
  ['total_beds', 'Total beds', 4],
  ['icu_beds', 'ICU beds', 4],
  ['emergency_beds', 'Emergency beds', 4],
  ['address_line1', 'Address line 1', 8],
  ['address_line2', 'Address line 2', 8],
  ['city', 'City', 4],
  ['state', 'State', 4],
  ['postal_code', 'Postal code', 4],
  ['country', 'Country', 4],
  ['phone', 'Phone', 4],
  ['emergency_number', 'Emergency number', 4],
  ['email', 'Email', 4],
  ['website', 'Website', 4],
]

export default function Settings() {
  const { can, refresh } = useAuth()
  const [form, setForm] = useState(null)
  const [status, setStatus] = useState(null)
  const [message, setMessage] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    Promise.all([api.get(endpoints.hospital), api.get(`${endpoints.hospital}status/`)])
      .then(([hospitalResponse, statusResponse]) => {
        setForm(hospitalResponse.data)
        setStatus(statusResponse.data)
      })
      .catch((err) => setMessage({ severity: 'error', text: err.friendlyMessage }))
  }, [])

  if (!form) return <Loading label="Loading hospital settings…" />

  const editable = can('hospital', 'edit')

  const save = async () => {
    setBusy(true)
    setMessage(null)
    const payload = {}
    FIELDS.forEach(([key]) => {
      payload[key] = form[key]
    })
    payload.about = form.about || ''
    try {
      const { data } = await api.patch(endpoints.hospital, payload)
      setForm(data)
      setMessage({ severity: 'success', text: 'Hospital settings saved.' })
      refresh?.()
    } catch (err) {
      setMessage({
        severity: 'error',
        text: err.friendlyMessage || 'Unable to save hospital settings.',
      })
    } finally {
      setBusy(false)
    }
  }

  return (
    <Box>
      <PageHeader
        title="Hospital Settings"
        subtitle="Demo hospital profile and runtime configuration"
        breadcrumb="Administration"
        actions={
          editable ? (
            <Button variant="contained" startIcon={<SaveIcon />} onClick={save} disabled={busy}>
              {busy ? 'Saving…' : 'Save changes'}
            </Button>
          ) : (
            <Chip label="Read-only for your role" />
          )
        }
      />
      <DemoNotice>
        Contact details here are fictional demo values. Settings changes are recorded in the audit log.
      </DemoNotice>
      {message ? <Alert severity={message.severity} sx={{ mb: 2 }}>{message.text}</Alert> : null}

      <SectionCard title="Hospital profile">
        <Grid container spacing={2}>
          {FIELDS.map(([key, label, span]) => (
            <Grid size={{ xs: 12, sm: span }} key={key}>
              <TextField
                fullWidth size="small" label={label} value={form[key] ?? ''}
                disabled={!editable}
                onChange={(event) => setForm({ ...form, [key]: event.target.value })}
              />
            </Grid>
          ))}
          <Grid size={{ xs: 12 }}>
            <TextField
              fullWidth size="small" multiline minRows={2} label="About"
              value={form.about ?? ''} disabled={!editable}
              onChange={(event) => setForm({ ...form, about: event.target.value })}
            />
          </Grid>
        </Grid>
      </SectionCard>

      {status ? (
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, lg: 4 }}>
            <SectionCard title="Runtime">
              <Stack spacing={1}>
                <Field label="Demo mode" value={status.demo_mode ? 'Enabled' : 'Disabled'} />
                <Field label="Debug" value={status.debug ? 'On' : 'Off'} />
                <Field label="Database" value={status.database_engine} />
                <Field label="Time zone" value={status.time_zone} />
              </Stack>
            </SectionCard>
          </Grid>
          <Grid size={{ xs: 12, lg: 4 }}>
            <SectionCard title="OCR & AI">
              <Stack spacing={1}>
                <Field label="OCR engine" value={status.ocr.engine} />
                <Field label="Tesseract available" value={status.ocr.tesseract_available ? 'Yes' : 'No'} />
                <Field label="PDF reader" value={status.ocr.pdf_reader} />
                <Field label="AI provider" value={status.ai.provider} />
                <Typography variant="caption" color="text.secondary">
                  {status.ocr.message}
                </Typography>
              </Stack>
            </SectionCard>
          </Grid>
          <Grid size={{ xs: 12, lg: 4 }}>
            <SectionCard title="Security & uploads">
              <Stack spacing={1}>
                <Field label="JWT access token" value={`${status.security.jwt_access_minutes} minutes`} />
                <Field label="JWT refresh token" value={`${status.security.jwt_refresh_days} days`} />
                <Field label="Audit logging" value={status.security.audit_logging ? 'Enabled' : 'Disabled'} />
                <Field label="Max upload size" value={`${status.uploads.max_size_mb} MB`} />
                <Field label="Allowed file types" value={status.uploads.allowed_extensions.join(', ').toUpperCase()} />
              </Stack>
            </SectionCard>
          </Grid>
        </Grid>
      ) : null}
    </Box>
  )
}
