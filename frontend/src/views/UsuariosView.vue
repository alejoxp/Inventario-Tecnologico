<script setup>
import { onMounted, reactive, ref } from 'vue'
import Navbar from '../components/Navbar.vue'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const usuarios = ref([])
const roles = ref([])
const error = ref('')
const mensajeExito = ref('')
const guardando = ref(false)
const eliminando = ref(false)
const usuarioAEliminar = ref(null)

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
  mensajeExito.value = ''
  try {
    await api.post('/usuarios', nuevo)
    mensajeExito.value = `Usuario "${nuevo.username}" creado exitosamente.`
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
  error.value = ''
  mensajeExito.value = ''
  try {
    const { data } = await api.patch(`/usuarios/${usuario.id}/rol`, { rol_id: usuario.rol.id })
    usuario.rol = data.rol
    mensajeExito.value = `Rol de "${usuario.username}" actualizado a ${data.rol.nombre}.`
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || 'No se pudo cambiar el rol.'
    await cargar()
  }
}

function abrirModalEliminar(usuario) {
  error.value = ''
  mensajeExito.value = ''
  usuarioAEliminar.value = usuario
}

function cerrarModalEliminar() {
  usuarioAEliminar.value = null
}

async function confirmarEliminar() {
  if (!usuarioAEliminar.value) return
  eliminando.value = true
  error.value = ''
  mensajeExito.value = ''
  const usernameEliminado = usuarioAEliminar.value.username

  try {
    await api.delete(`/usuarios/${usuarioAEliminar.value.id}`)
    mensajeExito.value = `El usuario "${usernameEliminado}" ha sido eliminado exitosamente.`
    cerrarModalEliminar()
    await cargar()
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || 'No se pudo eliminar el usuario.'
    cerrarModalEliminar()
  } finally {
    eliminando.value = false
  }
}

onMounted(cargar)
</script>

<template>
  <Navbar />
  <main class="contenido">
    <div class="encabezado-vista">
      <div>
        <p class="etiqueta">Administración Institucional</p>
        <h1>Usuarios y roles</h1>
      </div>
      <div v-if="usuarios.length" class="badge-conteo">
        Total cuentas: <strong>{{ usuarios.length }}</strong>
      </div>
    </div>

    <!-- Formulario para agregar usuario -->
    <section class="tarjeta-sombra bloque-formulario">
      <h2 class="subtitulo-seccion">Registrar nuevo trabajador / usuario</h2>
      <form class="formulario formulario-usuario" @submit.prevent="crear">
        <label class="campo-label">
          Nombre de usuario
          <input
            v-model="nuevo.username"
            class="input-form"
            placeholder="ej. jperez"
            minlength="3"
            required
          />
        </label>
        <label class="campo-label">
          Contraseña
          <input
            v-model="nuevo.password"
            class="input-form"
            placeholder="Mínimo 8 caracteres"
            minlength="8"
            type="password"
            required
          />
        </label>
        <label class="campo-label">
          Rol asignado
          <select v-model="nuevo.rol_id" class="input-form" required>
            <option v-for="rol in roles" :key="rol.id" :value="rol.id">{{ rol.nombre }}</option>
          </select>
        </label>
        <button class="btn-primario boton-usuario" type="submit" :disabled="guardando">
          {{ guardando ? 'Guardando...' : 'Crear usuario' }}
        </button>
      </form>
    </section>

    <!-- Notificaciones de éxito o error -->
    <div v-if="mensajeExito" class="mensaje-exito">
      ✓ {{ mensajeExito }}
    </div>
    <div v-if="error" class="mensaje-alerta-error">
      ⚠ {{ error }}
    </div>

    <!-- Tabla de gestión de usuarios -->
    <div class="tabla-contenedor tarjeta-sombra">
      <table>
        <thead>
          <tr>
            <th>Usuario</th>
            <th>Rol actual</th>
            <th>Modificar rol</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!usuarios.length">
            <td colspan="4" class="celda-centrada">Cargando lista de usuarios...</td>
          </tr>
          <tr v-for="usuario in usuarios" :key="usuario.id">
            <td>
              <strong>{{ usuario.username }}</strong>
              <span v-if="usuario.username === auth.username" class="badge-tu-usuario">Tú (Sesión activa)</span>
            </td>
            <td>
              <span class="badge-rol">{{ usuario.rol.nombre }}</span>
            </td>
            <td>
              <select
                v-model="usuario.rol.id"
                class="input-form selector-rol"
                @change="cambiarRol(usuario)"
              >
                <option v-for="rol in roles" :key="rol.id" :value="rol.id">
                  {{ rol.nombre }}
                </option>
              </select>
            </td>
            <td>
              <button
                v-if="usuario.username !== auth.username"
                class="btn-peligro btn-pequeno"
                type="button"
                title="Eliminar permanentemente este usuario"
                @click="abrirModalEliminar(usuario)"
              >
                Eliminar
              </button>
              <span v-else class="texto-deshabilitado" title="No puedes eliminar tu propia cuenta en sesión">
                Sesión actual
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal de confirmación para eliminar usuario -->
    <div v-if="usuarioAEliminar" class="modal-overlay" @click.self="cerrarModalEliminar">
      <div class="modal-contenedor tarjeta-sombra">
        <div class="modal-icono-peligro">⚠️</div>
        <h3>¿Eliminar cuenta de usuario?</h3>
        <p class="modal-mensaje">
          Estás a punto de eliminar definitivamente el usuario <strong>"{{ usuarioAEliminar.username }}"</strong>
          con rol <strong>{{ usuarioAEliminar.rol.nombre }}</strong>.
        </p>
        <p class="modal-advertencia">
          El trabajador perderá de inmediato el acceso al sistema de inventario. Esta acción no se puede deshacer.
        </p>
        <div class="modal-acciones">
          <button
            class="btn-secundario"
            type="button"
            :disabled="eliminando"
            @click="cerrarModalEliminar"
          >
            Cancelar
          </button>
          <button
            class="btn-peligro"
            type="button"
            :disabled="eliminando"
            @click="confirmarEliminar"
          >
            {{ eliminando ? 'Eliminando...' : 'Sí, eliminar usuario' }}
          </button>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.bloque-formulario {
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
}

.subtitulo-seccion {
  margin: 0 0 1rem;
  color: var(--azul-profundo);
  font-size: 1.1rem;
  font-weight: 600;
}

.badge-tu-usuario {
  display: inline-block;
  margin-left: 0.5rem;
  padding: 0.2rem 0.5rem;
  background: var(--azul-claro);
  color: var(--azul-profundo);
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 4px;
}

.badge-rol {
  display: inline-block;
  padding: 0.25rem 0.6rem;
  background: #edf2f6;
  color: var(--azul-profundo);
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 600;
}

.texto-deshabilitado {
  color: var(--texto-suave);
  font-size: 0.82rem;
  font-style: italic;
}

.mensaje-exito {
  color: var(--verde);
  background: var(--verde-fondo);
  padding: 0.85rem 1.2rem;
  border-radius: 6px;
  border: 1px solid #b7e4c7;
  font-size: 0.92rem;
  font-weight: 500;
  margin-bottom: 1.25rem;
}

.mensaje-alerta-error {
  color: var(--rojo);
  background: var(--rojo-fondo);
  padding: 0.85rem 1.2rem;
  border-radius: 6px;
  border: 1px solid #f5c2c7;
  font-size: 0.92rem;
  font-weight: 500;
  margin-bottom: 1.25rem;
}

/* Modal de Confirmación */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(11, 45, 69, 0.6);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
  padding: 1rem;
}

.modal-contenedor {
  background: white;
  padding: 2rem;
  border-radius: 10px;
  max-width: 480px;
  width: 100%;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
  animation: modalEntrada 0.2s ease-out;
}

@keyframes modalEntrada {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.modal-icono-peligro {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.modal-contenedor h3 {
  margin: 0.25rem 0 0.75rem;
  color: var(--azul-profundo);
  font-size: 1.3rem;
}

.modal-mensaje {
  color: var(--texto);
  font-size: 0.95rem;
  margin: 0.5rem 0;
  line-height: 1.4;
}

.modal-advertencia {
  color: var(--rojo);
  font-size: 0.85rem;
  margin: 0.75rem 0 1.5rem;
  line-height: 1.4;
  background: var(--rojo-fondo);
  padding: 0.6rem 0.8rem;
  border-radius: 6px;
}

.modal-acciones {
  display: flex;
  justify-content: center;
  gap: 1rem;
}
</style>