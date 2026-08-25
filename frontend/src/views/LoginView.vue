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
  } catch {
    error.value = 'No fue posible validar las credenciales.'
  }
}
</script>

<template>
  <main class="pantalla-login">
    <form class="panel-login tarjeta-sombra" @submit.prevent="enviar">
      <p class="etiqueta">Acceso institucional</p>
      <h1>Inventario Tecnologico</h1>
      <label class="campo-label" for="username">Usuario</label>
      <input id="username" v-model="username" class="input-form" required autocomplete="username" />
      <label class="campo-label" for="password">Contrasena</label>
      <input id="password" v-model="password" class="input-form" type="password" required autocomplete="current-password" />
      <p v-if="error" class="mensaje-error">{{ error }}</p>
      <button class="btn-primario" type="submit" :disabled="auth.cargando">Iniciar sesion</button>
    </form>
  </main>
</template>
