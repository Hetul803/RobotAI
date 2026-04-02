import { useEffect, useMemo, useRef, useState } from 'react'
import TelemetryCard from './components/TelemetryCard'

const defaultBackendUrl = 'http://raspberrypi.local:8000'
const sampleRoute = ['forward 2', 'right 90', 'forward 1', 'wait 1', 'stop'].join('\n')
const targetSample = { x: 1.5, y: 2.5 }
const manualButtons = [
  { label: 'Forward', command: 'forward' },
  { label: 'Left', command: 'left' },
  { label: 'Stop', command: 'stop', danger: true },
  { label: 'Right', command: 'right' },
  { label: 'Back', command: 'backward' },
]

const emptyTelemetry = {
  mode: 'idle',
  autonomy_enabled: false,
  waypoint_mode_active: false,
  current_command: null,
  completed_commands: 0,
  remaining_commands: 0,
  obstacle_distance: null,
  steering_angle: 90,
  camera_pan_angle: 90,
  speed: 0,
  drive_direction: 'stopped',
  camera_status: 'unknown',
  lidar_status: 'unknown',
  motor_controller_status: 'unknown',
  steering_servo_status: 'unknown',
  camera_pan_servo_status: 'unknown',
  camera_health_status: 'unknown',
  lidar_health_status: 'unknown',
  backend_ready: false,
  battery_level: 0,
  last_action: 'waiting for connection',
  error: null,
}

function normalizeBaseUrl(url) {
  return url.trim().replace(/\/$/, '')
}

function deriveWsUrl(baseUrl, wsPath) {
  if (!baseUrl) return ''
  const safePath = wsPath.startsWith('/') ? wsPath : `/${wsPath}`
  return `${baseUrl.replace(/^http/i, 'ws')}${safePath}`
}

function nowLabel() {
  return new Date().toLocaleTimeString()
}

export default function App() {
  const [backendUrl, setBackendUrl] = useState(defaultBackendUrl)
  const [wsOverride, setWsOverride] = useState('')
  const [wsPath, setWsPath] = useState('/ws')
  const [videoPath, setVideoPath] = useState('/video')
  const [frontendHint, setFrontendHint] = useState('')
  const [connectionState, setConnectionState] = useState('disconnected')
  const [telemetry, setTelemetry] = useState(emptyTelemetry)
  const [events, setEvents] = useState([])
  const [selectedMode, setSelectedMode] = useState('idle')
  const [cameraPan, setCameraPan] = useState(90)
  const [cameraPanLimits, setCameraPanLimits] = useState({ min: 30, max: 150 })
  const [waypoints, setWaypoints] = useState(sampleRoute)
  const [targetModeEnabled, setTargetModeEnabled] = useState(false)
  const [targetX, setTargetX] = useState(targetSample.x)
  const [targetY, setTargetY] = useState(targetSample.y)
  const socketRef = useRef(null)
  const lastEventSignatureRef = useRef('')

  const baseUrl = useMemo(() => normalizeBaseUrl(backendUrl), [backendUrl])
  const derivedWsUrl = useMemo(() => deriveWsUrl(baseUrl, wsPath), [baseUrl, wsPath])
  const wsUrl = wsOverride.trim() || derivedWsUrl
  const videoUrl = useMemo(() => `${baseUrl}${videoPath.startsWith('/') ? videoPath : `/${videoPath}`}`, [baseUrl, videoPath])

  const pushEvent = (level, message) => {
    setEvents((prev) => [{ time: nowLabel(), level, message }, ...prev].slice(0, 60))
  }

  const disconnectSocket = () => {
    if (socketRef.current) {
      socketRef.current.close()
      socketRef.current = null
    }
    setConnectionState('disconnected')
  }

  const fetchJson = async (path, options = {}) => {
    const response = await fetch(`${baseUrl}${path}`, {
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
      const [snapshot, backendConfig, backendInfo] = await Promise.all([
        fetchJson('/state', { method: 'GET', headers: undefined }),
        fetchJson('/config', { method: 'GET', headers: undefined }),
        fetchJson('/info', { method: 'GET', headers: undefined }),
      ])
      setTelemetry((prev) => ({ ...prev, ...snapshot }))
      setSelectedMode(snapshot.mode || 'idle')
      setCameraPan(snapshot.camera_pan_angle ?? 90)
      if (backendConfig?.camera_pan?.min != null && backendConfig?.camera_pan?.max != null) {
        setCameraPanLimits({ min: backendConfig.camera_pan.min, max: backendConfig.camera_pan.max })
      }
      if (backendConfig?.ws_path) setWsPath(backendConfig.ws_path)
      if (backendConfig?.video_path) setVideoPath(backendConfig.video_path)
      if (backendConfig?.frontend_url_hint) setFrontendHint(backendConfig.frontend_url_hint)
      if (backendInfo?.urls?.ws_url && !wsOverride.trim()) {
        setWsOverride('')
      }
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
    if (!wsUrl) {
      pushEvent('error', 'Missing WebSocket URL')
      return
    }
    if (socketRef.current) return
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
  }

  const setMode = async (mode) => {
    try {
      const payload = await fetchJson('/mode', { method: 'POST', body: JSON.stringify({ mode }) })
      setTelemetry((prev) => ({ ...prev, ...payload }))
      setSelectedMode(mode)
      pushEvent('system', `Mode set to ${mode}`)
    } catch (error) {
      pushEvent('error', error.message)
    }
  }

  const startAutonomy = async () => {
    try {
      const payload = await fetchJson('/autonomy/start', { method: 'POST', body: '{}' })
      setTelemetry((prev) => ({ ...prev, ...payload }))
      setSelectedMode('obstacle_avoidance')
    } catch (error) {
      pushEvent('error', error.message)
    }
  }

  const stopAutonomy = async () => {
    try {
      const payload = await fetchJson('/autonomy/stop', { method: 'POST', body: '{}' })
      setTelemetry((prev) => ({ ...prev, ...payload }))
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
      pushEvent('system', 'Route submitted')
    } catch (error) {
      pushEvent('error', error.message)
    }
  }

  const applyTargetAsCommands = () => {
    const x = Number(targetX)
    const y = Number(targetY)
    if (!Number.isFinite(x) || !Number.isFinite(y)) {
      pushEvent('error', 'Target needs numeric X and Y')
      return
    }
    const distance = Math.sqrt(x * x + y * y)
    if (distance < 0.01) {
      setWaypoints('stop')
      return
    }
    const heading = (Math.atan2(x, y) * 180) / Math.PI
    const direction = heading >= 0 ? 'right' : 'left'
    const lines = []
    if (Math.abs(heading) >= 1) lines.push(`${direction} ${Math.abs(heading).toFixed(1)}`)
    lines.push(`forward ${distance.toFixed(2)}`)
    lines.push('stop')
    setWaypoints(lines.join('\n'))
  }

  const connectionLabel = {
    connected: 'Connected',
    connecting: 'Connecting',
    error: 'Error',
    disconnected: 'Disconnected',
  }[connectionState]

  return (
    <main className="page-shell">
      <section className="dashboard-shell">
        <header className="hero-bar panel">
          <div>
            <p className="eyebrow">Rover Console</p>
            <h1>Pi Control Dashboard</h1>
            <p className="hero-copy">Connect to the Raspberry Pi backend, monitor status, and run local autonomy modes.</p>
          </div>
          <div className="hero-actions">
            <span className={`status-badge ${connectionState}`}>{connectionLabel}</span>
            <button className="stop-button" onClick={emergencyStop}>
              Emergency Stop
            </button>
          </div>
        </header>

        <section className="panel connection-row">
          <div className="field-group">
            <label htmlFor="backend-url">Backend HTTP URL</label>
            <input id="backend-url" value={backendUrl} onChange={(event) => setBackendUrl(event.target.value)} placeholder="http://192.168.1.54:8000" />
            <small>Derived WS URL: {derivedWsUrl || '—'}</small>
            <small>Video URL: {videoUrl || '—'}</small>
            {frontendHint ? <small>Frontend hint: {frontendHint}</small> : null}
          </div>
          <div className="field-group">
            <label htmlFor="ws-url">WebSocket URL (optional override)</label>
            <input id="ws-url" value={wsOverride} onChange={(event) => setWsOverride(event.target.value)} placeholder="ws://192.168.1.54:8000/ws" />
            <small>Active socket URL: {wsUrl || '—'}</small>
          </div>
          <div className="connection-buttons">
            <button className="primary" onClick={connectSocket}>Connect WS</button>
            <button className="secondary" onClick={disconnectSocket}>Disconnect</button>
            <button className="ghost" onClick={syncState}>Refresh</button>
          </div>
        </section>

        <div className="dashboard-grid">
          <section className="left-column">
            <section className="panel camera-panel">
              <div className="panel-heading compact">
                <h2>Camera</h2>
                <p>Live video stream from the backend.</p>
              </div>
              <div className="video-frame">
                <img src={videoUrl} alt="Rover camera stream" />
              </div>
              <label className="slider-label">
                Camera pan <strong>{cameraPan}°</strong>
                <input
                  type="range"
                  min={cameraPanLimits.min}
                  max={cameraPanLimits.max}
                  value={cameraPan}
                  onChange={(event) => {
                    const numeric = Number(event.target.value)
                    setCameraPan(numeric)
                    sendWsCommand('camera_pan', numeric)
                  }}
                />
              </label>
            </section>

            <section className="panel mode-panel">
              <div className="panel-heading">
                <h2>Mode</h2>
                <p>Idle, manual, obstacle avoidance, or waypoint-by-command.</p>
              </div>
              <div className="mode-grid">
                {[
                  ['idle', 'Idle'],
                  ['manual', 'Manual'],
                  ['obstacle_avoidance', 'Obstacle Avoidance'],
                  ['waypoint_by_command', 'Waypoint by Command'],
                ].map(([value, label]) => (
                  <button key={value} className={selectedMode === value ? 'mode-chip active' : 'mode-chip'} onClick={() => setMode(value)}>
                    {label}
                  </button>
                ))}
              </div>
              <div className="action-row">
                <button className="primary" onClick={startAutonomy}>Start Avoidance</button>
                <button className="secondary" onClick={stopAutonomy}>Stop Avoidance</button>
              </div>
            </section>

            <section className="panel waypoint-panel">
              <div className="panel-heading">
                <h2>Waypoint by Command</h2>
                <p>One command per line: forward/backward/left/right/wait/stop.</p>
              </div>
              <textarea value={waypoints} onChange={(event) => setWaypoints(event.target.value)} spellCheck={false} />
              <div className="action-row">
                <button className="primary" onClick={submitWaypoints}>Submit Route</button>
                <button className="secondary" onClick={() => setWaypoints(sampleRoute)}>Sample</button>
                <button className="ghost" onClick={() => setWaypoints('')}>Clear</button>
                <button className="ghost" onClick={() => setTargetModeEnabled((value) => !value)}>
                  {targetModeEnabled ? 'Hide Target Mode' : 'Target Mode'}
                </button>
              </div>
              {targetModeEnabled ? (
                <div className="target-mode">
                  <p>Convert a local target into a simple estimated route.</p>
                  <div className="target-grid">
                    <label>Target X (right +)
                      <input type="number" value={targetX} step="0.1" onChange={(event) => setTargetX(event.target.value)} />
                    </label>
                    <label>Target Y (forward +)
                      <input type="number" value={targetY} step="0.1" onChange={(event) => setTargetY(event.target.value)} />
                    </label>
                  </div>
                  <button className="primary" onClick={applyTargetAsCommands}>Convert to Route</button>
                </div>
              ) : null}
            </section>
          </section>

          <section className="right-column">
            <section className="panel telemetry-panel">
              <div className="panel-heading compact">
                <h2>Telemetry</h2>
                <p>Current movement, command queue, and component status.</p>
              </div>
              <div className="telemetry-grid">
                <TelemetryCard label="Mode" value={telemetry.mode} hint={telemetry.last_action} tone="purple" />
                <TelemetryCard label="Obstacle" value={telemetry.obstacle_distance != null ? `${telemetry.obstacle_distance} m` : '—'} hint={telemetry.lidar_status} tone="cyan" />
                <TelemetryCard label="Speed" value={`${telemetry.speed}`} hint={telemetry.drive_direction} tone="blue" />
                <TelemetryCard label="Queue" value={`${telemetry.completed_commands}/${telemetry.completed_commands + telemetry.remaining_commands}`} hint={`remaining ${telemetry.remaining_commands}`} tone="green" />
                <TelemetryCard label="Steering" value={`${telemetry.steering_angle}°`} hint="front servo" tone="amber" />
                <TelemetryCard label="Backend" value={telemetry.backend_ready ? 'Ready' : 'Check'} hint={telemetry.error || 'no active error'} tone="red" />
              </div>
              <div className="status-strip hardware-strip">
                <div><span>Motor</span><strong>{telemetry.motor_controller_status}</strong></div>
                <div><span>Steering</span><strong>{telemetry.steering_servo_status}</strong></div>
                <div><span>Cam Pan</span><strong>{telemetry.camera_pan_servo_status}</strong></div>
                <div><span>LiDAR</span><strong>{telemetry.lidar_health_status}</strong></div>
                <div><span>Camera</span><strong>{telemetry.camera_health_status}</strong></div>
              </div>
            </section>

            <section className="panel event-panel">
              <div className="panel-heading compact">
                <h2>Events</h2>
                <p>Recent operator and backend messages.</p>
              </div>
              <div className="event-list compact">
                {events.length === 0 ? <p className="empty-state">No events yet.</p> : null}
                {events.map((entry, index) => (
                  <div key={`${entry.time}-${index}`} className={`event-item ${entry.level}`}>
                    <span>{entry.time}</span>
                    <p>{entry.message}</p>
                  </div>
                ))}
              </div>
            </section>

            <details className="panel manual-panel">
              <summary>Manual debug controls</summary>
              <div className="manual-grid">
                {manualButtons.map((button) => (
                  <button key={button.command} className={button.danger ? 'manual-button danger' : 'manual-button'} onClick={() => sendWsCommand(button.command)}>
                    {button.label}
                  </button>
                ))}
              </div>
            </details>
          </section>
        </div>
      </section>
    </main>
  )
}
