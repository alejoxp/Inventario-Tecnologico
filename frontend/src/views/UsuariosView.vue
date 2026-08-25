<script setup>
import { onMounted, reactive, ref } from 'vue'
import Navbar from '../components/Navbar.vue'
import api from '../services/api'

const usuarios = ref([])
const roles = ref([])
const error = ref('')
const guardando = ref(false)
const nuevo = reactive({ username: '', password: '', rol_id: '' })

async function cargar() {
  try {
    const [usuariosResponse, rolesResponse] = await Promise.all([
      api.get('/usuarios'),
      api.get('/usuarios/roles'),
    ])
    usuarios.value = usuariosResponse.data
    roles.value = rolesResponse.data
    if (!nuevo.rol_id && roles.value.length) nuevo.rol_id = roles.value[0].id
  } catch {
    error.value = 'No se pudieron cargar los usuarios.'
  }
}


async function crear() {
  guardando.value = true
  error.value = ''
  try {
    await api.post('/usuarios', nuevo)
    nuevo.username = ''
    nuevo.password = ''
    await cargar()
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || 'No se pudo crear el usuario.'
  } finally {
    guardando.value = false
  }
}

async function cambiarRol(usuario) {
  try {
    const { data } = await api.patch(`/usuarios/${usuario.id}/rol`, { rol_id: usuario.rol.id })
    usuario.rol = data.rol
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || 'No se pudo cambiar el rol.'
    await cargar()
  }
}

onMounted(cargar)
</script>

<template>
  <Navbar />
  <main class="contenido">
    <p class="etiqueta">Administracion</p>
    <h1>Usuarios y roles</h1>
    <form class="formulario tarjeta-sombra formulario-usuario" @submit.prevent="crear">
      <label class="campo-label">Usuario<input v-model="nuevo.username" class="input-form" minlength="3" required /></label>
      <label class="campo-label">Contrasena<input v-model="nuevo.password" class="input-form" minlength="8" type="password" required /></label>
      <label class="campo-label">Rol<select v-model="nuevo.rol_id" class="input-form" required><option v-for="rol in roles" :key="rol.id" :value="rol.id">{{ rol.nombre }}</option></select></label>
      <button class="btn-primario boton-usuario" type="submit" :disabled="guardando">Crear usuario</button>
    </form>
    <p v-if="error" class="mensaje-error">{{ error }}</p>
    <div class="tabla-contenedor tarjeta-sombra">
      <table><thead><tr><th>Usuario</th><th>Rol asignado</th><th>Cambiar rol</th></tr></thead>
        <tbody><tr v-for="usuario in usuarios" :key="usuario.id"><td>{{ usuario.username }}</td><td>{{ usuario.rol.nombre }}</td><td><select v-model="usuario.rol.id" class="input-form selector-rol" @change="cambiarRol(usuario)"><option v-for="rol in roles" :key="rol.id" :value="rol.id">{{ rol.nombre }}</option></select></td></tr></tbody>
      </table>
    </div>
  </main>
</template>