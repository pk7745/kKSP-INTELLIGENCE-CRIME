import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell,
} from 'recharts'

// ── Risk helpers ───────────────────────────────────────────────────────────────
function riskLevel(score) {
  if (score >= 70) return 'HIGH'
  if (score >= 40) return 'MEDIUM'
  return 'LOW'
}
function riskColor(score) {
  if (score >= 70) return '#ef4444'
  if (score >= 40) return '#f97316'
  return '#22c55e'
}
function riskBadge(score) {
  const level = riskLevel(score)
  const cls   = level === 'HIGH'   ? 'bg-red-900 text-red-300 border-red-700'
              : level === 'MEDIUM' ? 'bg-orange-900 text-orange-300 border-orange-700'
              :                      'bg-green-900 text-green-300 border-green-700'
  return <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase border ${cls}`}>{level}</span>
}
function trendIcon(trend) {
  if (trend === 'up'   || trend === 'rising')  return <span className="text-red-400 font-bold">↑</span>
  if (trend === 'down' || trend === 'falling') return <span className="text-green-400 font-bold">↓</span>
  return <span className="text-gray-400">→</span>
}

// ── Dark tooltip ───────────────────────────────────────────────────────────────
function DarkTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs shadow-lg">
      <p className="font-semibold text-white mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color || p.fill }}>{p.name}: {p.value}</p>
      ))}
    </div>
  )
}

// ── Radar chart ────────────────────────────────────────────────────────────────
function DistrictRadar({ data }) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-white mb-3">District Risk Radar — Top 10</h3>
      <ResponsiveContainer width="100%" height={280}>
        <RadarChart data={data}>
          <PolarGrid stroke="#334155" />
          <PolarAngleAxis dataKey="district" tick={{ fill: '#94a3b8', fontSize: 9 }} />
          <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 8 }} />
          <Radar name="Risk Score" dataKey="risk_score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} strokeWidth={2} />
          <Tooltip content={<DarkTooltip />} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}

// ── Bar chart ──────────────────────────────────────────────────────────────────
const BAR_COLORS = ['#ef4444','#f97316','#3b82f6','#a855f7','#22c55e','#eab308','#06b6d4','#ec4899']

function CrimeCountChart({ data }) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-white mb-3">Crime Count by Type — Last 30 Days</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 4, right: 8, bottom: 24, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="crime_type" tick={{ fill: '#94a3b8', fontSize: 9 }} angle={-30} textAnchor="end" interval={0} />
          <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
          <Tooltip content={<DarkTooltip />} />
          <Bar dataKey="count" radius={[4,4,0,0]}>
            {data.map((_, i) => <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

// ── Risk table ─────────────────────────────────────────────────────────────────
function DistrictRiskTable({ data, t }) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-700">
        <h3 className="text-sm font-semibold text-white">District Risk Summary</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-700 text-gray-500 uppercase tracking-wider">
              <th className="text-left px-4 py-2">{t('district')}</th>
              <th className="text-right px-4 py-2">{t('riskScore')}</th>
              <th className="text-left px-4 py-2">{t('dominantCrime')}</th>
              <th className="text-center px-4 py-2">{t('severity')}</th>
              <th className="text-center px-4 py-2">{t('trend')}</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr key={i} className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors">
                <td className="px-4 py-2.5 text-gray-200 font-medium">{row.district}</td>
                <td className="px-4 py-2.5 text-right font-mono font-bold" style={{ color: riskColor(row.risk_score) }}>
                  {row.risk_score}
                </td>
                <td className="px-4 py-2.5 text-gray-400">{row.dominant_crime}</td>
                <td className="px-4 py-2.5 text-center">{riskBadge(row.risk_score)}</td>
                <td className="px-4 py-2.5 text-center">{trendIcon(row.trend)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Main ───────────────────────────────────────────────────────────────────────
export default function ThreatRadar({ district }) {
  const { t } = useTranslation()

  const [hotspots, setHotspots] = useState([])
  const [stats,    setStats]    = useState(null)
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const qs = district && district !== 'All Districts' ? `?district=${encodeURIComponent(district)}` : ''
        const [hsRes, stRes] = await Promise.allSettled([
          fetch(`/api/hotspots${qs}`),
          fetch('/api/stats/overview'),
        ])
        if (hsRes.status === 'fulfilled' && hsRes.value.ok) {
          const d = await hsRes.value.json()
          setHotspots(d.hotspots || d || [])
        } else {
          setHotspots(DEMO_HOTSPOTS)
          setError('API unavailable — demo data shown')
        }
        if (stRes.status === 'fulfilled' && stRes.value.ok) {
          const d = await stRes.value.json()
          setStats(d)
        } else {
          setStats(DEMO_STATS)
        }
      } catch (err) {
        setError(err.message)
        setHotspots(DEMO_HOTSPOTS)
        setStats(DEMO_STATS)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [district])

  const sorted    = [...hotspots].sort((a,b) => (b.risk_score||0) - (a.risk_score||0))
  const radarData = sorted.slice(0, 10).map(h => ({
    district:   h.district || h.DistrictName || 'Unknown',
    risk_score: Math.round(h.risk_score || 0),
  }))
  const tableData = sorted.map(h => ({
    district:      h.district || h.DistrictName || 'Unknown',
    risk_score:    Math.round(h.risk_score || 0),
    dominant_crime: h.dominant_crime || 'Theft',
    trend:         h.trend || 'stable',
  }))
  const crimeTypeData = stats?.crime_by_type || DEMO_STATS.crime_by_type

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

      {/* KPI row */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Total FIRs',       value: stats.total_firs?.toLocaleString()  || '—', color: 'text-indigo-400' },
            { label: 'This Month',        value: stats.month_firs?.toLocaleString() || '—', color: 'text-blue-400'  },
            { label: 'Active Alerts',     value: stats.active_alerts?.toString()    || '—', color: 'text-red-400'   },
            { label: 'Hotspot Districts', value: stats.hotspot_count?.toString()    || '—', color: 'text-orange-400'},
          ].map(({ label, value, color }) => (
            <div key={label} className="bg-gray-800 border border-gray-700 rounded-xl px-4 py-3">
              <p className={`text-xl font-bold font-mono ${color}`}>{value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{label}</p>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <DistrictRadar data={radarData} />
        <CrimeCountChart data={crimeTypeData} />
      </div>

      {tableData.length > 0 && <DistrictRiskTable data={tableData} t={t} />}

      {error && (
        <p className="text-xs text-yellow-500 text-center">{error}</p>
      )}
    </div>
  )
}

// ── Demo data ──────────────────────────────────────────────────────────────────
const DEMO_HOTSPOTS = [
  { district: 'Bengaluru Urban', risk_score: 92, dominant_crime: 'Theft',       trend: 'up'     },
  { district: 'Kalaburagi',      risk_score: 78, dominant_crime: 'Robbery',      trend: 'up'     },
  { district: 'Belagavi',        risk_score: 71, dominant_crime: 'Assault',      trend: 'stable' },
  { district: 'Ballari',         risk_score: 68, dominant_crime: 'Murder',       trend: 'down'   },
  { district: 'Mysuru',          risk_score: 61, dominant_crime: 'Cyber Fraud',  trend: 'up'     },
  { district: 'Raichur',         risk_score: 58, dominant_crime: 'Drug Traffic', trend: 'stable' },
  { district: 'Vijayapura',      risk_score: 52, dominant_crime: 'Theft',       trend: 'down'   },
  { district: 'Shivamogga',      risk_score: 44, dominant_crime: 'Burglary',     trend: 'stable' },
  { district: 'Dharwad',         risk_score: 38, dominant_crime: 'Theft',       trend: 'down'   },
  { district: 'Tumakuru',        risk_score: 31, dominant_crime: 'Cyber Fraud',  trend: 'stable' },
]

const DEMO_STATS = {
  total_firs:   48320,
  month_firs:   3210,
  active_alerts: 14,
  hotspot_count: 7,
  crime_by_type: [
    { crime_type: 'Theft',    count: 12400 },
    { crime_type: 'Burglary', count:  6800 },
    { crime_type: 'Assault',  count:  4200 },
    { crime_type: 'Robbery',  count:  3100 },
    { crime_type: 'Cyber',    count:  5900 },
    { crime_type: 'Murder',   count:   820 },
    { crime_type: 'Drugs',    count:  2300 },
    { crime_type: 'Other',    count:  4200 },
  ],
}
