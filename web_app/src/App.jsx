import { useEffect, useMemo, useRef, useState } from 'react'
import TelemetryCard from './components/TelemetryCard'

const defaultBackendUrl = 'http://raspberrypi.local:8000'
const sampleRoute = ['forward 10', 'right 90', 'forward 3', 'left 45', 'stop'].join('\n')
const manualButtons = [
  { label: 'Forward', command: 'forward' },
  { label: 'Left', command: 'left' },
  { label: 'STOP', command: 'stop', danger: true },
  { label: 'Right', command: 'right' },
  { label: 'Backward', command: 'backward' },
]

const emptyTelemetry = {
  mode: 'idle',
  autonomy_enabled: false,
  waypoint_mode_active: false,
  current_command: null,
  command_queue_length: 0,
  obstacle_distance: null,
  steering_angle: 90,
  camera_pan_angle: 90,
  speed: 0,
  battery_level: 0,
  camera_status: 'unknown',
  lidar_status: 'unknown',
  last_action: 'waiting for connection',
  error: null,
  completed_commands: 0,
  remaining_commands: 0,
}

function nowLabel() {
  return new Date().toLocaleTimeString()
}

function toWsUrl(httpUrl) {
  if (!httpUrl) return ''
  return `${httpUrl.replace(/^http/i, 'ws').replace(/\/$/, '')}/ws`
}

function normalizeBaseUrl(url) {
  return url.trim().replace(/\/$/, '')
}

export default function App() {
  const [backendUrl, setBackendUrl] = useState(defaultBackendUrl)
  const [connectionState, setConnectionState] = useState('disconnected')
  const [telemetry, setTelemetry] = useState(emptyTelemetry)
  const [events, setEvents] = useState([])
  const [selectedMode, setSelectedMode] = useState('idle')
  const [cameraPan, setCameraPan] = useState(90)
  const [waypoints, setWaypoints] = useState(sampleRoute)
  const socketRef = useRef(null)
  const lastEventSignatureRef = useRef('')

  const wsUrl = useMemo(() => toWsUrl(normalizeBaseUrl(backendUrl)), [backendUrl])
  const videoUrl = useMemo(() => `${normalizeBaseUrl(backendUrl)}/video`, [backendUrl])

  const pushEvent = (level, message) => {
    setEvents((prev) => [{ time: nowLabel(), level, message }, ...prev].slice(0, 140))
  }

  const disconnectSocket = () => {
    if (socketRef.current) {
      socketRef.current.close()
      socketRef.current = null
    }
    setConnectionState('disconnected')
  }

  const fetchJson = async (path, options = {}) => {
    const response = await fetch(`${normalizeBaseUrl(backendUrl)}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
    const payload = await response.json()
    if (!response.ok) {
      const message = payload.detail || payload.message || `Request failed: ${response.status}`
      throw new Error(message)
    }
    return payload
  }

  const syncState = async () => {
    try {
      const snapshot = await fetchJson('/state', { method: 'GET', headers: undefined })
      setTelemetry((prev) => ({ ...prev, ...snapshot }))
      setSelectedMode(snapshot.mode || 'idle')
      setCameraPan(snapshot.camera_pan_angle ?? 90)
    } catch (error) {
      pushEvent('error', error.message)
    }
  }

  useEffect(() => {
    syncState()
  }, [])

  useEffect(() => {
    return () => disconnectSocket()
  }, [])

  const connectSocket = () => {
    if (socketRef.current || !wsUrl) return
    const socket = new WebSocket(wsUrl)
    socketRef.current = socket
    setConnectionState('connecting')

    socket.onopen = () => {
      setConnectionState('connected')
      pushEvent('system', `Connected to ${wsUrl}`)
    }

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        setTelemetry((prev) => ({ ...prev, ...payload }))
        setSelectedMode(payload.mode || 'idle')
        setCameraPan(payload.camera_pan_angle ?? 90)
        const signature = [payload.mode, payload.current_command, payload.last_action, payload.error].join('|')
        if (payload.last_action && signature !== lastEventSignatureRef.current) {
          lastEventSignatureRef.current = signature
          pushEvent(payload.error ? 'error' : 'incoming', payload.last_action)
        }
      } catch {
        pushEvent('incoming', String(event.data))
      }
    }

    socket.onerror = () => {
      setConnectionState('error')
      pushEvent('error', 'WebSocket connection error')
    }

    socket.onclose = () => {
      socketRef.current = null
      setConnectionState('disconnected')
      pushEvent('system', 'WebSocket disconnected')
    }
  }

  const sendWsCommand = (command, value) => {
    const socket = socketRef.current
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      pushEvent('error', `Cannot send ${command}. Connect first.`)
      return
    }
    const payload = value === undefined ? { command } : { command, value }
    socket.send(JSON.stringify(payload))
    pushEvent('outgoing', JSON.stringify(payload))
  }

  const setMode = async (mode) => {
    try {
      const payload = await fetchJson('/mode', {
        method: 'POST',
        body: JSON.stringify({ mode }),
      })
      setTelemetry((prev) => ({ ...prev, ...payload }))
      setSelectedMode(mode)
      pushEvent('system', `Mode changed to ${mode}`)
    } catch (error) {
      pushEvent('error', error.message)
    }
  }

  const startAutonomy = async () => {
    try {
      const payload = await fetchJson('/autonomy/start', { method: 'POST', body: '{}' })
      setTelemetry((prev) => ({ ...prev, ...payload }))
      setSelectedMode('obstacle_avoidance')
      pushEvent('system', 'Obstacle avoidance started')
    } catch (error) {
      pushEvent('error', error.message)
    }
  }

  const stopAutonomy = async () => {
    try {
      const payload = await fetchJson('/autonomy/stop', { method: 'POST', body: '{}' })
      setTelemetry((prev) => ({ ...prev, ...payload }))
      pushEvent('system', 'Obstacle avoidance stopped')
    } catch (error) {
      pushEvent('error', error.message)
    }
  }

  const emergencyStop = async () => {
    try {
      const payload = await fetchJson('/stop', { method: 'POST', body: '{}' })
      setTelemetry((prev) => ({ ...prev, ...payload }))
      setSelectedMode('idle')
      pushEvent('error', 'Emergency stop issued')
    } catch (error) {
      pushEvent('error', error.message)
    }
  }

  const submitWaypoints = async () => {
    try {
      const payload = await fetchJson('/waypoints', {
        method: 'POST',
        body: JSON.stringify({ commands: waypoints }),
      })
      setTelemetry((prev) => ({ ...prev, ...payload }))
      setSelectedMode('waypoint_by_command')
      pushEvent('system', 'Waypoint route submitted')
    } catch (error) {
      pushEvent('error', error.message)
    }
  }

  const handlePanChange = (value) => {
    const numeric = Number(value)
    setCameraPan(numeric)
    sendWsCommand('camera_pan', numeric)
  }

  const connectionLabel = {
    connected: 'Connected',
    connecting: 'Connecting',
    error: 'Connection error',
    disconnected: 'Disconnected',
  }[connectionState]

  return (
    <main className="page-shell">
      <section className="dashboard-shell">
        <header className="hero-bar">
          <div>
            <p className="eyebrow">Autonomous Rover Dashboard</p>
            <h1>Field Control Console</h1>
            <p className="hero-copy">
              Manual driving, obstacle avoidance, waypoint-by-command execution, telemetry, and camera feed in one place.
            </p>
          </div>
          <div className="hero-actions">
            <span className={`status-badge ${connectionState}`}>{connectionLabel}</span>
            <button className="stop-button" onClick={emergencyStop}>
              Emergency Stop
            </button>
          </div>
        </header>

        <section className="connection-row panel">
          <div className="field-group wide">
            <label htmlFor="backend-url">Backend URL</label>
            <input
              id="backend-url"
              value={backendUrl}
              onChange={(event) => setBackendUrl(event.target.value)}
              placeholder="http://raspberrypi.local:8000"
            />
            <small>WebSocket: {wsUrl || '—'}</small>
          </div>
          <div className="connection-buttons">
            <button className="primary" onClick={connectSocket}>
              Connect
            </button>
            <button className="secondary" onClick={disconnectSocket}>
              Disconnect
            </button>
            <button className="ghost" onClick={syncState}>
              Refresh State
            </button>
          </div>
        </section>

        <div className="dashboard-grid">
          <section className="left-column">
            <section className="panel mode-panel">
              <div className="panel-heading">
                <h2>Rover Mode</h2>
                <p>Switch between standby, manual control, obstacle avoidance, and waypoint execution.</p>
              </div>
              <div className="mode-grid">
                {[
                  ['idle', 'Idle'],
                  ['manual', 'Manual'],
                  ['obstacle_avoidance', 'Obstacle Avoidance'],
                  ['waypoint_by_command', 'Waypoint by Command'],
                ].map(([value, label]) => (
                  <button
                    key={value}
                    className={selectedMode === value ? 'mode-chip active' : 'mode-chip'}
                    onClick={() => setMode(value)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </section>

            <section className="panel autonomy-panel">
              <div className="panel-heading">
                <h2>Obstacle Avoidance</h2>
                <p>Continuous LiDAR-guided driving with safe turning decisions when the path closes.</p>
              </div>
              <div className="action-row">
                <button className="primary" onClick={startAutonomy}>
                  Start Avoidance
                </button>
                <button className="secondary" onClick={stopAutonomy}>
                  Stop Avoidance
                </button>
              </div>
            </section>

            <section className="panel waypoint-panel">
              <div className="panel-heading">
                <h2>Waypoint by Command</h2>
                <p>Enter one instruction per line using forward, backward, left, right, wait, and stop.</p>
              </div>
              <textarea
                value={waypoints}
                onChange={(event) => setWaypoints(event.target.value)}
                spellCheck={false}
                placeholder={`forward 10\nright 90\nforward 3\nwait 2\nstop`}
              />
              <div className="action-row">
                <button className="primary" onClick={submitWaypoints}>
                  Submit Route
                </button>
                <button className="secondary" onClick={() => setWaypoints(sampleRoute)}>
                  Load Sample
                </button>
                <button className="ghost" onClick={() => setWaypoints('')}>
                  Clear
                </button>
              </div>
            </section>

            <section className="panel manual-panel">
              <div className="panel-heading compact">
                <h2>Manual Debug Drive</h2>
                <p>Useful for quick checks while tuning steering and drivetrain behavior.</p>
              </div>
              <div className="manual-grid">
                {manualButtons.map((button) => (
                  <button
                    key={button.command}
                    className={button.danger ? 'manual-button danger' : 'manual-button'}
                    onClick={() => sendWsCommand(button.command)}
                  >
                    {button.label}
                  </button>
                ))}
              </div>
            </section>
          </section>

          <section className="right-column">
            <section className="panel telemetry-panel">
              <div className="panel-heading compact">
                <h2>Live Telemetry</h2>
                <p>Current mode, queue progress, obstacle distance, and hardware status.</p>
              </div>
              <div className="telemetry-grid">
                <TelemetryCard label="Mode" value={telemetry.mode} hint={telemetry.last_action} tone="purple" />
                <TelemetryCard
                  label="Obstacle"
                  value={telemetry.obstacle_distance != null ? `${telemetry.obstacle_distance} m` : '—'}
                  hint={telemetry.lidar_status}
                  tone="cyan"
                />
                <TelemetryCard label="Speed" value={`${telemetry.speed}`} hint={telemetry.drive_direction} tone="blue" />
                <TelemetryCard
                  label="Queue"
                  value={`${telemetry.completed_commands}/${telemetry.completed_commands + telemetry.remaining_commands}`}
                  hint={`remaining ${telemetry.remaining_commands}`}
                  tone="green"
                />
                <TelemetryCard label="Steering" value={`${telemetry.steering_angle}°`} hint="front wheels" tone="amber" />
                <TelemetryCard label="Battery" value={`${telemetry.battery_level}%`} hint={telemetry.camera_status} tone="red" />
              </div>
              <div className="status-strip">
                <div>
                  <span>Autonomy</span>
                  <strong>{telemetry.autonomy_enabled ? 'Active' : 'Off'}</strong>
                </div>
                <div>
                  <span>Waypoint Mode</span>
                  <strong>{telemetry.waypoint_mode_active ? 'Running' : 'Idle'}</strong>
                </div>
                <div>
                  <span>Current Command</span>
                  <strong>{telemetry.current_command || '—'}</strong>
                </div>
                <div>
                  <span>Error</span>
                  <strong>{telemetry.error || 'None'}</strong>
                </div>
              </div>
            </section>

            <section className="panel camera-panel">
              <div className="panel-heading compact">
                <h2>Camera Feed</h2>
                <p>MJPEG stream from the backend with adjustable pan servo.</p>
              </div>
              <div className="video-frame">
                <img src={videoUrl} alt="Rover camera stream" />
              </div>
              <label className="slider-label">
                Camera Pan <strong>{cameraPan}°</strong>
                <input
                  type="range"
                  min="30"
                  max="150"
                  value={cameraPan}
                  onChange={(event) => handlePanChange(event.target.value)}
                />
              </label>
            </section>

            <section className="panel event-panel">
              <div className="panel-heading compact">
                <h2>Status and Events</h2>
                <p>Backend actions, telemetry updates, and operator commands.</p>
              </div>
              <div className="event-list">
                {events.length === 0 ? <p className="empty-state">No events yet.</p> : null}
                {events.map((entry, index) => (
                  <div key={`${entry.time}-${index}`} className={`event-item ${entry.level}`}>
                    <span>{entry.time}</span>
                    <p>{entry.message}</p>
                  </div>
                ))}
              </div>
            </section>
          </section>
        </div>
      </section>
    </main>
  )
}
