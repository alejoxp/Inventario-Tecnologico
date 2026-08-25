import { defineStore } from 'pinia'
import api from '../services/api'

function leerRol(token) {
  try {
    const payload = JSON.parse(window.atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
    return payload.rol || ''
  } catch {
    return ''
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    rol: localStorage.getItem('rol') || '',
    cargando: false,
  }),
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
        this.rol = data.rol || leerRol(this.token)
        localStorage.setItem('token', this.token)
        localStorage.setItem('rol', this.rol)
      } finally {
        this.cargando = false
      }
    },
    cerrarSesion() {
      this.token = ''
      this.rol = ''
      localStorage.removeItem('token')
      localStorage.removeItem('rol')
    },
  },
})
