import { useEffect, useState } from 'react'
import api from '../api/client'

function todayStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function firstOfMonthStr() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`
}

export default function WorkDayCount() {
  const [startDate, setStartDate] = useState(firstOfMonthStr)
  const [endDate,   setEndDate]   = useState(todayStr)
  const [project,   setProject]   = useState('')
  const [employee,  setEmployee]  = useState('')

  // Project list loaded from the Projects page via API on mount (no "All")
  const [projects,   setProjects]  = useState([])
  // Employee list loaded from current month's emails on mount (no "All")
  const [employees,  setEmployees] = useState([])

  const [rows,         setRows]        = useState([])
  const [loading,      setLoading]     = useState(false)
  const [loadingProj,  setLoadingProj] = useState(true)
  const [error,        setError]       = useState('')
  const [fetched,      setFetched]     = useState(false)
  const [emailsFound,  setEmailsFound]  = useState(null)
  const [emailsParsed, setEmailsParsed] = useState(null)
  // snapshot of filter values at the time the last Analyse was run
  const [lastQuery,    setLastQuery]   = useState(null)

  // clear stale results whenever any filter changes
  useEffect(() => {
    setFetched(false)
    setRows([])
    setEmailsFound(null)
    setEmailsParsed(null)
    setLastQuery(null)
  }, [startDate, endDate, project, employee])

  // ── load projects and employees on mount ────────────────────────────────
  useEffect(() => {
    // Projects — from the Projects page (no "All" option)
    api.get('/gmail/projects/')
      .then(r => {
        const names = r.data.map(p => p.name)
        setProjects(names)
        if (names.length) setProject(names[0])
      })
      .catch(() => {})
      .finally(() => setLoadingProj(false))

    // Employees — from all work-report emails (no date restriction)
    api.get('/gmail/employees/')
      .then(r => {
        if (r.data.employees?.length) {
          setEmployees(r.data.employees)
          setEmployee(r.data.employees[0])
        }
      })
      .catch(() => {})
  }, [])

  // ── analyse ──────────────────────────────────────────────────────────────
  function analyse() {
    if (!startDate || !endDate) return
    setLoading(true)
    setError('')
    const params = new URLSearchParams({
      start:    startDate,
      end:      endDate,
      project:  project,
      employee: employee,
    })
    api.get(`/gmail/workday-count/?${params}`)
      .then(r => {
        setRows(r.data.rows)
        setEmailsFound(r.data.emails_found  ?? null)
        setEmailsParsed(r.data.emails_parsed ?? null)
        setLastQuery({ project, employee, start: startDate, end: endDate })
        setFetched(true)
      })
      .catch(e => {
        const msg = e.response?.data?.detail || ''
        setError(
          msg === 'Gmail not connected.'
            ? 'Gmail not connected. Sign out and sign in again to reconnect.'
            : msg || 'Failed to load data.',
        )
      })
      .finally(() => setLoading(false))
  }

  return (
    <div className="container py-4">
      <div className="d-flex flex-column align-items-center">

        <h4 className="fw-bold mb-1">Work Day Count</h4>
        <p className="text-muted mb-4 text-center">
          Analyse employee working days by project and date range.
        </p>

        {/* ── Filter card ────────────────────────────────────────────────── */}
        <div className="card shadow-sm mb-4 w-100" style={{ maxWidth: 520 }}>
          <div className="card-body d-flex flex-column gap-3">

            {/* Project */}
            <div>
              <label className="form-label fw-semibold mb-1">Project</label>
              {loadingProj ? (
                <div className="form-text">
                  <span className="spinner-border spinner-border-sm me-1" style={{ width: 10, height: 10 }} />
                  Loading projects…
                </div>
              ) : projects.length === 0 ? (
                <div className="alert alert-warning py-2 small mb-0">
                  No projects added yet.{' '}
                  <a href="/projects" className="alert-link">Go to Projects page</a> to add one.
                </div>
              ) : (
                <select
                  className="form-select"
                  value={project}
                  onChange={e => { setProject(e.target.value); setEmployee('') }}
                >
                  <option value="" disabled>Select a project…</option>
                  {projects.map(p => <option key={p} value={p}>{p}</option>)}
                </select>
              )}
            </div>

            {/* Employee */}
            <div>
              <label className="form-label fw-semibold mb-1">Employee</label>
              <select
                className="form-select"
                value={employee}
                onChange={e => setEmployee(e.target.value)}
              >
                {employees.map(e => <option key={e} value={e}>{e}</option>)}
              </select>
            </div>

            {/* Start Date */}
            <div>
              <label className="form-label fw-semibold mb-1">Start Date</label>
              <input
                type="date"
                className="form-control"
                value={startDate}
                max={endDate}
                onChange={e => setStartDate(e.target.value)}
              />
            </div>

            {/* End Date */}
            <div>
              <label className="form-label fw-semibold mb-1">End Date</label>
              <input
                type="date"
                className="form-control"
                value={endDate}
                min={startDate}
                onChange={e => setEndDate(e.target.value)}
              />
            </div>

            <button
              className="btn" style={{backgroundColor:'#0d4f4f',color:'white'}}
              onClick={analyse}
              disabled={loading || !startDate || !endDate || !project}
            >
              {loading ? (
                <><span className="spinner-border spinner-border-sm me-2" />Analysing…</>
              ) : 'Analyse'}
            </button>
          </div>
        </div>

        {error && (
          <div className="alert alert-warning w-100" style={{ maxWidth: 900 }}>
            {error}
          </div>
        )}

        {/* ── Results ────────────────────────────────────────────────────── */}
        {fetched && !loading && (
          <>
            {emailsFound !== null && (
              <p className="text-muted small mb-2 w-100" style={{ maxWidth: 900 }}>
                {emailsFound === 0
                  ? 'No emails found in Gmail for this date range.'
                  : emailsParsed === 0
                    ? `${emailsFound} email(s) found but none matched the work-report subject format.`
                    : `${emailsFound} email(s) found · ${emailsParsed} work report(s) parsed.`}
              </p>
            )}

            {rows.length === 0 ? (
              <div className="alert alert-info w-100" style={{ maxWidth: 900 }}>
                No work reports found for{lastQuery?.project ? ` project "${lastQuery.project}"` : ''} in the selected date range.
              </div>
            ) : (
              <div className="card shadow-sm w-100" style={{ maxWidth: 900 }}>
                <div className="card-header fw-semibold bg-white py-2 d-flex align-items-center gap-2 flex-wrap">
                  Results
                  {lastQuery?.project  && <span className="badge bg-primary">{lastQuery.project}</span>}
                  {lastQuery?.employee && <span className="badge bg-secondary">{lastQuery.employee}</span>}
                  <span className="text-muted fw-normal small ms-auto">
                    {lastQuery?.start} → {lastQuery?.end}
                  </span>
                </div>

                <div className="card-body p-0">
                  <table className="table table-hover mb-0">
                    <thead className="table-light">
                      <tr>
                        <th style={{ width: 48 }}>#</th>
                        <th>Employee Name</th>
                        <th className="text-center" style={{ width: 140 }}>Work Reports</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((r, i) => (
                        <tr key={r.employee}>
                          <td className="text-muted">{i + 1}</td>
                          <td>{r.employee}</td>
                          <td className="text-center">
                            <span className="badge bg-success fs-6 px-3">{r.count}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="table-light">
                      <tr>
                        <td colSpan={2} className="fw-semibold text-end">Total employees</td>
                        <td className="text-center fw-semibold">{rows.length}</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            )}
          </>
        )}

      </div>
    </div>
  )
}
