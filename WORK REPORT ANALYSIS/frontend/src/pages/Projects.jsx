import { useEffect, useState } from 'react'
import api from '../api/client'

const EMPTY_FORM = { name: '', emails: [''] }

export default function Projects() {
  const [projects, setProjects]   = useState([])
  const [form,     setForm]       = useState(EMPTY_FORM)
  const [editId,   setEditId]     = useState(null)   // null = create mode
  const [saving,   setSaving]     = useState(false)
  const [error,    setError]      = useState('')
  const [loading,  setLoading]    = useState(true)

  // ── fetch ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    api.get('/gmail/projects/')
      .then(r => setProjects(r.data))
      .catch(() => setError('Failed to load projects.'))
      .finally(() => setLoading(false))
  }, [])

  // ── form helpers ──────────────────────────────────────────────────────────
  function setEmailAt(index, value) {
    const emails = [...form.emails]
    emails[index] = value
    setForm(f => ({ ...f, emails }))
  }

  function addEmailRow() {
    setForm(f => ({ ...f, emails: [...f.emails, ''] }))
  }

  function removeEmailRow(index) {
    const emails = form.emails.filter((_, i) => i !== index)
    setForm(f => ({ ...f, emails: emails.length ? emails : [''] }))
  }

  function resetForm() {
    setForm(EMPTY_FORM)
    setEditId(null)
    setError('')
  }

  function startEdit(project) {
    setEditId(project.id)
    setForm({
      name:   project.name,
      emails: project.emails.length ? [...project.emails] : [''],
    })
    setError('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // ── save (create or update) ───────────────────────────────────────────────
  async function handleSave(e) {
    e.preventDefault()
    const cleanEmails = form.emails.map(e => e.trim()).filter(Boolean)
    if (!form.name.trim()) { setError('Project name is required.'); return }

    setSaving(true)
    setError('')
    const payload = { name: form.name.trim(), emails: cleanEmails }

    try {
      if (editId) {
        const { data } = await api.put(`/gmail/projects/${editId}/`, payload)
        setProjects(ps => ps.map(p => p.id === editId ? data : p))
      } else {
        const { data } = await api.post('/gmail/projects/', payload)
        setProjects(ps => [...ps, data].sort((a, b) => a.name.localeCompare(b.name)))
      }
      resetForm()
    } catch (err) {
      const detail = err.response?.data?.name?.[0]
        || err.response?.data?.detail
        || 'Failed to save project.'
      setError(detail)
    } finally {
      setSaving(false)
    }
  }

  // ── delete ────────────────────────────────────────────────────────────────
  async function handleDelete(id) {
    if (!window.confirm('Delete this project?')) return
    try {
      await api.delete(`/gmail/projects/${id}/`)
      setProjects(ps => ps.filter(p => p.id !== id))
      if (editId === id) resetForm()
    } catch {
      setError('Failed to delete project.')
    }
  }

  // ── render ────────────────────────────────────────────────────────────────
  return (
    <div>
      <h4 className="fw-bold mb-1">Projects</h4>
      <p className="text-muted mb-4">Add projects and associate employee emails with each one.</p>

      <div className="row g-4">

        {/* ── Left: Add / Edit form ─────────────────────────────────────── */}
        <div className="col-lg-5">
          <div className="card shadow-sm">
            <div className="card-header bg-white fw-semibold">
              {editId ? 'Edit Project' : 'Add Project'}
            </div>
            <div className="card-body">
              {error && <div className="alert alert-danger py-2 small">{error}</div>}

              <form onSubmit={handleSave}>
                {/* Project Name */}
                <div className="mb-3">
                  <label className="form-label fw-semibold">Project Name</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. Odoo Apps & Theme"
                    value={form.name}
                    onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                    required
                  />
                </div>

                {/* Emails */}
                <div className="mb-3">
                  <label className="form-label fw-semibold">
                    Emails
                    <span className="text-muted fw-normal small ms-1">(one per line)</span>
                  </label>

                  {form.emails.map((email, i) => (
                    <div key={i} className="d-flex gap-2 mb-2">
                      <input
                        type="email"
                        className="form-control"
                        placeholder="employee@example.com"
                        value={email}
                        onChange={e => setEmailAt(i, e.target.value)}
                      />
                      <button
                        type="button"
                        className="btn btn-outline-danger btn-sm px-2"
                        onClick={() => removeEmailRow(i)}
                        disabled={form.emails.length === 1}
                        title="Remove"
                      >
                        ×
                      </button>
                    </div>
                  ))}

                  <button
                    type="button"
                    className="btn btn-outline-secondary btn-sm mt-1"
                    onClick={addEmailRow}
                  >
                    + Add Email
                  </button>
                </div>

                <div className="d-flex gap-2">
                  <button
                    type="submit"
                    className="btn" style={{backgroundColor:'#0d4f4f',color:'white'}}
                    disabled={saving}
                  >
                    {saving
                      ? <><span className="spinner-border spinner-border-sm me-2" />Saving…</>
                      : editId ? 'Update Project' : 'Save Project'}
                  </button>
                  {editId && (
                    <button
                      type="button"
                      className="btn btn-outline-secondary"
                      onClick={resetForm}
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </form>
            </div>
          </div>
        </div>

        {/* ── Right: Projects table ─────────────────────────────────────── */}
        <div className="col-lg-7">
          <div className="card shadow-sm">
            <div className="card-header bg-white fw-semibold d-flex justify-content-between align-items-center">
              <span>All Projects</span>
              <span className="badge bg-secondary">{projects.length}</span>
            </div>

            {loading ? (
              <div className="card-body text-center text-muted small py-5">
                <span className="spinner-border spinner-border-sm me-2" />Loading…
              </div>
            ) : projects.length === 0 ? (
              <div className="card-body text-muted small text-center py-5">
                No projects yet. Add one using the form.
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover mb-0">
                  <thead className="table-light">
                    <tr>
                      <th style={{ width: 40 }}>#</th>
                      <th>Project Name</th>
                      <th>Emails</th>
                      <th style={{ width: 100 }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {projects.map((p, i) => (
                      <tr key={p.id} className={editId === p.id ? 'table-primary' : ''}>
                        <td className="text-muted">{i + 1}</td>
                        <td className="fw-semibold">{p.name}</td>
                        <td>
                          {p.emails.length === 0 ? (
                            <span className="text-muted small">—</span>
                          ) : (
                            <div className="d-flex flex-wrap gap-1">
                              {p.emails.map(email => (
                                <span key={email} className="badge bg-light text-dark border small">
                                  {email}
                                </span>
                              ))}
                            </div>
                          )}
                        </td>
                        <td>
                          <div className="d-flex gap-1">
                            <button
                              className="btn btn-outline-primary btn-sm"
                              onClick={() => startEdit(p)}
                              title="Edit"
                            >
                              ✎
                            </button>
                            <button
                              className="btn btn-outline-danger btn-sm"
                              onClick={() => handleDelete(p.id)}
                              title="Delete"
                            >
                              ×
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  )
}
