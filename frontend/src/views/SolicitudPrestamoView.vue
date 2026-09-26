<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '../components/Navbar.vue'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const equipos = ref([])
const formulario = ref({ equipos_ids: [], fecha_inicio: '', fecha_fin: '', actividad: '', descripcion: '', observaciones: '' })
const cargando = ref(true)
const enviando = ref(false)
const mensaje = ref('')
const error = ref('')

async function cargarEquipos() {
  try {
    const { data } = await api.get('/equipos/')
    equipos.value = data.filter((equipo) => equipo.estado === 'Operativo')
  } catch {
    error.value = 'No se pudieron cargar los equipos.'
  } finally {
    cargando.value = false
  }
}

async function enviarSolicitud() {
  error.value = ''
  mensaje.value = ''
  enviando.value = true
  try {
    const fechaFin = new Date(`${formulario.value.fecha_fin}T00:00:00`)
    fechaFin.setDate(fechaFin.getDate() + 1)
    await api.post('/prestamos', {
      equipos_ids: formulario.value.equipos_ids.map(Number),
      custodio_solicitante: auth.username,
      fecha_inicio: new Date(formulario.value.fecha_inicio).toISOString(),
      fecha_fin: fechaFin.toISOString(),
      estado_solicitud: 'Pendiente',
      aprobado_por_usuario_id: null,
      actividad: formulario.value.actividad,
      motivo_uso: formulario.value.actividad,
      descripcion: formulario.value.descripcion || null,
      observaciones: formulario.value.observaciones || null,
    })
    mensaje.value = 'Solicitud enviada y pendiente de aprobación.'
    formulario.value = { equipos_ids: [], fecha_inicio: '', fecha_fin: '', actividad: '', descripcion: '', observaciones: '' }
  } catch (respuesta) {
    error.value = respuesta.response?.data?.detail || 'No se pudo registrar la solicitud.'
  } finally {
    enviando.value = false
  }
}

onMounted(cargarEquipos)
</script>

<template>
  <Navbar />
  <main class="contenido solicitud-vista">
    <div class="encabezado-vista">
      <div><p class="etiqueta">Gestión de equipos</p><h1>Solicitar préstamo</h1></div>
      <button class="btn-secundario" type="button" @click="router.push('/prestamos/calendario')">Ver calendario</button>
    </div>
    <form class="tarjeta-sombra formulario-prestamo" @submit.prevent="enviarSolicitud">
      <p class="subtexto">Elige el día y los equipos que usarás. La solicitud quedará pendiente de aprobación.</p>
      <label>Equipos que se llevarán
        <select v-model="formulario.equipos_ids" class="input-form equipos-select" multiple required :disabled="cargando">
          <option v-for="equipo in equipos" :key="equipo.id" :value="equipo.id">
            {{ equipo.bien_nacional }} · {{ equipo.marca?.nombre || 'Sin marca' }} {{ equipo.modelo || '' }}
          </option>
        </select>
      </label>
      <div class="fila-fechas">
        <label>Día de uso<input v-model="formulario.fecha_inicio" class="input-form" type="date" required /></label>
        <label>Hasta<input v-model="formulario.fecha_fin" class="input-form" type="date" required /></label>
      </div>
      <label>Actividad<input v-model="formulario.actividad" class="input-form" maxlength="200" required placeholder="Ej. Jornada de capacitación" /></label>
      <label>Descripción<textarea v-model="formulario.descripcion" class="input-form" rows="3" maxlength="2000" placeholder="Describe brevemente el uso de los equipos" /></label>
      <label>Observaciones<textarea v-model="formulario.observaciones" class="input-form" rows="3" maxlength="2000" /></label>
      <p v-if="mensaje" class="mensaje-exito">{{ mensaje }}</p>
      <p v-if="error" class="mensaje-error">{{ error }}</p>
      <button class="btn-primario" type="submit" :disabled="enviando || cargando || !formulario.equipos_ids.length">
        {{ enviando ? 'Enviando...' : 'Enviar solicitud' }}
      </button>
    </form>
  </main>
</template>

<style scoped>
.formulario-prestamo { max-width: 720px; display: grid; gap: 1rem; padding: 1.5rem; }
.formulario-prestamo label { display: grid; gap: .4rem; font-weight: 600; }
.fila-fechas { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
.subtexto { color: #64748b; margin: 0; }
.mensaje-exito { color: #166534; margin: 0; }
.equipos-select { min-height: 9rem; }
@media (max-width: 640px) { .fila-fechas { grid-template-columns: 1fr; } }
</style>
