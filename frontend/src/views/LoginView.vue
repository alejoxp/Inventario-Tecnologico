<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const username = ref('')
const password = ref('')
const error = ref('')
const auth = useAuthStore()
const router = useRouter()

async function enviar() {
  error.value = ''
  try {
    await auth.iniciarSesion(username.value, password.value)
    router.push('/inventario')
  } catch (err) {
    error.value = err.response?.data?.detail || 'No fue posible validar las credenciales. Verifique usuario y contraseña.'
  }
}
</script>

<template>
  <main class="pantalla-login">
    <div class="tarjeta-login-wrapper">
      <div class="panel-login tarjeta-sombra">
        <header class="login-header">
          <div class="emblema-institucional">
            <span class="emblema-icono">💻</span>
            <div>
              <p class="marca-pequena">Fundacite Sucre</p>
              <p class="etiqueta-sub">Coordinación de Telemática</p>
            </div>
          </div>
          <h1>Inventario Tecnológico</h1>
          <p class="login-descripcion">
            Sistema de control patrimonial, custodia y trazabilidad de bienes informáticos.
          </p>
        </header>

        <form class="formulario-login" @submit.prevent="enviar">
          <label class="campo-label" for="username">
            <span>Usuario</span>
            <input
              id="username"
              v-model="username"
              class="input-form"
              required
              autocomplete="username"
              placeholder="Ingrese su nombre de usuario"
              :disabled="auth.cargando"
            />
          </label>

          <label class="campo-label" for="password">
            <span>Contraseña</span>
            <input
              id="password"
              v-model="password"
              class="input-form"
              type="password"
              required
              autocomplete="current-password"
              placeholder="••••••••"
              :disabled="auth.cargando"
            />
          </label>

          <div v-if="error" class="mensaje-error alerta-error">
            <span class="icono-alerta">⚠️</span>
            <span>{{ error }}</span>
          </div>

          <button
            class="btn-primario btn-login"
            type="submit"
            :disabled="auth.cargando"
          >
            <span v-if="auth.cargando">Iniciando sesión...</span>
            <span v-else>Ingresar al Sistema →</span>
          </button>
        </form>

        <footer class="login-footer">
          <p>Acceso restringido para personal autorizado.</p>
        </footer>
      </div>
    </div>
  </main>
</template>
