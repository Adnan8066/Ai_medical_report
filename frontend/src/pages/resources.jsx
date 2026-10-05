import ResourcePage from '../components/ResourcePage.jsx'
import { endpoints } from '../services/api.js'
import { StatusChip } from '../components/ui.jsx'
import { formatCurrency, formatDate, formatNumber } from '../utils/format.js'

const page = (config) => () => <ResourcePage config={config} />

export const DoctorsPage = page({
  title: 'Doctors', subtitle: 'Clinicians across all departments', module: 'doctors',
  endpoint: endpoints.doctors, createLabel: 'Add doctor',
  columns: [
    { key: 'doctor_id', label: 'Doctor ID', render: (row) => <span className="mono">{row.doctor_id}</span> },
    { key: 'name', label: 'Name' },
    { key: 'department_name', label: 'Department' }, { key: 'designation_label', label: 'Designation' },
    { key: 'specialization', label: 'Specialisation' },
    { key: 'experience_years', label: 'Experience', numeric: true, render: (row) => `${formatNumber(row.experience_years)} yrs` },
    { key: 'consultation_fee', label: 'Consultation fee', numeric: true, render: (row) => formatCurrency(row.consultation_fee, { decimals: 0 }) },
    { key: 'availability', label: 'Availability', render: (row) => <StatusChip value={row.availability} label={row.availability_label} /> },
  ],
  filters: [{ key: 'is_hod', label: 'HOD', options: [{ value: 'true', label: 'HOD only' }, { value: 'false', label: 'Non-HOD' }] }],
  fields: [
    { section: 'Identity', name: 'doctor_id', label: 'Doctor ID', required: true, span: 4 },
    { section: 'Identity', name: 'name', label: 'Full name', required: true, span: 8 },

    { section: 'Department & role', name: 'department', label: 'Department', type: 'autocomplete', span: 6, lookup: { endpoint: '/departments/', labelKey: (row) => `${row.name}${row.code ? ` (${row.code})` : ''}` }, placeholder: 'Search department…' },
    { section: 'Department & role', name: 'designation', label: 'Designation', type: 'select', span: 6, options: ['hod','senior_consultant','consultant','associate_consultant','registrar','resident','visiting'] },

    { section: 'Department & role', name: 'qualification', label: 'Qualification', span: 6 },
    { section: 'Department & role', name: 'specialization', label: 'Specialisation', span: 6 },

    { section: 'Practice details', name: 'experience_years', label: 'Experience (years)', type: 'number', span: 4 },
    { section: 'Practice details', name: 'consultation_fee', label: 'Consultation fee', type: 'number', span: 4 },
    { section: 'Practice details', name: 'room_number', label: 'Room', span: 4 },

    { section: 'Contact & availability', name: 'phone_extension', label: 'Extension', span: 6 },
    { section: 'Contact & availability', name: 'email', label: 'Email', type: 'email', span: 6 },
    { section: 'Contact & availability', name: 'available_days', label: 'Available days', span: 6 },
    { section: 'Contact & availability', name: 'availability', label: 'Availability', type: 'select', span: 6, options: ['available','in_consultation','in_surgery','on_rounds','off_duty','on_leave'] },
    { section: 'Contact & availability', name: 'status', label: 'Status', type: 'select', span: 12, options: ['active','on_leave','inactive'] },
  ],
  detailFields: [
    { name: 'doctor_id', label: 'Doctor ID' }, { name: 'name', label: 'Name' },
    { name: 'department_name', label: 'Department' }, { name: 'qualification', label: 'Qualification' },
    { name: 'specialization', label: 'Specialisation' }, { name: 'room_number', label: 'Room' },
    { name: 'available_days', label: 'OPD days' },
  ],
})

export const DepartmentsPage = page({
  title: 'Departments', subtitle: 'Clinical and support departments', module: 'departments',
  endpoint: endpoints.departments, createLabel: 'Add department',
  columns: [
    { key: 'code', label: 'Code', render: (row) => <span className="mono">{row.code}</span> },
    { key: 'name', label: 'Department' },
    { key: 'hod_name', label: 'HOD', render: (row) => row.hod_name || '—' },
    { key: 'floor', label: 'Floor' }, { key: 'location', label: 'Location' },
    { key: 'contact_extension', label: 'Ext.', render: (row) => <span className="mono">{row.contact_extension || '—'}</span> },
    { key: 'doctor_count', label: 'Doctors', numeric: true, render: (row) => formatNumber(row.doctor_count) },
    { key: 'bed_count', label: 'Beds', numeric: true, render: (row) => formatNumber(row.bed_count) },
  ],
  fields: [
    { section: 'Department identity', name: 'name', label: 'Name', required: true, span: 6 },
    { section: 'Department identity', name: 'code', label: 'Code', required: true, span: 6 },

    { section: 'Location', name: 'floor', label: 'Floor', span: 4 },
    { section: 'Location', name: 'location', label: 'Location', span: 4 },
    { section: 'Location', name: 'contact_extension', label: 'Extension', span: 4 },

    { section: 'Capacity & leadership', name: 'bed_count', label: 'Beds', type: 'number', span: 6 },
    { section: 'Capacity & leadership', name: 'hod', label: 'Head of department', type: 'autocomplete', span: 6, lookup: { endpoint: '/doctors/', labelKey: (row) => `${row.name}${row.specialization ? ` — ${row.specialization}` : ''}` }, placeholder: 'Search doctor…' },

    { section: 'About', name: 'description', label: 'Description', type: 'multiline', span: 12, minRows: 3, maxRows: 8 },
  ],
  detailFields: [
    { name: 'name', label: 'Department' }, { name: 'code', label: 'Code' },
    { name: 'hod_name', label: 'HOD' }, { name: 'floor', label: 'Floor' },
    { name: 'bed_count', label: 'Beds' }, { name: 'description', label: 'Description' },
  ],
})

export const AppointmentsPage = page({
  title: 'Appointments', subtitle: 'Booking diary across every department', module: 'appointments',
  endpoint: endpoints.appointments, createLabel: 'Book appointment',
  columns: [
    { key: 'appointment_id', label: 'Appointment', render: (row) => <span className="mono">{row.appointment_id}</span> },
    { key: 'date', label: 'Date', render: (row) => formatDate(row.date) },
    { key: 'time', label: 'Time', render: (row) => String(row.time).slice(0, 5) },
    { key: 'patient_name', label: 'Patient' }, { key: 'doctor_name', label: 'Doctor' },
    { key: 'department_name', label: 'Department' }, { key: 'appointment_type_label', label: 'Type' },
    { key: 'status', label: 'Status', render: (row) => <StatusChip value={row.status} label={row.status_label} /> },
  ],
  filters: [{ key: 'status', label: 'Status', options: ['scheduled','confirmed','in_consultation','completed','cancelled','no_show'] }],
  fields: [
    { section: 'Patient & clinician', name: 'patient', label: 'Patient', type: 'autocomplete', required: true, span: 6, lookup: { endpoint: '/patients/', labelKey: (row) => `${row.name}${row.patient_id ? ` (${row.patient_id})` : ''}` }, placeholder: 'Search patient…' },
    { section: 'Patient & clinician', name: 'doctor', label: 'Doctor', type: 'autocomplete', required: true, span: 6, lookup: { endpoint: '/doctors/', labelKey: (row) => `${row.name}${row.specialization ? ` — ${row.specialization}` : ''}` }, placeholder: 'Search doctor…' },
    { section: 'Patient & clinician', name: 'department', label: 'Department', type: 'autocomplete', span: 12, lookup: { endpoint: '/departments/', labelKey: (row) => `${row.name}${row.code ? ` (${row.code})` : ''}` }, placeholder: 'Search department…' },

    { section: 'Schedule', name: 'date', label: 'Date', type: 'date', required: true, span: 4 },
    { section: 'Schedule', name: 'time', label: 'Time (HH:MM)', required: true, span: 4 },
    { section: 'Schedule', name: 'appointment_type', label: 'Type', type: 'select', span: 4, options: ['consultation','follow_up','procedure','diagnostic','vaccination','emergency','teleconsultation'] },

    { section: 'Details', name: 'reason', label: 'Reason', type: 'multiline', span: 12, minRows: 2, maxRows: 6 },
    { section: 'Details', name: 'status', label: 'Status', type: 'select', span: 12, options: ['scheduled','confirmed','completed','cancelled','no_show'] },
  ],
})

export const OpdPage = page({
  title: 'OPD Consultations', subtitle: 'Outpatient visit notes and diagnoses', module: 'opd',
  endpoint: endpoints.opd, createLabel: 'New consultation',
  columns: [
    { key: 'visit_id', label: 'Visit', render: (row) => <span className="mono">{row.visit_id}</span> },
    { key: 'visit_date', label: 'Visit date', render: (row) => formatDate(row.visit_date) },
    { key: 'patient_name', label: 'Patient' }, { key: 'doctor_name', label: 'Doctor' },
    { key: 'chief_complaint', label: 'Chief complaint', wrap: true },
    { key: 'diagnosis', label: 'Diagnosis', wrap: true, muted: true },
    { key: 'follow_up_date', label: 'Follow-up', render: (row) => formatDate(row.follow_up_date) },
    { key: 'status', label: 'Status', render: (row) => <StatusChip value={row.status} label={row.status_label} /> },
  ],
  fields: [
    { section: 'Visit context', name: 'patient', label: 'Patient', type: 'autocomplete', required: true, span: 6, lookup: { endpoint: '/patients/', labelKey: (row) => `${row.name}${row.patient_id ? ` (${row.patient_id})` : ''}` }, placeholder: 'Search patient…' },
    { section: 'Visit context', name: 'doctor', label: 'Doctor', type: 'autocomplete', required: true, span: 6, lookup: { endpoint: '/doctors/', labelKey: (row) => `${row.name}${row.specialization ? ` — ${row.specialization}` : ''}` }, placeholder: 'Search doctor…' },
    { section: 'Visit context', name: 'visit_date', label: 'Visit date', type: 'date', required: true, span: 12 },

    { section: 'Clinical notes', name: 'chief_complaint', label: 'Chief complaint', type: 'multiline', span: 12, minRows: 2, maxRows: 6 },
    { section: 'Clinical notes', name: 'symptoms', label: 'Symptoms', type: 'multiline', span: 12, minRows: 2, maxRows: 6 },
    { section: 'Clinical notes', name: 'consultation_notes', label: 'Consultation notes', type: 'multiline', span: 12, minRows: 3, maxRows: 10 },

    { section: 'Outcome', name: 'diagnosis', label: 'Diagnosis', span: 6 },
    { section: 'Outcome', name: 'follow_up_date', label: 'Follow-up date', type: 'date', span: 6 },
    { section: 'Outcome', name: 'status', label: 'Status', type: 'select', span: 12, options: ['waiting','in_consultation','completed','referred','follow_up_required','cancelled'] },
  ],
})