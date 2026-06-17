import axios from 'axios'

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

export const ACCESS_KEY = 'wra_access'
export const REFRESH_KEY = 'wra_refresh'

const api = axios.create({ baseURL: BASE_URL })

// Attach the access token to every request if present.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(ACCESS_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// On a 401, try a one-shot refresh, then replay the original request.
let refreshing = null
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const refresh = localStorage.getItem(REFRESH_KEY)
    if (
      error.response?.status === 401 &&
      refresh &&
      !original._retry
    ) {
      original._retry = true
      try {
        refreshing =
          refreshing ||
          axios.post(`${BASE_URL}/auth/refresh/`, { refresh })
        const { data } = await refreshing
        refreshing = null
        localStorage.setItem(ACCESS_KEY, data.access)
        original.headers.Authorization = `Bearer ${data.access}`
        return api(original)
      } catch (refreshErr) {
        refreshing = null
        localStorage.removeItem(ACCESS_KEY)
        localStorage.removeItem(REFRESH_KEY)
        return Promise.reject(refreshErr)
      }
    }
    return Promise.reject(error)
  },
)

export default api
