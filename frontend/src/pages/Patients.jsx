import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Box, Button, Chip, Divider, Grid, Paper, Stack, Tab, Tabs, Typography,
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import api, { endpoints } from '../services/api.js'
import ResourcePage from '../components/ResourcePage.jsx'
import { Field, PageHeader, SectionCard, StatusChip, DemoNotice, Loading, ErrorState } from '../components/ui.jsx'
import { formatDate, formatDateTime } from '../utils/format.js'

const PATIENT_COLUMNS = [
  { key: 'patient_id', label: 'Patient ID', render: (row) => <span className="mono">{row.patient_id}</span> },
  { key: 'name', label: 'Name' },
  { key: 'age', label: 'Age / Gender', numeric: true, render: (row) => `${row.age ?? '—'} · ${row.gender_label || '—'}` },
  { key: 'blood_group', label: 'Blood group', render: (row) => row.blood_group || '—' },
  { key: 'department_name', label: 'Department', render: (row) => row.department_name || '—' },
  { key: 'doctor_name', label: 'Doctor', render: (row) => row.doctor_name || '—' },
  { key: 'patient_type_label', label: 'Type' },
  { key: 'registration_date', label: 'Registered', render: (row) => formatDate(row.registration_date) },
  { key: 'status_label', label: 'Status', render: (row) => <StatusChip value={row.current_status} label={row.status_label} /> },
]

const PATIENT_FIELDS = [
  // Personal information
  { section: 'Personal information', name: 'name', label: 'Full name', required: true, span: 12 },
  { section: 'Personal information', name: 'date_of_birth', label: 'Date of birth', type: 'date', span: 12 },
  { section: 'Personal information', name: 'gender', label: 'Gender', type: 'select', span: 6, options: [
    { value: 'male', label: 'Male' }, { value: 'female', label: 'Female' }, { value: 'other', label: 'Other' },
  ] },
  { section: 'Personal information', name: 'blood_group', label: 'Blood group', type: 'select', span: 6, options: ['A+','A-','B+','B-','AB+','AB-','O+','O-'].map((v) => ({ value: v, label: v })) },
  { section: 'Personal information', name: 'phone', label: 'Phone', span: 6 },
  { section: 'Personal information', name: 'email', label: 'Email', type: 'email', span: 6 },
  { section: 'Personal information', name: 'registration_date', label: 'Registration date', type: 'date', span: 12 },

  // Department & care
  { section: 'Department & care', name: 'department', label: 'Department', type: 'autocomplete', span: 6, lookup: { endpoint: '/departments/', labelKey: (row) => `${row.name}${row.code ? ` (${row.code})` : ''}` }, placeholder: 'Search department…' },
  { section: 'Department & care', name: 'assigned_doctor', label: 'Assigned doctor', type: 'autocomplete', span: 6, lookup: { endpoint: '/doctors/', labelKey: (row) => `${row.name}${row.specialization ? ` — ${row.specialization}` : ''}` }, placeholder: 'Search doctor…' },
  { section: 'Department & care', name: 'patient_type', label: 'Patient type', type: 'select', span: 6, options: [
    'opd','outpatient','inpatient','emergency','icu','discharged','follow_up','scheduled',
  ] },
  { section: 'Department & care', name: 'current_status', label: 'Status', type: 'select', span: 6, options: [
    'registered','waiting','in_consultation','admitted','under_treatment','stable','critical',
    'ready_for_discharge','discharged','follow_up',
  ] },

  // Address
  { section: 'Address', name: 'address', label: 'Address', type: 'multiline', span: 12, minRows: 3, maxRows: 6, placeholder: 'Street, city, PIN code…' },

  // Emergency contact
  { section: 'Emergency contact', name: 'emergency_contact_name', label: 'Contact name', span: 6 },
  { section: 'Emergency contact', name: 'emergency_contact_phone', label: 'Contact phone', span: 6 },

  // Insurance
  { section: 'Insurance', name: 'insurance_provider', label: 'Insurance provider', span: 6 },
  { section: 'Insurance', name: 'insurance_policy_number', label: 'Policy number', span: 6 },

  // Clinical details
  { section: 'Clinical details', name: 'allergies', label: 'Allergies', placeholder: 'Comma separated…', span: 12 },
  { section: 'Clinical details', name: 'medical_history', label: 'Medical history', type: 'multiline', span: 12, minRows: 4, maxRows: 10, placeholder: 'Past conditions, surgeries, chronic illnesses…' },
]

export function PatientsList() {
  return (
    <Box>
      <DemoNotice />
      <ResourcePage
        config={{
          title: 'Patients',
          subtitle: 'Register patients and open the full clinical profile',
          module: 'patients',
          endpoint: endpoints.patients,
          createLabel: 'Register patient',
          columns: PATIENT_COLUMNS,
          fields: PATIENT_FIELDS,
          filters: [
            { key: 'patient_type', label: 'Type', options: ['opd','outpatient','inpatient','emergency','icu','discharged','follow_up','scheduled'] },
            { key: 'admission_status', label: 'Admission', options: ['not_admitted','admitted','discharged'] },
          ],
          detailFields: [
            { name: 'patient_id', label: 'Patient ID' },
            { name: 'name', label: 'Name' },
            { name: 'department_name', label: 'Department' },
            { name: 'doctor_name', label: 'Doctor' },
            { name: 'insurance_provider', label: 'Insurance' },
            { name: 'allergies', label: 'Allergies' },
            { name: 'medical_history', label: 'History' },
          ],
          // Clicking a row opens the complete clinical profile.
          rowLink: (row) => `/patients/${row.id}`,
          notice: 'Click any patient row to open the full profile, clinical timeline and related records.',
        }}
      />
    </Box>
  )
}

export function PatientDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [overview, setOverview] = useState(null)
  const [timeline, setTimeline] = useState([])
  const [tab, setTab] = useState(0)
  const [error, setError] = useState(null)
  const [records, setRecords] = useState({})

  useEffect(() => {
    let cancelled = false
    setError(null)
    Promise.all([
      api.get(`${endpoints.patients}${id}/overview/`),
      api.get(`${endpoints.patients}${id}/timeline/`),
      api.get(endpoints.appointments, { params: { patient: id, page_size: 50 } }),
      api.get(endpoints.opd, { params: { patient: id, page_size: 50 } }),
      api.get(endpoints.laboratory, { params: { patient: id, page_size: 50 } }),
      api.get(endpoints.prescriptions, { params: { patient: id, page_size: 50 } }),
      api.get(endpoints.documents, { params: { patient: id, page_size: 50 } }),
      api.get(endpoints.invoices, { params: { patient: id, page_size: 50 } }),
    ])
      .then(([o, t, appts, opd, lab, rx, docs, bills]) => {
        if (cancelled) return
        setOverview(o.data)
        setTimeline(t.data.events || [])
        setRecords({
          appointments: appts.data.results || [],
          opd: opd.data.results || [],
          laboratory: lab.data.results || [],
          prescriptions: rx.data.results || [],
          documents: docs.data.results || [],
          bills: bills.data.results || [],
        })
      })
      .catch((err) => !cancelled && setError(err.friendlyMessage || 'Unable to load the patient profile.'))
    return () => {
      cancelled = true
    }
  }, [id])

  if (error) return <ErrorState message={error} />
  if (!overview) return <Loading label="Loading patient profile…" />

  const patient = overview.patient
  const tabs = [
    ['Timeline', timeline, (row) => `${row.type} · ${row.title}`],
    ['Appointments', records.appointments, (row) => `${row.appointment_id} · ${row.date} ${row.time} · ${row.status_label}`],
    ['OPD visits', records.opd, (row) => `${row.visit_id} · ${row.visit_date} · ${row.diagnosis || 'no diagnosis'}`],
    ['Laboratory', records.laboratory, (row) => `${row.lab_id} · ${row.test_name} · ${row.status_label}`],
    ['Prescriptions', records.prescriptions, (row) => `${row.prescription_id} · ${row.status_label}`],
    ['Documents', records.documents, (row) => `${row.document_id} · ${row.title} · OCR ${row.ocr_status_label}`],
    ['Bills', records.bills, (row) => `${row.invoice_number} · payable ${row.patient_payable} · ${row.status_label}`],
  ]

  return (
    <Box>
      <PageHeader
        breadcrumb="Patients / Profile"
        title={patient.name}
        subtitle={`${patient.patient_id} · ${patient.age ?? '—'} years · ${patient.gender_label} · ${patient.blood_group || 'blood group not recorded'}`}
        actions={<Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/patients')}>Back to list</Button>}
      />
      <DemoNotice>Demo record — clinical content is fictional and must not be used for care.</DemoNotice>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <SectionCard title="Patient information">
            <Stack direction="row" flexWrap="wrap" gap={2}>
              <Field label="Department" value={patient.department_name} />
              <Field label="Assigned doctor" value={patient.doctor_name} />
              <Field label="Type" value={patient.patient_type_label} />
              <Field label="Status" value={<StatusChip value={patient.current_status} label={patient.status_label} />} />
              <Field label="Admission" value={patient.admission_status_label} />
              <Field label="Phone" value={patient.phone} />
              <Field label="Email" value={patient.email} />
              <Field label="Registered" value={formatDate(patient.registration_date)} />
              <Field label="Date of birth" value={formatDate(patient.date_of_birth)} />
              <Field label="Insurance" value={patient.insurance_provider || 'Self pay'} />
              <Field label="Policy" value={patient.insurance_policy_number} mono />
              <Field label="Emergency contact" value={`${patient.emergency_contact_name || '—'} (${patient.emergency_contact_relation || '—'})`} />
              <Field label="Emergency phone" value={patient.emergency_contact_phone} />
              <Field label="Allergies" value={patient.allergies} />
              <Field label="Chronic conditions" value={patient.chronic_conditions} />
            </Stack>
            {patient.medical_history ? (
              <>
                <Divider sx={{ my: 1.5 }} />
                <Typography variant="caption" color="text.secondary">Medical history</Typography>
                <Typography variant="body2">{patient.medical_history}</Typography>
              </>
            ) : null}
          </SectionCard>

          <SectionCard>
            <Tabs value={tab} onChange={(_, value) => setTab(value)} variant="scrollable" scrollButtons="auto">
              {tabs.map(([label]) => <Tab key={label} label={label} />)}
            </Tabs>
            <Box sx={{ pt: 2 }}>
              {tabs[tab][1].length === 0 ? (
                <Typography variant="body2" color="text.secondary">No records for this section.</Typography>
              ) : tab === 0 ? (
                tabs[0][1].map((event, index) => (
                  <Box className="timeline-item" key={`${event.type}-${index}`}>
                    <Box sx={{ position: 'absolute', left: 2, top: 6, width: 16, height: 16, borderRadius: '50%', background: '#0f766e', border: '3px solid #fff', boxShadow: '0 0 0 1px #cbd5e1' }} />
                    <Typography variant="caption" color="text.secondary">
                      {formatDateTime(event.date)}
                    </Typography>
                    <Typography variant="subtitle2">{event.title}</Typography>
                    {event.description ? (
                      <Typography variant="body2" color="text.secondary">{event.description}</Typography>
                    ) : null}
                    {event.status ? <Chip size="small" label={event.status} sx={{ mt: 0.5 }} /> : null}
                  </Box>
                ))
              ) : (
                <Stack spacing={1}>
                  {tabs[tab][1].map((row) => (
                    <Paper key={row.id} variant="outlined" sx={{ p: 1.5 }}>
                      <Typography variant="body2">{tabs[tab][2](row)}</Typography>
                    </Paper>
                  ))}
                </Stack>
              )}
            </Box>
          </SectionCard>
        </Grid>

        <Grid size={{ xs: 12, lg: 4 }}>
          <SectionCard title="Latest vitals">
            {overview.latest_vitals ? (
              <Stack direction="row" flexWrap="wrap" gap={2}>
                <Field label="Recorded" value={formatDateTime(overview.latest_vitals.recorded_at)} />
                <Field label="Blood pressure" value={overview.latest_vitals.blood_pressure} />
                <Field label="Pulse" value={overview.latest_vitals.pulse_bpm} />
                <Field label="SpO₂" value={`${overview.latest_vitals.spo2 ?? '—'}%`} />
                <Field label="Temperature" value={`${overview.latest_vitals.temperature_c ?? '—'} °C`} />
                <Field label="Status" value={<StatusChip value={overview.latest_vitals.status} label={overview.latest_vitals.status_label} />} />
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary">No vitals recorded yet.</Typography>
            )}
          </SectionCard>
          <SectionCard title="Record counts">
            <Stack direction="row" flexWrap="wrap" gap={2}>
              {Object.entries(overview.counts || {}).map(([key, value]) => (
                <Field key={key} label={key.replaceAll('_', ' ')} value={value} />
              ))}
            </Stack>
          </SectionCard>
        </Grid>
      </Grid>
    </Box>
  )
}

export default PatientsList
