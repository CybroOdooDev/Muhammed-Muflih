import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGoogleLogin } from '@react-oauth/google'

import { useAuth } from '../context/AuthContext'

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

const GMAIL_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly'

export default function Login() {
  const { loginWithGoogle } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleGoogleLogin = useGoogleLogin({
    flow: 'auth-code',
    scope: `openid email profile ${GMAIL_SCOPE}`,
    redirect_uri: 'postmessage',
    onSuccess: async ({ code }) => {
      setLoading(true)
      setError('')
      try {
        await loginWithGoogle(code)
        navigate('/', { replace: true })
      } catch (err) {
        const detail = err.response?.data?.detail || ''
        if (detail.includes('invalid_grant')) {
          setError('Google sign-in session expired. Please try again.')
        } else if (detail.includes('Code exchange failed')) {
          setError(`Sign-in failed: ${detail}`)
        } else {
          setError(detail || 'Login failed. Please try again.')
        }
      } finally {
        setLoading(false)
      }
    },
    onError: (err) => {
      const type = err?.type || err?.error || ''
      if (type === 'popup_closed') {
        setError('Sign-in popup was closed. Please try again.')
      } else if (type === 'access_denied') {
        setError('Access denied by Google. Your account may not be authorised to use this app yet — contact the admin.')
      } else {
        setError(`Google sign-in failed${type ? `: ${type}` : ''}. Please try again.`)
      }
    },
  })

  return (
    <div className="container-fluid">
      <div className="row vh-100">
        {/* Left form panel */}
        <div className="col-lg-6 d-flex align-items-center justify-content-center bg-white">
          <div className="w-100 px-4" style={{ maxWidth: 400 }}>
            <div className="d-flex align-items-center gap-2 mb-5">
              <span className="brand-mark">WR</span>
              <span className="fw-semibold fs-5">Work Report Analysis</span>
            </div>

            <h2 className="fw-bold mb-1">Welcome Back!</h2>
            <p className="text-muted mb-4">
              Sign in with your company Google account to access your dashboard.
            </p>

            {!CLIENT_ID && (
              <div className="alert alert-warning" role="alert">
                <strong>Google Client ID not set.</strong> Add
                <code> VITE_GOOGLE_CLIENT_ID</code> to
                <code> frontend/.env</code> to enable the button.
              </div>
            )}

            {error && (
              <div className="alert alert-danger" role="alert">
                {error}
              </div>
            )}

            <div className="d-grid my-3">
              <button
                className="btn btn-outline-dark d-flex align-items-center justify-content-center gap-2 py-2"
                onClick={() => handleGoogleLogin()}
                disabled={!CLIENT_ID || loading}
              >
                {loading ? (
                  <span className="spinner-border spinner-border-sm" />
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                  </svg>
                )}
                {loading ? 'Signing in…' : 'Continue with Google'}
              </button>
            </div>

            <p className="text-muted small text-center mt-4 mb-0">
              New employees are added automatically on first sign-in.
            </p>
          </div>
        </div>

        {/* Right marketing panel */}
        <div className="col-lg-6 d-none d-lg-flex login-hero flex-column justify-content-center p-5">
          <h1 className="display-5 fw-bold mb-4" style={{ maxWidth: 520 }}>
            Smarter work tracking, one dashboard.
          </h1>
          <p className="fs-5 opacity-75 hero-quote mb-5" style={{ maxWidth: 500 }}>
            Automatically collect employee work reports, compare them against
            timesheets, and monitor reporting activity — all in one place.
          </p>
          <div className="d-flex flex-column gap-3 fs-6">
            <div className="hero-feature">
              <span className="tick">✓</span>
              <span>Gmail-synced work reports</span>
            </div>
            <div className="hero-feature">
              <span className="tick">✓</span>
              <span>Timesheet comparison &amp; analytics</span>
            </div>
            <div className="hero-feature">
              <span className="tick">✓</span>
              <span>Manager dashboards</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
