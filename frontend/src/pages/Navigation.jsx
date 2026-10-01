import { useCallback, useEffect, useState } from 'react'
import {
  Alert, Box, Button, Chip, MenuItem, Stack, TextField, Typography,
} from '@mui/material'
import api, { endpoints } from '../services/api.js'
import { DemoNotice, ErrorState, Field, PageHeader, SectionCard } from '../components/ui.jsx'

const WIDTH = 1000
const HEIGHT = 700

const CATEGORY_COLOURS = {
  department: '#0f766e',
  diagnostics: '#1d4ed8',
  service: '#7c3aed',
  critical: '#dc2626',
  facility: '#64748b',
  support: '#0891b2',
}

export default function Navigation() {
  const [data, setData] = useState(null)
  const [floor, setFloor] = useState(0)
  const [query, setQuery] = useState('')
  const [destination, setDestination] = useState(null)
  const [route, setRoute] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(
    (params = {}) => {
      setError(null)
      api
        .get(endpoints.navigation, { params })
        .then(({ data: payload }) => {
          setData(payload)
          if (!params.to) setRoute(null)
        })
        .catch((err) => setError(err.friendlyMessage || 'Unable to load the hospital map.'))
    },
    [],
  )

  useEffect(() => {
    load()
  }, [load])

  const go = async (location) => {
    setDestination(location)
    const params = { to: location.id }
    if (query) params.q = query
    const { data: payload } = await api.get(endpoints.navigation, { params })
    setRoute(payload.route)
    setData(payload)
    setFloor(location.floor_number)
  }

  if (error) return <ErrorState message={error} onRetry={() => load()} />
  if (!data) return <SectionCard title="Loading indoor map…"><Box sx={{ height: 200 }} /></SectionCard>

  const locations = data.destinations || []
  const floorLocations = locations.filter((item) => item.floor_number === floor)

  return (
    <Box>
      <PageHeader
        title="Hospital Navigation"
        subtitle="Find a department, service or facility and view a step-free route"
        breadcrumb="Overview"
      />
      <DemoNotice>
        Schematic demo floor plan. Signage and staff guidance always take precedence in a real hospital.
      </DemoNotice>

      <Stack direction={{ xs: 'column', lg: 'row' }} spacing={2}>
        <Box sx={{ flex: 1 }}>
          <SectionCard
            title={`Floor ${floor} — ${(data.floors || []).find((item) => item.number === floor)?.name || ''}`}
            actions={
              <TextField
                select size="small" value={floor}
                onChange={(event) => setFloor(Number(event.target.value))}
                sx={{ minWidth: 240 }}
              >
                {(data.floors || []).map((item) => (
                  <MenuItem key={item.number} value={item.number}>
                    Floor {item.number} · {item.name}
                  </MenuItem>
                ))}
              </TextField>
            }
          >
            <Box sx={{ border: '1px solid #e2e8f0', borderRadius: 1.5, background: '#f8fafc', overflow: 'hidden' }}>
              <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} style={{ width: '100%', height: 380 }}>
                <rect x="20" y="20" width={WIDTH - 40} height={HEIGHT - 40} fill="#ffffff" stroke="#cbd5e1" />
                <text x="40" y="55" fontSize="20" fill="#94a3b8">
                  Corridor
                </text>
                <line x1="60" y1="430" x2={WIDTH - 60} y2="430" stroke="#e2e8f0" strokeWidth="26" />
                <line x1="500" y1="60" x2="500" y2={HEIGHT - 60} stroke="#e2e8f0" strokeWidth="26" />

                {floorLocations.map((location) => {
                  const isDestination = destination?.id === location.id
                  return (
                    <g key={location.id} onClick={() => go(location)} style={{ cursor: 'pointer' }}>
                      <rect
                        x={location.x - 34}
                        y={location.y - 26}
                        width={68}
                        height={52}
                        rx={8}
                        fill={isDestination ? '#fbbf24' : CATEGORY_COLOURS[location.category] || '#475569'}
                        opacity={isDestination ? 1 : 0.9}
                      />
                      <text
                        x={location.x}
                        y={location.y - 4}
                        fontSize="11"
                        fill="#ffffff"
                        textAnchor="middle"
                        fontWeight="600"
                      >
                        {(location.name.length > 14 ? `${location.name.slice(0, 13)}…` : location.name)}
                      </text>
                      <text x={location.x} y={location.y + 12} fontSize="10" fill="#e2e8f0" textAnchor="middle">
                        {location.code}
                      </text>
                    </g>
                  )
                })}

                {route?.points?.length ? (
                  <>
                    <polyline
                      points={route.points.map((point) => `${point.x},${point.y}`).join(' ')}
                      fill="none"
                      stroke="#dc2626"
                      strokeWidth="5"
                      strokeDasharray="12 8"
                    />
                    {route.points.map((point, index) => (
                      <circle key={index} cx={point.x} cy={point.y} r="7" fill="#dc2626" />
                    ))}
                  </>
                ) : null}
              </svg>
            </Box>
          </SectionCard>
        </Box>

        <Box sx={{ width: { xs: '100%', lg: 380 } }}>
          <SectionCard title="Find your destination">
            <Stack spacing={2}>
              <TextField
                size="small" fullWidth label="Search (department, service, code)"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') load({ q: query })
                }}
              />
              <Button variant="contained" onClick={() => load({ q: query })}>Search</Button>
              <Stack direction="row" gap={0.5} flexWrap="wrap">
                {['cardiology', 'emergency', 'laboratory', 'pharmacy', 'radiology', 'icu', 'reception', 'billing', 'blood bank', 'operation theatre'].map((term) => (
                  <Chip
                    key={term} size="small" label={term}
                    onClick={() => { setQuery(term); load({ q: term }) }}
                  />
                ))}
              </Stack>
            </Stack>
          </SectionCard>

          {route ? (
            <SectionCard title={`Route to ${route.to.name}`}>
              <Stack spacing={1}>
                <Stack direction="row" gap={1}>
                  <Chip size="small" color="primary" label={`${route.estimated_minutes} min walk`} />
                  <Chip size="small" variant="outlined" label={route.same_floor ? 'Same floor' : 'Lift required'} />
                </Stack>
                <Field label="From" value={route.from.name} />
                <Field label="To" value={`${route.to.name} · Floor ${route.to.floor_number}`} />
                <ol>
                  {route.steps.map((step, index) => (
                    <li key={index}><Typography variant="body2">{step}</Typography></li>
                  ))}
                </ol>
                <Alert severity="success">{route.accessibility_note}</Alert>
                <Typography variant="caption" color="text.secondary">{route.notice}</Typography>
              </Stack>
            </SectionCard>
          ) : (
            <SectionCard title="Destinations" subtitle={`${locations.length} points of interest`}>
              <Stack spacing={0.5} sx={{ maxHeight: 320, overflowY: 'auto' }}>
                {locations.slice(0, 40).map((location) => (
                  <Button
                    key={location.id} size="small" sx={{ justifyContent: 'flex-start' }}
                    onClick={() => go(location)}
                  >
                    Floor {location.floor_number} · {location.name}
                  </Button>
                ))}
              </Stack>
            </SectionCard>
          )}
        </Box>
      </Stack>
    </Box>
  )
}
