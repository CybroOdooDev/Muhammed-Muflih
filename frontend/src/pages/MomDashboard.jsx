import { useEffect, useState } from 'react'
import * as XLSX from 'xlsx'

import api from '../api/client'

const WEEKDAYS    = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const MONTH_NAMES = ['January','February','March','April','May','June',
                     'July','August','September','October','November','December']

const CELL = {
  present: { label: '✓', cls: 'cell-full',  title: 'Attended' },
  absent:  { label: '✗', cls: 'cell-leave-full', title: 'Absent' },
}

const XLSX_LABEL = {
  present: 'Attended',
  absent:  'Absent',
}

function monthLabel(monthStr) {
  const [y, m] = monthStr.split('-').map(Number)
  return new Date(y, m - 1).toLocaleString('default', { month: 'long', year: 'numeric' })
}

function exportXlsx(data) {
  const [year, monthNum] = data.month.split('-').map(Number)
  const label    = monthLabel(data.month)
  const totalCols = data.day_meta.length + 1

  const titleRow  = [`MOM Dashboard - ${label}`, ...Array(totalCols - 1).fill('')]
  const blankRow  = Array(totalCols).fill('')
  const headerRow = [
    'Employee Name',
    ...data.day_meta.map((d) => {
      const wd = (new Date(year, monthNum - 1, d.day).getDay() + 6) % 7
      return `${d.day} ${WEEKDAYS[wd]}`
    }),
  ]
  const rows = data.employees.map((emp) => [
    emp,
    ...data.day_meta.map((d) => {
      const wd = (new Date(year, monthNum - 1, d.day).getDay() + 6) % 7
      if (wd === 6) return ''
      return XLSX_LABEL[data.data[emp]?.[d.day]] || ''
    }),
  ])

  const ws = XLSX.utils.aoa_to_sheet([titleRow, blankRow, headerRow, ...rows])
  ws['!merges'] = [{ s: { r: 0, c: 0 }, e: { r: 0, c: totalCols - 1 } }]
  ws['!cols']   = [{ wch: 24 }, ...data.day_meta.map(() => ({ wch: 14 }))]

  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, label)
  XLSX.writeFile(wb, `MOM_Dashboard_${data.month}.xlsx`)
}

function MonthTable({ data }) {
  const [year, monthNum] = data.month.split('-').map(Number)
  return (
    <div className="report-table-wrap">
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
                const val  = data.data[emp]?.[d.day] ?? null
                const cell = CELL[val]
                return (
                  <td
                    key={d.day}
                    className={d.weekend ? 'is-weekend' : ''}
                    title={cell?.title || (d.weekend ? 'Weekend' : 'No record')}
                  >
                    {cell ? (
                      <span className={`cell-badge ${cell.cls}`}>{cell.label}</span>
                    ) : d.weekend ? null : (
                      <span className="cell-badge cell-missing">–</span>
                    )}
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

export default function MomDashboard() {
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

  // Initial load — fetch current month only (fast)
  useEffect(() => {
    setLoading(true)
    setError('')
    api.get(`/gmail/mom/?month=${curKey}`)
      .then(r => {
        const entry = r.data
        setMonthMap({ [entry.month]: entry })
        setFetched(true)
      })
      .catch(e => {
        const msg = e.response?.data?.detail || e.message || ''
        setError(msg || 'Failed to load MOM data.')
      })
      .finally(() => setLoading(false))
  }, [])

  // On month switch — fetch on-demand if not already cached
  // monthMap intentionally omitted from deps — only fires on year/month change
  useEffect(() => {
    if (!fetched) return
    const key = `${year}-${String(month).padStart(2, '0')}`
    if (monthMap[key]) return
    setMonthLoading(true)
    api.get(`/gmail/mom/?month=${key}`)
      .then(r => { setMonthMap(prev => ({ ...prev, [r.data.month]: r.data })) })
      .catch(() => {})
      .finally(() => setMonthLoading(false))
  }, [year, month, fetched]) // eslint-disable-line react-hooks/exhaustive-deps

  const selKey      = `${year}-${String(month).padStart(2, '0')}`
  const current     = monthMap[selKey] || null
  const showSpinner = loading || monthLoading

  return (
    <div>

      {/* ── Page header ───────────────────────────────────────────────── */}
      <div className="d-flex justify-content-between align-items-start mb-4 gap-3 flex-wrap">
        <div>
          <h4 className="fw-bold mb-1">MOM Dashboard</h4>
          <p className="text-muted mb-0">Minutes of meeting records fetched from Gmail.</p>
        </div>

        {/* Month + Year picker — top right */}
        <div className="d-flex flex-column align-items-end gap-1">
          <label className="small text-muted mb-0" style={{ letterSpacing: '0.03em' }}>
            Select Month
          </label>
          <div className="d-flex align-items-center gap-1">

            {/* Year navigation */}
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

            {/* Month dropdown — all 12 months */}
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
                  const mk     = `${year}-${String(i + 1).padStart(2, '0')}`
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

      {/* ── Legend ────────────────────────────────────────────────────── */}
      <div className="d-flex gap-3 mb-4 flex-wrap">
        {[
          { cls: 'cell-full',       label: '✓', text: 'Attended' },
          { cls: 'cell-leave-full', label: '✗', text: 'Absent' },
          { cls: 'cell-missing',    label: '–', text: 'No record' },
        ].map((l) => (
          <span key={l.cls} className="small d-flex align-items-center gap-1">
            <span className={`cell-badge ${l.cls}`}>{l.label}</span> {l.text}
          </span>
        ))}
      </div>

      {/* ── Loading ───────────────────────────────────────────────────── */}
      {showSpinner && (
        <div
          className="d-flex justify-content-center align-items-center"
          style={{ minHeight: 320 }}
        >
          <div className="spinner-border" style={{ width: 48, height: 48 }} role="status">
            <span className="visually-hidden">Loading…</span>
          </div>
        </div>
      )}

      {/* ── Error ─────────────────────────────────────────────────────── */}
      {!showSpinner && error && <div className="alert alert-warning">{error}</div>}

      {/* ── No data at all ────────────────────────────────────────────── */}
      {!showSpinner && !error && Object.keys(monthMap).length === 0 && (
        <div className="text-center py-5">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="#adb5bd" viewBox="0 0 16 16" className="mb-3">
            <path d="M0 4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V4zm2-1a1 1 0 0 0-1 1v.217l7 4.2 7-4.2V4a1 1 0 0 0-1-1H2zm13 2.383-4.708 2.825L15 11.105V5.383zm-.034 6.876-5.64-3.471L8 9.583l-1.326-.795-5.64 3.47A1 1 0 0 0 2 13h12a1 1 0 0 0 .966-.741zM1 11.105l4.708-2.897L1 5.383v5.722z"/>
          </svg>
          <p className="text-muted mb-0">No MOM records found in Gmail.</p>
          <p className="text-muted small">Make sure MOM emails are in your inbox.</p>
        </div>
      )}

      {/* ── No data for selected month ────────────────────────────────── */}
      {!showSpinner && !error && Object.keys(monthMap).length > 0 && !current && (
        <div className="text-center py-5">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="#adb5bd" viewBox="0 0 16 16" className="mb-3">
            <path d="M14 1a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H4.414A2 2 0 0 0 3 11.586l-2 2V2a1 1 0 0 1 1-1h12zM2 0a2 2 0 0 0-2 2v12.793a.5.5 0 0 0 .854.353l2.853-2.853A1 1 0 0 1 4.414 12H14a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2z"/>
            <path d="M3 3.5a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zM3 6a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9A.5.5 0 0 1 3 6zm0 2.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5z"/>
          </svg>
          <p className="fw-semibold text-muted mb-1">No MOM records found for {monthLabel(selKey)}.</p>
          <p className="text-muted small mb-0">No MOM emails received in this month.</p>
        </div>
      )}

      {/* ── Month table ───────────────────────────────────────────────── */}
      {!showSpinner && current && current.employees.length === 0 && (
        <div className="text-center py-5">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" fill="#adb5bd" viewBox="0 0 16 16" className="mb-3">
            <path d="M14 1a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H4.414A2 2 0 0 0 3 11.586l-2 2V2a1 1 0 0 1 1-1h12zM2 0a2 2 0 0 0-2 2v12.793a.5.5 0 0 0 .854.353l2.853-2.853A1 1 0 0 1 4.414 12H14a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2z"/>
            <path d="M3 3.5a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zM3 6a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9A.5.5 0 0 1 3 6zm0 2.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5z"/>
          </svg>
          <p className="fw-semibold text-muted mb-1">No MOM records found for {monthLabel(selKey)}.</p>
          <p className="text-muted small mb-0">No MOM emails received in this month.</p>
        </div>
      )}

      {!showSpinner && current && current.employees.length > 0 && (
        <>
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h5 className="fw-semibold mb-0">
              {monthLabel(selKey)}
              <span className="badge bg-secondary ms-2 fw-normal fs-6">
                {current.employees.length} employee(s)
              </span>
            </h5>
            <button
              className="btn btn-sm btn-outline-success d-flex align-items-center gap-1"
              onClick={() => exportXlsx(current)}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                <path d="M14 4.5V11h-1V4.5h-2A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v9H2V2a2 2 0 0 1 2-2h5.5L14 4.5z"/>
                <path d="M3.627 11.6 2.01 16H.84l1.74-4.4H.734V10.6H3.63v1zm3.089.075c0-.44-.153-.718-.47-.835-.153-.06-.328-.09-.528-.09H5v3.6h.718v-1.47h.483c.457 0 .787-.12.99-.36.2-.24.3-.54.3-.9l.225.055zM5.718 12.7v-1.1h.24c.23 0 .394.05.487.15.094.1.14.25.14.447 0 .195-.046.344-.14.445-.093.1-.256.15-.487.15h-.24zm3.184.9h1.326v.75H8.184V10.6H9.9v.75H8.902v.998h.904v.75h-.904v.502z"/>
              </svg>
              Export XLSX
            </button>
          </div>

          <MonthTable data={current} />
        </>
      )}
    </div>
  )
}
