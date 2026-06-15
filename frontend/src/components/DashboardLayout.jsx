import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

// Inline icons (no icon library needed)
const icons = {
  report: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 3v18h18" />
      <rect x="7" y="11" width="3" height="6" />
      <rect x="12" y="7" width="3" height="10" />
      <rect x="17" y="13" width="3" height="4" />
    </svg>
  ),
  comparison: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 6h7M3 12h7M3 18h7" />
      <path d="M14 6h7M14 12h7M14 18h7" />
      <path d="M12 3v18" />
    </svg>
  ),
  mom: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 4h16v16H4z" />
      <path d="M8 8h8M8 12h8M8 16h5" />
    </svg>
  ),
  workdays: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" />
      <path d="M16 2v4M8 2v4M3 10h18" />
    </svg>
  ),
  projects: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 7h20M2 12h20M2 17h20" />
      <circle cx="5" cy="7" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="5" cy="12" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="5" cy="17" r="1.5" fill="currentColor" stroke="none" />
    </svg>
  ),
  scrum: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="5" height="5" rx="1" />
      <rect x="3" y="10" width="5" height="5" rx="1" />
      <rect x="3" y="17" width="5" height="5" rx="1" />
      <rect x="10" y="3" width="5" height="5" rx="1" />
      <rect x="10" y="10" width="5" height="5" rx="1" />
      <rect x="17" y="3" width="5" height="5" rx="1" />
      <rect x="17" y="10" width="5" height="5" rx="1" />
    </svg>
  ),
  daily: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="17" rx="2" />
      <path d="M3 9h18" />
      <path d="M8 2v4M16 2v4" />
      <path d="M7 14l2 2 4-4" />
    </svg>
  ),
}

const MENU = [
  { to: '/', label: 'Report Dashboard', icon: icons.report, end: true },
  { to: '/comparison', label: 'Comparison', icon: icons.comparison },
  { to: '/mom', label: 'MOM Dashboard', icon: icons.mom },
  { to: '/work-days', label: 'Work Day Count', icon: icons.workdays },
  { to: '/projects', label: 'Projects',       icon: icons.projects },
  { to: '/odoo-daily',  label: 'Daily Tasks',     icon: icons.daily  },
]

export default function DashboardLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const profileRef = useRef(null)

  // Close the dropdown when clicking outside of it.
  useEffect(() => {
    function onClick(e) {
      if (profileRef.current && !profileRef.current.contains(e.target)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className="sidebar">
        {/* Logo — matches the login page */}
        <div className="d-flex align-items-center gap-2 mb-5">
          <span className="brand-mark">WR</span>
          <span className="fw-semibold">Work Report Analysis</span>
        </div>

        {/* Menu */}
        <nav className="nav flex-column">
          {MENU.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className="nav-link"
            >
              {item.icon}
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <div className="app-content d-flex flex-column">
        <header className="app-topbar d-flex justify-content-end align-items-center px-4 py-2">
          <div className="profile-menu" ref={profileRef}>
            <button
              type="button"
              className="profile-trigger d-flex align-items-center gap-2"
              onClick={() => setMenuOpen((o) => !o)}
            >
              {user?.picture && (
                <img
                  src={user.picture}
                  alt=""
                  width="36"
                  height="36"
                  className="rounded-circle"
                  referrerPolicy="no-referrer"
                />
              )}
              <div className="text-end lh-sm d-none d-sm-block">
                <div className="fw-semibold small">
                  {user?.first_name} {user?.last_name}
                </div>
                <div className="text-muted small">{user?.email}</div>
              </div>
              <svg
                viewBox="0 0 24 24" width="16" height="16" fill="none"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                strokeLinejoin="round" className="text-muted"
              >
                <path d="m6 9 6 6 6-6" />
              </svg>
            </button>

            {menuOpen && (
              <div className="profile-dropdown shadow-sm">
                <button
                  type="button"
                  className="dropdown-item-btn"
                  onClick={() => {
                    setMenuOpen(false)
                    navigate('/settings')
                  }}
                >
                  Settings
                </button>
                <button
                  type="button"
                  className="dropdown-item-btn text-danger"
                  onClick={() => {
                    setMenuOpen(false)
                    logout()
                  }}
                >
                  Sign out
                </button>
              </div>
            )}
          </div>
        </header>

        <main className="flex-fill p-4">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
