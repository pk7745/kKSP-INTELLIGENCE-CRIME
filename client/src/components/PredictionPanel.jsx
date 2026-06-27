import React, { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, Cell,
} from 'recharts'

// ── Karnataka districts for selector ─────────────────────────────────────────
const DISTRICTS = [
  'Bengaluru Urban','Mysuru','Belagavi','Kalaburagi','Mangaluru',
  'Shivamogga','Ballari','Dharwad','Tumakuru','Raichur',
  'Vijayapura','Hassan','Davanagere','Udupi','Bagalkote',
]

// ── Risk colour ────────────────────────────────────────────────────────────────
function riskColor(score) {
  if (score >= 0.7) return '#ef4444'
  if (score >= 0.4) return '#f97316'
  if (score >= 0.2) return '#eab308'
  return '#22c55e'
}

// ── Dark tooltip ───────────────────────────────────────────────────────────────
function DarkTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs shadow-lg max-w-xs">
      <p className="font-semibold text-white mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>{p.name}: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}</p>
      ))}
    </div>
  )
}

// ── Line chart — 7-day forecast ────────────────────────────────────────────────
function ForecastLineChart({ data, district }) {
  // data: array of { date, predicted_count, crime_type? }
  // Group by date
  const byDate = {}
  data.forEach(d => {
    const date = d.date || d.prediction_date || '—'
    if (!byDate[date]) byDate[date] = { date, total: 0 }
    byDate[date].total += d.predicted_count || 0
    if (d.crime_type) byDate[date][d.crime_type] = (byDate[date][d.crime_type] || 0) + (d.predicted_count || 0)
  })

  const chartData = Object.values(byDate).sort((a, b) => a.date.localeCompare(b.date))

  // Get unique crime types
  const crimeTypes = [...new Set(data.map(d => d.crime_type).filter(Boolean))].slice(0, 5)
  const LINE_COLORS = ['#6366f1','#ef4444','#f97316','#22c55e','#06b6d4']

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-white mb-3">
        {district} — 7-Day Crime Forecast
      </h3>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={chartData} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 9 }} />
          <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
          <Tooltip content={<DarkTooltip />} />
          <Legend wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
          {crimeTypes.length > 0 ? (
            crimeTypes.map((ct, i) => (
              <Line key={ct} type="monotone" dataKey={ct} name={ct}
                stroke={LINE_COLORS[i % LINE_COLORS.length]} strokeWidth={2} dot={false} />
            ))
          ) : (
            <Line type="monotone" dataKey="total" name="Total Predicted"
              stroke="#6366f1" strokeWidth={2.5} dot={{ fill: '#6366f1', r: 4 }} />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

// ── SHAP factors bar chart ────────────────────────────────────────────────────
function SHAPChart({ factors }) {
  if (!factors || factors.length === 0) return null
  const data = factors.map(f => ({
    feature: f.feature_name || f.feature,
    value:   Math.abs(f.shap_value || f.importance || 0),
    raw:     f.shap_value || f.importance || 0,
  })).sort((a, b) => b.value - a.value).slice(0, 8)

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-white mb-3">{`Contributing Factors (SHAP)`}</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 24, bottom: 4, left: 80 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
          <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 9 }} />
          <YAxis type="category" dataKey="feature" tick={{ fill: '#94a3b8', fontSize: 9 }} width={75} />
          <Tooltip content={<DarkTooltip />} />
          <Bar dataKey="value" name="SHAP" radius={[0, 4, 4, 0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.raw >= 0 ? '#ef4444' : '#22c55e'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="text-[10px] text-gray-500 mt-2">Red = increases risk · Green = decreases risk</p>
    </div>
  )
}

// ── Risk calendar (7 days × districts heatmap) ────────────────────────────────
function RiskCalendar({ predictions, t }) {
  // Build a date × district matrix
  const dates     = [...new Set(predictions.map(p => p.date || p.prediction_date).filter(Boolean))].sort().slice(0, 7)
  const districts = [...new Set(predictions.map(p => p.district || p.DistrictName).filter(Boolean))].slice(0, 10)

  if (dates.length === 0 || districts.length === 0) return null

  const lookup = {}
  predictions.forEach(p => {
    const key = `${p.district || p.DistrictName}__${p.date || p.prediction_date}`
    lookup[key] = Math.max(lookup[key] || 0, p.risk_score || 0)
  })

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 overflow-x-auto">
      <h3 className="text-sm font-semibold text-white mb-3">{t('calendarRisk')}</h3>
      <table className="text-[10px] border-collapse">
        <thead>
          <tr>
            <th className="pr-3 py-1 text-left text-gray-500 font-semibold min-w-[110px]">District</th>
            {dates.map(d => (
              <th key={d} className="px-2 py-1 text-center text-gray-500 font-semibold whitespace-nowrap">
                {formatDate(d)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {districts.map(dist => (
            <tr key={dist}>
              <td className="pr-3 py-1 text-gray-300 font-medium truncate max-w-[110px]">{dist}</td>
              {dates.map(date => {
                const score = lookup[`${dist}__${date}`] || 0
                const bg    = score >= 0.7 ? 'bg-red-700'
                            : score >= 0.4 ? 'bg-orange-600'
                            : score >= 0.2 ? 'bg-yellow-600'
                            :                'bg-green-800'
                return (
                  <td key={date} className="px-2 py-1 text-center">
                    <div className={`${bg} rounded px-2 py-1 font-mono text-white`} title={`${dist} ${date}: ${(score * 100).toFixed(0)}%`}>
                      {score > 0 ? (score * 100).toFixed(0) : '—'}
                    </div>
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex items-center gap-3 mt-3">
        {[
          { color: 'bg-red-700',    label: 'High (70+)' },
          { color: 'bg-orange-600', label: 'Medium (40-70)' },
          { color: 'bg-yellow-600', label: 'Low (20-40)' },
          { color: 'bg-green-800',  label: 'Minimal (<20)' },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-1">
            <span className={`h-2.5 w-2.5 rounded ${color}`} />
            <span className="text-[10px] text-gray-400">{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function PredictionPanel({ district, user }) {
  const { t } = useTranslation()

  const [predictions, setPredictions] = useState([])
  const [shapFactors, setShapFactors] = useState([])
  const [loading,     setLoading]     = useState(true)
  const [error,       setError]       = useState(null)
  const [selDistrict, setSelDistrict] = useState(
    (district && district !== 'All Districts') ? district : 'Bengaluru Urban'
  )
  const [patrolLoading, setPatrolLoading] = useState(false)

  // Sync prop district
  useEffect(() => {
    if (district && district !== 'All Districts') setSelDistrict(district)
  }, [district])

  // ── Load predictions ───────────────────────────────────────────────────────
  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const params = new URLSearchParams({ district: selDistrict })
        const res    = await fetch(`/api/predictions?${params}`)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        setPredictions(data.predictions || data || [])
        setShapFactors(data.shap_factors || data.factors || [])
      } catch (err) {
        setError(err.message)
        // Demo data
        setPredictions(getDemoPredictions(selDistrict))
        setShapFactors(DEMO_SHAP)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [selDistrict])

  // ── Patrol recommendation via chat ────────────────────────────────────────
  const getPatrolRec = useCallback(async () => {
    setPatrolLoading(true)
    try {
      const res = await fetch('/api/chat/query', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          query:   `Where should I deploy patrol in ${selDistrict} tonight? Use prediction data.`,
          intent:  'PATROL_RECOMMENDATION',
          district: selDistrict,
          session_id: `patrol-${Date.now()}`,
        }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      alert(`KAVERI Patrol Recommendation:\n\n${data.response || data.answer || 'No recommendation available.'}`)
    } catch (err) {
      alert('Patrol recommendation failed: ' + err.message)
    } finally {
      setPatrolLoading(false)
    }
  }, [selDistrict])

  if (loading) return (
    <div className="flex items-center justify-center h-full bg-gray-900">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
        <p className="text-sm text-gray-400">{t('loading')}</p>
      </div>
    </div>
  )

  return (
    <div className="h-full overflow-y-auto bg-gray-900 px-4 py-4 space-y-4">

      {/* Header controls */}
      <div className="flex items-center gap-3 flex-wrap">
        <h2 className="text-sm font-bold text-white">{t('predicted7Day')}</h2>
        <div className="flex-1 min-w-[160px] max-w-xs">
          <select
            value={selDistrict}
            onChange={e => setSelDistrict(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-1.5
                       focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            {DISTRICTS.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
        <button
          onClick={getPatrolRec}
          disabled={patrolLoading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold
                     bg-emerald-700 hover:bg-emerald-600 text-white transition-colors disabled:opacity-50"
        >
          {patrolLoading ? <SpinnerIcon /> : <PatrolIcon />}
          {t('patrolRec')}
        </button>
      </div>

      {error && (
        <div className="text-xs text-yellow-500 bg-yellow-900/20 border border-yellow-700 rounded-lg px-3 py-2">
          API unavailable — demo prediction data shown
        </div>
      )}

      {/* 7-day line chart */}
      {predictions.length > 0 && (
        <ForecastLineChart data={predictions} district={selDistrict} />
      )}

      {/* SHAP factors */}
      {shapFactors.length > 0 && (
        <SHAPChart factors={shapFactors} />
      )}

      {/* Risk calendar */}
      {predictions.length > 0 && (
        <RiskCalendar predictions={predictions} t={t} />
      )}

      {predictions.length === 0 && !loading && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <p className="text-gray-500 text-sm">{t('noData')}</p>
        </div>
      )}
    </div>
  )
}

// ── Helpers ────────────────────────────────────────────────────────────────────
function formatDate(dateStr) {
  try {
    return new Date(dateStr).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
  } catch { return dateStr }
}

// ── Demo data ──────────────────────────────────────────────────────────────────
function getDemoPredictions(district) {
  const today   = new Date()
  const types   = ['Theft','Robbery','Cyber Fraud','Assault']
  const rows    = []
  for (let i = 0; i < 7; i++) {
    const date = new Date(today)
    date.setDate(today.getDate() + i)
    const dateStr = date.toISOString().split('T')[0]
    types.forEach(ct => {
      rows.push({
        district,
        date:            dateStr,
        prediction_date: dateStr,
        crime_type:      ct,
        predicted_count: Math.round(10 + Math.random() * 40),
        risk_score:      Math.random(),
      })
    })
  }
  return rows
}

const DEMO_SHAP = [
  { feature: 'is_weekend',        shap_value:  0.42 },
  { feature: 'unemployment_rate', shap_value:  0.38 },
  { feature: 'festival_day',      shap_value:  0.31 },
  { feature: 'prev_week_crimes',  shap_value:  0.28 },
  { feature: 'youth_population',  shap_value:  0.21 },
  { feature: 'poverty_rate',      shap_value:  0.19 },
  { feature: 'literacy_rate',     shap_value: -0.15 },
  { feature: 'police_density',    shap_value: -0.24 },
]

// ── Icons ──────────────────────────────────────────────────────────────────────
function PatrolIcon() {
  return (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z" />
    </svg>
  )
}

function SpinnerIcon() {
  return (
    <svg className="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}
