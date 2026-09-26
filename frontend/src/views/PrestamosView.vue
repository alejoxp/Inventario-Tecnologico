<script setup>
import { computed, onMounted, ref } from 'vue'
import Navbar from '../components/Navbar.vue'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const prestamos = ref([])
const cargando = ref(true)
const error = ref('')
const filtro = ref('')
const puedeDevolver = computed(() => ['COORDINADOR', 'SUPERADMIN'].includes(auth.rol))
const prestamosVisibles = computed(() => {
  const termino = filtro.value.trim().toLowerCase()
  if (!termino) return prestamos.value
  return prestamos.value.filter((prestamo) => [prestamo.actividad, prestamo.custodio_solicitante, ...prestamo.equipos_nombres].some((valor) => String(valor || '').toLowerCase().includes(termino)))
})

async function cargarPrestamos() {
  try {
    const { data } = await api.get('/prestamos')
    prestamos.value = data
  } catch (respuesta) {
    error.value = respuesta.response?.data?.detail || 'No se pudieron cargar los préstamos.'
  } finally {
    cargando.value = false
  }
}

async function devolver(prestamo) {
  if (!window.confirm(`¿Confirmar devolución del préstamo #${prestamo.id}?`)) return
  try {
    await api.patch(`/prestamos/${prestamo.id}/devolver`, { observaciones: prestamo.observaciones || null })
    await cargarPrestamos()
  } catch (respuesta) {
    error.value = respuesta.response?.data?.detail || 'No se pudo registrar la devolución.'
  }
}

function formatoFecha(fecha) {
  return new Date(fecha).toLocaleDateString('es-VE')
}

onMounted(cargarPrestamos)
</script>

<template>
  <Navbar />
  <main class="contenido">
    <div class="encabezado-vista">
      <div><p class="etiqueta">Control de salidas</p><h1>Equipos prestados</h1></div>
      <RouterLink class="btn-primario" to="/prestamos/nuevo">Nueva solicitud</RouterLink>
    </div>
    <section class="barra-seguimiento tarjeta-sombra">
      <strong>{{ prestamosVisibles.length }} préstamos</strong>
      <input v-model="filtro" class="input-form" placeholder="Buscar por actividad, persona o equipo" />
    </section>
    <p v-if="error" class="mensaje-error">{{ error }}</p>
    <div class="tabla-contenedor tarjeta-sombra">
      <table>
        <thead><tr><th>Actividad</th><th>Responsable</th><th>Equipos</th><th>Fechas</th><th>Estado</th><th>Acción</th></tr></thead>
        <tbody>
          <tr v-if="cargando"><td colspan="6" class="celda-centrada">Cargando préstamos...</td></tr>
          <tr v-else-if="!prestamosVisibles.length"><td colspan="6" class="celda-centrada">No hay préstamos para mostrar.</td></tr>
          <tr v-for="prestamo in prestamosVisibles" :key="prestamo.id">
            <td><strong>{{ prestamo.actividad }}</strong><div class="subtexto-custodio">{{ prestamo.descripcion || 'Sin descripción' }}</div></td>
            <td>{{ prestamo.custodio_solicitante }}</td>
            <td><ul class="lista-equipos"><li v-for="equipo in prestamo.equipos_nombres" :key="equipo">{{ equipo }}</li></ul></td>
            <td>{{ formatoFecha(prestamo.fecha_inicio) }} al {{ formatoFecha(prestamo.fecha_fin) }}<div class="subtexto-custodio">{{ prestamo.dias }} día(s)</div></td>
            <td><span :class="['estado-badge', `estado-${prestamo.estado_temporal_equipo.toLowerCase()}`]">{{ prestamo.estado_temporal_equipo }}</span></td>
            <td><button v-if="puedeDevolver && prestamo.estado_temporal_equipo === 'Ocupado'" class="btn-secundario btn-pequeno" type="button" @click="devolver(prestamo)">Registrar devolución</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </main>
</template>

<style scoped>
.barra-seguimiento { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 1rem 1.25rem; margin-bottom: 1rem; }
.barra-seguimiento .input-form { max-width: 360px; }
.lista-equipos { margin: 0; padding-left: 1rem; }
@media (max-width: 640px) { .barra-seguimiento { align-items: stretch; flex-direction: column; } .barra-seguimiento .input-form { max-width: none; } }
</style>
