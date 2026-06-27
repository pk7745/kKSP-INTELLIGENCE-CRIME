import { useState, useEffect, useRef, useCallback } from 'react'

const BASE_DELAY = 1000   // 1 s initial reconnect delay
const MAX_DELAY  = 30000  // 30 s cap
const MULTIPLIER = 1.5

/**
 * useWebSocket
 * Connects to /ws, reconnects with exponential back-off on disconnect.
 * Returns { lastMessage, isConnected, sendMessage }
 * lastMessage is always the latest parsed JSON object (or null).
 */
export function useWebSocket() {
  const [lastMessage,  setLastMessage]  = useState(null)
  const [isConnected,  setIsConnected]  = useState(false)
  const wsRef       = useRef(null)
  const delayRef    = useRef(BASE_DELAY)
  const timerRef    = useRef(null)
  const mountedRef  = useRef(true)

  const connect = useCallback(() => {
    if (!mountedRef.current) return

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${protocol}://${window.location.host}/ws`

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        if (!mountedRef.current) return
        setIsConnected(true)
        delayRef.current = BASE_DELAY // reset back-off on success
      }

      ws.onmessage = (event) => {
        if (!mountedRef.current) return
        try {
          const data = JSON.parse(event.data)
          setLastMessage(data)
        } catch {
          // Non-JSON frames (ping / plain text) — ignore
        }
      }

      ws.onclose = () => {
        if (!mountedRef.current) return
        setIsConnected(false)
        wsRef.current = null
        scheduleReconnect()
      }

      ws.onerror = () => {
        // onclose will fire after onerror — do nothing extra here
        ws.close()
      }
    } catch (err) {
      scheduleReconnect()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const scheduleReconnect = useCallback(() => {
    if (!mountedRef.current) return
    const delay = delayRef.current
    delayRef.current = Math.min(delay * MULTIPLIER, MAX_DELAY)
    timerRef.current = setTimeout(() => {
      if (mountedRef.current) connect()
    }, delay)
  }, [connect])

  useEffect(() => {
    mountedRef.current = true
    connect()
    return () => {
      mountedRef.current = false
      clearTimeout(timerRef.current)
      if (wsRef.current) {
        wsRef.current.onclose = null // prevent reconnect on intentional close
        wsRef.current.close()
      }
    }
  }, [connect])

  const sendMessage = useCallback((data) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data))
      return true
    }
    return false
  }, [])

  return { lastMessage, isConnected, sendMessage }
}
