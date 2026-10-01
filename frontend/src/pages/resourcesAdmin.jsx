import ResourcePage from '../components/ResourcePage.jsx'
import { endpoints } from '../services/api.js'
import { StatusChip } from '../components/ui.jsx'
import { formatCurrency, formatDate, formatDateTime, formatNumber } from '../utils/format.js'

const page = (config) => () => <ResourcePage config={config} />
const st = (row, key = 'status') => (
  <StatusChip value={row[key]} label={row[`${key}_label`]} />
)
const money = (value) => formatCurrency(value)

export const BillingPage = page({
  title: 'Billing',
  subtitle: 'Invoices, payments and outstanding balances',
  module: 'billing',
  endpoint: endpoints.invoices,
  createLabel: 'New invoice',
  columns: [
    { key: 'invoice_number', label: 'Invoice', render: (row) => <span className="mono">{row.invoice_number}</span> },
    { key: 'patient_name', label: 'Patient' },
    { key: 'date', label: 'Date', render: (row) => formatDate(row.date) },
    { key: 'subtotal', label: 'Subtotal', numeric: true, render: (row) => money(row.subtotal) },
    { key: 'discount', label: 'Discount', numeric: true, render: (row) => money(row.discount) },
    { key: 'tax_amount', label: 'Tax', numeric: true, render: (row) => money(row.tax_amount) },
    { key: 'insurance_amount', label: 'Insurance', numeric: true, render: (row) => money(row.insurance_amount) },
    { key: 'patient_payable', label: 'Payable', numeric: true, render: (row) => money(row.patient_payable) },
    { key: 'paid_amount', label: 'Paid', numeric: true, render: (row) => money(row.paid_amount) },
    { key: 'balance_due', label: 'Balance', numeric: true, render: (row) => money(row.balance_due) },
    { key: 'payment_status', label: 'Status', render: (row) => st(row, 'payment_status') },
  ],
  filters: [
    { key: 'status', label: 'Payment', options: ['paid', 'partially_paid', 'pending', 'cancelled'] },
    { key: 'service_type', label: 'Service', options: ['consultation', 'laboratory', 'radiology', 'pharmacy', 'room_charge', 'surgery', 'procedure', 'nursing', 'other'].map((v) => ({ value: v, label: v.replaceAll('_', ' ') })) },
  ],
  fields: [
    { name: 'patient', label: 'Patient (ID)', type: 'number', required: true, span: 4 },
    { name: 'doctor', label: 'Doctor (ID)', type: 'number', span: 4 },
    { name: 'admission', label: 'Admission (ID)', type: 'number', span: 4 },
    { name: 'date', label: 'Invoice date', type: 'date', required: true, span: 4 },
    { name: 'discount', label: 'Discount', type: 'number', span: 4 },
    { name: 'tax_rate', label: 'Tax rate %', type: 'number', span: 4 },
    { name: 'insurance_amount', label: 'Insurance amount', type: 'number', span: 4 },
    { name: 'paid_amount', label: 'Paid amount', type: 'number', span: 4 },
    { name: 'payment_method', label: 'Payment method', type: 'select', span: 4, options: ['cash', 'card', 'upi', 'net_banking', 'insurance', 'pending'].map((v) => ({ value: v, label: v.replaceAll('_', ' ') })) },
    { name: 'notes', label: 'Notes', span: 12 },
    {
      name: 'items',
      label: 'Billable services',
      type: 'items',
      span: 12,
      addLabel: 'Add service line',
      help: 'Totals, tax and the patient payable amount are calculated from these lines.',
      emptyText: 'Add at least one service line (consultation, laboratory, pharmacy, room charge…).',
      itemDefaults: { service_type: 'consultation', description: '', quantity: 1, unit_price: '' },
      itemFields: [
        {
          name: 'service_type',
          label: 'Service',
          type: 'select',
          options: ['consultation', 'laboratory', 'radiology', 'pharmacy', 'room_charge', 'surgery', 'procedure', 'nursing', 'other'].map((v) => ({ value: v, label: v.replaceAll('_', ' ') })),
          width: 150,
        },
        { name: 'description', label: 'Description', width: 260 },
        { name: 'quantity', label: 'Qty', type: 'number', width: 80 },
        { name: 'unit_price', label: 'Unit price', type: 'number', width: 120 },
      ],
    },
  ],
  rowActions: [
    {
      label: 'Record payment',
      endpoint: (row) => `${endpoints.invoices}${row.id}/record_payment/`,
      payload: (row) => {
        const balance = Number(row.balance_due ?? 0)
        const amount = window.prompt(
          `Record a payment for ${row.invoice_number}.\nOutstanding balance: ${balance.toFixed(2)}`,
          balance.toFixed(2),
        )
        if (!amount) return null
        return { amount, payment_method: 'cash' }
      },
      confirm: 'Record this payment against the invoice?',
      successMessage: (row, data) =>
        `${row.invoice_number}: payment recorded, status is now ${data.payment_status}.`,
    },
  ],
  detailFields: [
    { name: 'invoice_number', label: 'Invoice' },
    { name: 'patient_name', label: 'Patient' },
    { name: 'patient_payable', label: 'Payable' },
    { name: 'paid_amount', label: 'Paid' },
    { name: 'balance_due', label: 'Balance' },
    { name: 'status_label', label: 'Status' },
  ],
})

export const InsurancePage = page({
  title: 'Insurance Claims',
  subtitle: 'Claim submission, review and settlement',
  module: 'insurance',
  endpoint: endpoints.insuranceClaims,
  createLabel: 'Raise claim',
  columns: [
    { key: 'claim_number', label: 'Claim', render: (row) => <span className="mono">{row.claim_number}</span> },
    { key: 'patient_name', label: 'Patient' },
    { key: 'provider_name', label: 'Insurer' },
    { key: 'policy_number', label: 'Policy', render: (row) => <span className="mono">{row.policy_number}</span> },
    { key: 'invoice_number', label: 'Invoice', render: (row) => <span className="mono">{row.invoice_number || '—'}</span> },
    { key: 'claim_amount', label: 'Claimed', numeric: true, render: (row) => money(row.claim_amount) },
    { key: 'approved_amount', label: 'Approved', numeric: true, render: (row) => money(row.approved_amount) },
    { key: 'rejected_amount', label: 'Rejected', numeric: true, render: (row) => money(row.rejected_amount) },
    { key: 'submitted_date', label: 'Submitted', render: (row) => formatDate(row.submitted_date) },
    { key: 'status', label: 'Status', render: (row) => st(row) },
  ],
  filters: [
    { key: 'status', label: 'Status', options: ['submitted', 'under_review', 'approved', 'partially_approved', 'rejected', 'settled'] },
  ],
  fields: [
    { name: 'policy', label: 'Policy (ID)', type: 'number', required: true, span: 4 },
    { name: 'patient', label: 'Patient (ID)', type: 'number', required: true, span: 4 },
    { name: 'invoice', label: 'Invoice (ID)', type: 'number', span: 4 },
    { name: 'claim_amount', label: 'Claim amount', type: 'number', required: true, span: 4 },
    { name: 'approved_amount', label: 'Approved amount', type: 'number', span: 4 },
    { name: 'submitted_date', label: 'Submitted date', type: 'date', span: 4 },
    { name: 'diagnosis_code', label: 'Diagnosis code', span: 4 },
    { name: 'status', label: 'Status', type: 'select', span: 4, options: ['submitted', 'under_review', 'approved', 'partially_approved', 'rejected', 'settled'].map((v) => ({ value: v, label: v.replaceAll('_', ' ') })) },
    { name: 'treatment_summary', label: 'Treatment summary', span: 12 },
    { name: 'notes', label: 'Notes', multiline: true, span: 12 },
  ],
  detailFields: [
    { name: 'claim_number', label: 'Claim' },
    { name: 'patient_name', label: 'Patient' },
    { name: 'provider_name', label: 'Insurer' },
    { name: 'claim_amount', label: 'Claimed' },
    { name: 'approved_amount', label: 'Approved' },
    { name: 'rejection_reason', label: 'Rejection reason' },
  ],
})

export const InventoryPage = page({
  title: 'Inventory & Stores',
  subtitle: 'Stock items, suppliers, purchase orders and movements',
  module: 'inventory',
  endpoint: endpoints.inventory,
  createLabel: 'Add stock item',
  columns: [
    { key: 'item_code', label: 'Item code', render: (row) => <span className="mono">{row.item_code}</span> },
    { key: 'name', label: 'Item' },
    { key: 'category_label', label: 'Category' },
    { key: 'stock', label: 'Stock', numeric: true, render: (row) => `${formatNumber(row.stock)} ${row.unit}` },
    { key: 'reorder_level', label: 'Reorder at', numeric: true, render: (row) => formatNumber(row.reorder_level) },
    { key: 'unit_price', label: 'Unit price', numeric: true, render: (row) => money(row.unit_price) },
    { key: 'stock_value', label: 'Value', numeric: true, render: (row) => money(row.stock_value) },
    { key: 'supplier_name', label: 'Supplier' },
    { key: 'location', label: 'Location' },
    { key: 'expiry_date', label: 'Expiry', render: (row) => formatDate(row.expiry_date) },
    { key: 'status', label: 'Status', render: (row) => st(row) },
  ],
  filters: [
    { key: 'category', label: 'Category', options: ['medical_equipment', 'surgical_supplies', 'ppe', 'laboratory_supplies', 'medicines', 'office_supplies', 'housekeeping', 'it_equipment'].map((v) => ({ value: v, label: v.replaceAll('_', ' ') })) },
    { key: 'status', label: 'Status', options: ['available', 'low_stock', 'out_of_stock', 'expiring_soon', 'expired', 'discontinued'] },
    { key: 'low_stock', label: 'Alert', options: [{ value: 'true', label: 'At/below reorder level' }] },
  ],
  fields: [
    { name: 'name', label: 'Item name', required: true, span: 6 },
    { name: 'category', label: 'Category', type: 'select', required: true, span: 6, options: ['medical_equipment', 'surgical_supplies', 'ppe', 'laboratory_supplies', 'medicines', 'office_supplies', 'housekeeping', 'it_equipment'].map((v) => ({ value: v, label: v.replaceAll('_', ' ') })) },
    { name: 'description', label: 'Description', span: 12 },
    { name: 'unit', label: 'Unit', span: 4 },
    { name: 'stock', label: 'Stock', type: 'number', span: 4 },
    { name: 'reorder_level', label: 'Reorder level', type: 'number', span: 4 },
    { name: 'unit_price', label: 'Unit price', type: 'number', span: 4 },
    { name: 'supplier', label: 'Supplier (ID)', type: 'number', span: 4 },
    { name: 'location', label: 'Store location', span: 4 },
    { name: 'batch_number', label: 'Batch number', span: 6 },
    { name: 'expiry_date', label: 'Expiry date', type: 'date', span: 6 },
    { name: 'status', label: 'Status', type: 'select', span: 6, options: ['available', 'discontinued'].map((v) => ({ value: v, label: v })) },
  ],
  detailFields: [
    { name: 'item_code', label: 'Item code' },
    { name: 'name', label: 'Item' },
    { name: 'category_label', label: 'Category' },
    { name: 'stock', label: 'Stock' },
    { name: 'location', label: 'Location' },
    { name: 'supplier_name', label: 'Supplier' },
  ],
})

export const PurchaseOrdersPage = page({
  title: 'Purchase Orders',
  subtitle: 'Procurement from suppliers',
  module: 'inventory',
  endpoint: endpoints.purchaseOrders,
  createLabel: 'New purchase order',
  columns: [
    { key: 'po_number', label: 'PO number', render: (row) => <span className="mono">{row.po_number}</span> },
    { key: 'supplier_name', label: 'Supplier' },
    { key: 'order_date', label: 'Ordered', render: (row) => formatDate(row.order_date) },
    { key: 'expected_date', label: 'Expected', render: (row) => formatDate(row.expected_date) },
    { key: 'total_amount', label: 'Total', numeric: true, render: (row) => money(row.total_amount) },
    { key: 'status', label: 'Status', render: (row) => st(row) },
  ],
  filters: [{ key: 'status', label: 'Status', options: ['draft', 'submitted', 'approved', 'partially_received', 'received', 'cancelled'] }],
  fields: [
    { name: 'supplier', label: 'Supplier (ID)', type: 'number', required: true, span: 4 },
    { name: 'order_date', label: 'Order date', type: 'date', span: 4 },
    { name: 'expected_date', label: 'Expected date', type: 'date', span: 4 },
    { name: 'status', label: 'Status', type: 'select', span: 6, options: ['draft', 'submitted', 'approved', 'partially_received', 'received', 'cancelled'].map((v) => ({ value: v, label: v.replaceAll('_', ' ') })) },
    { name: 'notes', label: 'Notes', span: 12 },
    {
      name: 'items',
      label: 'Order lines',
      type: 'items',
      span: 12,
      addLabel: 'Add order line',
      help: 'Link a stock item and quantity; the order total is calculated from the lines.',
      itemDefaults: { item: '', description: '', quantity: 10, unit_price: '' },
      itemFields: [
        { name: 'item', label: 'Item ID', type: 'number', width: 100 },
        { name: 'description', label: 'Description', width: 260 },
        { name: 'quantity', label: 'Qty', type: 'number', width: 80 },
        { name: 'unit_price', label: 'Unit price', type: 'number', width: 120 },
      ],
    },
  ],
  rowActions: [
    {
      label: 'Receive',
      endpoint: (row) => `${endpoints.purchaseOrders}${row.id}/receive/`,
      confirm: 'Receive this purchase order into stock? Stock levels will increase.',
      isDisabled: (row) => row.status === 'received' || row.status === 'cancelled',
      successMessage: (row) => `${row.po_number} received; stock movements recorded.`,
    },
  ],
  detailFields: [
    { name: 'po_number', label: 'PO number' },
    { name: 'supplier_name', label: 'Supplier' },
    { name: 'total_amount', label: 'Total' },
    { name: 'status_label', label: 'Status' },
  ],
})

export const StaffPage = page({
  title: 'Staff',
  subtitle: 'Doctors, nurses, technicians and support teams',
  module: 'staff',
  endpoint: endpoints.staff,
  createLabel: 'Add staff member',
  columns: [
    { key: 'employee_id', label: 'Employee ID', render: (row) => <span className="mono">{row.employee_id}</span> },
    { key: 'name', label: 'Name' },
    { key: 'role_label', label: 'Role' },
    { key: 'department_name', label: 'Department' },
    { key: 'designation', label: 'Designation' },
    { key: 'shift_name', label: 'Shift' },
    { key: 'shift_timing', label: 'Timing' },
    { key: 'joining_date', label: 'Joined', render: (row) => formatDate(row.joining_date) },
    { key: 'contact', label: 'Contact' },
    { key: 'status', label: 'Status', render: (row) => st(row) },
  ],
  filters: [
    { key: 'role', label: 'Role', options: ['doctor', 'nurse', 'technician', 'pharmacist', 'receptionist', 'billing', 'administrator', 'housekeeping', 'security', 'radiology', 'laboratory'].map((v) => ({ value: v, label: v })) },
    { key: 'status', label: 'Status', options: ['active', 'on_duty', 'off_duty', 'on_leave', 'inactive'] },
  ],
  fields: [
    { name: 'name', label: 'Name', required: true, span: 6 },
    { name: 'employee_id', label: 'Employee ID', required: true, span: 6 },
    { name: 'department', label: 'Department (ID)', type: 'number', span: 4 },
    { name: 'role', label: 'Role', type: 'select', span: 4, options: ['nurse', 'technician', 'pharmacist', 'receptionist', 'billing', 'administrator', 'housekeeping', 'security', 'radiology', 'laboratory'].map((v) => ({ value: v, label: v })) },
    { name: 'designation', label: 'Designation', span: 4 },
    { name: 'shift', label: 'Shift (ID)', type: 'number', span: 4 },
    { name: 'joining_date', label: 'Joining date', type: 'date', span: 4 },
    { name: 'contact', label: 'Contact number', span: 4 },
    { name: 'email', label: 'Email', span: 6 },
    { name: 'qualification', label: 'Qualification', span: 6 },
    { name: 'status', label: 'Status', type: 'select', span: 6, options: ['active', 'on_duty', 'off_duty', 'on_leave', 'inactive'].map((v) => ({ value: v, label: v.replaceAll('_', ' ') })) },
    { name: 'address', label: 'Address', span: 12 },
  ],
  detailFields: [
    { name: 'employee_id', label: 'Employee ID' },
    { name: 'name', label: 'Name' },
    { name: 'role_label', label: 'Role' },
    { name: 'department_name', label: 'Department' },
    { name: 'shift_name', label: 'Shift' },
    { name: 'contact', label: 'Contact' },
  ],
})

export const NotificationsPage = page({
  title: 'Notifications',
  subtitle: 'Operational alerts and history',
  module: 'notifications',
  endpoint: endpoints.notifications,
  canCreate: false,
  columns: [
    { key: 'title', label: 'Title' },
    { key: 'message', label: 'Message', wrap: true },
    { key: 'category_label', label: 'Category' },
    { key: 'level', label: 'Level', render: (row) => <StatusChip value={row.level} label={row.level_label} /> },
    { key: 'recipient_name', label: 'Recipient', render: (row) => row.recipient_name || 'Broadcast' },
    { key: 'is_read', label: 'Read', render: (row) => (row.is_read ? 'Yes' : 'No') },
    { key: 'created_at', label: 'Created', render: (row) => formatDateTime(row.created_at) },
  ],
  filters: [
    { key: 'category', label: 'Category', options: ['appointment', 'laboratory', 'radiology', 'pharmacy', 'bed', 'billing', 'insurance', 'admission', 'discharge', 'inventory', 'document', 'ai', 'system'].map((v) => ({ value: v, label: v })) },
    { key: 'unread', label: 'Read state', options: [{ value: 'true', label: 'Unread only' }] },
  ],
})
