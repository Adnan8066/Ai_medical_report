import { Navigate, Route, Routes } from 'react-router-dom'
import { Box, CircularProgress } from '@mui/material'
import { useAuth } from './context/AuthContext.jsx'
import Layout from './components/Layout.jsx'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Analytics from './pages/Analytics.jsx'
import Beds from './pages/Beds.jsx'
import Emergency from './pages/Emergency.jsx'
import Documents from './pages/Documents.jsx'
import Assistant from './pages/Assistant.jsx'
import NavigationMap from './pages/Navigation.jsx'
import AuditLogs from './pages/AuditLogs.jsx'
import Portal from './pages/Portal.jsx'
import SearchResults from './pages/Search.jsx'
import Admin from './pages/Admin.jsx'
import BloodBank from './pages/BloodBank.jsx'
import ShiftRoster from './pages/ShiftRoster.jsx'
import Settings from './pages/Settings.jsx'
import { PatientDetail, PatientsList } from './pages/Patients.jsx'
import {
  AppointmentsPage, DepartmentsPage, DoctorsPage, OpdPage,
} from './pages/resources.jsx'
import {
  AdmissionsPage, DischargePage, LaboratoryPage, PharmacyPage, PrescriptionsPage,
  RadiologyPage, SurgeryPage,
} from './pages/resourcesClinical.jsx'
import {
  BillingPage, InsurancePage, InventoryPage, NotificationsPage, PurchaseOrdersPage, StaffPage,
} from './pages/resourcesAdmin.jsx'

function Protected({ children }) {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}

const routes = [
  ['/dashboard', Dashboard],
  ['/analytics', Analytics],
  ['/navigation', NavigationMap],
  ['/patients', PatientsList],
  ['/patients/:id', PatientDetail],
  ['/doctors', DoctorsPage],
  ['/departments', DepartmentsPage],
  ['/staff', StaffPage],
  ['/roster', ShiftRoster],
  ['/appointments', AppointmentsPage],
  ['/opd', OpdPage],
  ['/emergency', Emergency],
  ['/admissions', AdmissionsPage],
  ['/discharge-summaries', DischargePage],
  ['/beds', Beds],
  ['/surgery', SurgeryPage],
  ['/laboratory', LaboratoryPage],
  ['/radiology', RadiologyPage],
  ['/pharmacy', PharmacyPage],
  ['/prescriptions', PrescriptionsPage],
  ['/blood-bank', BloodBank],
  ['/documents', Documents],
  ['/assistant', Assistant],
  ['/billing', BillingPage],
  ['/insurance', InsurancePage],
  ['/inventory', InventoryPage],
  ['/purchase-orders', PurchaseOrdersPage],
  ['/notifications', NotificationsPage],
  ['/audit', AuditLogs],
  ['/search', SearchResults],
  ['/admin', Admin],
  ['/settings', Settings],
  ['/portal', Portal],
]

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      {routes.map(([path, Component]) => (
        <Route key={path} path={path} element={<Protected><Component /></Protected>} />
      ))}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
