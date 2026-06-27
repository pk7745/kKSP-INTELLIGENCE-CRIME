import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import i18n from 'i18next'
import { useWebSocket } from './hooks/useWebSocket.js'
import KAVERIChat     from './components/KAVERIChat.jsx'
import CrimeMap       from './components/CrimeMap.jsx'
import NetworkGraph   from './components/NetworkGraph.jsx'
import AlertCenter    from './components/AlertCenter.jsx'
import ThreatRadar    from './components/ThreatRadar.jsx'
import PredictionPanel from './components/PredictionPanel.jsx'

// ── Karnataka districts ───────────────────────────────────────────────────────
const DISTRICTS = [
  'All Districts','Bagalkote','Ballari','Belagavi','Bengaluru Rural',
  'Bengaluru Urban','Bidar','Chamarajanagara','Chikkaballapura','Chikkamagaluru',
  'Chitradurga','Dakshina Kannada','Davanagere','Dharwad','Gadag',
  'Hassan','Haveri','Kalaburagi','Kodagu','Kolar','Koppal','Mandya',
  'Mysuru','Raichur','Ramanagara','Shivamogga','Tumakuru','Udupi',
  'Uttara Kannada','Vijayapura','Yadgir',
]

// ── Nav items ─────────────────────────────────────────────────────────────────
const NAV_ITEMS = [
  { id: 'chat',        icon: ChatIcon,        labelKey: 'chat',         roles: ['admin','analyst','officer','viewer'] },
  { id: 'map',         icon: MapIcon,         labelKey: 'crimeMap',     roles: ['admin','analyst','officer','viewer'] },
  { id: 'network',     icon: NetworkIcon,     labelKey: 'network',      roles: ['admin','analyst'] },
  { id: 'alerts',      icon: AlertIcon,       labelKey: 'alertCenter',  roles: ['admin','analyst','officer','viewer'] },
  { id: 'predictions', icon: PredictionIcon,  labelKey: 'predictions',  roles: ['admin','analyst'] },
  { id: 'analytics',   icon: AnalyticsIcon,   labelKey: 'analytics',    roles: ['admin','analyst'] },
]

// ── Severity colour helper ────────────────────────────────────────────────────
function severityColor(severity) {
  if (severity === 'CRITICAL') return 'bg-red-600'
  if (severity === 'HIGH')     return 'bg-orange-500'
  return 'bg-yellow-500'
}

// ── Toast notification ────────────────────────────────────────────────────────
function AlertToast({ alert, onDismiss }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 6000)
    return () => clearTimeout(t)
  }, [onDismiss])

  return (
    <div className={`animate-slide-in flex items-start gap-3 p-4 rounded-lg shadow-lg border border-gray-700
                     bg-gray-800 max-w-sm w-full pointer-events-auto`}>
      <span className={`mt-0.5 h-2.5 w-2.5 rounded-full flex-shrink-0 ${severityColor(alert.severity)}`} />
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold text-red-400 uppercase tracking-wider">
          {alert.severity} — {alert.alert_type?.replace(/_/g,' ')}
        </p>
        <p className="text-sm text-gray-200 mt-0.5 line-clamp-2">{alert.description}</p>
        {alert.crime_no && (
          <p className="text-xs text-indigo-400 mt-1 font-mono">{alert.crime_no}</p>
        )}
      </div>
      <button onClick={onDismiss} className="text-gray-500 hover:text-gray-300 flex-shrink-0 mt-0.5">
        <XIcon />
      </button>
    </div>
  )
}

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const { t } = useTranslation()
  const { lastMessage, isConnected } = useWebSocket()

  const [activeNav,       setActiveNav]       = useState('chat')
  const [selectedDistrict,setSelectedDistrict]= useState('All Districts')
  const [lang,            setLang]            = useState(localStorage.getItem('kaveri-lang') || 'en')
  const [user,            setUser]            = useState(null)           // null = not logged in
  const [loginOpen,       setLoginOpen]       = useState(false)
  const [toasts,          setToasts]          = useState([])
  const [alertCount,      setAlertCount]      = useState(0)
  const toastIdRef = useRef(0)

  // ── Language toggle ───────────────────────────────────────────────────────
  const toggleLang = () => {
    const next = lang === 'en' ? 'kn' : 'en'
    setLang(next)
    localStorage.setItem('kaveri-lang', next)
    i18n.changeLanguage(next)
  }

  // ── Handle WebSocket messages ─────────────────────────────────────────────
  useEffect(() => {
    if (!lastMessage) return
    const msg = lastMessage

    if (msg.type === 'alert' && msg.data) {
      const alert = msg.data
      setAlertCount(n => n + 1)
      const id = ++toastIdRef.current
      setToasts(prev => [...prev, { ...alert, _toastId: id }])
    }

    if (msg.type === 'new_fir') {
      // Other components subscribe via their own lastMessage prop — no extra action needed here
    }
  }, [lastMessage])

  const dismissToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t._toastId !== id))
  }, [])

  // ── Role-based nav filter ─────────────────────────────────────────────────
  const userRole = user?.role || 'viewer'
  const visibleNav = NAV_ITEMS.filter(item => item.roles.includes(userRole))

  // ── Simulate new FIR ─────────────────────────────────────────────────────
  const simulateFIR = async () => {
    try {
      await fetch('/webhook/fir/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          CrimeNo: `SIM${Date.now()}`,
          CrimeType: 'Theft',
          DateTime: new Date().toISOString(),
          DistrictName: selectedDistrict === 'All Districts' ? 'Bengaluru Urban' : selectedDistrict,
          Latitude:  12.9716 + (Math.random() - 0.5) * 0.5,
          Longitude: 77.5946 + (Math.random() - 0.5) * 0.5,
          BriefFacts: 'Simulated FIR for demonstration purposes.',
          GravityOffenceID: Math.random() > 0.8 ? 1 : 2,
        }),
      })
    } catch (err) {
      console.warn('Simulate FIR error:', err)
    }
  }

  // ── Login form (simple demo auth) ────────────────────────────────────────
  const handleLogin = (e) => {
    e.preventDefault()
    const fd = new FormData(e.target)
    const username = fd.get('username')
    // Demo: derive role from username prefix
    let role = 'viewer'
    if (username.startsWith('admin'))   role = 'admin'
    else if (username.startsWith('analyst')) role = 'analyst'
    else if (username.startsWith('officer')) role = 'officer'
    setUser({ username, role })
    setLoginOpen(false)
  }

  const handleLogout = () => {
    setUser(null)
    setActiveNav('chat')
  }

  // ── Render active component ───────────────────────────────────────────────
  const renderMain = () => {
    const props = { district: selectedDistrict, lastMessage, user }
    switch (activeNav) {
      case 'chat':        return <KAVERIChat      {...props} />
      case 'map':         return <CrimeMap        {...props} />
      case 'network':     return <NetworkGraph     {...props} />
      case 'alerts':      return <AlertCenter      {...props} />
      case 'predictions': return <PredictionPanel  {...props} />
      case 'analytics':   return <ThreatRadar      {...props} />
      default:            return <KAVERIChat      {...props} />
    }
  }

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100 overflow-hidden">

      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside className="flex flex-col w-16 lg:w-56 bg-gray-950 border-r border-gray-800 flex-shrink-0">
        {/* Logo */}
        <div className="flex items-center gap-2 px-3 py-4 border-b border-gray-800">
          <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
            <ShieldIcon />
          </div>
          <span className="hidden lg:block font-bold text-sm text-white tracking-wide">KAVERI</span>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-3 space-y-1 px-2">
          {visibleNav.map(item => {
            const Icon = item.icon
            const active = activeNav === item.id
            return (
              <button
                key={item.id}
                onClick={() => setActiveNav(item.id)}
                className={`w-full flex items-center gap-3 px-2 py-2.5 rounded-lg text-sm font-medium transition-colors
                  ${active
                    ? 'bg-indigo-600 text-white shadow-glow-indigo'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'}`}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                <span className="hidden lg:block">{t(item.labelKey)}</span>
                {item.id === 'alerts' && alertCount > 0 && (
                  <span className="hidden lg:flex ml-auto h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-red-600 text-[10px] font-bold px-1">
                    {alertCount > 99 ? '99+' : alertCount}
                  </span>
                )}
              </button>
            )
          })}
        </nav>

        {/* Connection status */}
        <div className="px-3 py-3 border-t border-gray-800">
          <div className="flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full flex-shrink-0 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="hidden lg:block text-xs text-gray-500">
              {isConnected ? 'Live' : 'Reconnecting…'}
            </span>
          </div>
        </div>
      </aside>

      {/* ── Main area ───────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">

        {/* Header */}
        <header className="flex items-center gap-3 px-4 py-3 bg-gray-900 border-b border-gray-800 flex-shrink-0">
          {/* Title (small screens) */}
          <div className="lg:hidden font-bold text-sm text-indigo-400">KAVERI</div>

          {/* Page title */}
          <div className="hidden lg:block text-sm font-semibold text-gray-300">
            {t(NAV_ITEMS.find(n => n.id === activeNav)?.labelKey || 'chat')}
          </div>

          <div className="flex-1" />

          {/* District filter */}
          <select
            value={selectedDistrict}
            onChange={e => setSelectedDistrict(e.target.value)}
            className="bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded-lg px-2 py-1.5
                       focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
          >
            {DISTRICTS.map(d => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>

          {/* Language toggle */}
          <button
            onClick={toggleLang}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold border border-gray-700
                       bg-gray-800 text-gray-200 hover:bg-gray-700 transition-colors"
          >
            {lang === 'en' ? 'ಕನ್ನಡ' : 'EN'}
          </button>

          {/* Simulate FIR */}
          <button
            onClick={simulateFIR}
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold
                       bg-orange-600 hover:bg-orange-500 text-white transition-colors"
          >
            <PlusIcon />
            <span>{t('simulateNewFIR')}</span>
          </button>

          {/* Login / Logout */}
          {user ? (
            <div className="flex items-center gap-2">
              <span className="hidden md:block text-xs text-gray-400">
                <span className="text-indigo-400 font-semibold">{user.username}</span>
                {' '}·{' '}
                <span className="capitalize text-gray-500">{user.role}</span>
              </span>
              <button
                onClick={handleLogout}
                className="px-3 py-1.5 rounded-lg text-xs border border-gray-700 text-gray-400
                           hover:bg-gray-800 hover:text-gray-200 transition-colors"
              >
                {t('logout')}
              </button>
            </div>
          ) : (
            <button
              onClick={() => setLoginOpen(true)}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
            >
              {t('login')}
            </button>
          )}
        </header>

        {/* Main content */}
        <main className="flex-1 overflow-hidden">
          {renderMain()}
        </main>
      </div>

      {/* ── Toast container ──────────────────────────────────────────────── */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
        {toasts.map(toast => (
          <AlertToast
            key={toast._toastId}
            alert={toast}
            onDismiss={() => dismissToast(toast._toastId)}
          />
        ))}
      </div>

      {/* ── Login modal ──────────────────────────────────────────────────── */}
      {loginOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 w-80 shadow-xl">
            <h2 className="text-lg font-bold text-white mb-1">KAVERI Login</h2>
            <p className="text-xs text-gray-400 mb-4">
              Demo: prefix username with <code className="text-indigo-400">admin</code>,{' '}
              <code className="text-indigo-400">analyst</code>, or{' '}
              <code className="text-indigo-400">officer</code> to set role.
            </p>
            <form onSubmit={handleLogin} className="space-y-3">
              <input
                name="username"
                placeholder="Username"
                required
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm
                           text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <input
                name="password"
                type="password"
                placeholder="Password"
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm
                           text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <div className="flex gap-2 pt-1">
                <button
                  type="submit"
                  className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold py-2 rounded-lg transition-colors"
                >
                  {t('login')}
                </button>
                <button
                  type="button"
                  onClick={() => setLoginOpen(false)}
                  className="flex-1 bg-gray-700 hover:bg-gray-600 text-gray-200 text-sm py-2 rounded-lg transition-colors"
                >
                  {t('close')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

// ── SVG Icon Components ───────────────────────────────────────────────────────
function ShieldIcon() {
  return (
    <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
    </svg>
  )
}

function ChatIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
    </svg>
  )
}

function MapIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z" />
    </svg>
  )
}

function NetworkIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
    </svg>
  )
}

function AlertIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
    </svg>
  )
}

function PredictionIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
    </svg>
  )
}

function AnalyticsIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z" />
    </svg>
  )
}

function XIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  )
}

function PlusIcon() {
  return (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
  )
}
