import { useMemo, useRef, useState } from 'react'
import TelemetryCard from './components/TelemetryCard'

const defaultUrl = 'ws://raspberrypi.local:8000/ws'

const movementButtons = [
  { command: 'forward', label: 'Forward' },
  { command: 'left', label: 'Left' },
  { command: 'stop', label: 'STOP', danger: true },
  { command: 'right', label: 'Right' },
  { command: 'backward', label: 'Backward' },
]

function nowLabel() {
  return new Date().toLocaleTimeString()
}

export default function App() {
  const [wsUrl, setWsUrl] = useState(defaultUrl)
  const [connected, setConnected] = useState(false)
  const [pan, setPan] = useState(90)
  const [tilt, setTilt] = useState(90)
  const [log, setLog] = useState([])
  const socketRef = useRef(null)

  const statusText = useMemo(() => (connected ? 'Connected' : 'Disconnected'), [connected])

  const pushLog = (type, message) => {
    setLog((prev) => [{ time: nowLabel(), type, message }, ...prev].slice(0, 120))
  }

  const disconnectSocket = () => {
    if (socketRef.current) {
      socketRef.current.close()
      socketRef.current = null
    }
    setConnected(false)
  }

  const connectSocket = () => {
    if (socketRef.current || !wsUrl.trim()) {
      return
    }

    try {
      const socket = new WebSocket(wsUrl.trim())
      socketRef.current = socket

      socket.onopen = () => {
        setConnected(true)
        pushLog('system', `Connected to ${wsUrl}`)
      }

      socket.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data)
          pushLog('incoming', JSON.stringify(parsed))
        } catch {
          pushLog('incoming', String(event.data))
        }
      }

      socket.onerror = () => {
        pushLog('error', 'WebSocket error occurred.')
      }

      socket.onclose = () => {
        setConnected(false)
        socketRef.current = null
        pushLog('system', 'Connection closed')
      }
    } catch (error) {
      pushLog('error', `Failed to connect: ${error.message}`)
    }
  }

  const sendCommand = (command, value) => {
    const socket = socketRef.current
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      pushLog('error', `Cannot send '${command}' while disconnected.`)
      return
    }

    const payload = value === undefined ? { command } : { command, value }
    socket.send(JSON.stringify(payload))
    pushLog('outgoing', JSON.stringify(payload))
  }

  const handleServoChange = (command, value, setState) => {
    const numeric = Number(value)
    setState(numeric)
    sendCommand(command, numeric)
  }

  return (
    <main className="page-shell">
      <section className="app-card">
        <header className="header-row">
          <div>
            <p className="kicker">Raspberry Pi Robotics</p>
            <h1>Neural Drive Control Console</h1>
          </div>
          <span className={`status-badge ${connected ? 'online' : 'offline'}`}>{statusText}</span>
        </header>

        <div className="connection-panel">
          <input
            value={wsUrl}
            onChange={(e) => setWsUrl(e.target.value)}
            placeholder="ws://raspberrypi.local:8000/ws"
            aria-label="WebSocket URL"
          />
          {connected ? (
            <button className="secondary" onClick={disconnectSocket}>
              Disconnect
            </button>
          ) : (
            <button className="primary" onClick={connectSocket}>
              Connect
            </button>
          )}
        </div>

        <div className="grid-layout">
          <section className="controls-panel">
            <h2>Motion Controls</h2>
            <div className="movement-grid">
              {movementButtons.map((btn) => (
                <button
                  key={btn.command}
                  className={btn.danger ? 'danger' : 'motion'}
                  onClick={() => sendCommand(btn.command)}
                >
                  {btn.label}
                </button>
              ))}
            </div>

            <div className="slider-wrap">
              <label>
                Servo Pan: <strong>{pan}°</strong>
                <input
                  type="range"
                  min="0"
                  max="180"
                  value={pan}
                  onChange={(e) => handleServoChange('servo_pan', e.target.value, setPan)}
                />
              </label>
              <label>
                Servo Tilt: <strong>{tilt}°</strong>
                <input
                  type="range"
                  min="0"
                  max="180"
                  value={tilt}
                  onChange={(e) => handleServoChange('servo_tilt', e.target.value, setTilt)}
                />
              </label>
            </div>
          </section>

          <section className="side-panel">
            <h2>Telemetry</h2>
            <div className="telemetry-grid">
              <TelemetryCard label="Battery" value="84%" tone="green" />
              <TelemetryCard label="Distance" value="1.7 m" tone="blue" />
              <TelemetryCard label="Mode" value="Manual" tone="purple" />
            </div>

            <h2>Command Log</h2>
            <div className="log-panel">
              {log.length === 0 && <p className="muted">No messages yet. Connect and send commands.</p>}
              {log.map((entry, index) => (
                <div key={`${entry.time}-${index}`} className={`log-item ${entry.type}`}>
                  <span>[{entry.time}]</span> {entry.message}
                </div>
              ))}
            </div>
          </section>
        </div>
      </section>
    </main>
  )
}
