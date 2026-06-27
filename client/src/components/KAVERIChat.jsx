import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useVoiceInput } from '../hooks/useVoiceInput.js'

// ── Session ID (persisted) ────────────────────────────────────────────────────
function getSessionId() {
  let sid = localStorage.getItem('kaveri-session-id')
  if (!sid) {
    sid = `sess-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
    localStorage.setItem('kaveri-session-id', sid)
  }
  return sid
}

// ── Confidence colour ─────────────────────────────────────────────────────────
function confidenceColor(conf) {
  if (!conf) return 'text-gray-500'
  const c = conf.toUpperCase()
  if (c === 'HIGH'   || c === 'ಅಧಿಕ') return 'text-green-400'
  if (c === 'MEDIUM' || c === 'ಮಧ್ಯಮ') return 'text-yellow-400'
  return 'text-red-400'
}

// ── Intent badge colour ───────────────────────────────────────────────────────
function intentColor(intent) {
  const map = {
    HOTSPOT_QUERY:        'bg-red-900 text-red-300',
    ACCUSED_QUERY:        'bg-orange-900 text-orange-300',
    VICTIM_QUERY:         'bg-purple-900 text-purple-300',
    ARREST_QUERY:         'bg-blue-900 text-blue-300',
    TREND_QUERY:          'bg-cyan-900 text-cyan-300',
    PREDICTION_QUERY:     'bg-indigo-900 text-indigo-300',
    NETWORK_QUERY:        'bg-pink-900 text-pink-300',
    CHARGESHEET_QUERY:    'bg-teal-900 text-teal-300',
    PATROL_RECOMMENDATION:'bg-emerald-900 text-emerald-300',
    DEMOGRAPHIC_QUERY:    'bg-amber-900 text-amber-300',
    SEASONAL_QUERY:       'bg-lime-900 text-lime-300',
    GENERAL:              'bg-gray-800 text-gray-400',
  }
  return map[intent] || map.GENERAL
}

// ── TTS helper ────────────────────────────────────────────────────────────────
function speakText(text, lang = 'en-US') {
  if (!window.speechSynthesis) return
  window.speechSynthesis.cancel()
  const utt = new SpeechSynthesisUtterance(text)
  utt.lang = lang
  utt.rate = 0.95
  window.speechSynthesis.speak(utt)
}

// ── Detect Kannada ─────────────────────────────────────────────────────────────
function isKannada(text) {
  return /[ಀ-೿]/.test(text)
}

// ── Example questions ─────────────────────────────────────────────────────────
const EXAMPLE_KEYS = ['exampleQ1', 'exampleQ2', 'exampleQ3', 'exampleQ4', 'exampleQ5']

// ── Message bubble ─────────────────────────────────────────────────────────────
function MessageBubble({ msg, ttsEnabled }) {
  if (msg.role === 'user') {
    return (
      <div className="flex justify-end animate-fade-in">
        <div className="max-w-[80%] bg-indigo-600 text-white rounded-2xl rounded-br-sm px-4 py-2.5 text-sm">
          {msg.content}
        </div>
      </div>
    )
  }

  // Assistant bubble
  const { response, intent, language, sources, confidence, crime_nos } = msg

  return (
    <div className="flex gap-3 animate-fade-in">
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-700 flex items-center justify-center text-xs font-bold text-white">
        K
      </div>
      <div className="max-w-[85%] space-y-2">
        {/* Response text */}
        <div className={`bg-gray-800 border border-gray-700 rounded-2xl rounded-tl-sm px-4 py-3 text-sm
                         text-gray-100 whitespace-pre-wrap leading-relaxed
                         ${isKannada(response) ? 'font-kannada' : ''}`}>
          {response}
        </div>

        {/* Metadata row */}
        <div className="flex flex-wrap gap-2 items-center px-1">
          {/* Intent badge */}
          {intent && (
            <span className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full ${intentColor(intent)}`}>
              {intent.replace(/_/g, ' ')}
            </span>
          )}

          {/* Language badge */}
          {language && (
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-700 text-gray-300 font-mono">
              {language === 'kn' ? 'ಕನ್ನಡ' : 'EN'}
            </span>
          )}

          {/* Confidence */}
          {confidence && (
            <span className={`text-[10px] font-semibold ${confidenceColor(confidence)}`}>
              ● {confidence}
            </span>
          )}

          {/* TTS replay */}
          {ttsEnabled && (
            <button
              onClick={() => speakText(response, language === 'kn' ? 'kn-IN' : 'en-US')}
              title="Play response"
              className="text-gray-500 hover:text-indigo-400 transition-colors"
            >
              <SpeakerIcon />
            </button>
          )}
        </div>

        {/* Sources chips */}
        {sources && sources.length > 0 && (
          <div className="flex flex-wrap gap-1 px-1">
            {sources.map((s, i) => (
              <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-gray-700 text-indigo-300 font-mono">
                {s}
              </span>
            ))}
          </div>
        )}

        {/* CrimeNo chips */}
        {crime_nos && crime_nos.length > 0 && (
          <div className="flex flex-wrap gap-1 px-1">
            {crime_nos.slice(0, 6).map((cn, i) => (
              <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-gray-900 text-orange-300 font-mono border border-gray-700">
                {cn}
              </span>
            ))}
            {crime_nos.length > 6 && (
              <span className="text-[10px] text-gray-500">+{crime_nos.length - 6} more</span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Typing indicator ───────────────────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div className="flex gap-3 animate-fade-in">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-700 flex items-center justify-center text-xs font-bold text-white">
        K
      </div>
      <div className="bg-gray-800 border border-gray-700 rounded-2xl rounded-tl-sm px-4 py-3">
        <div className="flex gap-1 items-center h-4">
          {[0, 1, 2].map(i => (
            <span
              key={i}
              className="h-2 w-2 rounded-full bg-indigo-500"
              style={{ animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite` }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function KAVERIChat({ district, user }) {
  const { t } = useTranslation()
  const sessionId = useRef(getSessionId())

  const [messages,    setMessages]    = useState([])
  const [inputText,   setInputText]   = useState('')
  const [isLoading,   setIsLoading]   = useState(false)
  const [ttsEnabled,  setTtsEnabled]  = useState(false)
  const [voiceLang,   setVoiceLang]   = useState('en-US')
  const [pdfLoading,  setPdfLoading]  = useState(false)

  const bottomRef   = useRef(null)
  const inputRef    = useRef(null)

  const { transcript, isListening, isSupported, error: voiceError, startListening, stopListening } = useVoiceInput()

  // ── Sync voice transcript into input ────────────────────────────────────
  useEffect(() => {
    if (transcript) setInputText(transcript)
  }, [transcript])

  // ── Scroll to bottom on new messages ────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // ── Auto-TTS new assistant messages ─────────────────────────────────────
  useEffect(() => {
    if (!ttsEnabled || messages.length === 0) return
    const last = messages[messages.length - 1]
    if (last.role === 'assistant' && last.response) {
      speakText(last.response, last.language === 'kn' ? 'kn-IN' : 'en-US')
    }
  }, [messages, ttsEnabled])

  // ── Send message ─────────────────────────────────────────────────────────
  const sendMessage = useCallback(async (text) => {
    const query = (text || inputText).trim()
    if (!query || isLoading) return

    stopListening()
    setInputText('')
    setMessages(prev => [...prev, { role: 'user', content: query }])
    setIsLoading(true)

    try {
      const res = await fetch('/api/chat/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(user?.token ? { Authorization: `Bearer ${user.token}` } : {}),
        },
        body: JSON.stringify({
          query,
          session_id: sessionId.current,
          district: district !== 'All Districts' ? district : undefined,
        }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()

      // Auto-switch voice to Kannada if response is in Kannada
      if (data.language === 'kn') setVoiceLang('kn-IN')
      else setVoiceLang('en-US')

      setMessages(prev => [...prev, {
        role:       'assistant',
        response:   data.response   || data.answer || '',
        intent:     data.intent,
        language:   data.language,
        sources:    data.sources    || [],
        confidence: data.confidence,
        crime_nos:  data.crime_nos  || [],
      }])
    } catch (err) {
      setMessages(prev => [...prev, {
        role:     'assistant',
        response: `Error: ${err.message}. Please check your connection or try again.`,
        intent:   'GENERAL',
      }])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }, [inputText, isLoading, district, user, stopListening])

  // ── Voice toggle ─────────────────────────────────────────────────────────
  const toggleVoice = () => {
    if (isListening) {
      stopListening()
      // After stopping, send whatever was transcribed
      if (transcript.trim()) setTimeout(() => sendMessage(transcript.trim()), 300)
    } else {
      startListening(voiceLang)
    }
  }

  // ── Export PDF ───────────────────────────────────────────────────────────
  const exportPDF = async () => {
    if (messages.length === 0) return
    setPdfLoading(true)
    try {
      const res = await fetch('/api/export/pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId.current,
          messages,
        }),
      })
      if (!res.ok) throw new Error('PDF export failed')
      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      a.download = `KAVERI-Report-${Date.now()}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      alert('PDF export failed: ' + err.message)
    } finally {
      setPdfLoading(false)
    }
  }

  // ── Key handler ──────────────────────────────────────────────────────────
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const isEmpty = messages.length === 0

  return (
    <div className="flex flex-col h-full bg-gray-900">

      {/* ── Chat header ───────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-800 bg-gray-900 flex-shrink-0">
        <div>
          <p className="text-xs text-gray-500 font-mono">
            Session: <span className="text-indigo-400">{sessionId.current.slice(-8)}</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* TTS toggle */}
          <button
            onClick={() => {
              setTtsEnabled(v => !v)
              if (ttsEnabled) window.speechSynthesis?.cancel()
            }}
            title={ttsEnabled ? t('ttsEnabled') : t('ttsDisabled')}
            className={`p-1.5 rounded-lg transition-colors ${ttsEnabled
              ? 'bg-indigo-700 text-indigo-200'
              : 'bg-gray-800 text-gray-500 hover:text-gray-300'}`}
          >
            <SpeakerIcon />
          </button>

          {/* Export PDF */}
          <button
            onClick={exportPDF}
            disabled={pdfLoading || isEmpty}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold
                       bg-gray-800 hover:bg-gray-700 text-gray-300 disabled:opacity-40 transition-colors"
          >
            {pdfLoading ? <SpinnerIcon /> : <PDFIcon />}
            {t('exportPDF')}
          </button>
        </div>
      </div>

      {/* ── Message list ──────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {isEmpty ? (
          <EmptyState t={t} onExample={q => sendMessage(q)} />
        ) : (
          messages.map((msg, i) => (
            <MessageBubble key={i} msg={msg} ttsEnabled={ttsEnabled} />
          ))
        )}
        {isLoading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* ── Voice error ────────────────────────────────────────────────── */}
      {voiceError && (
        <div className="mx-4 mb-2 px-3 py-2 bg-red-900/40 border border-red-700 rounded-lg text-xs text-red-300">
          {voiceError}
        </div>
      )}

      {/* ── Input area ────────────────────────────────────────────────── */}
      <div className="flex-shrink-0 border-t border-gray-800 px-4 py-3 bg-gray-900">
        <div className="flex gap-2 items-end">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t('chatPlaceholder')}
              rows={1}
              style={{ resize: 'none', minHeight: '40px', maxHeight: '120px' }}
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-sm
                         text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2
                         focus:ring-indigo-500 focus:border-transparent overflow-y-auto"
            />
            {/* Recording indicator overlay */}
            {isListening && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse-ring" />
                <span className="text-[10px] text-red-400 font-semibold">{t('recordingIn')}</span>
              </div>
            )}
          </div>

          {/* Voice button */}
          {isSupported && (
            <button
              onClick={toggleVoice}
              title={isListening ? t('stopRecording') : t('startRecording')}
              className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-all
                ${isListening
                  ? 'bg-red-600 text-white animate-pulse'
                  : 'bg-gray-700 text-gray-400 hover:bg-gray-600 hover:text-gray-200'}`}
            >
              <MicIcon />
            </button>
          )}

          {/* Send button */}
          <button
            onClick={() => sendMessage()}
            disabled={!inputText.trim() || isLoading}
            className="flex-shrink-0 w-10 h-10 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white
                       flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? <SpinnerIcon /> : <SendIcon />}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Empty state ───────────────────────────────────────────────────────────────
function EmptyState({ t, onExample }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-6 py-8">
      <div className="text-center">
        <div className="w-16 h-16 rounded-2xl bg-indigo-900/50 border border-indigo-700 flex items-center justify-center mx-auto mb-4">
          <span className="text-3xl font-black text-indigo-400">K</span>
        </div>
        <h2 className="text-xl font-bold text-white mb-1">KAVERI</h2>
        <p className="text-sm text-gray-400 max-w-xs text-center">
          Karnataka AI for Violence, Evidence & Risk Intelligence.<br />
          Ask me anything about crime data.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-xl">
        {EXAMPLE_KEYS.map(key => (
          <button
            key={key}
            onClick={() => onExample(t(key))}
            className="text-left px-4 py-3 rounded-xl bg-gray-800 border border-gray-700
                       hover:border-indigo-600 hover:bg-gray-750 text-sm text-gray-300
                       transition-all group"
          >
            <span className="text-indigo-400 group-hover:text-indigo-300 text-xs mr-1">→</span>
            {t(key)}
          </button>
        ))}
      </div>
    </div>
  )
}

// ── Icons ─────────────────────────────────────────────────────────────────────
function SendIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
    </svg>
  )
}

function MicIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
    </svg>
  )
}

function SpeakerIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z" />
    </svg>
  )
}

function PDFIcon() {
  return (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  )
}

function SpinnerIcon() {
  return (
    <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}
