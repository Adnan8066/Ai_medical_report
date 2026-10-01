import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { Box, Typography } from '@mui/material'

const CHART_COLOURS = [
  '#0f766e', '#1d4ed8', '#d97706', '#dc2626', '#7c3aed', '#0891b2',
  '#15803d', '#db2777', '#475569', '#c2410c',
]

function Frame({ title, height = 260, children, subtitle }) {
  return (
    <Box>
      {title ? (
        <Typography variant="subtitle2" sx={{ mb: 0.5 }}>{title}</Typography>
      ) : null}
      {subtitle ? (
        <Typography variant="caption" color="text.secondary">{subtitle}</Typography>
      ) : null}
      <ResponsiveContainer width="100%" height={height}>
        {children}
      </ResponsiveContainer>
    </Box>
  )
}

export function TrendArea({ title, data, xKey = 'label', yKey = 'total', height, subtitle }) {
  return (
    <Frame title={title} height={height} subtitle={subtitle}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#0f766e" stopOpacity={0.35} />
            <stop offset="95%" stopColor="#0f766e" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey={xKey} fontSize={11} interval="preserveStartEnd" />
        <YAxis fontSize={11} allowDecimals={false} />
        <Tooltip />
        <Area type="monotone" dataKey={yKey} stroke="#0f766e" fill="url(#trendFill)" strokeWidth={2} />
      </AreaChart>
    </Frame>
  )
}

export function TrendLine({ title, data, lines, xKey = 'label', height, subtitle }) {
  return (
    <Frame title={title} height={height} subtitle={subtitle}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey={xKey} fontSize={11} />
        <YAxis fontSize={11} />
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {lines.map((line, index) => (
          <Line
            key={line.key}
            type="monotone"
            dataKey={line.key}
            name={line.label}
            stroke={line.colour || CHART_COLOURS[index % CHART_COLOURS.length]}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    </Frame>
  )
}

export function Bars({ title, data, xKey, bars, height, layout = 'horizontal', subtitle }) {
  const vertical = layout === 'vertical'
  return (
    <Frame title={title} height={height} subtitle={subtitle}>
      <BarChart data={data} layout={layout}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        {vertical ? (
          <>
            <XAxis type="number" fontSize={11} />
            <YAxis type="category" dataKey={xKey} fontSize={11} width={130} />
          </>
        ) : (
          <>
            <XAxis dataKey={xKey} fontSize={11} interval={0} angle={-20} textAnchor="end" height={60} />
            <YAxis fontSize={11} />
          </>
        )}
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {bars.map((bar, index) => (
          <Bar
            key={bar.key}
            dataKey={bar.key}
            name={bar.label}
            fill={bar.colour || CHART_COLOURS[index % CHART_COLOURS.length]}
            radius={[4, 4, 0, 0]}
          />
        ))}
      </BarChart>
    </Frame>
  )
}

export function PieBreakdown({ title, data, nameKey = 'name', valueKey = 'value', height, subtitle }) {
  return (
    <Frame title={title} height={height} subtitle={subtitle}>
      <PieChart>
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Pie data={data} dataKey={valueKey} nameKey={nameKey} outerRadius={95} label={false}>
          {data.map((entry, index) => (
            <Cell key={entry[nameKey]} fill={CHART_COLOURS[index % CHART_COLOURS.length]} />
          ))}
        </Pie>
      </PieChart>
    </Frame>
  )
}
