import { useMemo, useState } from 'react'
import {
  Box, Button, Chip, IconButton, InputAdornment, MenuItem, Skeleton, Stack, Table,
  TableBody, TableCell, TableContainer, TableHead, TablePagination, TableRow,
  TableSortLabel, TextField, Tooltip, Typography,
} from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'
import VisibilityIcon from '@mui/icons-material/Visibility'
import InboxIcon from '@mui/icons-material/Inbox'
import { ErrorState } from './ui.jsx'
import { TOKENS } from '../theme.js'
import { formatNumber } from '../utils/format.js'

/**
 * Data table with search, filters, sorting and server-side pagination.
 *
 * Columns accept { key, label, render?, sortable?, align?, width?, numeric? }.
 * Numeric columns are right-aligned and use tabular figures so digits line up
 * down the column.
 */
export default function DataTable({
  columns, rows, loading, error, onRetry, count, page, onPageChange,
  search, onSearchChange, filters = [], onFilterChange, filterValues = {},
  onEdit, onDelete, onView, onRowClick, pageSize = 25, onPageSizeChange, dense = true,
  rowActions = [], onRowAction, emptyTitle, emptyHint,
}) {
  const [orderBy, setOrderBy] = useState(null)
  const [order, setOrder] = useState('asc')

  const sorted = useMemo(() => {
    if (!orderBy) return rows
    const column = columns.find((item) => item.key === orderBy)
    return [...rows].sort((a, b) => {
      const left = column?.sortValue ? column.sortValue(a) : a[orderBy]
      const right = column?.sortValue ? column.sortValue(b) : b[orderBy]
      if (left === right) return 0
      if (left === null || left === undefined) return 1
      if (right === null || right === undefined) return -1
      const result = String(left).localeCompare(String(right), undefined, { numeric: true })
      return order === 'asc' ? result : -result
    })
  }, [rows, orderBy, order, columns])

  const showActions = Boolean(onEdit || onDelete || onView || rowActions.length)

  const firstRow = count === 0 ? 0 : (page - 1) * pageSize + 1
  const lastRow = Math.min(page * pageSize, count)

  return (
    <Box>
      {(onSearchChange || filters.length > 0) && (
        <Stack
          direction={{ xs: 'column', lg: 'row' }}
          spacing={1.5}
          sx={{ mb: 2, alignItems: { lg: 'center' } }}
        >
          {onSearchChange ? (
            <TextField
              placeholder="Search…"
              value={search || ''}
              onChange={(event) => onSearchChange(event.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" sx={{ color: 'text.secondary' }} />
                  </InputAdornment>
                ),
              }}
              sx={{ minWidth: 280 }}
            />
          ) : null}
          {filters.map((filter) => (
            <TextField
              key={filter.key}
              select
              label={filter.label}
              value={filterValues[filter.key] || ''}
              onChange={(event) => onFilterChange(filter.key, event.target.value)}
              sx={{ minWidth: 190 }}
            >
              <MenuItem value="">All</MenuItem>
              {filter.options.map((option) => (
                <MenuItem
                  key={typeof option === 'string' ? option : option.value}
                  value={typeof option === 'string' ? option : option.value}
                >
                  {typeof option === 'string' ? option : option.label}
                </MenuItem>
              ))}
            </TextField>
          ))}
          {count > 0 ? (
            <Box sx={{ flexGrow: 1, textAlign: { lg: 'right' } }}>
              <Chip
                size="small"
                variant="outlined"
                label={`${formatNumber(firstRow)}–${formatNumber(lastRow)} of ${formatNumber(count)} records`}
                sx={{ color: 'text.secondary', borderColor: TOKENS.border }}
              />
            </Box>
          ) : null}
        </Stack>
      )}

      {error ? (
        <ErrorState message={error} onRetry={onRetry} />
      ) : loading ? (
        <Stack spacing={1} sx={{ pt: 1 }}>
          {Array.from({ length: 6 }).map((_, index) => (
            <Skeleton key={index} variant="rounded" height={40} />
          ))}
        </Stack>
      ) : sorted.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 7, px: 2 }}>
          <InboxIcon sx={{ fontSize: 40, color: TOKENS.borderStrong, mb: 1 }} />
          <Typography variant="subtitle2">{emptyTitle || 'No records found'}</Typography>
          <Typography variant="body2" color="text.secondary">
            {emptyHint || 'Adjust the search or filters, or add a new record.'}
          </Typography>
        </Box>
      ) : (
        <TableContainer sx={{ border: `1px solid ${TOKENS.border}`, borderRadius: 2 }}>
          <Table size={dense ? 'small' : 'medium'} stickyHeader={false}>
            <TableHead>
              <TableRow>
                {columns.map((column) => (
                  <TableCell
                    key={column.key}
                    align={column.align || (column.numeric ? 'right' : 'left')}
                    sx={{ width: column.width, whiteSpace: 'nowrap' }}
                  >
                    {column.sortable === false ? (
                      column.label
                    ) : (
                      <TableSortLabel
                        active={orderBy === column.key}
                        direction={orderBy === column.key ? order : 'asc'}
                        onClick={() => {
                          const isAsc = orderBy === column.key && order === 'asc'
                          setOrder(isAsc ? 'desc' : 'asc')
                          setOrderBy(column.key)
                        }}
                      >
                        {column.label}
                      </TableSortLabel>
                    )}
                  </TableCell>
                ))}
                {showActions ? (
                  <TableCell align="right" sx={{ width: 1 }}>
                    Actions
                  </TableCell>
                ) : null}
              </TableRow>
            </TableHead>
            <TableBody>
              {sorted.map((row) => (
                <TableRow
                  key={row.id}
                  hover
                  sx={{
                    cursor: onRowClick ? 'pointer' : 'default',
                    '& td': { verticalAlign: 'middle' },
                  }}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                >
                  {columns.map((column) => (
                    <TableCell
                      key={column.key}
                      align={column.align || (column.numeric ? 'right' : 'left')}
                      className={column.numeric ? 'numeric' : undefined}
                      sx={{
                        whiteSpace: column.wrap ? 'normal' : 'nowrap',
                        maxWidth: column.wrap ? 320 : undefined,
                        color: column.muted ? 'text.secondary' : undefined,
                      }}
                    >
                      {column.render ? column.render(row) : row[column.key] ?? '—'}
                    </TableCell>
                  ))}
                  {showActions ? (
                    <TableCell align="right" onClick={(event) => event.stopPropagation()}>
                      <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                        {rowActions.map((action) => (
                          <Button
                            key={action.label}
                            size="small"
                            variant="outlined"
                            color={action.color || 'primary'}
                            sx={{ whiteSpace: 'nowrap' }}
                            disabled={action.isDisabled ? action.isDisabled(row) : false}
                            onClick={() => onRowAction?.(action, row)}
                          >
                            {action.label}
                          </Button>
                        ))}
                        {onView ? (
                          <Tooltip title="View details">
                            <IconButton size="small" onClick={() => onView(row)}>
                              <VisibilityIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        ) : null}
                        {onEdit ? (
                          <Tooltip title="Edit">
                            <IconButton size="small" onClick={() => onEdit(row)}>
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        ) : null}
                        {onDelete ? (
                          <Tooltip title="Delete">
                            <IconButton size="small" color="error" onClick={() => onDelete(row)}>
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        ) : null}
                      </Stack>
                    </TableCell>
                  ) : null}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {count > 0 && !loading ? (
        <TablePagination
          component="div"
          count={count}
          page={(page || 1) - 1}
          onPageChange={(_, next) => onPageChange(next + 1)}
          rowsPerPage={pageSize}
          rowsPerPageOptions={[10, 25, 50]}
          onRowsPerPageChange={(event) => onPageSizeChange?.(Number(event.target.value))}
        />
      ) : null}
    </Box>
  )
}
