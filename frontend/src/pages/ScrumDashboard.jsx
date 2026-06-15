import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'

const STATE_BADGE = {
  draft:      { label: 'Draft',       cls: 'bg-secondary' },
  open:       { label: 'In Progress', cls: 'bg-primary'   },
  close:      { label: 'Closed',      cls: 'bg-success'   },
  cancelled:  { label: 'Cancelled',   cls: 'bg-danger'    },
}

function fmt(dateStr) {
  if (!dateStr || dateStr === false) return '—'
  const d = new Date(dateStr)
  return isNaN(d) ? dateStr : d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function SprintCard({ sprint }) {
  const badge = STATE_BADGE[sprint.state] || { label: sprint.state, cls: 'bg-secondary' }
  return (
    <div className="card shadow-sm h-100">
      <div className="card-body">
        <div className="d-flex justify-content-between align-items-start gap-2 mb-2">
          <h6 className="fw-semibold mb-0">{sprint.name}</h6>
          <span className={`badge ${badge.cls} text-nowrap`}>{badge.label}</span>
        </div>
        <div className="text-muted small mb-2">
          {fmt(sprint.date_start)} → {fmt(sprint.date_stop)}
        </div>
        {sprint.description && sprint.description !== false && (
          <p className="small text-muted mb-0" style={{ whiteSpace: 'pre-line' }}>
            {sprint.description}
          </p>
        )}
      </div>
    </div>
  )
}

export default function ScrumDashboard() {
  const [sprints, setSprints] = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState('')
  const [notConnected, setNotConnected] = useState(false)

  useEffect(() => {
    api.get('/odoo/scrum/')
      .then(r => setSprints(r.data.sprints || []))
      .catch(err => {
        const detail = err.response?.data?.detail || ''
        if (detail === 'Odoo not connected.') {
          setNotConnected(true)
        } else {
          setError(detail || 'Failed to load sprints.')
        }
      })
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <div className="mb-4">
        <h4 className="fw-bold mb-1">Scrum Dashboard</h4>
        <p className="text-muted mb-0">Sprint overview from Odoo Scrum module.</p>
      </div>

      {loading && (
        <div className="text-muted small py-4 text-center">
          <span className="spinner-border spinner-border-sm me-2" />
          Loading sprints from Odoo…
        </div>
      )}

      {!loading && notConnected && (
        <div className="alert alert-warning d-flex align-items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
            <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
            <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z"/>
          </svg>
          <span>
            Odoo is not connected.{' '}
            <Link to="/settings" className="alert-link">Go to Settings</Link> to connect your Odoo instance.
          </span>
        </div>
      )}

      {!loading && error && (
        <div className="alert alert-danger">{error}</div>
      )}

      {!loading && !notConnected && !error && sprints.length === 0 && (
        <div className="text-center py-5 text-muted">
          <p className="mb-0 fw-semibold">No sprints found.</p>
          <p className="small mb-0">No sprint records exist in the Odoo Scrum module.</p>
        </div>
      )}

      {!loading && sprints.length > 0 && (
        <>
          <p className="text-muted small mb-3">{sprints.length} sprint(s) found</p>
          <div className="row g-3">
            {sprints.map(s => (
              <div key={s.id} className="col-12 col-md-6 col-xl-4">
                <SprintCard sprint={s} />
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
