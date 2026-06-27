import React, { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'

// ── Chargesheet outcome labels ─────────────────────────────────────────────────
const CS_LABELS = {
  A: { label: 'Chargesheeted (A)', color: 'text-green-400',  bg: 'bg-green-900/30 border-green-700', desc: 'Accused chargesheeted — sent for trial.' },
  B: { label: 'False Case (B)',    color: 'text-yellow-400', bg: 'bg-yellow-900/30 border-yellow-700',desc: 'Case found false or no offence made out.' },
  C: { label: 'Undetected (C)',    color: 'text-orange-400', bg: 'bg-orange-900/30 border-orange-700',desc: 'Offence undetected — culprits not traced.' },
}

// ── Section chip ───────────────────────────────────────────────────────────────
function SectionChip({ section }) {
  return (
    <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-mono font-semibold
                     bg-indigo-900/50 text-indigo-300 border border-indigo-700">
      {section.act_name || section.ActName || ''}{' '}
      {section.section_number || section.SectionNumber || section.section || ''}
    </span>
  )
}

// ── Victim row ─────────────────────────────────────────────────────────────────
function VictimRow({ victim, index }) {
  return (
    <tr className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors">
      <td className="px-3 py-2 text-gray-400">V{index + 1}</td>
      <td className="px-3 py-2 text-gray-200">{victim.VictimName || victim.name || '—'}</td>
      <td className="px-3 py-2 text-gray-400">{victim.Age || victim.age || '—'}</td>
      <td className="px-3 py-2 text-gray-400">{victim.Gender || victim.gender || '—'}</td>
      <td className="px-3 py-2 text-gray-400">{victim.InjuryType || victim.injury_type || '—'}</td>
    </tr>
  )
}

// ── Accused row ────────────────────────────────────────────────────────────────
function AccusedRow({ accused, index }) {
  return (
    <tr className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors">
      <td className="px-3 py-2 text-orange-400 font-semibold">A{index + 1}</td>
      <td className="px-3 py-2 text-gray-200">{accused.AccusedName || accused.name || '—'}</td>
      <td className="px-3 py-2 text-gray-400">{accused.Age || accused.age || '—'}</td>
      <td className="px-3 py-2 text-gray-400">{accused.Gender || accused.gender || '—'}</td>
      <td className="px-3 py-2 text-gray-400">{accused.Address || accused.address || '—'}</td>
      <td className="px-3 py-2 text-center">
        {(accused.prior_cases || accused.PriorCases || 0) > 0 ? (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-900 text-red-300">
            {accused.prior_cases || accused.PriorCases} prior
          </span>
        ) : (
          <span className="text-gray-600 text-xs">—</span>
        )}
      </td>
    </tr>
  )
}

// ── FIR detail panel (can be used as modal or inline) ─────────────────────────
export default function FIRDetail({ crimeNo, firData: initialData, onClose }) {
  const { t } = useTranslation()

  const [fir,        setFir]        = useState(initialData || null)
  const [loading,    setLoading]    = useState(!initialData)
  const [error,      setError]      = useState(null)
  const [simLoading, setSimLoading] = useState(false)
  const [similar,    setSimilar]    = useState([])
  const [showSimilar,setShowSimilar]= useState(false)

  // ── Load FIR detail from API ───────────────────────────────────────────────
  useEffect(() => {
    if (initialData) { setFir(initialData); return }
    if (!crimeNo)    return

    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`/api/firs/${encodeURIComponent(crimeNo)}`)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        setFir(data.fir || data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [crimeNo, initialData])

  // ── Crime DNA — find similar cases ────────────────────────────────────────
  const findSimilar = useCallback(async () => {
    if (!fir) return
    setSimLoading(true)
    try {
      const cn = fir.CrimeNo || fir.crime_no || crimeNo
      const res = await fetch(`/api/firs/${encodeURIComponent(cn)}/similar`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setSimilar(data.similar || data || [])
      setShowSimilar(true)
    } catch (err) {
      alert('Similar cases search failed: ' + err.message)
    } finally {
      setSimLoading(false)
    }
  }, [fir, crimeNo])

  // ── Loading / error states ─────────────────────────────────────────────────
  if (loading) return (
    <div className="flex items-center justify-center h-full bg-gray-900">
      <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (error || !fir) return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4">
      <p className="text-red-400 text-sm mb-2">{t('error')}: {error || 'FIR not found'}</p>
      {onClose && (
        <button onClick={onClose} className="text-xs text-gray-500 hover:text-gray-300">{t('close')}</button>
      )}
    </div>
  )

  // Derived values
  const ipcSections   = fir.sections       || fir.ipc_sections   || []
  const victims        = fir.victims        || []
  const accused        = fir.accused        || []
  const chargesheet    = fir.chargesheet    || fir.ChargesheetDetails || null
  const csOutcome      = chargesheet?.Outcome || chargesheet?.outcome || null
  const csConfig       = CS_LABELS[csOutcome] || null
  const complainant    = fir.complainant    || fir.ComplainantDetails || null

  return (
    <div className="h-full overflow-y-auto bg-gray-900 px-4 py-4 space-y-4">

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-0.5">{t('firDetails')}</p>
          <h2 className="text-xl font-bold font-mono text-indigo-300">
            {fir.CrimeNo || fir.crime_no}
          </h2>
          <p className="text-sm text-gray-300 mt-1 font-semibold">
            {fir.CrimeType || fir.crime_type || '—'}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={findSimilar}
            disabled={simLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold
                       bg-indigo-700 hover:bg-indigo-600 text-white transition-colors disabled:opacity-50"
          >
            {simLoading ? <SpinnerIcon /> : <DnaIcon />}
            {t('findSimilar')}
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="px-3 py-1.5 rounded-lg text-xs bg-gray-800 text-gray-400 hover:bg-gray-700 transition-colors"
            >
              {t('close')}
            </button>
          )}
        </div>
      </div>

      {/* Core FIR fields */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {[
          { label: t('crimeNo'),   value: fir.CrimeNo || fir.crime_no },
          { label: t('crimeType'), value: fir.CrimeType || fir.crime_type },
          { label: t('dateTime'),  value: fir.DateTime ? new Date(fir.DateTime).toLocaleString('en-IN') : '—' },
          { label: t('station'),   value: fir.StationName || fir.station_name || '—' },
          { label: t('district'),  value: fir.DistrictName || fir.district || '—' },
          { label: 'Gravity',      value: fir.GravityOffenceName || (fir.GravityOffenceID === 1 ? 'Heinous' : fir.GravityOffenceID === 2 ? 'Serious' : 'Minor') },
        ].map(({ label, value }) => (
          <div key={label} className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5">
            <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-0.5">{label}</p>
            <p className="text-xs text-gray-200 font-medium">{value || '—'}</p>
          </div>
        ))}
      </div>

      {/* GPS */}
      {fir.Latitude && fir.Longitude && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5">
          <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-0.5">Location</p>
          <p className="text-xs font-mono text-gray-300">
            {parseFloat(fir.Latitude).toFixed(5)}, {parseFloat(fir.Longitude).toFixed(5)}
          </p>
        </div>
      )}

      {/* Brief Facts */}
      {(fir.BriefFacts || fir.brief_facts) && (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">{t('briefFacts')}</h3>
          <p className="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">
            {fir.BriefFacts || fir.brief_facts}
          </p>
        </div>
      )}

      {/* IPC Sections */}
      {ipcSections.length > 0 && (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">{t('ipcSections')}</h3>
          <div className="flex flex-wrap gap-2">
            {ipcSections.map((sec, i) => <SectionChip key={i} section={sec} />)}
          </div>
        </div>
      )}

      {/* Complainant */}
      {complainant && (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">{t('complainant')}</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
            <div><span className="text-gray-500">Name: </span><span className="text-gray-200">{complainant.ComplainantName || complainant.name || '—'}</span></div>
            <div><span className="text-gray-500">Age: </span><span className="text-gray-200">{complainant.Age || complainant.age || '—'}</span></div>
            <div><span className="text-gray-500">Gender: </span><span className="text-gray-200">{complainant.Gender || complainant.gender || '—'}</span></div>
            <div className="col-span-2 sm:col-span-3"><span className="text-gray-500">Address: </span><span className="text-gray-200">{complainant.Address || complainant.address || '—'}</span></div>
          </div>
        </div>
      )}

      {/* Victims table */}
      {victims.length > 0 && (
        <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-700">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              {t('victims')} ({victims.length})
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-700 text-gray-500 uppercase tracking-wider">
                  <th className="text-left px-3 py-2">#</th>
                  <th className="text-left px-3 py-2">Name</th>
                  <th className="text-left px-3 py-2">{t('age')}</th>
                  <th className="text-left px-3 py-2">{t('gender')}</th>
                  <th className="text-left px-3 py-2">{t('injuryType')}</th>
                </tr>
              </thead>
              <tbody>
                {victims.map((v, i) => <VictimRow key={i} victim={v} index={i} />)}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Accused table */}
      {accused.length > 0 && (
        <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-700">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Accused ({accused.length})
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-700 text-gray-500 uppercase tracking-wider">
                  <th className="text-left px-3 py-2">#</th>
                  <th className="text-left px-3 py-2">{t('accusedName')}</th>
                  <th className="text-left px-3 py-2">{t('age')}</th>
                  <th className="text-left px-3 py-2">{t('gender')}</th>
                  <th className="text-left px-3 py-2">{t('address')}</th>
                  <th className="text-center px-3 py-2">{t('priorCases')}</th>
                </tr>
              </thead>
              <tbody>
                {accused.map((a, i) => <AccusedRow key={i} accused={a} index={i} />)}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Chargesheet outcome */}
      {csConfig && (
        <div className={`border rounded-xl p-4 ${csConfig.bg}`}>
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">{t('chargesheet')}</h3>
          <div className="flex items-start gap-3">
            <span className={`text-2xl font-black ${csConfig.color}`}>{csOutcome}</span>
            <div>
              <p className={`text-sm font-semibold ${csConfig.color}`}>{csConfig.label}</p>
              <p className="text-xs text-gray-400 mt-0.5">{csConfig.desc}</p>
              {chargesheet?.CourtName && (
                <p className="text-xs text-gray-500 mt-1">Court: {chargesheet.CourtName}</p>
              )}
              {chargesheet?.ChargesheetDate && (
                <p className="text-xs text-gray-500">Filed: {new Date(chargesheet.ChargesheetDate).toLocaleDateString('en-IN')}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Similar cases panel */}
      {showSimilar && (
        <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Similar Cases ({similar.length})
            </h3>
            <button onClick={() => setShowSimilar(false)} className="text-gray-500 hover:text-gray-300 text-xs">Hide</button>
          </div>
          {similar.length === 0 ? (
            <p className="px-4 py-3 text-xs text-gray-500">{t('noData')}</p>
          ) : (
            <div className="divide-y divide-gray-700">
              {similar.slice(0, 10).map((s, i) => (
                <div key={i} className="px-4 py-3 flex items-start gap-3 hover:bg-gray-700/30 transition-colors">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-mono text-indigo-300">{s.CrimeNo || s.crime_no}</p>
                    <p className="text-xs text-gray-300 mt-0.5">{s.CrimeType || s.crime_type}</p>
                    {s.brief_facts_snippet && (
                      <p className="text-[10px] text-gray-500 mt-1 line-clamp-2">{s.brief_facts_snippet}</p>
                    )}
                  </div>
                  {s.similarity_score !== undefined && (
                    <span className="text-xs font-mono text-green-400 flex-shrink-0">
                      {Math.round(s.similarity_score * 100)}%
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Icons ─────────────────────────────────────────────────────────────────────
function DnaIcon() {
  return (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
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
