import axios from 'axios'

export const API_BASE = import.meta.env.VITE_API_BASE || '/api'
export const ACCESS_KEY = 'asternova.access'
export const REFRESH_KEY = 'asternova.refresh'

const api = axios.create({ baseURL: API_BASE, timeout: 30000 })

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY)
}

export function setTokens({ access, refresh }) {
  if (access) localStorage.setItem(ACCESS_KEY, access)
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Refresh once on a 401, then replay the original request. Anything else is
// converted into a friendly message the UI can show directly.
let refreshing = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { response, config } = error
    if (response && response.status === 401 && !config.__retried) {
      const refresh = localStorage.getItem(REFRESH_KEY)
      if (refresh) {
        config.__retried = true
        refreshing =
          refreshing ||
          axios.post(`${API_BASE}/auth/refresh/`, { refresh }).then((res) => {
            setTokens({ access: res.data.access, refresh: res.data.refresh })
            refreshing = null
            return res.data.access
          })
        try {
          const access = await refreshing
          config.headers.Authorization = `Bearer ${access}`
          return api.request(config)
        } catch {
          refreshing = null
          clearTokens()
        }
      }
    }
    error.friendlyMessage = friendlyMessage(error)
    return Promise.reject(error)
  },
)

export function friendlyMessage(error) {
  if (error.code === 'ERR_NETWORK') {
    return 'Unable to reach the AsterNova API. Check that the Django server is running.'
  }
  const data = error.response?.data
  if (!data) return 'Something went wrong. Please try again.'
  if (typeof data.detail === 'string') {
    const fieldErrors = data.errors ? Object.values(data.errors) : []
    return fieldErrors.length ? `${data.detail} ${fieldErrors.join(' ')}` : data.detail
  }
  return 'Something went wrong. Please try again.'
}

// API paths are centralised here so pages never hard-code URL strings.
export const endpoints = {
  login: '/auth/login/',
  logout: '/auth/logout/',
  me: '/auth/me/',
  demoAccounts: '/auth/demo-accounts/',
  changePassword: '/auth/change-password/',
  hospital: '/hospital/',
  dashboard: '/analytics/dashboard/',
  charts: '/analytics/charts/',
  forecast: '/analytics/forecast/',
  search: '/search/',
  users: '/users/',
  roles: '/users/roles/',
  permissionCatalogue: '/users/permissions/catalogue/',
  departments: '/departments/',
  doctors: '/doctors/',
  patients: '/patients/',
  vitals: '/patients/vitals/',
  nurseAssignments: '/patients/nurse-assignments/',
  appointments: '/appointments/',
  opd: '/opd/',
  emergency: '/emergency/',
  admissions: '/admissions/',
  dischargeSummaries: '/admissions/discharge-summaries/',
  beds: '/beds/',
  wards: '/beds/wards/',
  laboratory: '/laboratory/',
  labTests: '/laboratory/tests/',
  radiology: '/radiology/',
  medicines: '/pharmacy/medicines/',
  prescriptions: '/pharmacy/prescriptions/',
  surgery: '/surgery/',
  bloodStock: '/blood-bank/stock/',
  donations: '/blood-bank/donations/',
  bloodIssues: '/blood-bank/issues/',
  documents: '/documents/',
  invoices: '/billing/',
  insuranceProviders: '/insurance/providers/',
  insurancePolicies: '/insurance/policies/',
  insuranceClaims: '/insurance/claims/',
  inventory: '/inventory/',
  suppliers: '/inventory/suppliers/',
  purchaseOrders: '/inventory/purchase-orders/',
  staff: '/staff/',
  shifts: '/staff/shifts/',
  shiftAssignments: '/staff/shifts/assignments/',
  notifications: '/notifications/',
  auditLogs: '/audit/',
  navigation: '/navigation/directions/',
  aiCapabilities: '/ai/capabilities/',
  aiAsk: '/ai/ask/',
  aiDocumentAsk: '/ai/documents/ask/',
  aiSessions: '/ai/sessions/',
}

export default api
