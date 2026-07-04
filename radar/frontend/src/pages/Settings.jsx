/**
 * Settings Page
 * Live config: detection thresholds, IP whitelist, input mode, AI provider.
 * Offline fallback: if API fails, shows defaults instead of hanging.
 */
import { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { useStore } from '../lib/store'

const DEFAULT_SETTINGS = {
  detection_thresholds: { general_sensitivity: 74, anomaly_detection: 88, lateral_movement: 42 },
  ip_whitelist: ['192.168.1.1', '10.0.0.55', '172.16.254.1'],
  input_mode: 'synthetic',
  ai_provider: 'gemini',
  monitoring_active: true,
}

function ThresholdSlider({ label, value, onChange }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="mono-label text-on-surface-variant">{label}</p>
        <span className="mono-data text-on-surface font-bold text-sm">{value}%</span>
      </div>
      <input
        type="range"
        min={0}
        max={100}
        value={value}
        onChange={e => onChange(parseInt(e.target.value))}
        className="w-full h-1.5 bg-surface-high rounded-full appearance-none cursor-pointer"
        style={{ accentColor: '#3b9eff' }}
      />
    </div>
  )
}

const INPUT_MODES = [
  { id: 'synthetic', label: 'Synthetic', icon: '⚙', desc: 'AI-generated events' },
  { id: 'upload', label: 'File Upload', icon: '📁', desc: 'JSON/NDJSON logs' },
  { id: 'stream', label: 'Live Stream', icon: '📡', desc: 'Filebeat HTTP' },
]

export default function Settings() {
  const { state, dispatch } = useStore()
  const [settings, setSettings] = useState(DEFAULT_SETTINGS)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [offline, setOffline] = useState(false)
  const [newIp, setNewIp] = useState('')

  useEffect(() => {
    api.settings.get()
      .then(data => { setSettings({ ...DEFAULT_SETTINGS, ...data }); setOffline(false) })
      .catch(() => { setOffline(true) })
  }, [])

  const set = (path, value) => {
    setSettings(prev => {
      const next = { ...prev }
      const keys = path.split('.')
      let obj = next
      for (let i = 0; i < keys.length - 1; i++) {
        obj[keys[i]] = { ...obj[keys[i]] }
        obj = obj[keys[i]]
      }
      obj[keys[keys.length - 1]] = value
      return next
    })
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.settings.update(settings)
      dispatch({ type: 'STATUS_UPDATE', payload: { input_mode: settings.input_mode } })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      console.error('Settings save failed:', e)
    } finally {
      setSaving(false)
    }
  }

  const addIp = () => {
    const ip = newIp.trim()
    if (!ip || settings.ip_whitelist.includes(ip)) return
    set('ip_whitelist', [...settings.ip_whitelist, ip])
    setNewIp('')
  }

  const removeIp = (ip) => {
    set('ip_whitelist', settings.ip_whitelist.filter(x => x !== ip))
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-headline-md text-primary font-semibold">System Settings</h1>
          <p className="text-on-surface-variant text-sm mt-1">Configure core detection parameters and platform integration.</p>
          {offline && (
            <div className="mt-2 px-3 py-2 rounded border border-warning/30 bg-warning/10 text-warning text-xs mono-data fade-in">
              ⚠ Backend offline — showing local defaults. Changes will save when backend reconnects.
            </div>
          )}
        </div>

        {/* Detection Thresholds */}
        <div className="card p-5 space-y-4">
          <div>
            <h2 className="font-semibold text-on-surface">Detection Thresholds</h2>
            <p className="text-on-surface-variant text-sm">Adjust sensitivity for automated threat detection.</p>
          </div>
          <ThresholdSlider
            label="GENERAL SENSITIVITY"
            value={settings.detection_thresholds.general_sensitivity}
            onChange={v => set('detection_thresholds.general_sensitivity', v)}
          />
          <ThresholdSlider
            label="ANOMALY DETECTION"
            value={settings.detection_thresholds.anomaly_detection}
            onChange={v => set('detection_thresholds.anomaly_detection', v)}
          />
          <ThresholdSlider
            label="LATERAL MOVEMENT"
            value={settings.detection_thresholds.lateral_movement}
            onChange={v => set('detection_thresholds.lateral_movement', v)}
          />
        </div>

        {/* IP Whitelist */}
        <div className="card p-5 space-y-4">
          <div>
            <h2 className="font-semibold text-on-surface">IP Whitelist</h2>
            <p className="text-on-surface-variant text-sm">Requests from these addresses will not trigger alerts.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {settings.ip_whitelist.map(ip => (
              <span
                key={ip}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded border border-outline/30 bg-surface-high mono-data text-xs text-on-surface"
              >
                {ip}
                <button
                  onClick={() => removeIp(ip)}
                  className="text-outline hover:text-critical transition-colors ml-0.5"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Enter IP address (e.g. 1.1.1.1)"
              value={newIp}
              onChange={e => setNewIp(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && addIp()}
              className="flex-1 bg-surface-lowest border border-outline/30 rounded px-3 py-2 mono-data text-sm text-on-surface placeholder-outline focus:outline-none focus:border-primary/50"
              id="ip-whitelist-input"
            />
            <button onClick={addIp} className="btn-primary text-xs" id="add-ip-btn">+ ADD IP</button>
          </div>
        </div>

        {/* Input Mode */}
        <div className="card p-5 space-y-4">
          <div>
            <h2 className="font-semibold text-on-surface">Input Mode</h2>
            <p className="text-on-surface-variant text-sm">Select the primary telemetry source.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {INPUT_MODES.map(mode => (
              <button
                key={mode.id}
                onClick={() => set('input_mode', mode.id)}
                className={`p-4 rounded-lg border flex flex-col items-center gap-2 transition-all ${
                  settings.input_mode === mode.id
                    ? 'bg-primary/15 border-primary/40 text-primary shadow-glow-sm'
                    : 'bg-surface-low border-outline/20 text-on-surface-variant hover:border-outline/40'
                }`}
                id={`mode-${mode.id}`}
              >
                {settings.input_mode === mode.id && (
                  <span className="self-end text-xs">✓</span>
                )}
                <span className="text-2xl">{mode.icon}</span>
                <span className="font-semibold text-sm">{mode.label}</span>
                <span className="text-xs opacity-70">{mode.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* AI Provider */}
        <div className="card p-5 space-y-4">
          <div>
            <h2 className="font-semibold text-on-surface">AI Provider</h2>
            <p className="text-on-surface-variant text-sm">Select the LLM for incident playbook generation.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {['gemini', 'claude'].map(provider => (
              <button
                key={provider}
                onClick={() => set('ai_provider', provider)}
                className={`py-2.5 px-4 rounded border font-semibold text-sm transition-all ${
                  settings.ai_provider === provider
                    ? 'bg-primary/20 border-primary/40 text-primary'
                    : 'bg-surface-low border-outline/20 text-on-surface-variant hover:border-outline/40'
                }`}
                id={`provider-${provider}`}
              >
                {provider === 'gemini' ? 'Gemini 2.0 Flash' : 'Claude'}
              </button>
            ))}
          </div>
        </div>

        {/* Connection Status */}
        <div className="card p-5">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-on-surface">Connection Status</h2>
              <div className="flex items-center gap-2 mt-1">
                <span className={`w-2 h-2 rounded-full pulse-dot ${state.wsConnected ? 'bg-secondary text-secondary' : 'bg-critical text-critical'}`} />
                <span className={`mono-label ${state.wsConnected ? 'text-secondary' : 'text-critical'}`}>
                  {state.wsConnected ? 'SYSTEM CONNECTED' : 'DISCONNECTED'}
                </span>
              </div>
              <p className="mono-data text-xs text-on-surface-variant mt-0.5">
                PRIMARY US-EAST-1 NODE ACTIVE · {state.wsClients} WS CLIENTS
              </p>
            </div>
            <svg className="w-10 h-10 text-on-surface-variant" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
              <rect x="2" y="2" width="8" height="8" rx="1"/><rect x="14" y="2" width="8" height="8" rx="1"/>
              <rect x="2" y="14" width="8" height="8" rx="1"/><rect x="14" y="14" width="8" height="8" rx="1"/>
              <line x1="10" y1="6" x2="14" y2="6"/><line x1="10" y1="18" x2="14" y2="18"/>
              <line x1="6" y1="10" x2="6" y2="14"/><line x1="18" y1="10" x2="18" y2="14"/>
            </svg>
          </div>
        </div>

        {/* Save button */}
        <button
          onClick={handleSave}
          disabled={saving}
          className={`w-full py-4 rounded border font-bold text-sm tracking-widest transition-all ${
            saved
              ? 'bg-secondary/20 border-secondary/40 text-secondary'
              : 'bg-primary/10 border-primary/30 text-on-surface hover:bg-primary/20 hover:border-primary/50'
          } disabled:opacity-50`}
          id="settings-save-btn"
        >
          {saving ? 'SAVING...' : saved ? '✓ SAVED' : 'SAVE CHANGES'}
        </button>
      </div>
    </div>
  )
}
