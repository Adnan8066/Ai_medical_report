import { useEffect, useRef, useState } from 'react'
import {
  Alert, Box, Button, Chip, MenuItem, Paper, Stack, TextField, ToggleButton,
  ToggleButtonGroup, Typography,
} from '@mui/material'
import SendIcon from '@mui/icons-material/Send'
import api, { endpoints } from '../services/api.js'
import { DemoNotice, PageHeader, SectionCard } from '../components/ui.jsx'
import { useAuth } from '../context/AuthContext.jsx'

export default function Assistant() {
  const { user } = useAuth()
  const [mode, setMode] = useState('hospital')
  const [capabilities, setCapabilities] = useState(null)
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [busy, setBusy] = useState(false)
  const [patients, setPatients] = useState([])
  const [patientId, setPatientId] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    api.get(endpoints.aiCapabilities).then(({ data }) => setCapabilities(data)).catch(() => undefined)
    api
      .get(endpoints.patients, { params: { page_size: 100 } })
      .then(({ data }) => setPatients(data.results || []))
      .catch(() => undefined)
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (text) => {
    const value = (text || question).trim()
    if (!value || busy) return
    setMessages((current) => [...current, { role: 'user', content: value }])
    setQuestion('')
    setBusy(true)
    try {
      const { data } =
        mode === 'hospital'
          ? await api.post(endpoints.aiAsk, { question: value })
          : await api.post(endpoints.aiDocumentAsk, {
              question: value,
              patient: patientId ? Number(patientId) : undefined,
            })
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: data.answer,
          sources: data.sources || [],
          results: data.results || [],
          disclaimer: data.disclaimer,
        },
      ])
    } catch (err) {
      setMessages((current) => [
        ...current,
        { role: 'assistant', content: err.friendlyMessage || 'The assistant is unavailable right now.' },
      ])
    } finally {
      setBusy(false)
    }
  }

  return (
    <Box>
      <PageHeader
        title="AI Hospital Assistant"
        subtitle={`Signed in as ${user?.role_name} · answers are limited to data your role can access`}
        breadcrumb="Intelligence"
      />
      <DemoNotice>
        The assistant organises and retrieves information only. It does not diagnose, prescribe or
        recommend treatment, and it never invents content that is not present in the records.
      </DemoNotice>

      <Stack direction={{ xs: 'column', lg: 'row' }} spacing={2}>
        <Box sx={{ flex: 1 }}>
          <SectionCard
            title={mode === 'hospital' ? 'Hospital assistant' : 'Document assistant (RAG)'}
            actions={
              <ToggleButtonGroup
                size="small" exclusive value={mode}
                onChange={(_, value) => value && setMode(value)}
              >
                <ToggleButton value="hospital">Hospital data</ToggleButton>
                <ToggleButton value="document">Documents</ToggleButton>
              </ToggleButtonGroup>
            }
          >
            {mode === 'document' ? (
              <TextField
                select size="small" fullWidth label="Limit to patient (optional)"
                value={patientId} onChange={(event) => setPatientId(event.target.value)}
                sx={{ mb: 2 }}
              >
                <MenuItem value="">All documents I can access</MenuItem>
                {patients.map((patient) => (
                  <MenuItem key={patient.id} value={patient.id}>
                    {patient.patient_id} · {patient.name}
                  </MenuItem>
                ))}
              </TextField>
            ) : null}

            <Stack spacing={1.5} sx={{ maxHeight: '52vh', overflowY: 'auto', pr: 1 }}>
              {messages.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  Ask a question or pick one of the suggestions on the right.
                </Typography>
              ) : (
                messages.map((message, index) => (
                  <Paper
                    key={index}
                    variant="outlined"
                    sx={{
                      p: 1.5,
                      bgcolor: message.role === 'user' ? '#f0fdfa' : '#ffffff',
                      alignSelf: message.role === 'user' ? 'flex-end' : 'flex-start',
                      maxWidth: '92%',
                    }}
                  >
                    <Typography variant="caption" color="text.secondary">
                      {message.role === 'user' ? 'You' : 'AsterNova assistant'}
                    </Typography>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{message.content}</Typography>
                    {message.results?.length ? (
                      <Stack direction="row" gap={0.5} flexWrap="wrap" sx={{ mt: 1 }}>
                        {message.results.map((item) => (
                          <Chip key={`${item.document_id}-${item.chunk_index}`} size="small" label={`${item.document_code} · ${item.score}`} />
                        ))}
                      </Stack>
                    ) : null}
                    {message.disclaimer ? (
                      <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                        {message.disclaimer}
                      </Typography>
                    ) : null}
                  </Paper>
                ))
              )}
              <div ref={bottomRef} />
            </Stack>

            <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
              <TextField
                fullWidth size="small"
                label={mode === 'hospital' ? 'Ask about hospital operations' : 'Ask about the documents'}
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault()
                    send()
                  }
                }}
              />
              <Button variant="contained" endIcon={<SendIcon />} onClick={() => send()} disabled={busy}>
                {busy ? 'Thinking…' : 'Send'}
              </Button>
            </Stack>
          </SectionCard>
        </Box>

        <Box sx={{ width: { xs: '100%', lg: 340 } }}>
          <SectionCard title="Suggested questions">
            <Stack spacing={1}>
              {(capabilities?.suggestions || [
                'What appointments are scheduled today?',
                'Which beds are available?',
                'Show today’s emergency patients.',
              ]).map((suggestion) => (
                <Button
                  key={suggestion}
                  size="small"
                  variant="outlined"
                  sx={{ justifyContent: 'flex-start', textAlign: 'left' }}
                  onClick={() => send(suggestion)}
                >
                  {suggestion}
                </Button>
              ))}
            </Stack>
          </SectionCard>
          <SectionCard title="What the assistant can and cannot do">
            <Typography variant="subtitle2">Can</Typography>
            <ul>
              {(capabilities?.can || []).map((item) => (
                <li key={item}><Typography variant="body2">{item}</Typography></li>
              ))}
            </ul>
            <Typography variant="subtitle2">Cannot</Typography>
            <ul>
              {(capabilities?.cannot || []).map((item) => (
                <li key={item}><Typography variant="body2">{item}</Typography></li>
              ))}
            </ul>
            {capabilities?.provider ? (
              <Alert severity="info">
                Provider: <strong>{capabilities.provider.provider}</strong>
                <Typography variant="caption" display="block">{capabilities.provider.message}</Typography>
              </Alert>
            ) : null}
          </SectionCard>
        </Box>
      </Stack>
    </Box>
  )
}
