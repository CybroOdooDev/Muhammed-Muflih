import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'

function todayStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function firstOfMonthStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`
}

function fmtHours(h) {
  return h ? `${h}h` : '0h'
}

function totalHours(entries) {
  return Math.round(entries.reduce((s, e) => s + (e.hours || 0), 0) * 100) / 100
}

export default function Comparison() {
  const [startDate,   setStartDate]   = useState(firstOfMonthStr)
  const [endDate,     setEndDate]     = useState(todayStr)
  const [gmailEmps,   setGmailEmps]   = useState([])
  const [odooEmps,    setOdooEmps]    = useState([])
  const [employee,    setEmployee]    = useState('')    // currently selected name
  const [loading,     setLoading]     = useState(false)
  const [initLoading, setInitLoading] = useState(true)
  const [entries,     setEntries]     = useState(null)
  const [error,       setError]       = useState('')
  const [fetchedFor,  setFetchedFor]  = useState(null) // {name, odooId, odooEmail, start, end}

  useEffect(() => {
    setInitLoading(true)
    Promise.all([
      api.get('/gmail/employees/').then(r => r.data.employees || []).catch(() => []),
      api.get('/odoo/employees2/').then(r => r.data.employees || []).catch(e => {
        const msg = e.response?.data?.detail || ''
        if (msg.toLowerCase().includes('connection 2')) setError(msg)
        return []
      }),
    ]).then(([gmail, odoo]) => {
      setGmailEmps(gmail)
      setOdooEmps(odoo)
      if (gmail.length) setEmployee(prev => prev || gmail[0])
    }).finally(() => setInitLoading(false))
  }, [])

  function resolveOdoo(name, odooList) {
    if (!name) return null
    const key = name.toLowerCase()
    return odooList.find(e => (e.work_email || '').split('@')[0].toLowerCase() === key) || null
  }

  function fetchComparison() {
    const selName  = employee
    const selStart = startDate
    const selEnd   = endDate
    const matched  = resolveOdoo(selName, odooEmps)

    // If a specific employee is selected but has no Odoo email match, stop here
    if (selName && !matched) {
      setEntries(null)
      setFetchedFor(null)
      setError(`Record Not Found!`)
      return
    }

    setLoading(true)
    setError('')
    setEntries(null)
    setFetchedFor(null)

    const params = { start: selStart, end: selEnd }
    if (selName && matched) params.employee_id = matched.id

    api.get('/odoo/timesheet2/', { params })
      .then(r => {
        setEntries(r.data.entries || [])
        setFetchedFor({
          name:      selName,
          odooId:    matched?.id   || null,
          odooEmail: matched?.work_email || null,
          odooName:  matched?.name || selName,
          start:     selStart,
          end:       selEnd,
        })
      })
      .catch(e => setError(e.response?.data?.detail || 'Failed to load.'))
      .finally(() => setLoading(false))
  }

  const notConnected = error.toLowerCase().includes('connection 2 not set up')
  const previewMatch = resolveOdoo(employee, odooEmps)

  return (
    <div className="d-flex flex-column align-items-center">
      <div className="mb-4">
        <h4 className="fw-bold mb-1">Comparison</h4>
        <p className="text-muted mb-0">
          Timesheet entries from Odoo Connection 2 — task, description and hours per day.
        </p>
      </div>

      {/* ── Not connected ────────────────────────────────────────────────── */}
      {notConnected && (
        <div className="alert alert-warning d-flex align-items-center gap-2 mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16">
            <path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767H13.9c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/>
          </svg>
          <span>
            Odoo Connection 2 is not set up.{' '}
            <Link to="/settings" className="alert-link">Go to Settings</Link> to connect.
          </span>
        </div>
      )}

      {/* ── Filters ─────────────────────────────────────────────────────── */}
      {!notConnected && (
        
        <div className="card shadow-sm mb-4" style={{ maxWidth: 600 }}>
          <div className="card-body d-flex flex-column gap-3">
            <div className="row g-3">
              <div className="col-6">
                <label className="form-label fw-semibold mb-1">From Date</label>
                <input type="date" className="form-control"
                  value={startDate} max={endDate}
                  onChange={e => setStartDate(e.target.value)} />
              </div>
              <div className="col-6">
                <label className="form-label fw-semibold mb-1">To Date</label>
                <input type="date" className="form-control"
                  value={endDate} min={startDate}
                  onChange={e => setEndDate(e.target.value)} />
              </div>
            </div>

            <div>
              <label className="form-label fw-semibold mb-1">Employee</label>
              {initLoading ? (
                <div className="text-muted small">Loading employees…</div>
              ) : (
                <>
                  <select className="form-select" value={employee}
                    onChange={e => setEmployee(e.target.value)}>
                    {gmailEmps.map(name => (
                      <option key={name} value={name}>
                        {name}{resolveOdoo(name, odooEmps) ? '' : ' ⚠'}
                      </option>
                    ))}
                  </select>
                  {employee && (
                    <div className="form-text mt-1">
                      {previewMatch
                        ? <span className="text-success">✓ Matched Odoo employee: {previewMatch.work_email}</span>
                        : <span className="text-warning">⚠ No Odoo match for "{employee.toLowerCase()}@…"</span>}
                    </div>
                  )}
                </>
              )}
            </div>

            <button className="btn w-100"
              style={{ backgroundColor: '#0d4f4f', color: 'white' }}
              onClick={fetchComparison}
              disabled={loading || !startDate || !endDate || initLoading}>
              {loading
                ? <><span className="spinner-border spinner-border-sm me-2" />Fetching…</>
                : 'Get Records'}
            </button>
          </div>
        </div>
      )}

      {/* ── Errors ──────────────────────────────────────────────────────── */}
      {error && !notConnected && (
        <div className="alert alert-warning mb-4">{error}</div>
      )}

      {/* ── Spinner ─────────────────────────────────────────────────────── */}
      {loading && (
        <div className="d-flex justify-content-center align-items-center" style={{ minHeight: 200 }}>
          <div className="spinner-border" style={{ width: 48, height: 48 }} role="status">
            <span className="visually-hidden">Loading…</span>
          </div>
        </div>
      )}

      {/* ── No data ─────────────────────────────────────────────────────── */}
      {!loading && entries && entries.length === 0 && (
        <div className="text-center py-5 text-muted">
          No timesheet entries found for the selected range.
        </div>
      )}

      {/* ── Results ─────────────────────────────────────────────────────── */}
      {!loading && entries && entries.length > 0 && fetchedFor && (
        <>
          <div className="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
            <h5 className="fw-semibold mb-0">
              {fetchedFor.name ? fetchedFor.odooName : 'All Employees'}
              <span className="badge bg-secondary ms-2 fw-normal" style={{ fontSize: '0.8rem' }}>
                {fetchedFor.start} → {fetchedFor.end}
              </span>
            </h5>
            <span className="fw-semibold" style={{ color: '#065f46' }}>
              Total: {fmtHours(totalHours(entries))}
            </span>
          </div>

          <div className="report-table-wrap">
            <table className="report-table">
              <thead>
                <tr>
                  <th style={{ minWidth: 100 }}>Date</th>
                  {!fetchedFor.odooId && <th style={{ minWidth: 140 }}>Employee</th>}
                  <th style={{ minWidth: 140 }}>Project</th>
                  <th style={{ minWidth: 160 }}>Task</th>
                  <th style={{ minWidth: 220, textAlign: 'left' }}>Description</th>
                  <th style={{ minWidth: 70 }}>Hours</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((e, i) => (
                  <tr key={i}>
                    <td>{e.date}</td>
                    {!fetchedFor.odooId && (
                      <td style={{ textAlign: 'left', fontWeight: 500 }}>{e.employee}</td>
                    )}
                    <td>{e.project || '–'}</td>
                    <td>{e.task || '–'}</td>
                    <td style={{ textAlign: 'left', maxWidth: 320, whiteSpace: 'normal' }}>
                      {e.description || <span className="text-muted">–</span>}
                    </td>
                    <td>
                      <span className={`cell-badge ${e.hours >= 8 ? 'cell-ts-full' : e.hours > 0 ? 'cell-ts-partial' : 'cell-missing'}`}>
                        {fmtHours(e.hours)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <td colSpan={fetchedFor.odooId ? 4 : 5}
                    style={{ textAlign: 'right', fontWeight: 600, paddingRight: '0.7rem' }}>
                    Total
                  </td>
                  <td>
                    <span className="cell-badge cell-ts-full">
                      {fmtHours(totalHours(entries))}
                    </span>
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </>

      )}
    </div>
  )
}
