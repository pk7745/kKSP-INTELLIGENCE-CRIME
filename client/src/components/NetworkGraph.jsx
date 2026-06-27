import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Network } from 'vis-network'

// ── Node colour by case count ─────────────────────────────────────────────────
function nodeColor(caseCount = 1) {
  if (caseCount >= 5) return { background: '#ef4444', border: '#b91c1c', highlight: { background: '#f87171', border: '#b91c1c' } }
  if (caseCount >= 3) return { background: '#f97316', border: '#c2410c', highlight: { background: '#fb923c', border: '#c2410c' } }
  if (caseCount === 2) return { background: '#eab308', border: '#a16207', highlight: { background: '#facc15', border: '#a16207' } }
  return { background: '#6b7280', border: '#4b5563', highlight: { background: '#9ca3af', border: '#4b5563' } }
}

// ── vis-network options ───────────────────────────────────────────────────────
const VIS_OPTIONS = {
  nodes: {
    shape: 'dot',
    font:  { color: '#f1f5f9', size: 11, face: 'Inter, sans-serif' },
    borderWidth: 2,
    shadow: true,
  },
  edges: {
    color:  { color: '#334155', highlight: '#6366f1', hover: '#818cf8' },
    width:  1.5,
    smooth: { type: 'dynamic' },
    font:   { color: '#64748b', size: 9, face: 'Inter, sans-serif' },
  },
  physics: {
    solver: 'forceAtlas2Based',
    forceAtlas2Based: {
      gravitationalConstant: -50,
      centralGravity:        0.005,
      springLength:          120,
      springConstant:        0.05,
    },
    stabilization: { iterations: 150 },
  },
  interaction: {
    hover:         true,
    tooltipDelay:  150,
    navigationButtons: false,
    keyboard:      true,
  },
  layout: { improvedLayout: true },
}

// ── Accused detail panel ──────────────────────────────────────────────────────
function AccusedPanel({ node, onClose, t }) {
  if (!node) return null
  return (
    <div className="absolute top-3 right-3 z-10 w-72 bg-gray-800 border border-gray-700 rounded-xl shadow-xl p-4 animate-fade-in">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-sm font-bold text-white">{node.label}</h3>
          <p className="text-xs text-orange-400 font-semibold mt-0.5">
            {node.caseCount || 1} {t('casesCount')}
          </p>
        </div>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-300">
          <XIcon />
        </button>
      </div>

      {node.bio && (
        <div className="mb-3 space-y-1">
          {node.bio.age     && <p className="text-xs text-gray-400"><span className="text-gray-500">Age:</span> {node.bio.age}</p>}
          {node.bio.gender  && <p className="text-xs text-gray-400"><span className="text-gray-500">Gender:</span> {node.bio.gender}</p>}
          {node.bio.address && <p className="text-xs text-gray-400"><span className="text-gray-500">Address:</span> {node.bio.address}</p>}
        </div>
      )}

      {node.firs && node.firs.length > 0 && (
        <div>
          <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">FIRs</p>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {node.firs.map((fir, i) => (
              <div key={i} className="px-2 py-1.5 bg-gray-900 rounded border border-gray-700">
                <p className="text-xs font-mono text-indigo-300">{fir.CrimeNo || fir.crime_no}</p>
                <p className="text-[10px] text-gray-400">{fir.CrimeType || fir.crime_type}</p>
                {fir.DateTime && (
                  <p className="text-[10px] text-gray-600">{new Date(fir.DateTime).toLocaleDateString('en-IN')}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function NetworkGraph({ district, lastMessage }) {
  const { t } = useTranslation()
  const containerRef = useRef(null)
  const networkRef   = useRef(null)

  const [networkData,     setNetworkData]     = useState(null)
  const [loading,         setLoading]         = useState(true)
  const [error,           setError]           = useState(null)
  const [selectedNode,    setSelectedNode]    = useState(null)
  const [highlightRepeat, setHighlightRepeat] = useState(false)

  // ── Load network data ─────────────────────────────────────────────────────
  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const params = new URLSearchParams()
        if (district && district !== 'All Districts') params.set('district', district)
        const res = await fetch(`/api/network?${params}`)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        setNetworkData(data)
      } catch (err) {
        setError(err.message)
        // Use demo data when API unavailable
        setNetworkData(getDemoData())
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [district])

  // ── Build vis-network ──────────────────────────────────────────────────────
  useEffect(() => {
    if (!networkData || !containerRef.current) return

    // Build vis dataset
    const nodes = (networkData.nodes || []).map(n => ({
      id:        n.id,
      label:     n.label || n.name,
      value:     n.caseCount || 1,
      size:      Math.max(10, Math.min(40, (n.caseCount || 1) * 6)),
      color:     nodeColor(n.caseCount || 1),
      title:     `${n.label || n.name} — ${n.caseCount || 1} case(s)`,
      // Extra data stored on node
      caseCount: n.caseCount || 1,
      bio:       n.bio,
      firs:      n.firs || [],
    }))

    const edges = (networkData.edges || []).map(e => ({
      from:  e.from || e.source,
      to:    e.to   || e.target,
      label: e.label || e.shared_fir_count ? `${e.shared_fir_count} FIR${e.shared_fir_count > 1 ? 's' : ''}` : '',
      width: Math.max(1, Math.min(6, e.weight || 1)),
    }))

    if (networkRef.current) {
      networkRef.current.destroy()
      networkRef.current = null
    }

    const net = new Network(
      containerRef.current,
      { nodes, edges },
      VIS_OPTIONS
    )
    networkRef.current = net

    net.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId   = params.nodes[0]
        const nodeData = nodes.find(n => n.id === nodeId)
        setSelectedNode(nodeData || null)
      } else {
        setSelectedNode(null)
      }
    })

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy()
        networkRef.current = null
      }
    }
  }, [networkData])

  // ── Highlight repeat offenders ────────────────────────────────────────────
  const handleHighlightRepeat = () => {
    setHighlightRepeat(v => !v)
    if (!networkRef.current || !networkData) return
    const nodes = networkRef.current.body.data.nodes
    networkData.nodes.forEach(n => {
      if (!highlightRepeat && (n.caseCount || 1) >= 2) {
        nodes.update({ id: n.id, borderWidth: 4, color: { border: '#ef4444', background: nodeColor(n.caseCount || 1).background } })
      } else {
        nodes.update({ id: n.id, borderWidth: 2, color: nodeColor(n.caseCount || 1) })
      }
    })
  }

  const zoomIn  = () => networkRef.current?.moveTo({ scale: (networkRef.current.getScale() * 1.3) })
  const zoomOut = () => networkRef.current?.moveTo({ scale: (networkRef.current.getScale() * 0.77) })
  const resetView = () => networkRef.current?.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } })

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

  const nodeCount = networkData?.nodes?.length || 0
  const edgeCount = networkData?.edges?.length || 0

  return (
    <div className="relative h-full w-full bg-gray-900">
      {/* Toolbar */}
      <div className="absolute top-3 left-3 z-10 flex flex-col gap-2">
        {/* Stats */}
        <div className="bg-gray-900/90 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-400 space-y-0.5">
          <p><span className="text-indigo-400 font-bold">{nodeCount}</span> accused</p>
          <p><span className="text-gray-300 font-bold">{edgeCount}</span> {t('connections')}</p>
        </div>

        {/* Controls */}
        <div className="bg-gray-900/90 border border-gray-700 rounded-lg p-1.5 space-y-1">
          <button onClick={zoomIn}  className="w-full px-2 py-1 text-xs text-gray-300 hover:bg-gray-700 rounded">{t('zoomIn')}</button>
          <button onClick={zoomOut} className="w-full px-2 py-1 text-xs text-gray-300 hover:bg-gray-700 rounded">{t('zoomOut')}</button>
          <button onClick={resetView} className="w-full px-2 py-1 text-xs text-gray-300 hover:bg-gray-700 rounded">{t('resetView')}</button>
        </div>

        {/* Highlight repeat offenders */}
        <button
          onClick={handleHighlightRepeat}
          className={`px-2 py-2 rounded-lg text-xs font-semibold border transition-colors
            ${highlightRepeat
              ? 'bg-red-700 border-red-600 text-white'
              : 'bg-gray-900/90 border-gray-700 text-gray-300 hover:border-red-600 hover:text-red-300'}`}
        >
          {t('highlightRepeat')}
        </button>
      </div>

      {/* Error banner */}
      {error && (
        <div className="absolute top-3 right-3 z-10 bg-yellow-900/80 border border-yellow-700 rounded-lg px-3 py-2 text-xs text-yellow-200 max-w-xs">
          API unavailable — showing demo data
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 left-3 z-10 bg-gray-900/90 border border-gray-700 rounded-lg p-2.5 text-xs space-y-1">
        {[
          { label: '5+ cases', color: '#ef4444' },
          { label: '3-4 cases', color: '#f97316' },
          { label: '2 cases',  color: '#eab308' },
          { label: '1 case',   color: '#6b7280' },
        ].map(({ label, color }) => (
          <div key={label} className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: color }} />
            <span className="text-gray-300">{label}</span>
          </div>
        ))}
      </div>

      {/* vis-network canvas */}
      <div ref={containerRef} className="h-full w-full" />

      {/* Node detail panel */}
      {selectedNode && (
        <AccusedPanel
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
          t={t}
        />
      )}
    </div>
  )
}

// ── Demo data (fallback when API unavailable) ─────────────────────────────────
function getDemoData() {
  return {
    nodes: [
      { id: 1, label: 'Ravi Kumar',   caseCount: 7, bio: { age: 34, gender: 'M', address: 'Whitefield, Bengaluru' }, firs: [{ CrimeNo: 'SIM001', CrimeType: 'Theft' }] },
      { id: 2, label: 'Suresh Nayak', caseCount: 5, bio: { age: 28, gender: 'M', address: 'Shivajinagar, Bengaluru' }, firs: [{ CrimeNo: 'SIM002', CrimeType: 'Robbery' }] },
      { id: 3, label: 'Mahesh G',     caseCount: 4, bio: { age: 31, gender: 'M', address: 'Mysuru Road' }, firs: [{ CrimeNo: 'SIM003', CrimeType: 'Burglary' }] },
      { id: 4, label: 'Anita Rao',    caseCount: 3, bio: { age: 26, gender: 'F', address: 'Kalaburagi' }, firs: [] },
      { id: 5, label: 'Deepak S',     caseCount: 2, bio: { age: 22, gender: 'M', address: 'Belagavi' }, firs: [] },
      { id: 6, label: 'Ramesh T',     caseCount: 1, bio: { age: 45, gender: 'M', address: 'Dharwad' }, firs: [] },
      { id: 7, label: 'Venkat B',     caseCount: 3, bio: { age: 38, gender: 'M', address: 'Tumakuru' }, firs: [] },
      { id: 8, label: 'Lakshmi P',    caseCount: 2, bio: { age: 29, gender: 'F', address: 'Mangaluru' }, firs: [] },
    ],
    edges: [
      { from: 1, to: 2, shared_fir_count: 3, weight: 3 },
      { from: 1, to: 3, shared_fir_count: 2, weight: 2 },
      { from: 2, to: 4, shared_fir_count: 2, weight: 2 },
      { from: 3, to: 5, shared_fir_count: 1, weight: 1 },
      { from: 2, to: 3, shared_fir_count: 2, weight: 2 },
      { from: 4, to: 7, shared_fir_count: 1, weight: 1 },
      { from: 6, to: 1, shared_fir_count: 1, weight: 1 },
      { from: 7, to: 8, shared_fir_count: 2, weight: 2 },
    ],
  }
}

function XIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  )
}
