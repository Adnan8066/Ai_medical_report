import { useCallback, useEffect, useState } from 'react'
import {
  Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Divider, Grid,
  MenuItem, Paper, Stack, Tab, Tabs, TextField, Typography,
} from '@mui/material'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import api, { endpoints } from '../services/api.js'
import useResource from '../hooks/useResource.js'
import DataTable from '../components/DataTable.jsx'
import {
  DemoNotice, ErrorState, Field, PageHeader, SectionCard, StatCard, StatusChip,
} from '../components/ui.jsx'
import DescriptionIcon from '@mui/icons-material/Description'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import ErrorIcon from '@mui/icons-material/Error'
import SmartToyIcon from '@mui/icons-material/SmartToy'
import ExtensionIcon from '@mui/icons-material/Extension'
import HourglassIcon from '@mui/icons-material/HourglassEmpty'

const CATEGORIES = [
  ['lab_report', 'Lab report'], ['prescription', 'Prescription'],
  ['discharge_summary', 'Discharge summary'], ['medical_certificate', 'Medical certificate'],
  ['referral_letter', 'Referral letter'], ['imaging_report', 'Imaging report'],
  ['insurance_document', 'Insurance document'], ['consultation_note', 'Consultation note'],
  ['consent_form', 'Consent form'], ['other', 'Other'],
]

const COLUMNS = [
  { key: 'document_id', label: 'Document' },
  { key: 'title', label: 'Title' },
  { key: 'patient_name', label: 'Patient' },
  { key: 'category_label', label: 'Category' },
  { key: 'ocr_status', label: 'OCR', render: (row) => <StatusChip value={row.ocr_status} label={row.ocr_status_label} /> },
  { key: 'chunk_count', label: 'Chunks' },
  { key: 'file_size', label: 'Size', render: (row) => `${Math.max(1, Math.round(row.file_size / 1024))} KB` },
  { key: 'uploaded_at', label: 'Uploaded', render: (row) => String(row.uploaded_at).slice(0, 16).replace('T', ' ') },
]

export default function Documents() {
  const [tab, setTab] = useState(0)
  const [stats, setStats] = useState(null)
  const [runtime, setRuntime] = useState(null)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [ocrStatus, setOcrStatus] = useState('')
  const [uploadOpen, setUploadOpen] = useState(false)
  const [detail, setDetail] = useState(null)
  const [summary, setSummary] = useState(null)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState(null)

  const resource = useResource(endpoints.documents, {
    params: { search, category, ocr_status: ocrStatus },
  })

  const loadMeta = useCallback(() => {
    Promise.all([api.get(`${endpoints.documents}stats/`), api.get(`${endpoints.documents}ocr_status/`)])
      .then(([statsResponse, runtimeResponse]) => {
        setStats(statsResponse.data)
        setRuntime(runtimeResponse.data)
      })
      .catch((err) => setError(err.friendlyMessage || 'Unable to load document statistics.'))
  }, [])

  useEffect(() => {
    loadMeta()
  }, [loadMeta])

  const openDetail = async (row) => {
    setDetail(row)
    setSummary(null)
    try {
      const { data } = await api.get(`${endpoints.documents}${row.id}/summary/`)
      setSummary(data)
    } catch (err) {
      setMessage({ severity: 'error', text: err.friendlyMessage || 'Unable to load the summary.' })
    }
  }

  const reprocess = async () => {
    if (!detail) return
    setBusy(true)
    try {
      const { data } = await api.post(`${endpoints.documents}${detail.id}/process/`)
      setMessage({ severity: 'info', text: `Pipeline: ${data.message}` })
      await openDetail(data.document)
      resource.reload()
      loadMeta()
    } finally {
      setBusy(false)
    }
  }

  if (error) return <ErrorState message={error} onRetry={loadMeta} />

  return (
    <Box>
      <PageHeader
        title="Medical Documents"
        subtitle="Upload, OCR, AI summarisation and retrieval-augmented search"
        breadcrumb="Intelligence"
        actions={
          <Button variant="contained" startIcon={<CloudUploadIcon />} onClick={() => setUploadOpen(true)}>
            Upload document
          </Button>
        }
      />
      <DemoNotice>
        Uploaded documents in this demo are fictional sample reports generated locally. AI output is for
        administrative support only and must be reviewed by an authorised healthcare professional.
      </DemoNotice>

      {runtime ? (
        <Alert severity={runtime.ocr?.tesseract_available ? 'success' : 'warning'} sx={{ mb: 2 }}>
          <strong>OCR engine:</strong> {runtime.ocr?.engine} · <strong>PDF reader:</strong>{' '}
          {runtime.ocr?.pdf_reader} · <strong>Image preprocessing:</strong>{' '}
          {runtime.ocr?.image_preprocessing} · <strong>AI provider:</strong> {runtime.ai?.provider}
          <Typography variant="caption" display="block">{runtime.ocr?.message}</Typography>
          <Typography variant="caption" display="block">{runtime.ai?.message}</Typography>
        </Alert>
      ) : null}

      {message ? (
        <Alert severity={message.severity} sx={{ mb: 2 }} onClose={() => setMessage(null)}>
          {message.text}
        </Alert>
      ) : null}

      {stats ? (
        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid size={{ xs: 12, sm: 6, lg: 2 }}><StatCard label="Documents" value={stats.total} icon={<DescriptionIcon />} /></Grid>
          <Grid size={{ xs: 12, sm: 6, lg: 2 }}><StatCard label="OCR completed" value={stats.completed} tone="success" icon={<CheckCircleIcon />} /></Grid>
          <Grid size={{ xs: 12, sm: 6, lg: 2 }}><StatCard label="OCR failed" value={stats.failed} tone="error" icon={<ErrorIcon />} /></Grid>
          <Grid size={{ xs: 12, sm: 6, lg: 2 }}><StatCard label="AI summaries" value={stats.summarised} tone="secondary" icon={<SmartToyIcon />} /></Grid>
          <Grid size={{ xs: 12, sm: 6, lg: 2 }}><StatCard label="RAG chunks" value={stats.chunks} tone="info" icon={<ExtensionIcon />} /></Grid>
          <Grid size={{ xs: 12, sm: 6, lg: 2 }}><StatCard label="Processing" value={stats.processing} tone="warning" icon={<HourglassIcon />} /></Grid>
        </Grid>
      ) : null}

      <SectionCard>
        <Tabs value={tab} onChange={(_, value) => setTab(value)}>
          <Tab label="Document library" />
          <Tab label="Document assistant (RAG)" />
          <Tab label="Duplicate detection" />
        </Tabs>
        <Divider sx={{ mb: 2 }} />
        {tab === 0 ? (
          <DataTable
            columns={COLUMNS}
            rows={resource.rows}
            loading={resource.loading}
            error={resource.error}
            onRetry={resource.reload}
            count={resource.count}
            page={resource.page}
            onPageChange={resource.setPage}
            search={search}
            onSearchChange={setSearch}
            filters={[
              { key: 'category', label: 'Category', options: CATEGORIES.map(([value, label]) => ({ value, label })) },
              { key: 'ocr_status', label: 'OCR status', options: ['uploaded', 'processing', 'completed', 'failed'] },
            ]}
            filterValues={{ category, ocr_status: ocrStatus }}
            onFilterChange={(key, value) => {
              if (key === 'category') setCategory(value)
              if (key === 'ocr_status') setOcrStatus(value)
            }}
            onView={openDetail}
          />
        ) : null}
        {tab === 1 ? <RagSearch /> : null}
        {tab === 2 ? <Duplicates /> : null}
      </SectionCard>

      <UploadDialog
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onDone={(payload) => {
          setMessage({ severity: 'info', text: payload })
          resource.reload()
          loadMeta()
        }}
      />

      <Dialog open={Boolean(detail)} onClose={() => setDetail(null)} maxWidth="md" fullWidth>
        <DialogTitle>
          {detail?.title}
          <Typography variant="caption" display="block" color="text.secondary">
            {detail?.document_id} · {detail?.patient_name} ({detail?.patient_code}) · {detail?.category_label}
          </Typography>
        </DialogTitle>
        <DialogContent dividers>
          {summary ? (
            <Stack spacing={2}>
              <Stack direction="row" gap={2} flexWrap="wrap">
                <Field label="OCR status" value={<StatusChip value={summary.ocr_status} />} />
                <Field label="Engine" value={summary.engine} />
                <Field label="Confidence" value={summary.confidence ? summary.confidence.toFixed(2) : '—'} />
                <Field label="Characters extracted" value={summary.extracted_text?.length ?? 0} />
              </Stack>
              {summary.ocr_error ? <Alert severity="warning">{summary.ocr_error}</Alert> : null}

              {summary.summary ? (
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="subtitle2">AI summary</Typography>
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mt: 1 }}>
                    {summary.summary.summary}
                  </Typography>
                  {summary.summary.key_points?.length ? (
                    <>
                      <Typography variant="subtitle2" sx={{ mt: 2 }}>Key points</Typography>
                      <ul>
                        {summary.summary.key_points.map((point, index) => (
                          <li key={index}><Typography variant="body2">{point}</Typography></li>
                        ))}
                      </ul>
                    </>
                  ) : null}
                  {summary.summary.medications?.length ? (
                    <>
                      <Typography variant="subtitle2">Medications mentioned</Typography>
                      <Stack direction="row" gap={1} flexWrap="wrap" sx={{ mt: 0.5 }}>
                        {summary.summary.medications.map((item) => (
                          <Chip key={item.name} size="small" label={`${item.name} ${item.dosage || ''}`.trim()} />
                        ))}
                      </Stack>
                    </>
                  ) : null}
                  {summary.summary.lab_values?.length ? (
                    <>
                      <Typography variant="subtitle2" sx={{ mt: 2 }}>Laboratory values detected</Typography>
                      <Stack direction="row" gap={1} flexWrap="wrap" sx={{ mt: 0.5 }}>
                        {summary.summary.lab_values.map((item, index) => (
                          <Chip key={`${item.name}-${index}`} size="small" variant="outlined" label={`${item.name}: ${item.value} ${item.unit || ''}`} />
                        ))}
                      </Stack>
                    </>
                  ) : null}
                  {summary.summary.important_dates?.length ? (
                    <>
                      <Typography variant="subtitle2" sx={{ mt: 2 }}>Dates detected</Typography>
                      <Typography variant="body2">
                        {summary.summary.important_dates.map((item) => item.date).join(', ')}
                      </Typography>
                    </>
                  ) : null}
                  <Alert severity="info" sx={{ mt: 2 }}>{summary.summary.disclaimer}</Alert>
                </Paper>
              ) : null}

              <Paper variant="outlined" sx={{ p: 2, maxHeight: 260, overflow: 'auto' }}>
                <Typography variant="subtitle2">Extracted text</Typography>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mt: 1, fontSize: 13 }}>
                  {summary.extracted_text || 'No machine-readable text was extracted from this file.'}
                </Typography>
              </Paper>
            </Stack>
          ) : (
            <Typography variant="body2" color="text.secondary">Loading summary…</Typography>
          )}
        </DialogContent>
        <DialogActions>
          {detail?.file_url ? (
            <Button href={detail.file_url} target="_blank" rel="noreferrer">Open file</Button>
          ) : null}
          <Button onClick={reprocess} disabled={busy}>Re-run OCR &amp; AI</Button>
          <Button onClick={() => setDetail(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

function UploadDialog({ open, onClose, onDone }) {
  const [patients, setPatients] = useState([])
  const [form, setForm] = useState({ patient: '', category: 'lab_report', title: '', description: '', file: null })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!open) return
    api
      .get(endpoints.patients, { params: { page_size: 100 } })
      .then(({ data }) => setPatients(data.results || []))
      .catch(() => undefined)
  }, [open])

  const submit = async () => {
    if (!form.patient || !form.title || !form.file) {
      setError('Select a patient, add a title and choose a PDF or image file.')
      return
    }
    setBusy(true)
    setError(null)
    const payload = new FormData()
    payload.append('patient', form.patient)
    payload.append('category', form.category)
    payload.append('title', form.title)
    payload.append('description', form.description)
    payload.append('file', form.file)
    try {
      const { data } = await api.post(endpoints.documents, payload, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      const pipeline = data.pipeline || {}
      onDone(
        `Uploaded ${data.document_id}. OCR status: ${data.ocr_status_label}. ` +
          `${pipeline.char_count ?? 0} characters extracted, ${pipeline.chunks_indexed ?? 0} chunks indexed ` +
          `(${pipeline.engine || 'engine'}, AI: ${pipeline.ai_provider || 'n/a'}).`,
      )
      setForm({ patient: '', category: 'lab_report', title: '', description: '', file: null })
      onClose()
    } catch (err) {
      const details = err.response?.data?.errors
      setError(
        details ? Object.entries(details).map(([key, value]) => `${key}: ${value}`).join(' • ')
          : err.friendlyMessage || 'Document upload failed.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Upload medical document</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error ? <Alert severity="error">{error}</Alert> : null}
          <TextField
            select size="small" label="Patient" value={form.patient}
            onChange={(event) => setForm({ ...form, patient: event.target.value })}
          >
            {patients.map((patient) => (
              <MenuItem key={patient.id} value={patient.id}>
                {patient.patient_id} · {patient.name}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            select size="small" label="Category" value={form.category}
            onChange={(event) => setForm({ ...form, category: event.target.value })}
          >
            {CATEGORIES.map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
          </TextField>
          <TextField
            size="small" label="Document title" value={form.title}
            onChange={(event) => setForm({ ...form, title: event.target.value })}
          />
          <TextField
            size="small" label="Description" value={form.description}
            onChange={(event) => setForm({ ...form, description: event.target.value })}
          />
          <Button variant="outlined" component="label" startIcon={<CloudUploadIcon />}>
            {form.file ? form.file.name : 'Choose PDF, PNG or JPG'}
            <input
              type="file"
              hidden
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={(event) => setForm({ ...form, file: event.target.files?.[0] || null })}
            />
          </Button>
          <Typography variant="caption" color="text.secondary">
            Allowed: PDF, PNG, JPG, JPEG · maximum 15 MB. The file is validated on the server before
            OCR runs.
          </Typography>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={submit} disabled={busy}>
          {busy ? 'Uploading & processing…' : 'Upload and process'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

function RagSearch() {
  const [question, setQuestion] = useState('What medications are mentioned in the uploaded documents?')
  const [patients, setPatients] = useState([])
  const [patientId, setPatientId] = useState('')
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api
      .get(endpoints.patients, { params: { page_size: 100 } })
      .then(({ data }) => setPatients(data.results || []))
      .catch(() => undefined)
  }, [])

  const ask = async () => {
    setBusy(true)
    try {
      const { data } = await api.get(`${endpoints.documents}search/`, {
        params: { q: question, patient: patientId || undefined },
      })
      setResult(data)
    } catch (err) {
      setResult({ answer: err.friendlyMessage || 'Search failed.', results: [] })
    } finally {
      setBusy(false)
    }
  }

  return (
    <Stack spacing={2}>
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
        <TextField
          select size="small" label="Limit to patient (optional)" value={patientId}
          onChange={(event) => setPatientId(event.target.value)}
          sx={{ minWidth: 260 }}
        >
          <MenuItem value="">All authorised documents</MenuItem>
          {patients.map((patient) => (
            <MenuItem key={patient.id} value={patient.id}>{patient.patient_id} · {patient.name}</MenuItem>
          ))}
        </TextField>
        <TextField
          size="small" fullWidth label="Ask about the documents" value={question}
          onChange={(event) => setQuestion(event.target.value)}
        />
        <Button variant="contained" onClick={ask} disabled={busy} sx={{ whiteSpace: 'nowrap' }}>
          {busy ? 'Searching…' : 'Ask'}
        </Button>
      </Stack>
      {result ? (
        <>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle2">Answer (grounded in retrieved text)</Typography>
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mt: 1 }}>{result.answer}</Typography>
            <Alert severity="info" sx={{ mt: 2 }}>{result.disclaimer}</Alert>
          </Paper>
          <Typography variant="subtitle2">Source references</Typography>
          {result.results?.length ? result.results.map((item) => (
            <Paper key={`${item.document_id}-${item.chunk_index}`} variant="outlined" sx={{ p: 1.5 }}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Chip size="small" label={item.document_code} />
                <Typography variant="subtitle2">{item.title}</Typography>
                <Chip size="small" variant="outlined" label={`score ${item.score}`} />
              </Stack>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>{item.snippet}</Typography>
            </Paper>
          )) : (
            <Typography variant="body2" color="text.secondary">
              No matching passages were found in the documents you can access.
            </Typography>
          )}
        </>
      ) : null}
    </Stack>
  )
}

function Duplicates() {
  const [groups, setGroups] = useState(null)

  useEffect(() => {
    api
      .get(`${endpoints.documents}duplicates/`)
      .then(({ data }) => setGroups(data.groups || []))
      .catch(() => setGroups([]))
  }, [])

  if (groups === null) return <Typography variant="body2" color="text.secondary">Checking for duplicates…</Typography>
  if (!groups.length) return <Typography variant="body2" color="text.secondary">No duplicate documents detected.</Typography>

  return (
    <Stack spacing={2}>
      {groups.map((group) => (
        <Paper key={group.checksum} variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle2">
            {group.count} copies for {group.patient}
          </Typography>
          <Typography variant="caption" className="mono">SHA-256 {group.checksum}</Typography>
          <Stack spacing={1} sx={{ mt: 1 }}>
            {group.documents.map((document) => (
              <Stack key={document.id} direction="row" spacing={1} alignItems="center">
                <Chip size="small" label={document.document_id} />
                <Typography variant="body2">{document.title}</Typography>
              </Stack>
            ))}
          </Stack>
        </Paper>
      ))}
    </Stack>
  )
}
