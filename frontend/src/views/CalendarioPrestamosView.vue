<script setup>
import { computed, onMounted, ref } from 'vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'
import Navbar from '../components/Navbar.vue'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const eventos = ref([])
const seleccionado = ref(null)
const cargando = ref(true)
const error = ref('')
const puedeDecidir = computed(() => ['COORDINADOR', 'SUPERADMIN'].includes(auth.rol))
const opcionesCalendario = computed(() => ({
  plugins: [dayGridPlugin, interactionPlugin],
  initialView: 'dayGridMonth',
  locale: 'es',
  height: 'auto',
  eventDisplay: 'block',
  events: eventos.value,
  eventClick: (info) => { seleccionado.value = info.event },
}))

async function cargarEventos() {
  try {
    const { data } = await api.get('/prestamos/calendario/eventos')
    eventos.value = data
  } catch {
    error.value = 'No se pudo cargar el calendario de préstamos.'
  } finally {
    cargando.value = false
  }
}

async function decidir(estado) {
  try {
    await api.patch(`/prestamos/${seleccionado.value.id}/decision`, { estado_solicitud: estado })
    seleccionado.value = null
    await cargarEventos()
  } catch (respuesta) {
    error.value = respuesta.response?.data?.detail || 'No se pudo actualizar la solicitud.'
  }
}

function imprimirSolicitud() {
  window.print()
}

onMounted(cargarEventos)
</script>

<template>
  <Navbar />
  <main class="contenido calendario-vista">
    <div class="encabezado-vista">
      <div><p class="etiqueta">Disponibilidad y reservas</p><h1>Calendario de préstamos</h1></div>
      <RouterLink class="btn-primario" to="/prestamos/nuevo">Nueva solicitud</RouterLink>
    </div>
    <p v-if="error" class="mensaje-error">{{ error }}</p>
    <div v-if="cargando" class="tarjeta-sombra estado-carga">Cargando calendario...</div>
    <div v-else class="tarjeta-sombra calendario-panel"><FullCalendar :options="opcionesCalendario" /></div>
    <div v-if="seleccionado" class="modal-fondo" @click.self="seleccionado = null">
      <section class="modal-prestamo">
        <button class="cerrar-modal" type="button" aria-label="Cerrar" @click="seleccionado = null">×</button>
        <p class="etiqueta">Solicitud #{{ seleccionado.id }}</p>
        <h2>{{ seleccionado.extendedProps.equipo }}</h2>
        <p><strong>Estado:</strong> {{ seleccionado.extendedProps.estado || seleccionado.title.split('·').pop().trim() }}</p>
        <p><strong>Custodio:</strong> {{ seleccionado.extendedProps.custodio }}</p>
        <p><strong>Motivo:</strong> {{ seleccionado.extendedProps.motivo }}</p>
        <div class="datos-impresion">
          <p><strong>Inicio:</strong> {{ new Date(seleccionado.start).toLocaleString('es-VE') }}</p>
          <p><strong>Fin:</strong> {{ new Date(seleccionado.end).toLocaleString('es-VE') }}</p>
        </div>
        <button class="btn-secundario boton-imprimir" type="button" @click="imprimirSolicitud">Imprimir / Guardar PDF</button>
        <div v-if="puedeDecidir && (seleccionado.extendedProps.estado === 'Pendiente' || seleccionado.title.includes('Pendiente'))" class="acciones-modal">
          <button class="btn-primario" type="button" @click="decidir('Aprobada')">Aprobar</button>
          <button class="btn-peligro" type="button" @click="decidir('Rechazada')">Rechazar</button>
        </div>
      </section>
    </div>
  </main>
</template>

<style scoped>
.calendario-panel { padding: 1rem; background: #fff; }
.estado-carga { padding: 2rem; }
.modal-fondo { position: fixed; inset: 0; z-index: 10; display: grid; place-items: center; padding: 1rem; background: rgb(15 23 42 / .45); }
.modal-prestamo { position: relative; width: min(100%, 460px); padding: 1.5rem; background: #fff; border-radius: 8px; box-shadow: 0 20px 50px rgb(15 23 42 / .25); }
.cerrar-modal { position: absolute; top: .6rem; right: .8rem; border: 0; background: transparent; font-size: 1.6rem; cursor: pointer; }
.acciones-modal { display: flex; gap: .75rem; margin-top: 1.25rem; }
.boton-imprimir { margin-top: 1rem; width: 100%; }
.datos-impresion { border-top: 1px solid #e2e8f0; margin-top: 1rem; padding-top: .5rem; }
@media print {
  @page { size: A4; margin: 1.5cm; }
  :global(body) { background: #fff; }
  :global(.barra-navegacion),
  .encabezado-vista,
  .calendario-panel,
  .mensaje-error,
  .cerrar-modal,
  .boton-imprimir,
  .acciones-modal { display: none !important; }
  .calendario-vista { width: 100%; margin: 0; padding: 0; }
  .modal-fondo { position: static; display: block; padding: 0; background: #fff; }
  .modal-prestamo { width: 100%; padding: 0; border: 0; box-shadow: none; }
  .modal-prestamo::before { content: 'FUNDACITE SUCRE\\A Coordinación de Telemática\\A FICHA DE PRÉSTAMO DE EQUIPO'; white-space: pre; display: block; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 2px solid #124e78; color: #124e78; font-size: 1.1rem; font-weight: 700; line-height: 1.6; text-align: center; }
  .modal-prestamo h2 { color: #0b2d45; }
}
</style>
