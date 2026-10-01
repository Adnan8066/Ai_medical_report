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
    { name: 'doctor_id', label: 'Doctor ID', required: true, span: 4 },
    { name: 'name', label: 'Name', required: true, span: 8 },
    { name: 'department', label: 'Department (ID)', type: 'number', span: 4 },
    { name: 'designation', label: 'Designation', type: 'select', span: 4, options: ['hod','senior_consultant','consultant','associate_consultant','registrar','resident','visiting'].map((v) => ({ value: v, label: v.replaceAll('_', ' ') })) },
    { name: 'qualification', label: 'Qualification', span: 4 },
    { name: 'experience_years', label: 'Experience (years)', type: 'number', span: 3 },
    { name: 'consultation_fee', label: 'Consultation fee', type: 'number', span: 3 },
    { name: 'room_number', label: 'Room', span: 3 },
    { name: 'phone_extension', label: 'Extension', span: 3 },
    { name: 'email', label: 'Email', span: 6 },
    { name: 'available_days', label: 'Available days', span: 6 },
    { name: 'availability', label: 'Availability', type: 'select', span: 4, options: ['available','in_consultation','in_surgery','on_rounds','off_duty','on_leave'].map((v) => ({ value: v, label: v.replaceAll('_', ' ') })) },
    { name: 'status', label: 'Status', type: 'select', span: 4, options: ['active','on_leave','inactive'].map((v) => ({ value: v, label: v.replaceAll('_', ' ') })) },
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
    { name: 'name', label: 'Name', required: true, span: 6 },
    { name: 'code', label: 'Code', required: true, span: 6 },
    { name: 'floor', label: 'Floor', span: 4 }, { name: 'location', label: 'Location', span: 4 },
    { name: 'contact_extension', label: 'Extension', span: 4 },
    { name: 'bed_count', label: 'Beds', type: 'number', span: 4 },
    { name: 'hod', label: 'HOD (doctor ID)', type: 'number', span: 4 },
    { name: 'description', label: 'Description', multiline: true, span: 12 },
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
    { name: 'patient', label: 'Patient (ID)', type: 'number', required: true, span: 4 },
    { name: 'doctor', label: 'Doctor (ID)', type: 'number', required: true, span: 4 },
    { name: 'department', label: 'Department (ID)', type: 'number', span: 4 },
    { name: 'date', label: 'Date', type: 'date', required: true, span: 4 },
    { name: 'time', label: 'Time (HH:MM)', required: true, span: 4 },
    { name: 'appointment_type', label: 'Type', type: 'select', span: 4, options: ['consultation','follow_up','procedure','diagnostic','vaccination','emergency','teleconsultation'].map((v) => ({ value: v, label: v.replaceAll('_', ' ') })) },
    { name: 'reason', label: 'Reason', span: 12 },
    { name: 'status', label: 'Status', type: 'select', span: 6, options: ['scheduled','confirmed','completed','cancelled','no_show'].map((v) => ({ value: v, label: v.replaceAll('_', ' ') })) },
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
    { name: 'patient', label: 'Patient (ID)', type: 'number', required: true, span: 4 },
    { name: 'doctor', label: 'Doctor (ID)', type: 'number', required: true, span: 4 },
    { name: 'visit_date', label: 'Visit date', type: 'date', required: true, span: 4 },
    { name: 'chief_complaint', label: 'Chief complaint', span: 12 },
    { name: 'symptoms', label: 'Symptoms', multiline: true, span: 12 },
    { name: 'consultation_notes', label: 'Consultation notes', multiline: true, span: 12 },
    { name: 'diagnosis', label: 'Diagnosis', span: 6 },
    { name: 'follow_up_date', label: 'Follow-up date', type: 'date', span: 6 },
    { name: 'status', label: 'Status', type: 'select', span: 6, options: ['waiting','in_consultation','completed','referred','follow_up_required','cancelled'].map((v) => ({ value: v, label: v.replaceAll('_', ' ') })) },
  ],
})
