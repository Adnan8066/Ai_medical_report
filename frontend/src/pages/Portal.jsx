import { useEffect, useState } from 'react'
import {
  Alert, Box, Chip, Divider, Grid, Paper, Stack, Tab, Tabs, Typography,
} from '@mui/material'
import api, { endpoints } from '../services/api.js'
import { useAuth } from '../context/AuthContext.jsx'
import {
  DemoNotice, ErrorState, Field, Loading, PageHeader, SectionCard, StatusChip,
} from '../components/ui.jsx'

const TABS = [
  ['appointments', 'Appointments'],
  ['prescriptions', 'Prescriptions'],
  ['laboratory', 'Lab reports'],
  ['radiology', 'Radiology'],
  ['documents', 'Documents'],
  ['invoices', 'Bills'],
  ['insurance', 'Insurance'],
  ['discharges', 'Discharge summaries'],
]

export default function Portal() {
  const { user } = useAuth()
  const [tab, setTab] = useState(0)
  const [profile, setProfile] = useState(null)
  const [timeline, setTimeline] = useState([])
  const [data, setData] = useState({})
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    setError(null)

    const load = async () => {
      // A patient account is scoped to its own record by the API; staff viewing
      // this screen see the patient they are linked to (or the first record).
      const patientList = await api.get(endpoints.patients, { params: { page_size: 1 } })
      const patient = patientList.data.results?.[0]
      if (!patient) {
        if (!cancelled) setError('No patient record is linked to this account.')
        return
      }
      const [overview, timelineResponse, appointments, prescriptions, laboratory, radiology,
        documents, invoices, policies, discharges] = await Promise.all([
        api.get(`${endpoints.patients}${patient.id}/overview/`),
        api.get(`${endpoints.patients}${patient.id}/timeline/`),
        api.get(endpoints.appointments, { params: { patient: patient.id, page_size: 20 } }),
        api.get(endpoints.prescriptions, { params: { patient: patient.id, page_size: 20 } }),
        api.get(endpoints.laboratory, { params: { patient: patient.id, page_size: 20 } }),
        api.get(endpoints.radiology, { params: { patient: patient.id, page_size: 20 } }),
        api.get(endpoints.documents, { params: { patient: patient.id, page_size: 20 } }),
        api.get(endpoints.invoices, { params: { patient: patient.id, page_size: 20 } }),
        api.get(endpoints.insurancePolicies, { params: { patient: patient.id, page_size: 20 } }),
        api.get(endpoints.dischargeSummaries, { params: { patient: patient.id, page_size: 20 } }),
      ])
      if (cancelled) return
      setProfile(overview.data)
      setTimeline(timelineResponse.data.events || [])
      setData({
        appointments: appointments.data.results || [],
        prescriptions: prescriptions.data.results || [],
        laboratory: laboratory.data.results || [],
        radiology: radiology.data.results || [],
        documents: documents.data.results || [],
        invoices: invoices.data.results || [],
        insurance: policies.data.results || [],
        discharges: discharges.data.results || [],
      })
    }

    load().catch((err) =>
      !cancelled && setError(err.friendlyMessage || 'Unable to load the patient portal.'),
    )
    return () => {
      cancelled = true
    }
  }, [])

  if (error) return <ErrorState message={error} />
  if (!profile) return <Loading label="Loading your records…" />

  const patient = profile.patient
  const rows = data[TABS[tab][0]] || []

  return (
    <Box>
      <PageHeader
        title="My Health Portal"
        subtitle={`${patient.name} · ${patient.patient_id} · signed in as ${user?.role_name}`}
        breadcrumb="Patient"
      />
      <DemoNotice>
        This portal shows only the records linked to your account. All content is fictional demo data.
      </DemoNotice>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 4 }}>
          <SectionCard title="Profile">
            <Stack direction="row" flexWrap="wrap" gap={2}>
              <Field label="Age / Gender" value={`${patient.age ?? '—'} · ${patient.gender_label}`} />
              <Field label="Blood group" value={patient.blood_group} />
              <Field label="Phone" value={patient.phone} />
              <Field label="Email" value={patient.email} />
              <Field label="Department" value={patient.department_name} />
              <Field label="Doctor" value={patient.doctor_name} />
              <Field label="Insurance" value={patient.insurance_provider || 'Self pay'} />
              <Field label="Policy" value={patient.insurance_policy_number} mono />
            </Stack>
            {patient.allergies ? (
              <>
                <Divider sx={{ my: 1.5 }} />
                <Typography variant="caption" color="text.secondary">Known allergies</Typography>
                <Box>
                  {(patient.allergy_list || []).map((allergy) => (
                    <Chip key={allergy} size="small" color="warning" label={allergy} sx={{ mr: 0.5, mt: 0.5 }} />
                  ))}
                </Box>
              </>
            ) : null}
          </SectionCard>

          <SectionCard title="Latest vitals">
            {profile.latest_vitals ? (
              <Stack direction="row" flexWrap="wrap" gap={2}>
                <Field label="BP" value={profile.latest_vitals.blood_pressure} />
                <Field label="Pulse" value={profile.latest_vitals.pulse_bpm} />
                <Field label="SpO₂" value={`${profile.latest_vitals.spo2}%`} />
                <Field label="Recorded" value={String(profile.latest_vitals.recorded_at).slice(0, 16).replace('T', ' ')} />
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary">No vitals recorded yet.</Typography>
            )}
          </SectionCard>
        </Grid>

        <Grid size={{ xs: 12, lg: 8 }}>
          <SectionCard>
            <Tabs value={tab} onChange={(_, value) => setTab(value)} variant="scrollable" scrollButtons="auto">
              {TABS.map(([key, label]) => <Tab key={key} label={`${label} (${(data[key] || []).length})`} />)}
            </Tabs>
            <Box sx={{ pt: 2 }}>
              {rows.length === 0 ? (
                <Alert severity="info">No records in this section.</Alert>
              ) : (
                <Stack spacing={1}>
                  {rows.map((row) => (
                    <Paper key={row.id} variant="outlined" sx={{ p: 1.5 }}>
                      {tab === 0 ? (
                        <Stack direction="row" gap={2} flexWrap="wrap" alignItems="center">
                          <Chip size="small" label={row.appointment_id} />
                          <Typography variant="body2">{row.date} · {String(row.time).slice(0, 5)}</Typography>
                          <Typography variant="body2">{row.doctor_name}</Typography>
                          <StatusChip value={row.status} label={row.status_label} />
                        </Stack>
                      ) : null}
                      {tab === 1 ? (
                        <Stack gap={0.5}>
                          <Stack direction="row" gap={1} alignItems="center">
                            <Chip size="small" label={row.prescription_id} />
                            <Typography variant="body2">{row.date} · {row.doctor_name}</Typography>
                            <StatusChip value={row.status} label={row.status_label} />
                          </Stack>
                          <Typography variant="body2" color="text.secondary">
                            {(row.items || []).map((item) => `${item.medicine_name} (${item.dosage}, ${item.frequency})`).join(' · ')}
                          </Typography>
                        </Stack>
                      ) : null}
                      {tab === 2 ? (
                        <Stack direction="row" gap={2} flexWrap="wrap" alignItems="center">
                          <Chip size="small" label={row.lab_id} />
                          <Typography variant="body2">{row.test_name}</Typography>
                          <Typography variant="body2">{row.result || 'pending'} {row.unit}</Typography>
                          <StatusChip value={row.flag} label={row.flag_label} />
                          <StatusChip value={row.status} label={row.status_label} />
                        </Stack>
                      ) : null}
                      {tab === 3 ? (
                        <Stack direction="row" gap={2} flexWrap="wrap" alignItems="center">
                          <Chip size="small" label={row.scan_id} />
                          <Typography variant="body2">{row.scan_type_label} · {row.body_part}</Typography>
                          <StatusChip value={row.status} label={row.status_label} />
                        </Stack>
                      ) : null}
                      {tab === 4 ? (
                        <Stack direction="row" gap={2} flexWrap="wrap" alignItems="center">
                          <Chip size="small" label={row.document_id} />
                          <Typography variant="body2">{row.title}</Typography>
                          <StatusChip value={row.ocr_status} label={row.ocr_status_label} />
                        </Stack>
                      ) : null}
                      {tab === 5 ? (
                        <Stack direction="row" gap={2} flexWrap="wrap" alignItems="center">
                          <Chip size="small" label={row.invoice_number} />
                          <Typography variant="body2">{row.date}</Typography>
                          <Typography variant="body2">Payable {row.patient_payable}</Typography>
                          <Typography variant="body2">Paid {row.paid_amount}</Typography>
                          <StatusChip value={row.payment_status} label={row.status_label} />
                        </Stack>
                      ) : null}
                      {tab === 6 ? (
                        <Stack direction="row" gap={2} flexWrap="wrap" alignItems="center">
                          <Chip size="small" label={row.policy_number} />
                          <Typography variant="body2">{row.provider_name}</Typography>
                          <Typography variant="body2">Coverage {row.coverage_amount}</Typography>
                          <StatusChip value={row.status} label={row.status_label} />
                        </Stack>
                      ) : null}
                      {tab === 7 ? (
                        <Stack direction="row" gap={2} flexWrap="wrap" alignItems="center">
                          <Chip size="small" label={row.discharge_id} />
                          <Typography variant="body2">{String(row.discharge_date || '—').slice(0, 10)}</Typography>
                          <StatusChip value={row.status} label={row.status_label} />
                        </Stack>
                      ) : null}
                    </Paper>
                  ))}
                </Stack>
              )}
            </Box>
          </SectionCard>

          <SectionCard title="My timeline" subtitle={`${timeline.length} event(s)`}>
            <Stack spacing={0} sx={{ maxHeight: 320, overflowY: 'auto' }}>
              {timeline.slice(0, 20).map((event, index) => (
                <Box className="timeline-item" key={`${event.type}-${index}`}>
                  <Box sx={{ position: 'absolute', left: 2, top: 6, width: 16, height: 16, borderRadius: '50%', background: '#0f766e', border: '3px solid #fff', boxShadow: '0 0 0 1px #cbd5e1' }} />
                  <Typography variant="caption" color="text.secondary">
                    {String(event.date).slice(0, 16).replace('T', ' · ')}
                  </Typography>
                  <Typography variant="subtitle2">{event.title}</Typography>
                  {event.description ? (
                    <Typography variant="body2" color="text.secondary">{event.description}</Typography>
                  ) : null}
                </Box>
              ))}
            </Stack>
          </SectionCard>
        </Grid>
      </Grid>
    </Box>
  )
}
