import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { Alert, Box, Button, Chip, Paper, Stack, TextField, Typography } from '@mui/material'
import api, { endpoints } from '../services/api.js'
import { PageHeader, SectionCard, Loading } from '../components/ui.jsx'

const SECTION_LABELS = {
  patients: 'Patients',
  doctors: 'Doctors',
  appointments: 'Appointments',
  documents: 'Documents',
  departments: 'Departments',
  laboratory: 'Laboratory',
  medicines: 'Medicines',
  bills: 'Bills',
}

export default function SearchResults() {
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const [query, setQuery] = useState(params.get('q') || '')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const run = (value) => {
    if (!value || value.trim().length < 2) return
    setLoading(true)
    setError(null)
    api
      .get(endpoints.search, { params: { q: value, limit: 10 } })
      .then(({ data }) => setResult(data))
      .catch((err) => setError(err.friendlyMessage || 'Search failed.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    const initial = params.get('q')
    if (initial) {
      setQuery(initial)
      run(initial)
    }
  }, [params]) // eslint-disable-line react-hooks/exhaustive-deps

  const submit = (event) => {
    event.preventDefault()
    setParams({ q: query })
  }

  return (
    <Box>
      <PageHeader
        title="Global Search"
        subtitle="Search across every module your role can access"
        breadcrumb="Overview"
      />
      <SectionCard>
        <Box component="form" onSubmit={submit}>
          <Stack direction="row" spacing={1}>
            <TextField
              fullWidth size="small"
              label="Search patients, doctors, appointments, documents, medicines, bills…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <Button type="submit" variant="contained">Search</Button>
          </Stack>
        </Box>
        {query.length === 1 ? (
          <Alert severity="info" sx={{ mt: 2 }}>Type at least two characters to search.</Alert>
        ) : null}
      </SectionCard>

      {loading ? <Loading label="Searching…" /> : null}
      {error ? <Alert severity="error">{error}</Alert> : null}

      {result ? (
        result.total === 0 ? (
          <Alert severity="info">No matches found for “{result.query}”.</Alert>
        ) : (
          <Stack spacing={2}>
            <Typography variant="body2" color="text.secondary">
              {result.total} match(es) for “{result.query}”
            </Typography>
            {Object.entries(result.results).map(([section, items]) =>
              items.length === 0 ? null : (
                <SectionCard key={section} title={`${SECTION_LABELS[section] || section} (${items.length})`}>
                  <Stack spacing={1}>
                    {items.map((item) => (
                      <Paper
                        key={`${section}-${item.id}`}
                        variant="outlined"
                        sx={{ p: 1.5, cursor: 'pointer' }}
                        onClick={() => item.url && navigate(item.url.replace(/^\/(\w+)\/(\d+)$/, (_, resource, id) => `/${resource === 'patients' ? 'patients' : resource}/${id}`))}
                      >
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Chip size="small" label={item.title} />
                          <Typography variant="body2" color="text.secondary">{item.subtitle}</Typography>
                        </Stack>
                      </Paper>
                    ))}
                  </Stack>
                </SectionCard>
              ),
            )}
          </Stack>
        )
      ) : null}
    </Box>
  )
}
