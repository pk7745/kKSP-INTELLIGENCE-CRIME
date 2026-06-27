import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useTranslation } from 'react-i18next'

// ── Alert type config ──────────────────────────────────────────────────────────
const ALERT_TYPE_CONFIG = {
  HEINOUS_OFFENCE:  { icon: SkullIcon,       labelKey: 'heinousOffence', bgClass: 'bg-red-950',    borderClass: 'border-red-700' },
  CRIME_SPIKE:      { icon: TrendingUpIcon,  labelKey: 'crimeSpike',    bgClass: 'bg-orange-950', borderClass: 'border-orange-700' },
  CLUSTER_ALERT:    { icon: MapPinIcon,      labelKey: 'clusterAlert',  bgClass: 'bg-yellow-950', borderClass: 'border-yellow-700' },
  REPEAT_ACCUSED:   { icon: UserWarnIcon,    labelKey: 'repeatAccused', bgClass: 'bg-purple-950', borderClass: 'border-purple-700' },
}

function getAlertConfig(alertType) {
  return ALERT_TYPE_CONFIG[alertType] || {
    icon:        AlertBellIcon,
    labelKey:    'criticalAlert',
    bgClass:     'bg-gray-800',
    borderClass: 'border-gray-600',
  }
}

// ── Severity badge ────────────────────────────────────────────────────────────
function SeverityBadge({ severity }) {
  const cls = severity === 'CRITICAL'
    ? 'bg-red-600 text-white'
    : severity === 'HIGH'
      ? 'bg-orange-500 text-white'
      : 'bg-yellow-500 text-black'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${cls}`}>
      {severity}
    </span>
  )
}

// ── Single alert card ─────────────────────────────────────────────────────────
function AlertCard({ alert, onAcknowledge, isNew, t }) {
  const config = getAlertConfig(alert.alert_type)
  const Icon   = config.icon
  return (
    <div className={`flex gap-3 p-4 rounded-xl border transition-all
                     ${config.bgClass} ${config.borderClass}
                     ${isNew ? 'animate-flash' : ''}`}>
      <div className="flex-shrink-0 mt-0.5">
        <Icon className="w-5 h-5 text-gray-300" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap mb-1">
          <SeverityBadge severity={alert.severity} />
          <span className="text-xs text-gray-400 font-semibold">
            {t(config.labelKey)}
          </span>
        </div>
        <p className="text-sm text-gray-200 leading-snug mb-2">
          {alert.description}
        </p>
        <div className="flex items-center gap-3 flex-wrap">
          {alert.crime_no && (
            <span className="text-xs font-mono text-indigo-300 bg-gray-900/60 px-2 py-0.5 rounded">
              {alert.crime_no}
            </span>
          )}
          {alert.district && (
            <span className="text-xs text-gray-400">{alert.district}</span>
          )}
          <span className="text-xs text-gray-600 ml-auto">
            {alert.created_at ? formatTime(alert.created_at) : 'Just now'}
          </span>
        </div>
        {!alert.acknowledged ? (
          <button
            onClick={() => onAcknowledge(alert.id)}
            className="mt-2.5 text-xs px-3 py-1 rounded-lg bg-gray-800 border border-gray-600
                       text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
          >
            {t('acknowledge')}
          </button>
        ) : (
          <p className="mt-2 text-xs text-green-500 font-semibold">{t('acknowledged')}</p>
        )}
      </div>
    </div>
  )
}

// ── Simulate FIR form ─────────────────────────────────────────────────────────
function SimulateFIRForm({ t }) {
  const [submitting, setSubmitting] = useState(false)
  const [status,     setStatus]     = useState(null)
  const [form,       setForm]       = useState({
    CrimeType:        'Theft',
    DistrictName:     'Bengaluru Urban',
    GravityOffenceID: 2,
    BriefFacts:       'Test FIR submitted via KAVERI demo interface.',
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setStatus(null)
    try {
      const res = await fetch('/webhook/fir/ingest', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          ...form,
          CrimeNo:   `SIM${Date.now()}`,
          DateTime:  new Date().toISOString(),
          Latitude:  12.9716 + (Math.random() - 0.5) * 0.4,
          Longitude: 77.5946 + (Math.random() - 0.5) * 0.4,
        }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setStatus({ ok: true, msg: 'FIR submitted. Watch for alerts via WebSocket.' })
    } catch (err) {
      setStatus({ ok: false, msg: `Error: ${err.message}` })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
      <h3 className="text-sm font-bold text-white mb-3">{t('newFIRForm')}</h3>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Crime Type</label>
            <select
              value={form.CrimeType}
              onChange={e => setForm(f => ({ ...f, CrimeType: e.target.value }))}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-2 py-1.5 text-xs text-gray-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              {['Theft','Murder','Rape','Robbery','Cyber Fraud','Burglary','Assault','Drug Trafficking'].map(ct => (
                <option key={ct} value={ct}>{ct}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">District</label>
            <select
              value={form.DistrictName}
              onChange={e => setForm(f => ({ ...f, DistrictName: e.target.value }))}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-2 py-1.5 text-xs text-gray-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              {['Bengaluru Urban','Mysuru','Belagavi','Kalaburagi','Mangaluru','Shivamogga','Ballari','Dharwad'].map(d => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Gravity</label>
          <select
            value={form.GravityOffenceID}
            onChange={e => setForm(f => ({ ...f, GravityOffenceID: parseInt(e.target.value) }))}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-2 py-1.5 text-xs text-gray-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value={1}>1 — Heinous (triggers CRITICAL alert)</option>
            <option value={2}>2 — Serious</option>
            <option value={3}>3 — Minor</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Brief Facts</label>
          <textarea
            value={form.BriefFacts}
            onChange={e => setForm(f => ({ ...f, BriefFacts: e.target.value }))}
            rows={2}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-2 py-1.5 text-xs text-gray-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-none"
          />
        </div>
        {status && (
          <p className={`text-xs px-2 py-1.5 rounded ${status.ok ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'}`}>
            {status.msg}
          </p>
        )}
        <button
          type="submit"
          disabled={submitting}
          className="w-full py-2 rounded-lg text-xs font-semibold bg-orange-600 hover:bg-orange-500 text-white disabled:opacity-50 transition-colors"
        >
          {submitting ? 'Submitting…' : t('submitFIR')}
        </button>
      </form>
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function AlertCenter({ district, lastMessage }) {
  const { t } = useTranslation()

  const [alerts,         setAlerts]         = useState([])
  const [loading,        setLoading]        = useState(true)
  const [error,          setError]          = useState(null)
  const [severityFilter, setSeverityFilter] = useState('ALL')
  const [newAlertIds,    setNewAlertIds]    = useState(new Set())

  // ── Load alerts from API ───────────────────────────────────────────────────
  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const params = new URLSearchParams()
        if (district && district !== 'All Districts') params.set('district', district)
        const res = await fetch(`/api/alerts?${params}`)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        setAlerts(data.alerts || data || [])
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [district])

  // ── Handle WebSocket alerts ───────────────────────────────────────────────
  useEffect(() => {
    if (!lastMessage || lastMessage.type !== 'alert' || !lastMessage.data) return
    const incoming = { ...lastMessage.data, _clientTs: Date.now() }

    setAlerts(prev => {
      if (prev.some(a => a.id === incoming.id)) return prev
      return [incoming, ...prev]
    })

    if (incoming.id) {
      setNewAlertIds(prev => new Set([...prev, incoming.id]))
      setTimeout(() => {
        setNewAlertIds(prev => {
          const next = new Set(prev)
          next.delete(incoming.id)
          return next
        })
      }, 3000)
    }
  }, [lastMessage])

  // ── Acknowledge ───────────────────────────────────────────────────────────
  const handleAcknowledge = useCallback(async (alertId) => {
    try { await fetch(`/api/alerts/${alertId}`, { method: 'DELETE' }) } catch { /* optimistic */ }
    setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, acknowledged: true } : a))
  }, [])

  const filteredAlerts = alerts.filter(a => severityFilter === 'ALL' || a.severity === severityFilter)
  const criticalCount  = alerts.filter(a => a.severity === 'CRITICAL' && !a.acknowledged).length
  const highCount      = alerts.filter(a => a.severity === 'HIGH'     && !a.acknowledged).length

  return (
    <div className="flex flex-col h-full bg-gray-900 overflow-hidden">

      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-800 flex-shrink-0">
        <h2 className="text-sm font-bold text-white">{t('alertCenter')}</h2>
        {criticalCount > 0 && (
          <span className="h-5 min-w-[1.25rem] px-1 flex items-center justify-center rounded-full bg-red-600 text-[10px] font-bold text-white">
            {criticalCount}
          </span>
        )}
        {highCount > 0 && (
          <span className="h-5 min-w-[1.25rem] px-1 flex items-center justify-center rounded-full bg-orange-500 text-[10px] font-bold text-white">
            {highCount}
          </span>
        )}
        <div className="flex-1" />
        {['ALL', 'CRITICAL', 'HIGH'].map(sev => (
          <button
            key={sev}
            onClick={() => setSeverityFilter(sev)}
            className={`px-3 py-1 rounded-full text-xs font-semibold transition-colors
              ${severityFilter === sev
                ? sev === 'CRITICAL' ? 'bg-red-600 text-white'
                  : sev === 'HIGH'     ? 'bg-orange-500 text-white'
                  : 'bg-indigo-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
          >
            {sev}
          </button>
        ))}
      </div>

      {/* Alert list */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2.5">
        {loading && (
          <div className="flex justify-center py-8">
            <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
        {error && !loading && (
          <div className="text-center py-8">
            <p className="text-sm text-red-400">{t('error')}: {error}</p>
          </div>
        )}
        {!loading && filteredAlerts.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertBellIcon className="w-10 h-10 text-gray-700 mb-3" />
            <p className="text-sm text-gray-500">{t('noAlertsYet')}</p>
          </div>
        )}
        {filteredAlerts.map(alert => (
          <AlertCard
            key={alert.id || alert._clientTs}
            alert={alert}
            onAcknowledge={handleAcknowledge}
            isNew={newAlertIds.has(alert.id)}
            t={t}
          />
        ))}
      </div>

      {/* Simulate FIR panel */}
      <div className="flex-shrink-0 border-t border-gray-800 px-4 py-3">
        <SimulateFIRForm t={t} />
      </div>
    </div>
  )
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function formatTime(ts) {
  try {
    const d    = new Date(ts)
    const diff = Date.now() - d.getTime()
    if (diff < 60000)    return 'Just now'
    if (diff < 3600000)  return `${Math.floor(diff / 60000)}m ago`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
    return d.toLocaleDateString('en-IN')
  } catch { return ts }
}

// ── Icons ─────────────────────────────────────────────────────────────────────
function SkullIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M12 2C8.134 2 5 5.134 5 9c0 2.386 1.137 4.5 2.9 5.85V17a1 1 0 001 1h6.2a1 1 0 001-1v-2.15C17.863 13.5 19 11.386 19 9c0-3.866-3.134-7-7-7z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 17v2h6v-2" />
      <circle cx="9.5"  cy="10" r="1" fill="currentColor" />
      <circle cx="14.5" cy="10" r="1" fill="currentColor" />
    </svg>
  )
}

function TrendingUpIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
    </svg>
  )
}

function MapPinIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
    </svg>
  )
}

function UserWarnIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
    </svg>
  )
}

function AlertBellIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
    </svg>
  )
}
