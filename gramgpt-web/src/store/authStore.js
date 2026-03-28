import { create } from 'zustand'
import { authAPI } from '../services/api'

export const useAuthStore = create((set, get) => ({
  user: null,
  loading: true,   // true пока не проверили токен при старте
  error: null,

  // Проверяем есть ли токен при загрузке приложения
  init: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      set({ loading: false })
      return
    }
    try {
      const { data } = await authAPI.me()
      set({ user: data, loading: false })
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      set({ user: null, loading: false })
    }
  },

  login: async (email, password) => {
    set({ error: null })
    try {
      const { data } = await authAPI.login(email, password)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      const me = await authAPI.me()
      set({ user: me.data, error: null })
      return true
    } catch (err) {
      const msg = err.response?.data?.detail || 'Ошибка входа'
      set({ error: msg })
      return false
    }
  },

  logout: async () => {
    try { await authAPI.logout() } catch {}
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null })
  },

  clearError: () => set({ error: null }),
}))
