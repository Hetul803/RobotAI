export default function TelemetryCard({ label, value, hint, tone = 'blue' }) {
  return (
    <article className={`telemetry-card ${tone}`}>
      <p className="telemetry-label">{label}</p>
      <p className="telemetry-value">{value}</p>
      {hint ? <p className="telemetry-hint">{hint}</p> : null}
    </article>
  )
}
