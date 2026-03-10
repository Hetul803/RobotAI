export default function TelemetryCard({ label, value, tone = 'blue' }) {
  return (
    <div className={`telemetry-card ${tone}`}>
      <p className="telemetry-label">{label}</p>
      <p className="telemetry-value">{value}</p>
    </div>
  )
}
