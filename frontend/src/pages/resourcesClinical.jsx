import ResourcePage from '../components/ResourcePage.jsx'
import { endpoints } from '../services/api.js'
import { StatusChip } from '../components/ui.jsx'
import { formatCurrency, formatDate, formatDateTime, formatDays, formatNumber } from '../utils/format.js'

const page = (config) => () => <ResourcePage config={config} />
const st = (row, key = 'status') => (
  <StatusChip value={row[key]} label={row[`${key}_label`]} />
)
const money = (value) => formatCurrency(value)

const patientLookup = { endpoint: '/patients/', labelKey: (row) => `${row.name}${row.patient_id ? ` (${row.patient_id})` : ''}` }
const doctorLookup = { endpoint: '/doctors/', labelKey: (row) => `${row.name}${row.specialization ? ` — ${row.specialization}` : ''}` }
const departmentLookup = { endpoint: '/departments/', labelKey: (row) => `${row.name}${row.code ? ` (${row.code})` : ''}` }

export const AdmissionsPage = page({
  title: 'Admissions & IPD',
  subtitle: 'Inpatient stays, ward allocation and discharge status',
  module: 'admissions',
  endpoint: endpoints.admissions,
  createLabel: 'Admit patient',
  columns: [
    { key: 'admission_id', label: 'Admission', render: (row) => <span className="mono">{row.admission_id}</span> },
    { key: 'patient_name', label: 'Patient' },
    { key: 'doctor_name', label: 'Doctor' },
    { key: 'department_name', label: 'Department' },
    { key: 'ward_name', label: 'Ward', render: (row) => row.ward_name || '—' },
    { key: 'bed_number', label: 'Bed', render: (row) => <span className="mono">{row.bed_number || '—'}</span> },
    { key: 'admission_date', label: 'Admitted', render: (row) => formatDateTime(row.admission_date) },
    { key: 'length_of_stay', label: 'Length of stay', numeric: true, render: (row) => formatDays(row.length_of_stay) },
    { key: 'status', label: 'Status', render: (row) => st(row) },
  ],
  filters: [{ key: 'status', label: 'Status', options: ['admitted', 'under_treatment', 'ready_for_discharge', 'discharged', 'transferred'] }],
  fields: [
    { section: 'Patient & clinician', name: 'patient', label: 'Patient', type: 'autocomplete', required: true, span: 6, lookup: patientLookup, placeholder: 'Search patient…' },
    { section: 'Patient & clinician', name: 'doctor', label: 'Doctor', type: 'autocomplete', required: true, span: 6, lookup: doctorLookup, placeholder: 'Search doctor…' },
    { section: 'Patient & clinician', name: 'department', label: 'Department', type: 'autocomplete', span: 12, lookup: departmentLookup, placeholder: 'Search department…' },

    { section: 'Stay schedule', name: 'admission_date', label: 'Admission date/time', required: true, span: 6, placeholder: 'YYYY-MM-DD HH:MM', help: 'YYYY-MM-DD HH:MM' },
    { section: 'Stay schedule', name: 'expected_discharge_date', label: 'Expected discharge', type: 'date', span: 6 },
    { section: 'Stay schedule', name: 'bed', label: 'Bed ID', type: 'number', span: 6, help: 'Occupies the bed automatically' },
    { section: 'Stay schedule', name: 'nurse', label: 'Nurse (staff ID)', type: 'number', span: 6 },

    { section: 'Clinical context', name: 'admission_reason', label: 'Reason', type: 'multiline', span: 12, minRows: 2, maxRows: 6 },
    { section: 'Clinical context', name: 'diagnosis', label: 'Provisional diagnosis', span: 6 },
    { section: 'Clinical context', name: 'status', label: 'Status', type: 'select', span: 6, options: ['admitted', 'under_treatment', 'ready_for_discharge', 'discharged'] },
    { section: 'Clinical context', name: 'treatment_plan', label: 'Treatment plan', type: 'multiline', span: 12, minRows: 3, maxRows: 10 },
  ],
  detailFields: [
    { name: 'admission_id', label: 'Admission' },
    { name: 'patient_name', label: 'Patient' },
    { name: 'bed_number', label: 'Bed' },
    { name: 'admission_reason', label: 'Reason' },
    { name: 'diagnosis', label: 'Diagnosis' },
    { name: 'treatment_plan', label: 'Plan' },
  ],
})

export const DischargePage = page({
  title: 'Discharge Summaries',
  subtitle: 'Doctor approval and clearance checklist',
  module: 'admissions',
  endpoint: endpoints.dischargeSummaries,
  createLabel: 'New discharge summary',
  columns: [
    { key: 'discharge_id', label: 'Summary', render: (row) => <span className="mono">{row.discharge_id}</span> },
    { key: 'patient_name', label: 'Patient' },
    { key: 'doctor_name', label: 'Doctor' },
    { key: 'admission_code', label: 'Admission', render: (row) => <span className="mono">{row.admission_code || '—'}</span> },
    { key: 'discharge_date', label: 'Discharge', render: (row) => formatDateTime(row.discharge_date) },
    { key: 'status', label: 'Status', render: (row) => st(row) },
    {
      key: 'workflow_progress',
      label: 'Workflow',
      sortable: false,
      numeric: true,
      render: (row) => `${row.workflow_progress?.completed ?? 0}/${row.workflow_progress?.total ?? 0} steps`,
    },
  ],
  filters: [{ key: 'status', label: 'Status', options: ['draft', 'pending_approval', 'approved', 'completed'] }],
  fields: [
    { section: 'Links', name: 'patient', label: 'Patient', type: 'autocomplete', required: true, span: 6, lookup: patientLookup, placeholder: 'Search patient…' },
    { section: 'Links', name: 'admission', label: 'Admission (ID)', type: 'number', span: 6 },
    { section: 'Links', name: 'doctor', label: 'Doctor', type: 'autocomplete', span: 12, lookup: doctorLookup, placeholder: 'Search doctor…' },

    { section: 'Schedule', name: 'discharge_date', label: 'Discharge date/time', span: 6, placeholder: 'YYYY-MM-DD HH:MM', help: 'YYYY-MM-DD HH:MM' },
    { section: 'Schedule', name: 'follow_up_date', label: 'Follow-up date', type: 'date', span: 6 },
    { section: 'Schedule', name: 'condition_on_discharge', label: 'Condition on discharge', span: 12 },

    { section: 'Clinical summary', name: 'diagnosis_summary', label: 'Diagnosis summary', type: 'multiline', span: 12, minRows: 3, maxRows: 10 },
    { section: 'Clinical summary', name: 'procedures', label: 'Procedures', type: 'multiline', span: 12, minRows: 2, maxRows: 6 },

    { section: 'Discharge plan', name: 'medications', label: 'Medications on discharge', type: 'multiline', span: 12, minRows: 2, maxRows: 8 },
    { section: 'Discharge plan', name: 'follow_up_instructions', label: 'Follow-up instructions', type: 'multiline', span: 12, minRows: 2, maxRows: 8 },
    { section: 'Discharge plan', name: 'status', label: 'Status', type: 'select', span: 12, options: ['draft', 'pending_approval', 'approved', 'completed'] },
  ],
  rowActions: [
    {
      label: 'Approve',
      endpoint: (row) => `${endpoints.dischargeSummaries}${row.id}/approve/`,
      confirm: 'Approve this discharge summary as the treating doctor?',
      isDisabled: (row) => row.doctor_approved,
      successMessage: (row) => `${row.discharge_id} approved and sent for final clearance.`,
    },
    {
      label: 'Complete discharge',
      endpoint: (row) => `${endpoints.dischargeSummaries}${row.id}/complete/`,
      confirm:
        'Complete the discharge? The patient will be marked discharged and their bed will be released for cleaning.',
      isDisabled: (row) => !row.doctor_approved || row.status === 'completed',
      successMessage: (row) => `${row.discharge_id} completed; bed released.`,
    },
  ],
  notice:
    'Discharge workflow: doctor approval → discharge summary → final bill → pharmacy clearance → insurance processing → follow-up appointment → discharge.',
  detailFields: [
    { name: 'discharge_id', label: 'Summary' },
    { name: 'patient_name', label: 'Patient' },
    { name: 'diagnosis_summary', label: 'Diagnosis' },
    { name: 'medications', label: 'Medications' },
    { name: 'follow_up_instructions', label: 'Instructions' },
  ],
})

export const LaboratoryPage = page({
  title: 'Laboratory',
  subtitle: 'Ordered tests, sample collection and reported results',
  module: 'laboratory',
  endpoint: endpoints.laboratory,
  createLabel: 'Order test',
  columns: [
    { key: 'lab_id', label: 'Lab ID', render: (row) => <span className="mono">{row.lab_id}</span> },
    { key: 'patient_name', label: 'Patient' },
    { key: 'doctor_name', label: 'Ordered by' },
    { key: 'test_name', label: 'Test' },
    { key: 'test_category', label: 'Category' },
    { key: 'result', label: 'Result', numeric: true, render: (row) => (row.result ? `${row.result} ${row.unit || ''}`.trim() : '—') },
    { key: 'reference_range', label: 'Reference range', muted: true },
    { key: 'flag', label: 'Flag', render: (row) => <StatusChip value={row.flag} label={row.flag_label} /> },
    { key: 'status', label: 'Status', render: (row) => st(row) },
    { key: 'report_date', label: 'Reported', render: (row) => formatDateTime(row.report_date) },
  ],
  filters: [
    { key: 'status', label: 'Status', options: ['ordered', 'sample_collected', 'processing', 'completed', 'cancelled'] },
    { key: 'flag', label: 'Flag', options: ['normal', 'high', 'low', 'critical', 'unknown'] },
  ],
  fields: [
    { section: 'Order', name: 'patient', label: 'Patient', type: 'autocomplete', required: true, span: 6, lookup: patientLookup, placeholder: 'Search patient…' },
    { section: 'Order', name: 'doctor', label: 'Doctor', type: 'autocomplete', span: 6, lookup: doctorLookup, placeholder: 'Search doctor…' },
    { section: 'Order', name: 'test', label: 'Test (ID)', type: 'number', required: true, span: 6 },
    { section: 'Order', name: 'status', label: 'Status', type: 'select', span: 6, options: ['ordered', 'sample_collected', 'processing', 'completed'] },

    { section: 'Result', name: 'result', label: 'Result', span: 6 },
    { section: 'Result', name: 'numeric_value', label: 'Numeric value', type: 'number', span: 6, help: 'Used to compute the normal/high/low flag' },
    { section: 'Result', name: 'reference_range', label: 'Reference range', span: 6 },
    { section: 'Result', name: 'remarks', label: 'Remarks', span: 6 },
  ],
  detailFields: [
    { name: 'lab_id', label: 'Lab ID' },
    { name: 'patient_name', label: 'Patient' },
    { name: 'test_name', label: 'Test' },
    { name: 'result', label: 'Result' },
    { name: 'reference_range', label: 'Reference range' },
    { name: 'remarks', label: 'Remarks' },
  ],
})

export const RadiologyPage = page({
  title: 'Radiology',
  subtitle: 'Imaging requests, findings and reports',
  module: 'radiology',
  endpoint: endpoints.radiology,
  createLabel: 'Request study',
  columns: [
    { key: 'scan_id', label: 'Scan ID', render: (row) => <span className="mono">{row.scan_id}</span> },
    { key: 'patient_name', label: 'Patient' },
    { key: 'scan_type_label', label: 'Study' },
    { key: 'body_part', label: 'Body part' },
    { key: 'appointment_date', label: 'Scheduled', render: (row) => formatDateTime(row.appointment_date) },
    { key: 'radiologist_name', label: 'Radiologist' },
    { key: 'price', label: 'Price', numeric: true, render: (row) => money(row.price) },
    { key: 'status', label: 'Status', render: (row) => st(row) },
  ],
  filters: [
    { key: 'scan_type', label: 'Type', options: ['xray', 'ct', 'mri', 'ultrasound', 'ecg', 'echo', 'mammography', 'pet'] },
    { key: 'status', label: 'Status', options: ['ordered', 'scheduled', 'in_progress', 'completed', 'cancelled'] },
  ],
  fields: [
    { section: 'Order', name: 'patient', label: 'Patient', type: 'autocomplete', required: true, span: 6, lookup: patientLookup, placeholder: 'Search patient…' },
    { section: 'Order', name: 'doctor', label: 'Referring doctor', type: 'autocomplete', span: 6, lookup: doctorLookup, placeholder: 'Search doctor…' },
    { section: 'Order', name: 'scan_type', label: 'Study type', type: 'select', required: true, span: 6, options: ['xray', 'ct', 'mri', 'ultrasound', 'ecg', 'echo', 'mammography', 'pet'] },
    { section: 'Order', name: 'body_part', label: 'Body part', span: 6 },

    { section: 'Schedule & cost', name: 'appointment_date', label: 'Appointment', span: 6, placeholder: 'YYYY-MM-DD HH:MM', help: 'YYYY-MM-DD HH:MM' },
    { section: 'Schedule & cost', name: 'price', label: 'Price', type: 'number', span: 6 },
    { section: 'Schedule & cost', name: 'radiologist_name', label: 'Radiologist', span: 6 },
    { section: 'Schedule & cost', name: 'status', label: 'Status', type: 'select', span: 6, options: ['ordered', 'scheduled', 'in_progress', 'completed'] },

    { section: 'Report', name: 'findings', label: 'Findings', type: 'multiline', span: 12, minRows: 2, maxRows: 8 },
    { section: 'Report', name: 'impression', label: 'Impression', type: 'multiline', span: 12, minRows: 2, maxRows: 6 },
    { section: 'Report', name: 'report', label: 'Full report', type: 'multiline', span: 12, minRows: 3, maxRows: 12 },
  ],
  detailFields: [
    { name: 'scan_id', label: 'Scan ID' },
    { name: 'patient_name', label: 'Patient' },
    { name: 'scan_type_label', label: 'Study' },
    { name: 'findings', label: 'Findings' },
    { name: 'impression', label: 'Impression' },
  ],
})

export const PharmacyPage = page({
  title: 'Pharmacy Stock',
  subtitle: 'Medicines, stock levels and expiry alerts',
  module: 'pharmacy',
  endpoint: endpoints.medicines,
  createLabel: 'Add medicine',
  columns: [
    { key: 'medicine_id', label: 'Medicine ID', render: (row) => <span className="mono">{row.medicine_id}</span> },
    { key: 'name', label: 'Medicine' },
    { key: 'generic_name', label: 'Generic' },
    { key: 'category_label', label: 'Category' },
    { key: 'manufacturer', label: 'Manufacturer' },
    { key: 'batch_number', label: 'Batch', render: (row) => <span className="mono">{row.batch_number || '—'}</span> },
    { key: 'stock', label: 'Stock', numeric: true, render: (row) => `${formatNumber(row.stock)} ${row.unit}` },
    { key: 'reorder_level', label: 'Reorder at', numeric: true, render: (row) => formatNumber(row.reorder_level) },
    { key: 'expiry_date', label: 'Expiry', render: (row) => formatDate(row.expiry_date) },
    { key: 'price', label: 'Price', numeric: true, render: (row) => money(row.price) },
    { key: 'status', label: 'Status', render: (row) => st(row) },
  ],
  filters: [
    { key: 'status', label: 'Status', options: ['available', 'low_stock', 'out_of_stock', 'expiring_soon', 'expired', 'discontinued'] },
    { key: 'low_stock', label: 'Stock alert', options: [{ value: 'true', label: 'At/below reorder level' }] },
    { key: 'expiring', label: 'Expiry', options: [{ value: 'true', label: 'Expiring within 90 days' }] },
  ],
  fields: [
    { section: 'Identity', name: 'name', label: 'Medicine name', required: true, span: 6 },
    { section: 'Identity', name: 'generic_name', label: 'Generic name', span: 6 },
    { section: 'Identity', name: 'category', label: 'Category', type: 'select', span: 6, options: ['antibiotic', 'analgesic', 'cardiovascular', 'antidiabetic', 'respiratory', 'gastrointestinal', 'neurological', 'vitamin', 'vaccine', 'iv_fluid', 'topical', 'other'] },
    { section: 'Identity', name: 'manufacturer', label: 'Manufacturer', span: 6 },

    { section: 'Stock & batch', name: 'batch_number', label: 'Batch number', span: 6 },
    { section: 'Stock & batch', name: 'expiry_date', label: 'Expiry date', type: 'date', span: 6 },
    { section: 'Stock & batch', name: 'stock', label: 'Stock', type: 'number', span: 4 },
    { section: 'Stock & batch', name: 'reorder_level', label: 'Reorder level', type: 'number', span: 4 },
    { section: 'Stock & batch', name: 'unit', label: 'Unit', span: 4 },

    { section: 'Pricing & policy', name: 'price', label: 'Selling price', type: 'number', span: 4 },
    { section: 'Pricing & policy', name: 'cost_price', label: 'Cost price', type: 'number', span: 4 },
    { section: 'Pricing & policy', name: 'prescription_required', label: 'Prescription required', type: 'select', span: 4, options: [{ value: 'true', label: 'Yes' }, { value: 'false', label: 'No' }] },

    { section: 'Storage & status', name: 'storage', label: 'Storage', span: 6 },
    { section: 'Storage & status', name: 'status', label: 'Status', type: 'select', span: 6, options: ['available', 'discontinued'], help: 'Stock-driven statuses are calculated automatically' },
  ],
  detailFields: [
    { name: 'medicine_id', label: 'Medicine ID' },
    { name: 'name', label: 'Medicine' },
    { name: 'generic_name', label: 'Generic' },
    { name: 'manufacturer', label: 'Manufacturer' },
    { name: 'stock', label: 'Stock' },
    { name: 'expiry_date', label: 'Expiry' },
  ],
})

export const PrescriptionsPage = page({
  title: 'Prescriptions',
  subtitle: 'Prescribing and dispensing record',
  module: 'prescriptions',
  endpoint: endpoints.prescriptions,
  createLabel: 'New prescription',
  columns: [
    { key: 'prescription_id', label: 'Rx ID', render: (row) => <span className="mono">{row.prescription_id}</span> },
    { key: 'patient_name', label: 'Patient' },
    { key: 'doctor_name', label: 'Prescriber' },
    { key: 'date', label: 'Date', render: (row) => formatDate(row.date) },
    {
      key: 'items',
      label: 'Medicines',
      sortable: false,
      wrap: true,
      muted: true,
      render: (row) => (row.items || []).map((item) => item.medicine_name).join(', ') || '—',
    },
    { key: 'total_amount', label: 'Value', numeric: true, render: (row) => money(row.total_amount) },
    { key: 'status', label: 'Status', render: (row) => st(row) },
  ],
  filters: [{ key: 'status', label: 'Status', options: ['pending', 'partially_dispensed', 'dispensed', 'cancelled'] }],
  fields: [
    { section: 'Order', name: 'patient', label: 'Patient', type: 'autocomplete', required: true, span: 6, lookup: patientLookup, placeholder: 'Search patient…' },
    { section: 'Order', name: 'doctor', label: 'Doctor', type: 'autocomplete', span: 6, lookup: doctorLookup, placeholder: 'Search doctor…' },
    { section: 'Order', name: 'date', label: 'Date', type: 'date', span: 6 },
    { section: 'Order', name: 'status', label: 'Status', type: 'select', span: 6, options: ['pending', 'partially_dispensed', 'dispensed', 'cancelled'] },

    { section: 'Prescribed medicines', name: 'notes', label: 'Notes', type: 'multiline', span: 12, minRows: 2, maxRows: 6 },
    {
      section: 'Prescribed medicines',
      name: 'items',
      label: 'Prescribed medicines',
      type: 'items',
      span: 12,
      addLabel: 'Add medicine',
      help: 'Link a medicine from the pharmacy catalogue so dispensing can decrement stock.',
      emptyText: 'Add at least one medicine line.',
      itemDefaults: { medicine: '', medicine_name: '', dosage: '', frequency: 'Twice daily', duration: '5 days', quantity: 10 },
      itemFields: [
        { name: 'medicine', label: 'Medicine ID', type: 'number', width: 110 },
        { name: 'medicine_name', label: 'Medicine name', width: 240 },
        { name: 'dosage', label: 'Dosage', width: 130 },
        { name: 'frequency', label: 'Frequency', width: 140 },
        { name: 'duration', label: 'Duration', width: 120 },
        { name: 'quantity', label: 'Qty', type: 'number', width: 80 },
      ],
    },
  ],
  rowActions: [
    {
      label: 'Dispense',
      endpoint: (row) => `${endpoints.prescriptions}${row.id}/dispense/`,
      confirm: 'Dispense every pending medicine on this prescription? Stock will be decremented.',
      isDisabled: (row) => row.status === 'dispensed',
      successMessage: (row) => `${row.prescription_id} dispensed and pharmacy stock updated.`,
    },
  ],
  detailFields: [
    { name: 'prescription_id', label: 'Rx ID' },
    { name: 'patient_name', label: 'Patient' },
    { name: 'doctor_name', label: 'Prescriber' },
    { name: 'status_label', label: 'Status' },
    { name: 'notes', label: 'Notes' },
  ],
})

export const SurgeryPage = page({
  title: 'Operation Theatre',
  subtitle: 'Surgical scheduling across all theatres',
  module: 'surgery',
  endpoint: endpoints.surgery,
  createLabel: 'Schedule surgery',
  columns: [
    { key: 'surgery_id', label: 'Surgery', render: (row) => <span className="mono">{row.surgery_id}</span> },
    { key: 'patient_name', label: 'Patient' },
    { key: 'surgery_name', label: 'Procedure' },
    { key: 'surgeon_name', label: 'Surgeon' },
    { key: 'department_name', label: 'Department' },
    { key: 'ot_room', label: 'Theatre', render: (row) => <span className="mono">{row.ot_room}</span> },
    { key: 'date', label: 'Date', render: (row) => formatDate(row.date) },
    { key: 'start_time', label: 'Start', render: (row) => String(row.start_time).slice(0, 5) },
    { key: 'end_time', label: 'End', render: (row) => String(row.end_time || '—').slice(0, 5) },
    { key: 'anesthesia_label', label: 'Anaesthesia' },
    { key: 'status', label: 'Status', render: (row) => st(row) },
  ],
  filters: [
    { key: 'status', label: 'Status', options: ['scheduled', 'preparing', 'in_progress', 'completed', 'cancelled', 'postponed'] },
    { key: 'ot_room', label: 'Theatre', options: ['OT-1', 'OT-2', 'OT-3', 'OT-4', 'OT-5', 'OT-6'] },
  ],
  fields: [
    { section: 'Patient & procedure', name: 'patient', label: 'Patient', type: 'autocomplete', required: true, span: 6, lookup: patientLookup, placeholder: 'Search patient…' },
    { section: 'Patient & procedure', name: 'surgeon', label: 'Surgeon', type: 'autocomplete', required: true, span: 6, lookup: doctorLookup, placeholder: 'Search doctor…' },
    { section: 'Patient & procedure', name: 'department', label: 'Department', type: 'autocomplete', span: 6, lookup: departmentLookup, placeholder: 'Search department…' },
    { section: 'Patient & procedure', name: 'surgery_name', label: 'Procedure', required: true, span: 6 },
    { section: 'Patient & procedure', name: 'procedure_code', label: 'Procedure code', span: 12 },

    { section: 'Theatre schedule', name: 'ot_room', label: 'Theatre', required: true, span: 3 },
    { section: 'Theatre schedule', name: 'date', label: 'Date', type: 'date', required: true, span: 3 },
    { section: 'Theatre schedule', name: 'start_time', label: 'Start (HH:MM)', required: true, span: 3 },
    { section: 'Theatre schedule', name: 'end_time', label: 'End (HH:MM)', span: 3 },

    { section: 'Anaesthesia & cost', name: 'anesthetist', label: 'Anaesthetist (ID)', type: 'number', span: 6 },
    { section: 'Anaesthesia & cost', name: 'anesthesia_type', label: 'Anaesthesia type', type: 'select', span: 6, options: ['general', 'spinal', 'epidural', 'regional', 'local', 'sedation'] },
    { section: 'Anaesthesia & cost', name: 'estimated_cost', label: 'Estimated cost', type: 'number', span: 6 },
    { section: 'Anaesthesia & cost', name: 'blood_units_reserved', label: 'Blood units reserved', type: 'number', span: 6 },

    { section: 'Outcome', name: 'status', label: 'Status', type: 'select', span: 12, options: ['scheduled', 'preparing', 'in_progress', 'completed', 'cancelled', 'postponed'] },
    { section: 'Outcome', name: 'pre_op_notes', label: 'Pre-operative notes', type: 'multiline', span: 12, minRows: 2, maxRows: 8 },
    { section: 'Outcome', name: 'post_op_notes', label: 'Post-operative notes', type: 'multiline', span: 12, minRows: 2, maxRows: 8 },
  ],
  detailFields: [
    { name: 'surgery_id', label: 'Surgery' },
    { name: 'patient_name', label: 'Patient' },
    { name: 'surgery_name', label: 'Procedure' },
    { name: 'surgeon_name', label: 'Surgeon' },
    { name: 'ot_room', label: 'Theatre' },
    { name: 'pre_op_notes', label: 'Pre-op notes' },
    { name: 'post_op_notes', label: 'Post-op notes' },
  ],
})