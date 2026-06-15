import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import api from '../api/client'

const WEEKDAYS    = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const MONTH_NAMES = ['January','February','March','April','May','June',
                     'July','August','September','October','November','December']

function isFriday(year, monthNum, day) {
  return new Date(year, monthNum - 1, day).getDay() === 5
}

function monthLabel(monthStr) {
  const [y, m] = monthStr.split('-').map(Number)
  return new Date(y, m - 1).toLocaleString('default', { month: 'long', year: 'numeric' })
}

function DayCell({ row, friday }) {
  const wr        = row?.work_report   ?? false
  const ts        = row?.timesheet     ?? false
  const wk        = row?.weekly_report ?? false
  const commit    = row?.commit_id     || ''
  const hasCommit = !!commit

  // Green ✓  = WR + TS + commit  (all days except Friday)
  // Teal  ✓  = WR + TS + WK + commit  (Friday only)
  const allDone = friday ? (wr && ts && wk && hasCommit) : (wr && ts && hasCommit)

  if (allDone) {
    const cls   = friday ? 'cell-friday-all' : 'cell-full'
    const title = friday
      ? 'WR + TS + Weekly + Commit all submitted'
      : 'WR + TS + Commit all submitted'
    return commit.startsWith('http')
      ? <a href={commit} target="_blank" rel="noopener noreferrer"
           className={`cell-badge ${cls}`} title={title}
           onClick={e => e.stopPropagation()}>✓</a>
      : <span className={`cell-badge ${cls}`} title={title}>✓</span>
  }

  // No record at all
  if (!wr && !ts && (!friday || !wk) && !hasCommit) {
    return <span className="cell-badge cell-missing">–</span>
  }

  // Non-Friday (Mon–Thu, Sat) partial → single red mark
  if (!friday) {
    return <span className="cell-badge cell-danger" title="One or more items not submitted">✗</span>
  }

  // Friday partial → show which items are missing
  return (
    <div className="d-flex flex-wrap gap-1 justify-content-center">
      {!wr        && <span className="cell-badge cell-warn" title="Work Report not submitted">WR</span>}
      {!ts        && <span className="cell-badge cell-warn" title="Timesheet not submitted">TS</span>}
      {!wk        && <span className="cell-badge cell-warn" title="Weekly Report not submitted">WK</span>}
      {!hasCommit && <span className="cell-badge cell-warn" title="Commit link not submitted">GIT</span>}
    </div>
  )
}

function MonthTable({ data }) {
  const [year, monthNum] = data.month.split('-').map(Number)
  return (
    <div className="report-table-wrap daily-table-wrap">
      <table className="report-table">
        <thead>
          <tr>
            <th className="emp-col">Employee Name</th>
            {data.day_meta.map((d) => {
              const wd = (new Date(year, monthNum - 1, d.day).getDay() + 6) % 7
              return (
                <th key={d.day} className={d.weekend ? 'is-weekend' : ''}>
                  {d.day}<small>{WEEKDAYS[wd]}</small>
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {data.employees.map((emp) => (
            <tr key={emp}>
              <td className="emp-col">{emp}</td>
              {data.day_meta.map((d) => {
                const row    = data.data[emp]?.[d.day] ?? null
                const friday = isFriday(year, monthNum, d.day)
                return (
                  <td
                    key={d.day}
                    className={d.weekend ? 'is-weekend' : ''}
                  >
                    <DayCell row={row} friday={friday} />
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function OdooDailyDashboard() {
  const today    = new Date()
  const curYear  = today.getFullYear()
  const curMonth = today.getMonth() + 1
  const curKey   = `${curYear}-${String(curMonth).padStart(2, '0')}`

  const [monthMap,     setMonthMap]     = useState({})
  const [loading,      setLoading]      = useState(true)
  const [monthLoading, setMonthLoading] = useState(false)
  const [fetched,      setFetched]      = useState(false)
  const [error,        setError]        = useState('')
  const [year,         setYear]         = useState(curYear)
  const [month,        setMonth]        = useState(curMonth)

  // Tracks keys that the background loop has already queued — prevents duplicate bg requests
  const bgQueued = useRef(new Set())

  // Initial load — current month
  useEffect(() => {
    setLoading(true)
    setError('')
    api.get(`/odoo/daily-tasks/?month=${curKey}`)
      .then(r => {
        setMonthMap({ [r.data.month]: r.data })
        setFetched(true)
      })
      .catch(e => {
        const msg = e.response?.data?.detail || e.message || ''
        setError(msg || 'Failed to load daily task data.')
      })
      .finally(() => setLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Background pre-fetch — after current month loads, silently fetch the past 12 months
  useEffect(() => {
    if (!fetched) return
    let active = true

    // Build ordered list: most-recent month first, going back 12 months
    const queue = []
    let yr = curYear, mo = curMonth - 1
    for (let i = 0; i < 12; i++) {
      if (mo === 0) { mo = 12; yr-- }
      const key = `${yr}-${String(mo).padStart(2, '0')}`
      if (!bgQueued.current.has(key)) {
        bgQueued.current.add(key)
        queue.push(key)
      }
      mo--
    }

    ;(async () => {
      for (const key of queue) {
        if (!active) break
        try {
          const r = await api.get(`/odoo/daily-tasks/?month=${key}`)
          if (active) setMonthMap(prev => ({ ...prev, [r.data.month]: r.data }))
        } catch { /* silently skip months with no data or errors */ }
        // small gap between requests so we don't flood the server
        if (active) await new Promise(res => setTimeout(res, 300))
      }
    })()

    return () => { active = false }
  }, [fetched]) // eslint-disable-line react-hooks/exhaustive-deps

  // On month switch — fetch on-demand (with spinner) if not already in cache
  useEffect(() => {
    if (!fetched) return
    const key = `${year}-${String(month).padStart(2, '0')}`
    if (monthMap[key]) return
    setMonthLoading(true)
    setError('')
    api.get(`/odoo/daily-tasks/?month=${key}`)
      .then(r => { setMonthMap(prev => ({ ...prev, [r.data.month]: r.data })) })
      .catch(e => {
        const msg = e.response?.data?.detail || e.message || ''
        setError(msg || 'Failed to load daily task data.')
      })
      .finally(() => setMonthLoading(false))
  }, [year, month, fetched]) // eslint-disable-line react-hooks/exhaustive-deps

  const selKey       = `${year}-${String(month).padStart(2, '0')}`
  const current      = monthMap[selKey] || null
  const showSpinner  = loading || monthLoading
  const notConnected = error.toLowerCase().includes('not connected')

  return (
    <div>

      {/* ── Page header ─────────────────────────────────────────────────── */}
      <div className="d-flex justify-content-between align-items-start mb-4 gap-3 flex-wrap">
        <div>
          <h4 className="fw-bold mb-1">Daily Tasks</h4>
          <p className="text-muted mb-0">Employee daily task completion from Odoo Scrum.</p>
        </div>

        {/* Month + Year picker */}
        <div className="d-flex flex-column align-items-end gap-1">
          <label className="small text-muted mb-0" style={{ letterSpacing: '0.03em' }}>
            Select Month
          </label>
          <div className="d-flex align-items-center gap-1">

            <button
              className="btn btn-sm btn-outline-secondary"
              onClick={() => setYear(y => y - 1)}
              title="Previous year"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                <path fillRule="evenodd" d="M11.354 1.646a.5.5 0 0 1 0 .708L5.707 8l5.647 5.646a.5.5 0 0 1-.708.708l-6-6a.5.5 0 0 1 0-.708l6-6a.5.5 0 0 1 .708 0z"/>
              </svg>
            </button>
            <span className="fw-semibold px-1" style={{ minWidth: 42, textAlign: 'center' }}>{year}</span>
            <button
              className="btn btn-sm btn-outline-secondary"
              onClick={() => setYear(y => y + 1)}
              disabled={year >= today.getFullYear()}
              title="Next year"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                <path fillRule="evenodd" d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"/>
              </svg>
            </button>

            <div className="input-group ms-1" style={{ width: 170 }}>
              <span className="input-group-text bg-white py-1">
                <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M3.5 0a.5.5 0 0 1 .5.5V1h8V.5a.5.5 0 0 1 1 0V1h1a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2h1V.5a.5.5 0 0 1 .5-.5zM1 4v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V4H1z"/>
                </svg>
              </span>
              <select
                className="form-select form-select-sm fw-semibold"
                value={month}
                onChange={(e) => setMonth(Number(e.target.value))}
                disabled={showSpinner}
              >
                {MONTH_NAMES.map((name, i) => {
                  const mk      = `${year}-${String(i + 1).padStart(2, '0')}`
                  const hasData = !!(monthMap[mk]?.employees?.length)
                  return (
                    <option key={i + 1} value={i + 1}>
                      {name}{hasData ? ' ●' : ''}
                    </option>
                  )
                })}
              </select>
            </div>

          </div>
        </div>
      </div>

      {/* ── Legend ──────────────────────────────────────────────────────── */}
      <div className="d-flex gap-3 mb-4 flex-wrap">
        {[
          { cls: 'cell-full',       label: '✓',            text: 'WR + TS + Commit done (Mon–Sat)' },
          { cls: 'cell-friday-all', label: '✓',            text: 'WR + TS + Weekly + Commit done (Friday)' },
          { cls: 'cell-danger',     label: '✗',            text: 'Missing item(s) — Mon–Sat' },
          { cls: 'cell-warn',       label: 'WR/TS/WK/GIT', text: 'Missing item(s) — Friday' },
          { cls: 'cell-missing',    label: '–',            text: 'No record' },
        ].map((l, i) => (
          <span key={i} className="small d-flex align-items-center gap-1">
            <span className={`cell-badge ${l.cls}`}>{l.label}</span> {l.text}
          </span>
        ))}
      </div>

      {/* ── Loading ─────────────────────────────────────────────────────── */}
      {showSpinner && (
        <div className="d-flex justify-content-center align-items-center" style={{ minHeight: 320 }}>
          <div className="spinner-border" style={{ width: 48, height: 48 }} role="status">
            <span className="visually-hidden">Loading…</span>
          </div>
        </div>
      )}

      {/* ── Odoo not connected ──────────────────────────────────────────── */}
      {!showSpinner && notConnected && (
        <div className="alert alert-warning d-flex align-items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16">
            <path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/>
          </svg>
          <span>
            Odoo is not connected.{' '}
            <Link to="/settings" className="alert-link">Go to Settings</Link> to connect.
          </span>
        </div>
      )}

      {/* ── Other errors ────────────────────────────────────────────────── */}
      {!showSpinner && error && !notConnected && (
        <div className="alert alert-warning">{error}</div>
      )}

      {/* ── No data at all ──────────────────────────────────────────────── */}
      {!showSpinner && !error && Object.keys(monthMap).length === 0 && (
        <div className="text-center py-5">
          <p className="text-muted mb-0">No daily task records found.</p>
        </div>
      )}

      {/* ── No data for selected month ───────────────────────────────────── */}
      {!showSpinner && !error && Object.keys(monthMap).length > 0 && !current && (
        <div className="text-center py-5">
          <p className="fw-semibold text-muted mb-1">No daily tasks for {monthLabel(selKey)}.</p>
          <p className="text-muted small mb-0">No records in Odoo for this month.</p>
        </div>
      )}

      {/* ── Month fetched but no employees ───────────────────────────── */}
      {!showSpinner && current && current.employees.length === 0 && (
        <div className="text-center py-5">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="#adb5bd" viewBox="0 0 16 16" className="mb-3">
            <path d="M14 1a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H4.414A2 2 0 0 0 3 11.586l-2 2V2a1 1 0 0 1 1-1h12zM2 0a2 2 0 0 0-2 2v12.793a.5.5 0 0 0 .854.353l2.853-2.853A1 1 0 0 1 4.414 12H14a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2z"/>
            <path d="M3 3.5a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zM3 6a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9A.5.5 0 0 1 3 6zm0 2.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5z"/>
          </svg>
          <p className="fw-semibold text-muted mb-1">No daily tasks found for {monthLabel(selKey)}.</p>
          <p className="text-muted small mb-0">No records in Odoo for this month.</p>
        </div>
      )}

      {/* ── Month table ─────────────────────────────────────────────────── */}
      {!showSpinner && current && current.employees.length > 0 && (
        <>
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h5 className="fw-semibold mb-0">
              {monthLabel(selKey)}
              <span className="badge bg-secondary ms-2 fw-normal fs-6">
                {current.employees.length} employee(s)
              </span>
            </h5>
          </div>
          <MonthTable data={current} />
        </>
      )}

    </div>
  )
}
