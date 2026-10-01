import { createTheme, alpha } from '@mui/material/styles'

/**
 * AsterNova design tokens.
 *
 * A restrained clinical palette: deep teal for primary actions, indigo for
 * secondary emphasis, amber/red reserved for clinical risk. Surfaces are flat
 * with hairline borders rather than heavy shadows, and numeric data uses
 * tabular figures so table columns align.
 */

export const TOKENS = {
  border: '#e3e8ef',
  borderStrong: '#cbd5e1',
  surface: '#ffffff',
  surfaceMuted: '#f8fafc',
  canvas: '#f4f6f8',
  textPrimary: '#0f172a',
  textSecondary: '#526079',
  primary: '#0f766e',
  secondary: '#1d4ed8',
}

const monoFont = '"JetBrains Mono", "Cascadia Mono", Consolas, monospace'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: TOKENS.primary, light: '#14b8a6', dark: '#115e59', contrastText: '#ffffff' },
    secondary: { main: TOKENS.secondary, light: '#3b82f6', dark: '#1e3a8a' },
    success: { main: '#15803d', light: '#22c55e', dark: '#14532d' },
    warning: { main: '#b45309', light: '#f59e0b', dark: '#78350f' },
    error: { main: '#b91c1c', light: '#ef4444', dark: '#7f1d1d' },
    info: { main: '#0369a1', light: '#0ea5e9', dark: '#0c4a6e' },
    background: { default: TOKENS.canvas, paper: TOKENS.surface },
    text: { primary: TOKENS.textPrimary, secondary: TOKENS.textSecondary },
    divider: TOKENS.border,
  },
  shape: { borderRadius: 8 },
  typography: {
    fontFamily: 'Roboto, "Helvetica Neue", Arial, sans-serif',
    h4: { fontWeight: 600, letterSpacing: '-0.015em' },
    h5: { fontWeight: 600, letterSpacing: '-0.01em', fontSize: '1.375rem' },
    h6: { fontWeight: 600, fontSize: '1.0625rem' },
    subtitle1: { fontWeight: 600 },
    subtitle2: { fontWeight: 600, fontSize: '0.875rem' },
    body2: { fontSize: '0.875rem' },
    button: { textTransform: 'none', fontWeight: 600, letterSpacing: 0 },
    overline: { fontSize: '0.6875rem', fontWeight: 700, letterSpacing: '0.08em' },
    caption: { fontSize: '0.75rem' },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: { backgroundColor: TOKENS.canvas },
        '.numeric': { fontVariantNumeric: 'tabular-nums' },
        '.mono': { fontFamily: monoFont, fontSize: '0.8125rem' },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: { backgroundImage: 'none' },
        rounded: { borderRadius: 10 },
      },
    },
    MuiCard: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          border: `1px solid ${TOKENS.border}`,
          borderRadius: 10,
          boxShadow: '0 1px 2px rgba(15, 23, 42, 0.04)',
        },
      },
    },
    MuiCardContent: {
      styleOverrides: { root: { padding: 20, '&:last-child': { paddingBottom: 20 } } },
    },
    MuiAppBar: {
      defaultProps: { elevation: 0, color: 'inherit' },
      styleOverrides: {
        root: { backgroundColor: TOKENS.surface, borderBottom: `1px solid ${TOKENS.border}` },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: { borderRadius: 8, paddingInline: 14 },
        sizeSmall: { paddingInline: 10 },
        containedPrimary: { '&:hover': { backgroundColor: '#0d5f59' } },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 600, fontSize: '0.75rem', borderRadius: 6 },
        sizeSmall: { height: 22 },
        outlined: { borderColor: TOKENS.borderStrong },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${TOKENS.border}`,
          padding: '10px 16px',
          fontSize: '0.875rem',
        },
        head: {
          backgroundColor: TOKENS.surfaceMuted,
          color: TOKENS.textSecondary,
          fontSize: '0.6875rem',
          fontWeight: 700,
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
          borderBottom: `1px solid ${TOKENS.borderStrong}`,
          whiteSpace: 'nowrap',
          position: 'sticky',
          top: 0,
          zIndex: 2,
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': { backgroundColor: alpha(TOKENS.primary, 0.04) },
          '&:last-child td': { borderBottom: 'none' },
        },
      },
    },
    MuiTablePagination: {
      styleOverrides: {
        root: { borderTop: `1px solid ${TOKENS.border}` },
        toolbar: { minHeight: 48, paddingLeft: 16 },
        selectLabel: { fontSize: '0.8125rem' },
        displayedRows: { fontSize: '0.8125rem' },
      },
    },
    MuiTextField: { defaultProps: { size: 'small' } },
    MuiOutlinedInput: {
      styleOverrides: {
        root: { backgroundColor: TOKENS.surface, borderRadius: 8 },
        input: { fontSize: '0.875rem' },
      },
    },
    MuiInputLabel: { styleOverrides: { root: { fontSize: '0.875rem' } } },
    MuiDialog: { styleOverrides: { paper: { borderRadius: 12 } } },
    MuiDialogTitle: { styleOverrides: { root: { fontSize: '1.0625rem', fontWeight: 600 } } },
    MuiTabs: {
      styleOverrides: {
        root: { minHeight: 40 },
        indicator: { height: 2.5, borderRadius: 2 },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: { textTransform: 'none', fontWeight: 600, minHeight: 40, fontSize: '0.875rem' },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          marginInline: 8,
          marginBottom: 2,
          '&.Mui-selected': {
            backgroundColor: alpha(TOKENS.primary, 0.1),
            color: TOKENS.primary,
            '& .MuiListItemIcon-root': { color: TOKENS.primary },
            '&:hover': { backgroundColor: alpha(TOKENS.primary, 0.14) },
          },
        },
      },
    },
    MuiListItemIcon: { styleOverrides: { root: { minWidth: 36, color: TOKENS.textSecondary } } },
    MuiTooltip: {
      styleOverrides: {
        tooltip: { backgroundColor: '#0f172a', fontSize: '0.75rem', borderRadius: 6, padding: '6px 10px' },
      },
    },
    MuiAlert: { styleOverrides: { root: { borderRadius: 8, fontSize: '0.8125rem' } } },
    MuiSkeleton: { defaultProps: { animation: 'wave' } },
  },
})

export default theme
