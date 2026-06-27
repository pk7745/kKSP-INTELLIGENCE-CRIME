import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { MapContainer, TileLayer, Marker, Popup, CircleMarker, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix Leaflet default icon path broken by Vite bundling
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

// ── Karnataka centre + default zoom ──────────────────────────────────────────
const KARNATAKA_CENTRE = [15.3173, 75.7139]
const DEFAULT_ZOOM     = 7

// ── Crime type → colour ───────────────────────────────────────────────────────
function crimeColor(crimeType = '') {
  const t = crimeType.toLowerCase()
  if (t.includes('murder') || t.includes('rape') || t.includes('heinous') || t.includes('robbery')) return '#ef4444'
  if (t.includes('theft')  || t.includes('burglary'))  return '#f97316'
  if (t.includes('cyber')  || t.includes('fraud'))     return '#3b82f6'
  if (t.includes('assault') || t.includes('hurt'))     return '#a855f7'
  return '#22c55e'
}

// ── Crime type → label ────────────────────────────────────────────────────────
function crimeCategory(crimeType = '') {
  const t = crimeType.toLowerCase()
  if (t.includes('murder') || t.includes('rape') || t.includes('heinous') || t.includes('robbery')) return 'heinous'
  if (t.includes('theft') || t.includes('burglary'))  return 'theft'
  if (t.includes('cyber') || t.includes('fraud'))     return 'cyber'
  return 'other'
}

// ── Animated new-pin component ────────────────────────────────────────────────
function NewPinFlash({ fir }) {
  const map = useMap()
  useEffect(() => {
    if (fir.Latitude && fir.Longitude) {
      const lat = parseFloat(fir.Latitude)
      const lng = parseFloat(fir.Longitude)
      if (!isNaN(lat) && !isNaN(lng)) {
        map.flyTo([lat, lng], 11, { duration: 1.2 })
      }
    }
  }, [fir, map])
  return null
}

// ── Heatmap layer (via leaflet.heat) ─────────────────────────────────────────
function HeatmapLayer({ firs }) {
  const map = useMap()
  const heatRef = useRef(null)

  useEffect(() => {
    if (!window.L || !window.L.heatLayer) return
    if (heatRef.current) map.removeLayer(heatRef.current)

    const points = firs
      .filter(f => f.Latitude && f.Longitude)
      .map(f => [parseFloat(f.Latitude), parseFloat(f.Longitude), 0.8])

    if (points.length > 0) {
      heatRef.current = window.L.heatLayer(points, {
        radius:  25,
        blur:    20,
        maxZoom: 13,
        gradient: { 0.2: '#3b82f6', 0.5: '#f97316', 0.8: '#ef4444', 1.0: '#7f0000' },
      }).addTo(map)
    }

    return () => {
      if (heatRef.current) map.removeLayer(heatRef.current)
    }
  }, [firs, map])

  return null
}

// ── Controls overlay ──────────────────────────────────────────────────────────
function MapControls({ showHeatmap, setShowHeatmap, showMarkers, setShowMarkers,
                       crimeFilter, setCrimeFilter, t }) {
  return (
    <div className="absolute top-3 left-3 z-[1000] flex flex-col gap-2">
      {/* Layer toggles */}
      <div className="bg-gray-900/90 backdrop-blur border border-gray-700 rounded-lg p-2 space-y-1.5">
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={showHeatmap}
            onChange={e => setShowHeatmap(e.target.checked)}
            className="accent-indigo-500" />
          <span className="text-xs text-gray-300">{t('heatmap')}</span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={showMarkers}
            onChange={e => setShowMarkers(e.target.checked)}
            className="accent-indigo-500" />
          <span className="text-xs text-gray-300">{t('markers')}</span>
        </label>
      </div>

      {/* Crime type filter */}
      <div className="bg-gray-900/90 backdrop-blur border border-gray-700 rounded-lg p-2">
        <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1.5">{t('filterCrimeType')}</p>
        {['all', 'heinous', 'theft', 'cyber', 'other'].map(type => (
          <button
            key={type}
            onClick={() => setCrimeFilter(type)}
            className={`block w-full text-left text-xs px-2 py-1 rounded transition-colors
              ${crimeFilter === type
                ? 'bg-indigo-700 text-white'
                : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'}`}
          >
            {t(type)}
          </button>
        ))}
      </div>
    </div>
  )
}

// ── FIR popup content ─────────────────────────────────────────────────────────
function FIRPopup({ fir }) {
  return (
    <div className="min-w-[200px]">
      <p className="font-bold text-sm font-mono text-indigo-300 mb-1">{fir.CrimeNo || fir.crime_no}</p>
      <p className="text-xs font-semibold text-white mb-1">{fir.CrimeType || fir.crime_type || 'Unknown'}</p>
      {fir.DateTime && (
        <p className="text-xs text-gray-400 mb-1">
          {new Date(fir.DateTime).toLocaleString('en-IN')}
        </p>
      )}
      {(fir.StationName || fir.station) && (
        <p className="text-xs text-gray-400 mb-1">
          PS: {fir.StationName || fir.station}
        </p>
      )}
      {(fir.DistrictName || fir.district) && (
        <p className="text-xs text-gray-400 mb-1">
          {fir.DistrictName || fir.district}
        </p>
      )}
      {fir.BriefFacts && (
        <p className="text-xs text-gray-300 mt-2 line-clamp-3 border-t border-gray-700 pt-2">
          {fir.BriefFacts}
        </p>
      )}
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function CrimeMap({ district, lastMessage }) {
  const { t } = useTranslation()

  const [firs,         setFirs]         = useState([])
  const [loading,      setLoading]      = useState(true)
  const [error,        setError]        = useState(null)
  const [showHeatmap,  setShowHeatmap]  = useState(false)
  const [showMarkers,  setShowMarkers]  = useState(true)
  const [crimeFilter,  setCrimeFilter]  = useState('all')
  const [newFIR,       setNewFIR]       = useState(null)
  const [liveFIRs,     setLiveFIRs]    = useState([])

  // ── Load FIRs from API ────────────────────────────────────────────────────
  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const params = new URLSearchParams()
        if (district && district !== 'All Districts') params.set('district', district)
        params.set('limit', '200')
        const res = await fetch(`/api/firs?${params}`)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        setFirs(data.firs || data || [])
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [district])

  // ── Handle WebSocket new FIR events ──────────────────────────────────────
  useEffect(() => {
    if (!lastMessage) return
    if (lastMessage.type === 'new_fir' && lastMessage.data) {
      const fir = lastMessage.data
      setLiveFIRs(prev => [fir, ...prev].slice(0, 50))
      setNewFIR(fir)
      // Add to main FIR list
      setFirs(prev => [fir, ...prev])
    }
    if (lastMessage.type === 'alert' && lastMessage.data?.latitude && lastMessage.data?.longitude) {
      // Also pin alert location
    }
  }, [lastMessage])

  // ── Filtered FIRs ─────────────────────────────────────────────────────────
  const displayedFIRs = [...firs, ...liveFIRs].filter(fir => {
    if (crimeFilter === 'all') return true
    return crimeCategory(fir.CrimeType || fir.crime_type) === crimeFilter
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-900">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="text-sm text-gray-400">{t('loading')}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative h-full w-full">
      {/* Error banner */}
      {error && (
        <div className="absolute top-3 right-3 z-[1000] bg-red-900/80 border border-red-700 rounded-lg px-3 py-2 text-xs text-red-200">
          {t('error')}: {error}
        </div>
      )}

      {/* FIR count badge */}
      <div className="absolute top-3 right-3 z-[1000] bg-gray-900/90 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-gray-300">
        <span className="text-indigo-400 font-bold">{displayedFIRs.length}</span> FIRs
        {liveFIRs.length > 0 && (
          <span className="ml-2 text-green-400 font-semibold">+{liveFIRs.length} live</span>
        )}
      </div>

      <MapContainer
        center={KARNATAKA_CENTRE}
        zoom={DEFAULT_ZOOM}
        className="h-full w-full"
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />

        {/* Heatmap layer (loaded via script tag if available) */}
        {showHeatmap && <HeatmapLayer firs={displayedFIRs} />}

        {/* FIR markers */}
        {showMarkers && displayedFIRs.map((fir, i) => {
          const lat = parseFloat(fir.Latitude || fir.latitude)
          const lng = parseFloat(fir.Longitude || fir.longitude)
          if (isNaN(lat) || isNaN(lng)) return null
          const color = crimeColor(fir.CrimeType || fir.crime_type)
          const isNew = liveFIRs.some(lf => lf.CrimeNo === fir.CrimeNo)

          return (
            <CircleMarker
              key={fir.CrimeNo || fir.crime_no || i}
              center={[lat, lng]}
              radius={isNew ? 10 : 6}
              pathOptions={{
                color,
                fillColor: color,
                fillOpacity: isNew ? 0.95 : 0.7,
                weight: isNew ? 3 : 1.5,
              }}
              className={isNew ? 'animate-flash' : ''}
            >
              <Popup maxWidth={280}>
                <FIRPopup fir={fir} />
              </Popup>
            </CircleMarker>
          )
        })}

        {/* Animate to new live FIR */}
        {newFIR && <NewPinFlash fir={newFIR} key={newFIR.CrimeNo || Date.now()} />}
      </MapContainer>

      {/* Controls */}
      <MapControls
        showHeatmap={showHeatmap} setShowHeatmap={setShowHeatmap}
        showMarkers={showMarkers} setShowMarkers={setShowMarkers}
        crimeFilter={crimeFilter} setCrimeFilter={setCrimeFilter}
        t={t}
      />

      {/* Legend */}
      <div className="absolute bottom-6 left-3 z-[1000] bg-gray-900/90 backdrop-blur border border-gray-700 rounded-lg p-2.5 text-xs space-y-1">
        {[
          { label: 'Heinous / Robbery', color: '#ef4444' },
          { label: 'Theft',             color: '#f97316' },
          { label: 'Cyber / Fraud',     color: '#3b82f6' },
          { label: 'Assault',           color: '#a855f7' },
          { label: 'Other',             color: '#22c55e' },
        ].map(({ label, color }) => (
          <div key={label} className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full flex-shrink-0" style={{ background: color }} />
            <span className="text-gray-300">{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
