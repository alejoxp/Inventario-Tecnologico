import { defineStore } from 'pinia'
import api from '../services/api'

function leerPayload(token) {
  try {
    return JSON.parse(window.atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
  } catch {
    return {}
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => {
    const token = localStorage.getItem('token') || ''
    const payload = token ? leerPayload(token) : {}
    return {
      token,
      rol: localStorage.getItem('rol') || payload.rol || '',
      username: localStorage.getItem('username') || payload.sub || '',
      cargando: false,
    }
  },
  getters: {
    autenticado: (state) => Boolean(state.token),
  },
  actions: {
    async iniciarSesion(username, password) {
      this.cargando = true
      try {
        const datos = new URLSearchParams({ username, password })
        const { data } = await api.post('/auth/login', datos, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        })
        this.token = data.access_token
        const payload = leerPayload(this.token)
        this.rol = data.rol || payload.rol || ''
        this.username = payload.sub || username
        localStorage.setItem('token', this.token)
        localStorage.setItem('rol', this.rol)
        localStorage.setItem('username', this.username)
      } finally {
        this.cargando = false
      }
    },
    cerrarSesion() {
      this.token = ''
      this.rol = ''
      this.username = ''
      localStorage.removeItem('token')
      localStorage.removeItem('rol')
      localStorage.removeItem('username')
    },
  },
})

