import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuthStore } from '../../app/providers/AuthProvider'

interface CollabMessage {
  type: string
  scenario_id?: string
  user_id?: string
  payload?: unknown
}

interface CollabPanelProps {
  scenarioId: string
}

/**
 * CollabPanel — floating collaboration panel for a scenario room.
 *
 * Features:
 * - Live presence list (users in the room via user:join / user:leave messages)
 * - Map control: request / release exclusive map edit rights
 * - Shows who currently holds map control
 */
export function CollabPanel({ scenarioId }: CollabPanelProps) {
  const token = useAuthStore((s) => s.token)
  const currentUser = useAuthStore((s) => s.user)

  const [connected, setConnected] = useState(false)
  const [users, setUsers] = useState<string[]>([])
  const [controller, setController] = useState<string | null>(null)
  const [statusMsg, setStatusMsg] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  const myUserId = currentUser?.id ?? ''

  const connect = useCallback(() => {
    if (!token || !scenarioId) return

    const wsBase = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8084'
    const url = `${wsBase}/ws/${scenarioId}?token=${encodeURIComponent(token)}`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      setStatusMsg(null)
    }

    ws.onclose = () => {
      setConnected(false)
      wsRef.current = null
    }

    ws.onerror = () => {
      setConnected(false)
    }

    ws.onmessage = (evt) => {
      try {
        const msg: CollabMessage = JSON.parse(evt.data as string)
        handleMessage(msg)
      } catch {
        // ignore malformed messages
      }
    }
  }, [token, scenarioId])

  function handleMessage(msg: CollabMessage) {
    switch (msg.type) {
      case 'user:join':
        if (msg.user_id) setUsers((prev) => [...new Set([...prev, msg.user_id!])])
        break
      case 'user:leave':
        if (msg.user_id) setUsers((prev) => prev.filter((u) => u !== msg.user_id))
        break
      case 'map:control:granted':
        setController(msg.user_id ?? null)
        setStatusMsg(msg.user_id === myUserId ? '✅ You have map control' : null)
        break
      case 'map:control:released':
        setController(null)
        setStatusMsg(null)
        break
      case 'map:control:busy': {
        const p = msg.payload as { controller_id?: string } | undefined
        setStatusMsg(`⚠ Map controlled by ${p?.controller_id ?? 'another user'}`)
        break
      }
      case 'map:control:denied':
        setStatusMsg('⛔ Your role cannot request map control')
        break
    }
  }

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
    }
  }, [connect])

  const sendMessage = (msg: CollabMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    }
  }

  const requestControl = () => {
    sendMessage({ type: 'map:control:request' })
  }

  const releaseControl = () => {
    sendMessage({ type: 'map:control:release' })
  }

  const iHaveControl = controller === myUserId

  return (
    <div className="absolute top-4 right-4 z-20 w-56 bg-gray-900/90 backdrop-blur border border-gray-700 rounded-lg shadow-xl text-sm">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-700">
        <span className="font-semibold text-white text-xs uppercase tracking-wide">Collaboration</span>
        <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-gray-600'}`} title={connected ? 'Connected' : 'Disconnected'} />
      </div>

      {/* Presence */}
      <div className="px-3 py-2 border-b border-gray-700">
        <p className="text-xs text-gray-400 mb-1">In Room ({users.length})</p>
        {users.length === 0 ? (
          <p className="text-xs text-gray-600 italic">No users</p>
        ) : (
          <ul className="space-y-0.5">
            {users.slice(0, 6).map((uid) => (
              <li key={uid} className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-sky-400 flex-shrink-0" />
                <span className="text-xs text-gray-300 truncate font-mono">{uid.slice(0, 8)}…</span>
                {uid === myUserId && <span className="text-xs text-gray-500">(you)</span>}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Map control */}
      <div className="px-3 py-2">
        <p className="text-xs text-gray-400 mb-1">Map Control</p>
        {controller ? (
          <p className="text-xs text-gray-300 mb-2">
            {iHaveControl ? (
              <span className="text-green-400 font-medium">You have control</span>
            ) : (
              <span className="text-yellow-400">Held by {controller.slice(0, 8)}…</span>
            )}
          </p>
        ) : (
          <p className="text-xs text-gray-500 mb-2 italic">No one has control</p>
        )}

        {iHaveControl ? (
          <button
            onClick={releaseControl}
            className="w-full text-xs py-1 px-2 bg-yellow-700 hover:bg-yellow-600 text-white rounded transition-colors"
          >
            Release Control
          </button>
        ) : (
          <button
            onClick={requestControl}
            disabled={!connected}
            className="w-full text-xs py-1 px-2 bg-sky-700 hover:bg-sky-600 text-white rounded transition-colors disabled:opacity-40"
          >
            Request Control
          </button>
        )}

        {statusMsg && (
          <p className="text-xs text-gray-400 mt-1.5">{statusMsg}</p>
        )}
      </div>
    </div>
  )
}
