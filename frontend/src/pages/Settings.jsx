import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../api/client'

function OdooSettings() {
  const [status,  setStatus]  = useState(null)   // null = loading
  const [url,     setUrl]     = useState('')
  const [db,      setDb]      = useState('')
  const [login,   setLogin]   = useState('')
  const [apiKey,  setApiKey]  = useState('')
  const [saving,  setSaving]  = useState(false)
  const [error,   setError]   = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    api.get('/odoo/status/')
      .then(r => {
        setStatus(r.data)
        if (r.data.connected) {
          setUrl(r.data.url)
          setDb(r.data.db)
          setLogin(r.data.login)
        }
      })
      .catch(() => setStatus({ connected: false }))
  }, [])

  function connect(e) {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')
    api.post('/odoo/connect/', { url, db, login, api_key: apiKey })
      .then(() => {
        setStatus({ connected: true, url, db, login })
        setSuccess('Connected to Odoo successfully.')
        setApiKey('')
      })
      .catch(err => setError(err.response?.data?.detail || 'Connection failed.'))
      .finally(() => setSaving(false))
  }

  function disconnect() {
    api.delete('/odoo/status/')
      .then(() => {
        setStatus({ connected: false })
        setUrl('')
        setDb('')
        setLogin('')
        setApiKey('')
        setSuccess('')
        setError('')
      })
      .catch(() => {})
  }

  if (!status) return null

  return (
    <div className="card shadow-sm mt-4" style={{ maxWidth: 560 }}>
      <div className="card-body">
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h5 className="card-title mb-0">Odoo Connection</h5>
          {status.connected && (
            <span className="badge bg-success">Connected</span>
          )}
        </div>

        {status.connected && (
          <div className="mb-3 small text-muted">
            <div><span className="fw-semibold">URL:</span> {status.url}</div>
            <div><span className="fw-semibold">Database:</span> {status.db}</div>
            <div><span className="fw-semibold">Login:</span> {status.login}</div>
          </div>
        )}

        {error   && <div className="alert alert-warning py-2 small mb-3">{error}</div>}
        {success && <div className="alert alert-success py-2 small mb-3">{success}</div>}

        {!status.connected && (
          <form onSubmit={connect} className="d-flex flex-column gap-3">
            <div>
              <label className="form-label fw-semibold mb-1">Odoo URL</label>
              <input
                type="url"
                className="form-control"
                placeholder="https://mycompany.odoo.com"
                value={url}
                onChange={e => setUrl(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="form-label fw-semibold mb-1">Database Name</label>
              <input
                type="text"
                className="form-control"
                placeholder="mycompany_db"
                value={db}
                onChange={e => setDb(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="form-label fw-semibold mb-1">Login Email</label>
              <input
                type="email"
                className="form-control"
                placeholder="admin@mycompany.com"
                value={login}
                onChange={e => setLogin(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="form-label fw-semibold mb-1">API Key</label>
              <input
                type="password"
                className="form-control"
                placeholder="Enter Odoo API key"
                value={apiKey}
                onChange={e => setApiKey(e.target.value)}
                required
              />
              <div className="form-text">
                Generate an API key in Odoo → Settings → Technical → API Keys.
              </div>
            </div>
            <button className="btn btn-primary" type="submit" disabled={saving}>
              {saving
                ? <><span className="spinner-border spinner-border-sm me-2" />Connecting…</>
                : 'Connect'}
            </button>
          </form>
        )}

        {status.connected && (
          <button className="btn btn-outline-danger btn-sm" onClick={disconnect}>
            Disconnect
          </button>
        )}
      </div>
    </div>
  )
}

export default function Settings() {
  const { user } = useAuth()

  return (
    <div>
      <h4 className="fw-bold mb-1">Settings</h4>
      <p className="text-muted mb-4">Manage your account and preferences.</p>

      {/* Profile card */}
      <div className="card shadow-sm" style={{ maxWidth: 560 }}>
        <div className="card-body">
          <h5 className="card-title mb-3">Profile</h5>

          <div className="d-flex align-items-center gap-3 mb-3">
            {user?.picture && (
              <img
                src={user.picture}
                alt=""
                width="56"
                height="56"
                className="rounded-circle"
                referrerPolicy="no-referrer"
              />
            )}
            <div>
              <div className="fw-semibold fs-5">
                {user?.first_name} {user?.last_name}
              </div>
              <div className="text-muted">{user?.email}</div>
              <span className="badge bg-primary mt-1 text-capitalize">
                {user?.role}
              </span>
            </div>
          </div>

          <p className="text-muted small mb-0">
            Your name, email, and photo come from your Google account and
            cannot be edited here.
          </p>
        </div>
      </div>

      {/* Odoo connection card */}
      <OdooSettings />
    </div>
  )
}
