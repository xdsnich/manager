import axios from 'axios'

// Базовый URL — через vite proxy идёт на localhost:8000
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

// Автоматически добавляем JWT токен в каждый запрос
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// При 401 — очищаем токен и редиректим на логин
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── AUTH ─────────────────────────────────────────────────────
export const authAPI = {
  login: (email, password) =>
    api.post('/auth/login', { email, password }),

  register: (email, password) =>
    api.post('/auth/register', { email, password }),

  me: () =>
    api.get('/auth/me'),

  logout: () =>
    api.post('/auth/logout'),

  changePassword: (old_password, new_password) =>
    api.post('/auth/change-password', { old_password, new_password }),
}

// ── ACCOUNTS ─────────────────────────────────────────────────
export const accountsAPI = {
  list: () =>
    api.get('/accounts/'),

  get: (id) =>
    api.get(`/accounts/${id}`),

  create: (phone) =>
    api.post('/accounts/', { phone }),

  update: (id, data) =>
    api.patch(`/accounts/${id}`, data),

  delete: (id) =>
    api.delete(`/accounts/${id}`),

  stats: () =>
    api.get('/accounts/stats'),

  importJson: () =>
    api.post('/accounts/import-json'),
}

// ── PROXIES ──────────────────────────────────────────────────
export const proxiesAPI = {
  list: () =>
    api.get('/proxies/'),

  create: (data) =>
    api.post('/proxies/', data),

  bulkCreate: (text) =>
    api.post('/proxies/bulk', { proxies_text: text }),

  delete: (id) =>
    api.delete(`/proxies/${id}`),
}

// ── TASKS ────────────────────────────────────────────────────
export const tasksAPI = {
  checkAccounts: (check_spam = false) =>
    api.post('/tasks/check-accounts', { check_spam }),

  checkProxies: () =>
    api.post('/tasks/check-proxies'),

  getStatus: (taskId) =>
    api.get(`/tasks/${taskId}`),

  cancel: (taskId) =>
    api.delete(`/tasks/${taskId}`),
}

export default api
