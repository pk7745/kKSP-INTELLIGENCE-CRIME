import { useState, useRef, useCallback, useEffect } from 'react'

/**
 * useVoiceInput
 * Wraps the browser Web Speech API (SpeechRecognition).
 * Works in Chrome / Edge; gracefully degrades elsewhere.
 *
 * Returns:
 *   transcript   — current interim/final recognised text
 *   isListening  — true while mic is active
 *   isSupported  — false if browser has no SpeechRecognition
 *   error        — latest error string or null
 *   startListening(language: 'en-US' | 'kn-IN')
 *   stopListening()
 */
export function useVoiceInput() {
  const SpeechRecognition =
    typeof window !== 'undefined'
      ? window.SpeechRecognition || window.webkitSpeechRecognition
      : null

  const isSupported = Boolean(SpeechRecognition)

  const [transcript,  setTranscript]  = useState('')
  const [isListening, setIsListening] = useState(false)
  const [error,       setError]       = useState(null)

  const recognitionRef = useRef(null)
  const mountedRef     = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      if (recognitionRef.current) {
        recognitionRef.current.onend = null
        recognitionRef.current.stop()
      }
    }
  }, [])

  const startListening = useCallback((language = 'en-US') => {
    if (!isSupported) {
      setError('Speech recognition is not supported in this browser. Use Chrome.')
      return
    }
    if (isListening) return

    setError(null)
    setTranscript('')

    const recognition = new SpeechRecognition()
    recognitionRef.current = recognition

    recognition.continuous     = true
    recognition.interimResults = true
    recognition.lang           = language  // 'en-US' or 'kn-IN'
    recognition.maxAlternatives = 1

    recognition.onstart = () => {
      if (mountedRef.current) setIsListening(true)
    }

    recognition.onresult = (event) => {
      if (!mountedRef.current) return
      let interim  = ''
      let finalStr = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          finalStr += result[0].transcript
        } else {
          interim += result[0].transcript
        }
      }

      // Accumulate final + show interim in real time
      setTranscript((prev) => {
        const base = prev.replace(/\s*…$/, '') // strip prior interim suffix
        if (finalStr) return (base + ' ' + finalStr).trim()
        if (interim)  return (base + ' ' + interim + '…').trim()
        return base
      })
    }

    recognition.onerror = (event) => {
      if (!mountedRef.current) return
      const msg = {
        'no-speech':         'No speech detected. Please try again.',
        'audio-capture':     'Microphone not available.',
        'not-allowed':       'Microphone permission denied.',
        'network':           'Network error during speech recognition.',
        'aborted':           null, // user-initiated stop — not an error
      }[event.error] || `Speech error: ${event.error}`

      if (msg) setError(msg)
      setIsListening(false)
    }

    recognition.onend = () => {
      if (mountedRef.current) setIsListening(false)
    }

    try {
      recognition.start()
    } catch (err) {
      setError('Could not start speech recognition: ' + err.message)
    }
  }, [isSupported, isListening, SpeechRecognition])

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }
    setIsListening(false)
  }, [])

  return {
    transcript,
    isListening,
    isSupported,
    error,
    startListening,
    stopListening,
  }
}
