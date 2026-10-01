import { useEffect, useState } from 'react'
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom'
import {
  AppBar, Avatar, Badge, Box, Chip, Divider, Drawer, IconButton, List, ListItemButton,
  ListItemIcon, ListItemText, Menu, MenuItem, Stack, Toolbar, Tooltip, Typography, useMediaQuery,
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import NotificationsIcon from '@mui/icons-material/Notifications'
import LogoutIcon from '@mui/icons-material/Logout'
import LocalHospitalIcon from '@mui/icons-material/LocalHospital'
import DashboardIcon from '@mui/icons-material/Dashboard'
import PeopleIcon from '@mui/icons-material/People'
import MedicalServicesIcon from '@mui/icons-material/MedicalServices'
import EventIcon from '@mui/icons-material/Event'
import AssignmentIcon from '@mui/icons-material/Assignment'
import LocalShippingIcon from '@mui/icons-material/LocalShipping'
import ScienceIcon from '@mui/icons-material/Science'
import BiotechIcon from '@mui/icons-material/Biotech'
import MedicationIcon from '@mui/icons-material/Medication'
import BloodtypeIcon from '@mui/icons-material/Bloodtype'
import FolderSharedIcon from '@mui/icons-material/FolderShared'
import SmartToyIcon from '@mui/icons-material/SmartToy'
import SearchIcon from '@mui/icons-material/Search'
import InputBase from '@mui/material/InputBase'
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong'
import ShieldIcon from '@mui/icons-material/Shield'
import InventoryIcon from '@mui/icons-material/Inventory'
import BadgeIcon from '@mui/icons-material/Badge'
import InsightsIcon from '@mui/icons-material/Insights'
import HistoryIcon from '@mui/icons-material/History'
import MapIcon from '@mui/icons-material/Map'
import SettingsIcon from '@mui/icons-material/Settings'
import api, { endpoints } from '../services/api.js'
import { useAuth } from '../context/AuthContext.jsx'

const NAV_SECTIONS = [
  {
    label: 'Overview',
    items: [
      { to: '/dashboard', label: 'Dashboard', icon: <DashboardIcon />, module: null },
      { to: '/analytics', label: 'Analytics & AI', icon: <InsightsIcon />, module: 'analytics' },
      { to: '/navigation', label: 'Hospital Navigation', icon: <MapIcon />, module: 'navigation' },
    ],
  },
  {
    label: 'People',
    items: [
      { to: '/patients', label: 'Patients', icon: <PeopleIcon />, module: 'patients' },
      { to: '/doctors', label: 'Doctors', icon: <MedicalServicesIcon />, module: 'doctors' },
      { to: '/departments', label: 'Departments', icon: <AssignmentIcon />, module: 'departments' },
      { to: '/staff', label: 'Staff & Shifts', icon: <BadgeIcon />, module: 'staff' },
      { to: '/roster', label: 'Shift Roster', icon: <BadgeIcon />, module: 'staff' },
    ],
  },
  {
    label: 'Clinical',
    items: [
      { to: '/appointments', label: 'Appointments', icon: <EventIcon />, module: 'appointments' },
      { to: '/opd', label: 'OPD Consultations', icon: <AssignmentIcon />, module: 'opd' },
      { to: '/emergency', label: 'Emergency', icon: <LocalHospitalIcon />, module: 'emergency' },
      { to: '/admissions', label: 'Admissions', icon: <AssignmentIcon />, module: 'admissions' },
      { to: '/beds', label: 'Bed Management', icon: <LocalShippingIcon />, module: 'beds' },
      { to: '/surgery', label: 'Operation Theatre', icon: <LocalHospitalIcon />, module: 'surgery' },
    ],
  },
  {
    label: 'Diagnostics & Pharmacy',
    items: [
      { to: '/laboratory', label: 'Laboratory', icon: <ScienceIcon />, module: 'laboratory' },
      { to: '/radiology', label: 'Radiology', icon: <BiotechIcon />, module: 'radiology' },
      { to: '/pharmacy', label: 'Pharmacy', icon: <MedicationIcon />, module: 'pharmacy' },
      { to: '/blood-bank', label: 'Blood Bank', icon: <BloodtypeIcon />, module: 'bloodbank' },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { to: '/documents', label: 'Medical Documents', icon: <FolderSharedIcon />, module: 'documents' },
      { to: '/assistant', label: 'AI Assistant', icon: <SmartToyIcon />, module: 'ai' },
      { to: '/audit', label: 'Audit Logs', icon: <HistoryIcon />, module: 'audit' },
    ],
  },
  {
    label: 'Administration',
    items: [
      { to: '/billing', label: 'Billing', icon: <ReceiptLongIcon />, module: 'billing' },
      { to: '/insurance', label: 'Insurance', icon: <ShieldIcon />, module: 'insurance' },
      { to: '/inventory', label: 'Inventory', icon: <InventoryIcon />, module: 'inventory' },
      { to: '/admin', label: 'Users & Roles', icon: <SettingsIcon />, module: 'users' },
      { to: '/settings', label: 'Hospital Settings', icon: <SettingsIcon />, module: 'hospital' },
      { to: '/portal', label: 'Patient Portal', icon: <PeopleIcon />, module: 'portal' },
    ],
  },
]

const DRAWER_WIDTH = 268

export default function Layout({ children }) {
  const { user, hospital, logout, can } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const isDesktop = useMediaQuery('(min-width:1024px)')
  const [open, setOpen] = useState(isDesktop)
  const [notifications, setNotifications] = useState([])
  const [anchor, setAnchor] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => setOpen(isDesktop), [isDesktop])

  useEffect(() => {
    let cancelled = false
    api
      .get(endpoints.notifications, { params: { unread: 'true', page_size: 8 } })
      .then(({ data }) => {
        if (!cancelled) setNotifications(data.results || [])
      })
      .catch(() => undefined)
    return () => {
      cancelled = true
    }
  }, [location.pathname])

  const markRead = async (notification) => {
    try {
      await api.post(`${endpoints.notifications}${notification.id}/mark_read/`)
      setNotifications((current) => current.filter((item) => item.id !== notification.id))
    } catch {
      /* ignore */
    }
  }

  const drawer = (
    <Box sx={{ width: DRAWER_WIDTH }} role="navigation">
      <Stack
        direction="row"
        spacing={1.25}
        alignItems="center"
        sx={{ px: 2.25, py: 2, borderBottom: '1px solid #e3e8ef' }}
      >
        <Box
          sx={{
            width: 38,
            height: 38,
            borderRadius: 1.5,
            display: 'grid',
            placeItems: 'center',
            background: 'linear-gradient(135deg, #0f766e 0%, #115e59 60%, #1d4ed8 100%)',
            color: '#fff',
            flexShrink: 0,
          }}
        >
          <LocalHospitalIcon sx={{ fontSize: 21 }} />
        </Box>
        <Box sx={{ minWidth: 0 }}>
          <Typography variant="subtitle1" sx={{ lineHeight: 1.15, letterSpacing: '-.01em' }}>
            AsterNova
          </Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            Hospital Intelligence Platform
          </Typography>
        </Box>
      </Stack>
      <Chip
        size="small"
        label="DEMO DATA ONLY"
        sx={{
          ml: 2.25,
          mt: 1.5,
          mb: 1,
          fontWeight: 700,
          fontSize: '0.625rem',
          letterSpacing: '.08em',
          bgcolor: 'rgba(180, 83, 9, 0.1)',
          color: '#b45309',
          border: '1px solid rgba(180, 83, 9, 0.25)',
        }}
      />
      <Box sx={{ overflowY: 'auto', height: 'calc(100vh - 190px)', pb: 1.5, pt: 0.5 }}>
        {NAV_SECTIONS.map((section) => {
          const items = section.items.filter((item) => !item.module || can(item.module))
          if (!items.length) return null
          return (
            <List
              key={section.label}
              dense
              disablePadding
              subheader={
                <Typography
                  variant="overline"
                  sx={{ pl: 2.5, pt: 1.5, pb: 0.5, display: 'block', color: 'text.secondary', opacity: 0.75 }}
                >
                  {section.label}
                </Typography>
              }
            >
              {items.map((item) => (
                <ListItemButton
                  key={item.to}
                  component={RouterLink}
                  to={item.to}
                  selected={location.pathname.startsWith(item.to)}
                  onClick={() => !isDesktop && setOpen(false)}
                >
                  <ListItemIcon sx={{ minWidth: 34 }}>
                    {isDesktop ? (
                      // Clone the icon at a consistent size for the sidebar.
                      <Box sx={{ display: 'flex', fontSize: 20 }}>{item.icon}</Box>
                    ) : (
                      item.icon
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={item.label}
                    primaryTypographyProps={{ fontSize: 13.5, fontWeight: 500 }}
                  />
                </ListItemButton>
              ))}
            </List>
          )
        })}
      </Box>
      <Box
        sx={{
          borderTop: '1px solid #e3e8ef',
          px: 2.25,
          py: 1.25,
          mt: 'auto',
        }}
      >
        <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
          AsterNova v1.0 · demonstration build
        </Typography>
        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
          Not for clinical use
        </Typography>
      </Box>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Drawer
        variant={isDesktop ? 'permanent' : 'temporary'}
        open={open}
        onClose={() => setOpen(false)}
        sx={{
          '& .MuiDrawer-paper': {
            width: DRAWER_WIDTH,
            borderRight: '1px solid #e3e8ef',
            display: 'flex',
            flexDirection: 'column',
          },
        }}
      >
        {drawer}
      </Drawer>
      <Box
        sx={{
          flexGrow: 1,
          minWidth: 0,
          // The permanent drawer is fixed, so the content column must be
          // offset by its width on desktop or the sidebar covers the page.
          '@media (min-width:1024px)': { ml: `${DRAWER_WIDTH}px` },
        }}
      >
        <AppBar position="sticky" color="inherit" elevation={0} sx={{ borderBottom: '1px solid #e2e8f0' }}>
          <Toolbar sx={{ gap: 1 }}>
            {!isDesktop ? (
              <IconButton onClick={() => setOpen(true)}><MenuIcon /></IconButton>
            ) : null}
            <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
              {hospital?.name || 'AsterNova Multispeciality Hospital'}
              <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                {hospital ? `${hospital.city}, ${hospital.state} · ${hospital.total_beds} beds (demo)` : ''}
              </Typography>
            </Typography>
            <Box
              component="form"
              onSubmit={(event) => {
                event.preventDefault()
                if (searchTerm.trim().length >= 2) navigate(`/search?q=${encodeURIComponent(searchTerm)}`)
              }}
              sx={{
                display: { xs: 'none', md: 'flex' },
                alignItems: 'center',
                gap: 0.5,
                border: '1px solid #e2e8f0',
                borderRadius: 2,
                px: 1,
                py: 0.25,
                minWidth: 290,
              }}
            >
              <SearchIcon fontSize="small" sx={{ color: 'text.secondary' }} />
              <InputBase
                placeholder="Search patients, doctors, documents, bills…"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                sx={{ fontSize: 14, flex: 1 }}
              />
            </Box>
            <Tooltip title="Notifications">
              <IconButton onClick={(event) => setAnchor(event.currentTarget)}>
                <Badge badgeContent={notifications.length} color="error">
                  <NotificationsIcon />
                </Badge>
              </IconButton>
            </Tooltip>
            <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={() => setAnchor(null)}>
              {notifications.length === 0 ? (
                <MenuItem disabled>No unread notifications</MenuItem>
              ) : (
                notifications.map((notification) => (
                  <MenuItem
                    key={notification.id}
                    onClick={() => {
                      markRead(notification)
                      if (notification.link) navigate(notification.link)
                      setAnchor(null)
                    }}
                    sx={{ maxWidth: 360, whiteSpace: 'normal' }}
                  >
                    <Box>
                      <Typography variant="body2">{notification.title}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {notification.category_label} · {notification.level_label}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))
              )}
            </Menu>
            <Divider orientation="vertical" flexItem sx={{ my: 1.5, display: { xs: 'none', sm: 'block' } }} />
            <Stack direction="row" spacing={1} alignItems="center">
              <Avatar
                sx={{
                  width: 34,
                  height: 34,
                  bgcolor: 'primary.main',
                  fontSize: 14,
                  fontWeight: 600,
                }}
              >
                {(user?.full_name || 'U')
                  .split(' ')
                  .map((part) => part.charAt(0))
                  .slice(0, 2)
                  .join('')}
              </Avatar>
              <Box sx={{ display: { xs: 'none', sm: 'block' }, lineHeight: 1.2 }}>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {user?.full_name}
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  {user?.role_name}
                  {user?.department_name ? ` · ${user.department_name}` : ''}
                </Typography>
              </Box>
              <Tooltip title="Sign out">
                <IconButton onClick={logout} size="small" sx={{ ml: 0.5 }}>
                  <LogoutIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Stack>
          </Toolbar>
        </AppBar>
        <Box
          component="main"
          sx={{ p: { xs: 2, md: 3 }, maxWidth: 1680, mx: 'auto', width: '100%' }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  )
}
