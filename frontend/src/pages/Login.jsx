import { useEffect, useState } from 'react'
import {
  Alert, Box, Button, Card, CardContent, Chip, Divider, Grid, Stack, TextField, Typography,
} from '@mui/material'
import LocalHospitalIcon from '@mui/icons-material/LocalHospital'
import { useNavigate } from 'react-router-dom'
import api, { endpoints } from '../services/api.js'
import { useAuth } from '../context/AuthContext.jsx'

export default function Login() {
  const { login, user } = useAuth()
  const navigate = useNavigate()
  const [identifier, setIdentifier] = useState('admin@asternova.demo')
  const [password, setPassword] = useState('AsterNova@2024')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [demo, setDemo] = useState(null)

  useEffect(() => {
    if (user) navigate('/dashboard', { replace: true })
  }, [user, navigate])

  useEffect(() => {
    api
      .get(endpoints.demoAccounts)
      .then(({ data }) => {
        setDemo(data)
        if (data?.password) setPassword(data.password)
      })
      .catch(() => undefined)
  }, [])

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(identifier, password)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err.friendlyMessage || 'Invalid email/username or password.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Grid container sx={{ minHeight: '100vh' }}>
      <Grid size={{ xs: 12, md: 6 }} sx={{
          background: 'linear-gradient(135deg, #0f766e 0%, #115e59 45%, #1d4ed8 100%)',
          color: '#fff',
          p: { xs: 4, md: 6 },
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
        }}
      >
        <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 3 }}>
          <Box
            sx={{
              width: 52,
              height: 52,
              borderRadius: 2,
              display: 'grid',
              placeItems: 'center',
              bgcolor: 'rgba(255,255,255,.14)',
              border: '1px solid rgba(255,255,255,.25)',
            }}
          >
            <LocalHospitalIcon sx={{ fontSize: 28 }} />
          </Box>
          <Box>
            <Typography variant="h4">AsterNova</Typography>
            <Typography variant="subtitle1" sx={{ opacity: 0.85 }}>
              Hospital Intelligence Platform
            </Typography>
          </Box>
        </Stack>
        <Typography variant="body1" sx={{ maxWidth: 520, opacity: 0.92 }}>
          Integrated hospital management and intelligence: patients, appointments, beds,
          laboratory, pharmacy, billing, insurance, medical documents with OCR, AI
          document intelligence and retrieval-augmented search.
        </Typography>
        <Stack direction="row" spacing={1} sx={{ mt: 3, flexWrap: 'wrap', gap: 1 }}>
          {['Django REST API', 'JWT + RBAC', 'OCR + RAG', '350 beds seeded', 'Demo data only'].map(
            (label, index) => (
              <Chip
                key={label}
                label={label}
                sx={{
                  bgcolor: index === 4 ? 'rgba(180,83,9,.9)' : 'rgba(255,255,255,.14)',
                  color: '#fff',
                  border: '1px solid rgba(255,255,255,.22)',
                  fontWeight: 600,
                }}
              />
            ),
          )}
        </Stack>
        <Typography variant="caption" sx={{ mt: 4, opacity: 0.7, display: 'block' }}>
          Demonstration build · not for clinical use · all records are fictional
        </Typography>
      </Grid>

      <Grid size={{ xs: 12, md: 6 }} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', p: 3 }}>
        <Card sx={{ width: '100%', maxWidth: 460 }}>
          <CardContent>
            <Typography variant="h6">Sign in</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Authenticate with a seeded demo account. Role-based access control decides what each
              account can see and change.
            </Typography>
            {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
            <Box component="form" onSubmit={submit}>
              <Stack spacing={2}>
                <TextField
                  label="Email or username"
                  value={identifier}
                  onChange={(event) => setIdentifier(event.target.value)}
                  fullWidth
                  required
                />
                <TextField
                  label="Password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  fullWidth
                  required
                />
                <Button type="submit" variant="contained" size="large" disabled={busy}>
                  {busy ? 'Signing in…' : 'Sign in'}
                </Button>
              </Stack>
            </Box>
            <Divider sx={{ my: 2 }}>Demo accounts</Divider>
            {demo?.notice ? (
              <Alert severity="info" variant="outlined" sx={{ mb: 1.5 }}>
                {demo.notice}
              </Alert>
            ) : null}
            <Typography variant="caption" color="text.secondary">
              Password for every account: <strong>{demo?.password || 'AsterNova@2024'}</strong>
            </Typography>
            <Stack spacing={0.25} sx={{ maxHeight: 240, overflowY: 'auto', mt: 1 }}>
              {(demo?.accounts || []).map((account) => (
                <Button
                  key={account.email}
                  size="small"
                  variant="text"
                  sx={{
                    justifyContent: 'space-between',
                    px: 1,
                    borderRadius: 1,
                    '&:hover': { bgcolor: 'rgba(15,118,110,.06)' },
                  }}
                  onClick={() => {
                    setIdentifier(account.email)
                    setPassword(demo.password)
                  }}
                >
                  <span style={{ fontWeight: 600, fontSize: 13 }}>{account.role_label}</span>
                  <span className="mono" style={{ fontSize: 11.5, opacity: 0.7 }}>
                    {account.email}
                  </span>
                </Button>
              ))}
            </Stack>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  )
}
