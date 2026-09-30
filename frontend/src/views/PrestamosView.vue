<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import Navbar from '../components/Navbar.vue'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const prestamos = ref([])
const cargando = ref(true)
const error = ref('')
const mensajeAccion = ref('')

// Filtros y pestañas
const pestanaActiva = ref('todos') // 'todos', 'olvidados', 'activos', 'devueltos', 'pendientes'
const filtro = ref('')

// Paginación
const paginaActual = ref(1)
const prestamosPorPagina = ref(10)

// Modal de devolución
const modalDevolucion = ref({
  abierto: false,
  prestamo: null,
  observaciones: '',
  procesando: false,
})

const puedeDevolver = computed(() => ['TECNICO', 'COORDINADOR', 'SUPERADMIN'].includes(auth.rol))
const puedeDecidir = computed(() => ['COORDINADOR', 'SUPERADMIN'].includes(auth.rol))

async function cargarPrestamos() {
  cargando.value = true
  error.value = ''
  try {
    const { data } = await api.get('/prestamos')
    prestamos.value = data
  } catch (respuesta) {
    error.value = respuesta.response?.data?.detail || 'No se pudieron cargar los préstamos.'
  } finally {
    cargando.value = false
  }
}

// Clasificaciones de préstamos
const prestamosOlvidados = computed(() => {
  return prestamos.value.filter((p) => p.estado_temporal_equipo === 'Olvidado')
})

const prestamosActivos = computed(() => {
  return prestamos.value.filter((p) => p.estado_temporal_equipo === 'Ocupado')
})

const prestamosDevueltos = computed(() => {
  return prestamos.value.filter((p) => p.estado_temporal_equipo === 'Devuelto')
})

const prestamosPendientes = computed(() => {
  return prestamos.value.filter(
    (p) => p.estado_solicitud === 'Pendiente' || p.estado_temporal_equipo === 'Pendiente'
  )
})

// Total de equipos físicos que están actualmente fuera (en curso o atrasados)
const totalEquiposFuera = computed(() => {
  const enLaCalle = prestamos.value.filter(
    (p) => p.estado_temporal_equipo === 'Ocupado' || p.estado_temporal_equipo === 'Olvidado'
  )
  return enLaCalle.reduce((acc, p) => acc + (p.equipos_ids?.length || 1), 0)
})

// Filtrado según pestaña y término de búsqueda
const prestamosFiltrados = computed(() => {
  let lista = prestamos.value

  // Filtro por pestaña
  if (pestanaActiva.value === 'olvidados') {
    lista = prestamosOlvidados.value
  } else if (pestanaActiva.value === 'activos') {
    lista = prestamos.value.filter((p) => p.estado_temporal_equipo === 'Ocupado' || p.estado_temporal_equipo === 'Olvidado')
  } else if (pestanaActiva.value === 'devueltos') {
    lista = prestamosDevueltos.value
  } else if (pestanaActiva.value === 'pendientes') {
    lista = prestamosPendientes.value
  }

  // Filtro por texto de búsqueda
  const termino = filtro.value.trim().toLowerCase()
  if (!termino) return lista

  return lista.filter((prestamo) => {
    return [
      prestamo.actividad,
      prestamo.custodio_solicitante,
      prestamo.descripcion,
      prestamo.observaciones,
      prestamo.estado_temporal_equipo,
      ...(prestamo.equipos_nombres || []),
    ].some((valor) => String(valor || '').toLowerCase().includes(termino))
  })
})

// Paginación
const totalPaginas = computed(() =>
  Math.max(1, Math.ceil(prestamosFiltrados.value.length / prestamosPorPagina.value))
)
const indiceInicio = computed(() => (paginaActual.value - 1) * prestamosPorPagina.value)
const indiceFin = computed(() =>
  Math.min(indiceInicio.value + prestamosPorPagina.value, prestamosFiltrados.value.length)
)

const prestamosPaginados = computed(() => {
  return prestamosFiltrados.value.slice(indiceInicio.value, indiceFin.value)
})

const paginasPaginador = computed(() => {
  const total = totalPaginas.value
  const actual = paginaActual.value
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }
  if (actual <= 4) {
    return [1, 2, 3, 4, 5, '...', total]
  }
  if (actual >= total - 3) {
    return [1, '...', total - 4, total - 3, total - 2, total - 1, total]
  }
  return [1, '...', actual - 1, actual, actual + 1, '...', total]
})

function cambiarPagina(pagina) {
  if (pagina === '...') return
  paginaActual.value = Math.min(Math.max(1, Number(pagina)), totalPaginas.value)
}

function cambiarPestana(pestana) {
  pestanaActiva.value = pestana
  paginaActual.value = 1
}

function reiniciarPagina() {
  paginaActual.value = 1
}

// Modal y proceso de devolución
function abrirModalDevolucion(prestamo) {
  modalDevolucion.value = {
    abierto: true,
    prestamo,
    observaciones: prestamo.observaciones ? `Previo: ${prestamo.observaciones} | Devolución: ` : '',
    procesando: false,
  }
}

function cerrarModalDevolucion() {
  modalDevolucion.value.abierto = false
  modalDevolucion.value.prestamo = null
}

async function confirmarDevolucion() {
  const p = modalDevolucion.value.prestamo
  if (!p) return

  modalDevolucion.value.procesando = true
  try {
    await api.patch(`/prestamos/${p.id}/devolver`, {
      observaciones: modalDevolucion.value.observaciones.trim() || p.observaciones || null,
    })
    mensajeAccion.value = `¡Préstamo #${p.id} devuelto con éxito! Los equipos quedaron liberados en el inventario.`
    cerrarModalDevolucion()
    await cargarPrestamos()
    setTimeout(() => {
      mensajeAccion.value = ''
    }, 5000)
  } catch (respuesta) {
    error.value = respuesta.response?.data?.detail || 'No se pudo registrar la devolución del préstamo.'
  } finally {
    modalDevolucion.value.procesando = false
  }
}

// Aprobación o rechazo de solicitudes pendientes
async function decidirSolicitud(prestamoId, decision) {
  try {
    await api.patch(`/prestamos/${prestamoId}/decision`, { estado_solicitud: decision })
    mensajeAccion.value = `Solicitud #${prestamoId} marcada como "${decision}".`
    await cargarPrestamos()
    setTimeout(() => {
      mensajeAccion.value = ''
    }, 4000)
  } catch (respuesta) {
    error.value = respuesta.response?.data?.detail || 'No se pudo actualizar la solicitud.'
  }
}

// Formato de fechas y cálculo de días
function formatoFecha(fecha) {
  if (!fecha) return 'Sin fecha'
  return new Date(fecha).toLocaleDateString('es-VE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

function calcularDetallePlazo(prestamo) {
  if (prestamo.estado_temporal_equipo === 'Devuelto') {
    return { clase: 'plazo-devuelto', texto: '✅ Devuelto al inventario' }
  }
  if (prestamo.estado_temporal_equipo === 'Olvidado') {
    const fin = new Date(prestamo.fecha_fin)
    const hoy = new Date()
    const diffDias = Math.max(1, Math.round((hoy - fin) / (1000 * 60 * 60 * 24)))
    return {
      clase: 'plazo-olvidado',
      texto: `🚨 ¡Vencido hace ${diffDias} día${diffDias > 1 ? 's' : ''}! (Olvidado)`,
    }
  }
  if (prestamo.estado_temporal_equipo === 'Ocupado') {
    const fin = new Date(prestamo.fecha_fin)
    const hoy = new Date()
    const diffDias = Math.round((fin - hoy) / (1000 * 60 * 60 * 24))
    if (diffDias <= 0) {
      return { clase: 'plazo-hoy', texto: '⚠️ Vence hoy' }
    }
    return {
      clase: 'plazo-ocupado',
      texto: `⏳ Quedan ${diffDias} día${diffDias > 1 ? 's' : ''} de uso`,
    }
  }
  if (prestamo.estado_temporal_equipo === 'Apartado') {
    return { clase: 'plazo-apartado', texto: '📅 Préstamo programado' }
  }
  return { clase: 'plazo-pendiente', texto: '🟡 Solicitud pendiente' }
}

onMounted(cargarPrestamos)
</script>

<template>
  <Navbar />
  <main class="contenido prestamos-vista">
    <!-- Encabezado de la Vista -->
    <div class="encabezado-vista">
      <div>
        <p class="etiqueta">Control de salidas y préstamos</p>
        <h1>Equipos Prestados y Control de Salidas</h1>
      </div>
      <div class="acciones-cabecera">
        <RouterLink class="btn-primario" to="/prestamos/nuevo">
          + Generar nuevo préstamo
        </RouterLink>
        <RouterLink class="btn-secundario" to="/prestamos/calendario">
          📅 Ver en calendario
        </RouterLink>
      </div>
    </div>

    <!-- Banner de Notificación de Préstamos Olvidados -->
    <div v-if="prestamosOlvidados.length > 0" class="alerta-olvidados tarjeta-sombra">
      <div class="icono-alerta-olvidados">🚨</div>
      <div class="contenido-alerta-olvidados">
        <h3>
          ¡Notificación de Préstamos Olvidados! ({{ prestamosOlvidados.length }} préstamo{{ prestamosOlvidados.length > 1 ? 's' : '' }} vencido{{ prestamosOlvidados.length > 1 ? 's' : '' }})
        </h3>
        <p>
          Los siguientes préstamos han sobrepasado su fecha prevista de entrega y no han sido devueltos al inventario.
        </p>
        <div class="lista-olvidados-resumen">
          <span
            v-for="p in prestamosOlvidados"
            :key="p.id"
            class="chip-olvidado-alerta"
            @click="cambiarPestana('olvidados')"
          >
            👤 <strong>{{ p.custodio_solicitante }}</strong>: {{ p.actividad }} ({{ p.equipos_nombres?.length || 1 }} equipo{{ (p.equipos_nombres?.length || 1) > 1 ? 's' : '' }})
          </span>
        </div>
      </div>
      <button
        type="button"
        class="btn-peligro btn-pequeno btn-ver-olvidados"
        @click="cambiarPestana('olvidados')"
      >
        Ver solo olvidados
      </button>
    </div>

    <!-- Tarjetas KPIs de Resumen -->
    <section class="kpis-prestamos">
      <div class="kpi-tarjeta kpi-total-fuera" @click="cambiarPestana('activos')">
        <div class="kpi-icono">📦</div>
        <div class="kpi-datos">
          <span class="kpi-numero">{{ totalEquiposFuera }}</span>
          <span class="kpi-label">Equipos prestados fuera</span>
        </div>
      </div>

      <div class="kpi-tarjeta kpi-en-curso" @click="cambiarPestana('activos')">
        <div class="kpi-icono">⏳</div>
        <div class="kpi-datos">
          <span class="kpi-numero">{{ prestamosActivos.length }}</span>
          <span class="kpi-label">Préstamos en curso</span>
        </div>
      </div>

      <div
        class="kpi-tarjeta kpi-alerta-olvidados"
        :class="{ 'kpi-con-olvidados': prestamosOlvidados.length > 0 }"
        @click="cambiarPestana('olvidados')"
      >
        <div class="kpi-icono">🚨</div>
        <div class="kpi-datos">
          <span class="kpi-numero">{{ prestamosOlvidados.length }}</span>
          <span class="kpi-label">Olvidados / Atrasados</span>
        </div>
      </div>

      <div class="kpi-tarjeta kpi-devueltos" @click="cambiarPestana('devueltos')">
        <div class="kpi-icono">✅</div>
        <div class="kpi-datos">
          <span class="kpi-numero">{{ prestamosDevueltos.length }}</span>
          <span class="kpi-label">Devueltos finalizados</span>
        </div>
      </div>
    </section>

    <!-- Feedback de acciones -->
    <p v-if="mensajeAccion" class="mensaje-exito-flotante">✅ {{ mensajeAccion }}</p>
    <p v-if="error" class="mensaje-error">⚠️ {{ error }}</p>

    <!-- Panel de Navegación por Pestañas y Búsqueda -->
    <section class="panel-control-prestamos tarjeta-sombra">
      <div class="pestanas-estados">
        <button
          type="button"
          class="pestana-btn"
          :class="{ 'pestana-activa': pestanaActiva === 'todos' }"
          @click="cambiarPestana('todos')"
        >
          Todos ({{ prestamos.length }})
        </button>

        <button
          type="button"
          class="pestana-btn pestana-btn-olvidados"
          :class="{ 'pestana-activa': pestanaActiva === 'olvidados' }"
          @click="cambiarPestana('olvidados')"
        >
          🚨 Olvidados / Atrasados
          <span v-if="prestamosOlvidados.length" class="badge-contador-olvidados">
            {{ prestamosOlvidados.length }}
          </span>
        </button>

        <button
          type="button"
          class="pestana-btn"
          :class="{ 'pestana-activa': pestanaActiva === 'activos' }"
          @click="cambiarPestana('activos')"
        >
          ⏳ En Préstamo (Activos)
        </button>

        <button
          type="button"
          class="pestana-btn"
          :class="{ 'pestana-activa': pestanaActiva === 'devueltos' }"
          @click="cambiarPestana('devueltos')"
        >
          ✅ Devueltos (Historial)
        </button>

        <button
          v-if="prestamosPendientes.length > 0"
          type="button"
          class="pestana-btn"
          :class="{ 'pestana-activa': pestanaActiva === 'pendientes' }"
          @click="cambiarPestana('pendientes')"
        >
          🟡 Pendientes ({{ prestamosPendientes.length }})
        </button>
      </div>

      <div class="barra-busqueda-prestamos">
        <input
          v-model="filtro"
          class="input-form input-buscar-prestamo"
          placeholder="🔍 Buscar por actividad, custodio / técnico o equipo..."
          @input="reiniciarPagina"
        />

        <div class="selector-prestamos-pagina">
          <label for="selectPaginasPrestamo">Mostrar:</label>
          <select
            id="selectPaginasPrestamo"
            v-model="prestamosPorPagina"
            class="input-form select-tamano"
            @change="reiniciarPagina"
          >
            <option :value="5">5 por pág.</option>
            <option :value="10">10 por pág.</option>
            <option :value="20">20 por pág.</option>
            <option :value="50">50 por pág.</option>
          </select>
        </div>
      </div>
    </section>

    <!-- Tabla Detallada de Préstamos -->
    <div class="tabla-contenedor tarjeta-sombra">
      <table>
        <thead>
          <tr>
            <th>Actividad & Trabajo</th>
            <th>¿A quién se le prestó?</th>
            <th>¿Qué equipos están prestados?</th>
            <th>¿Cuántos días serán? & Plazo</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="cargando">
            <td colspan="6" class="celda-centrada">Cargando préstamos...</td>
          </tr>
          <tr v-else-if="!prestamosFiltrados.length">
            <td colspan="6" class="celda-centrada">
              No se encontraron préstamos en esta categoría o con los términos buscados.
            </td>
          </tr>
          <tr
            v-for="prestamo in prestamosPaginados"
            :key="prestamo.id"
            :class="{ 'fila-olvidado': prestamo.estado_temporal_equipo === 'Olvidado' }"
          >
            <!-- 1. Actividad -->
            <td class="col-actividad">
              <strong class="titulo-actividad">{{ prestamo.actividad }}</strong>
              <div v-if="prestamo.descripcion" class="descripcion-prestamo">
                {{ prestamo.descripcion }}
              </div>
              <div v-if="prestamo.observaciones" class="observaciones-prestamo">
                📝 <em>{{ prestamo.observaciones }}</em>
              </div>
            </td>

            <!-- 2. Solicitante / Custodio -->
            <td class="col-solicitante">
              <div class="avatar-solicitante">
                <span class="icono-persona">👤</span>
                <div>
                  <strong>{{ prestamo.custodio_solicitante }}</strong>
                  <div class="sub-solicitante">Solicitante</div>
                </div>
              </div>
            </td>

            <!-- 3. Equipos Prestados -->
            <td class="col-equipos-prestados">
              <div class="etiqueta-cant-equipos">
                <strong>{{ prestamo.equipos_nombres?.length || 1 }} equipo{{ (prestamo.equipos_nombres?.length || 1) > 1 ? 's' : '' }}:</strong>
              </div>
              <ul class="lista-chips-equipos">
                <li
                  v-for="(nombreEq, idx) in prestamo.equipos_nombres"
                  :key="idx"
                  class="badge-equipo-item"
                >
                  💻 {{ nombreEq }}
                </li>
              </ul>
            </td>

            <!-- 4. Duración y Plazos -->
            <td class="col-fechas-dias">
              <div class="duracion-destacada">
                <strong>{{ prestamo.dias }} día{{ prestamo.dias > 1 ? 's' : '' }}</strong> de préstamo
              </div>
              <div class="rango-fechas">
                {{ formatoFecha(prestamo.fecha_inicio) }} ➔ {{ formatoFecha(prestamo.fecha_fin) }}
              </div>
              <div :class="['indicador-plazo', calcularDetallePlazo(prestamo).clase]">
                {{ calcularDetallePlazo(prestamo).texto }}
              </div>
            </td>

            <!-- 5. Estado Temporal -->
            <td>
              <span
                :class="[
                  'estado-badge',
                  `estado-${(prestamo.estado_temporal_equipo || '').toLowerCase()}`,
                ]"
              >
                {{ prestamo.estado_temporal_equipo }}
              </span>
            </td>

            <!-- 6. Acciones -->
            <td class="col-acciones-prestamo">
              <!-- Botón Devolver para préstamos en curso o vencidos/olvidados -->
              <button
                v-if="puedeDevolver && (prestamo.estado_temporal_equipo === 'Ocupado' || prestamo.estado_temporal_equipo === 'Olvidado')"
                class="btn-secundario btn-pequeno btn-devolver-destacado"
                :class="{ 'btn-devolver-urgente': prestamo.estado_temporal_equipo === 'Olvidado' }"
                type="button"
                @click="abrirModalDevolucion(prestamo)"
              >
                ✅ Registrar devolución
              </button>

              <!-- Opciones de Aprobación para Coordinador en solicitudes pendientes -->
              <div
                v-else-if="puedeDecidir && (prestamo.estado_solicitud === 'Pendiente' || prestamo.estado_temporal_equipo === 'Pendiente')"
                class="botones-decision"
              >
                <button
                  class="btn-primario btn-pequeno"
                  type="button"
                  @click="decidirSolicitud(prestamo.id, 'Aprobada')"
                >
                  Aprobar
                </button>
                <button
                  class="btn-peligro btn-pequeno"
                  type="button"
                  @click="decidirSolicitud(prestamo.id, 'Rechazada')"
                >
                  Rechazar
                </button>
              </div>

              <span v-else-if="prestamo.estado_temporal_equipo === 'Devuelto'" class="texto-devuelto-final">
                Devuelto
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Paginación completa con elipsis: 1...2...3..4..5...6... -> -->
    <nav v-if="totalPaginas > 1" class="paginacion" aria-label="Paginación de préstamos">
      <button
        class="btn-secundario btn-pequeno btn-nav"
        type="button"
        :disabled="paginaActual === 1"
        title="Primera página"
        @click="cambiarPagina(1)"
      >
        ««
      </button>
      <button
        class="btn-secundario btn-pequeno btn-nav"
        type="button"
        :disabled="paginaActual === 1"
        title="Página anterior"
        @click="cambiarPagina(paginaActual - 1)"
      >
        ← Anterior
      </button>

      <div class="numeros-paginas">
        <template v-for="(elem, idx) in paginasPaginador" :key="idx">
          <span v-if="elem === '...'" class="paginacion-elipsis">...</span>
          <button
            v-else
            class="btn-secundario btn-pequeno pagina"
            :class="{ 'pagina-activa': elem === paginaActual }"
            type="button"
            :aria-current="elem === paginaActual ? 'page' : undefined"
            @click="cambiarPagina(elem)"
          >
            {{ elem }}
          </button>
        </template>
      </div>

      <button
        class="btn-secundario btn-pequeno btn-nav"
        type="button"
        :disabled="paginaActual === totalPaginas"
        title="Página siguiente"
        @click="cambiarPagina(paginaActual + 1)"
      >
        Siguiente →
      </button>
      <button
        class="btn-secundario btn-pequeno btn-nav"
        type="button"
        :disabled="paginaActual === totalPaginas"
        title="Última página"
        @click="cambiarPagina(totalPaginas)"
      >
        »»
      </button>

      <span class="info-pagina-actual">
        Mostrando <strong>{{ prestamosFiltrados.length ? indiceInicio + 1 : 0 }} - {{ indiceFin }}</strong> de <strong>{{ prestamosFiltrados.length }}</strong> préstamos
      </span>
    </nav>

    <!-- Modal para Registrar Devolución -->
    <div
      v-if="modalDevolucion.abierto"
      class="modal-fondo"
      @click.self="cerrarModalDevolucion"
    >
      <div class="modal-tarjeta tarjeta-sombra">
        <button class="cerrar-modal" type="button" @click="cerrarModalDevolucion">×</button>
        <div class="modal-encabezado">
          <span class="etiqueta">Retorno de inventario</span>
          <h2>Registrar Devolución de Equipos</h2>
          <p class="modal-subtexto">
            Confirme la recepción de los equipos prestados para reintegrarlos como <strong>Operativos</strong> al inventario.
          </p>
        </div>

        <div v-if="modalDevolucion.prestamo" class="modal-cuerpo">
          <div class="resumen-modal-prestamo">
            <div>
              <strong>Actividad:</strong> {{ modalDevolucion.prestamo.actividad }}
            </div>
            <div>
              <strong>Responsable:</strong> {{ modalDevolucion.prestamo.custodio_solicitante }}
            </div>
            <div class="modal-equipos-lista">
              <strong>Equipos a reintegrar:</strong>
              <ul>
                <li v-for="eq in modalDevolucion.prestamo.equipos_nombres" :key="eq">
                  {{ eq }}
                </li>
              </ul>
            </div>
          </div>

          <label class="campo-modal">
            <span>Observaciones de entrega / Estado de devolución:</span>
            <textarea
              v-model="modalDevolucion.observaciones"
              class="input-form"
              rows="3"
              placeholder="Indique si los equipos fueron devueltos en buen estado, si faltó algún cable, etc."
            ></textarea>
          </label>
        </div>

        <div class="modal-acciones">
          <button class="btn-secundario" type="button" @click="cerrarModalDevolucion">
            Cancelar
          </button>
          <button
            class="btn-primario"
            type="button"
            :disabled="modalDevolucion.procesando"
            @click="confirmarDevolucion"
          >
            {{ modalDevolucion.procesando ? 'Procesando...' : 'Confirmar Devolución' }}
          </button>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.prestamos-vista {
  max-width: 1280px;
  margin: 0 auto;
}
.acciones-cabecera {
  display: flex;
  gap: 0.5rem;
}

/* Banner de alerta de préstamos olvidados */
.alerta-olvidados {
  background: #fef2f2;
  border: 2px solid #ef4444;
  border-radius: 10px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15);
}
.icono-alerta-olvidados {
  font-size: 2rem;
  flex-shrink: 0;
}
.contenido-alerta-olvidados {
  flex: 1;
}
.contenido-alerta-olvidados h3 {
  margin: 0 0 0.25rem 0;
  color: #991b1b;
  font-size: 1.05rem;
}
.contenido-alerta-olvidados p {
  margin: 0 0 0.5rem 0;
  color: #7f1d1d;
  font-size: 0.88rem;
}
.lista-olvidados-resumen {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}
.chip-olvidado-alerta {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
  border-radius: 6px;
  padding: 0.2rem 0.5rem;
  font-size: 0.8rem;
  cursor: pointer;
}
.chip-olvidado-alerta:hover {
  background: #fecaca;
}
.btn-ver-olvidados {
  white-space: nowrap;
}

/* Tarjetas KPIs */
.kpis-prestamos {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.kpi-tarjeta {
  background: #ffffff;
  border-radius: 8px;
  padding: 1rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  border: 1px solid #e2e8f0;
}
.kpi-tarjeta:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.08);
}
.kpi-icono {
  font-size: 1.8rem;
}
.kpi-datos {
  display: flex;
  flex-direction: column;
}
.kpi-numero {
  font-size: 1.6rem;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.1;
}
.kpi-label {
  font-size: 0.82rem;
  color: #64748b;
  font-weight: 500;
}
.kpi-con-olvidados {
  border-color: #ef4444;
  background: #fff5f5;
}
.kpi-con-olvidados .kpi-numero {
  color: #dc2626;
}

/* Panel de Filtros y Pestañas */
.panel-control-prestamos {
  background: #ffffff;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.pestanas-estados {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 0.75rem;
}
.pestana-btn {
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 0.45rem 0.9rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  transition: all 0.15s ease;
}
.pestana-btn:hover {
  background: #f1f5f9;
  color: #0f172a;
}
.pestana-activa {
  background: var(--azul-institucional, #0284c7) !important;
  color: #ffffff !important;
  border-color: transparent !important;
}
.pestana-btn-olvidados {
  color: #b91c1c;
}
.badge-contador-olvidados {
  background: #ef4444;
  color: white;
  border-radius: 10px;
  padding: 0.1rem 0.45rem;
  font-size: 0.75rem;
  font-weight: 700;
}
.barra-busqueda-prestamos {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}
.input-buscar-prestamo {
  flex: 1;
  min-width: 260px;
}
.selector-prestamos-pagina {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #64748b;
}
.select-tamano {
  padding: 0.25rem 0.5rem;
  font-size: 0.85rem;
}

/* Tabla de Préstamos */
.fila-olvidado {
  background: #fff8f8;
}
.titulo-actividad {
  font-size: 0.95rem;
  color: #0f172a;
  display: block;
}
.descripcion-prestamo {
  font-size: 0.82rem;
  color: #475569;
  margin-top: 0.2rem;
}
.observaciones-prestamo {
  font-size: 0.78rem;
  color: #64748b;
  margin-top: 0.2rem;
}

.avatar-solicitante {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.icono-persona {
  font-size: 1.25rem;
}
.sub-solicitante {
  font-size: 0.75rem;
  color: #94a3b8;
}

.col-equipos-prestados {
  max-width: 280px;
}
.etiqueta-cant-equipos {
  font-size: 0.8rem;
  color: #475569;
  margin-bottom: 0.25rem;
}
.lista-chips-equipos {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.badge-equipo-item {
  background: #f1f5f9;
  border-radius: 4px;
  padding: 0.15rem 0.45rem;
  font-size: 0.8rem;
  color: #1e293b;
  border: 1px solid #e2e8f0;
}

.col-fechas-dias {
  font-size: 0.85rem;
}
.duracion-destacada {
  color: #0f172a;
  margin-bottom: 0.2rem;
}
.rango-fechas {
  font-size: 0.8rem;
  color: #64748b;
  margin-bottom: 0.35rem;
}
.indicador-plazo {
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  display: inline-block;
}
.plazo-devuelto {
  background: #f0fdf4;
  color: #166534;
}
.plazo-olvidado {
  background: #fee2e2;
  color: #991b1b;
  font-weight: 700;
  border: 1px solid #f87171;
}
.plazo-ocupado {
  background: #eff6ff;
  color: #1d4ed8;
}
.plazo-hoy {
  background: #fffbeb;
  color: #b45309;
  font-weight: 700;
}
.plazo-apartado {
  background: #f8fafc;
  color: #475569;
}
.plazo-pendiente {
  background: #fefce8;
  color: #854d0e;
}

/* Badges de estado */
.estado-badge {
  display: inline-block;
  padding: 0.25rem 0.6rem;
  border-radius: 12px;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: capitalize;
}
.estado-ocupado {
  background: #dbeafe;
  color: #1e40af;
}
.estado-olvidado {
  background: #dc2626;
  color: #ffffff;
  box-shadow: 0 2px 6px rgba(220, 38, 38, 0.4);
}
.estado-devuelto {
  background: #e2e8f0;
  color: #475569;
}
.estado-apartado {
  background: #e0f2fe;
  color: #0369a1;
}
.estado-pendiente {
  background: #fef3c7;
  color: #92400e;
}
.estado-rechazado {
  background: #fee2e2;
  color: #991b1b;
}

/* Acciones */
.btn-devolver-destacado {
  font-weight: 600;
}
.btn-devolver-urgente {
  background: #ef4444 !important;
  color: white !important;
  border-color: #dc2626 !important;
}
.btn-devolver-urgente:hover {
  background: #dc2626 !important;
}
.botones-decision {
  display: flex;
  gap: 0.35rem;
}
.texto-devuelto-final {
  color: #94a3b8;
  font-size: 0.85rem;
}

/* Paginación */
.paginacion {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-top: 1.5rem;
  padding-bottom: 2rem;
}
.numeros-paginas {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
.btn-nav {
  font-weight: 600;
  padding: 0.35rem 0.65rem;
}
.pagina {
  min-width: 2.3rem;
  height: 2.3rem;
  padding: 0;
  display: inline-flex;
  justify-content: center;
  align-items: center;
  font-weight: 500;
  border-radius: 6px;
  transition: all 0.15s ease-in-out;
}
.pagina-activa {
  color: white !important;
  background: var(--azul-institucional, #0284c7) !important;
  font-weight: 700;
  box-shadow: 0 2px 6px rgba(2, 132, 199, 0.35);
  border-color: transparent;
}
.paginacion-elipsis {
  padding: 0 0.35rem;
  color: #94a3b8;
  font-weight: 700;
  user-select: none;
}
.info-pagina-actual {
  font-size: 0.85rem;
  color: #64748b;
  margin-left: 0.75rem;
}
.paginacion button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* Modal Devolución */
.modal-fondo {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;
  padding: 1rem;
}
.modal-tarjeta {
  background: #ffffff;
  border-radius: 10px;
  max-width: 520px;
  width: 100%;
  padding: 1.75rem;
  position: relative;
  display: grid;
  gap: 1.25rem;
}
.cerrar-modal {
  position: absolute;
  top: 0.75rem;
  right: 1rem;
  border: none;
  background: transparent;
  font-size: 1.5rem;
  cursor: pointer;
  color: #64748b;
}
.modal-encabezado h2 {
  margin: 0.25rem 0 0.5rem 0;
  font-size: 1.25rem;
}
.modal-subtexto {
  color: #64748b;
  font-size: 0.88rem;
  margin: 0;
}
.resumen-modal-prestamo {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.85rem;
  font-size: 0.88rem;
  display: grid;
  gap: 0.4rem;
}
.modal-equipos-lista ul {
  margin: 0.25rem 0 0 1.2rem;
  padding: 0;
}
.campo-modal {
  display: grid;
  gap: 0.4rem;
  font-size: 0.88rem;
  font-weight: 600;
  color: #334155;
  margin-top: 0.5rem;
}
.modal-acciones {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.mensaje-exito-flotante {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

@media (max-width: 768px) {
  .barra-busqueda-prestamos {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
