<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '../components/Navbar.vue'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

// Datos del formulario
const formulario = ref({
  equipos_ids: [],
  solicitante: auth.username || '',
  fecha_inicio: '',
  fecha_fin: '',
  actividad: '',
  descripcion: '',
  observaciones: '',
  aprobarInmediato: ['TECNICO', 'COORDINADOR', 'SUPERADMIN'].includes(auth.rol),
})

const equipos = ref([])
const cargando = ref(true)
const enviando = ref(false)
const mensajeExito = ref('')
const error = ref('')

// Filtros para selección de equipos
const busquedaEquipo = ref('')
const filtroTipo = ref('')

// Mini-calendario estado
const fechaCalendario = ref(new Date())
const nombresMeses = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
]
const nombresDias = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sá', 'Do']

const mesActualNombre = computed(() => nombresMeses[fechaCalendario.value.getMonth()])
const anioActual = computed(() => fechaCalendario.value.getFullYear())

// Generación de la cuadrícula de días para el mini-calendario
const diasMatriz = computed(() => {
  const anio = fechaCalendario.value.getFullYear()
  const mes = fechaCalendario.value.getMonth()
  const primerDiaMes = new Date(anio, mes, 1)
  const ultimoDiaMes = new Date(anio, mes + 1, 0)

  // Ajuste a Lunes = 0, Domingo = 6
  let primerDiaSemana = primerDiaMes.getDay() - 1
  if (primerDiaSemana === -1) primerDiaSemana = 6

  const dias = []
  const hoyIso = new Date().toISOString().split('T')[0]

  // Días del mes anterior para rellenar
  const ultimoDiaMesAnt = new Date(anio, mes, 0).getDate()
  for (let i = primerDiaSemana - 1; i >= 0; i--) {
    const diaNum = ultimoDiaMesAnt - i
    const f = new Date(anio, mes - 1, diaNum)
    const iso = f.toISOString().split('T')[0]
    dias.push({ numero: diaNum, fechaIso: iso, esMesActual: false, esPasado: iso < hoyIso })
  }

  // Días del mes actual
  for (let d = 1; d <= ultimoDiaMes.getDate(); d++) {
    const f = new Date(anio, mes, d)
    const iso = `${anio}-${String(mes + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    dias.push({ numero: d, fechaIso: iso, esMesActual: true, esPasado: iso < hoyIso })
  }

  // Completar cuadrícula a múltiplos de 7
  const restantes = (7 - (dias.length % 7)) % 7
  for (let r = 1; r <= restantes; r++) {
    const f = new Date(anio, mes + 1, r)
    const iso = f.toISOString().split('T')[0]
    dias.push({ numero: r, fechaIso: iso, esMesActual: false, esPasado: iso < hoyIso })
  }

  return dias
})

function mesAnterior() {
  const nueva = new Date(fechaCalendario.value)
  nueva.setMonth(nueva.getMonth() - 1)
  fechaCalendario.value = nueva
}

function mesSiguiente() {
  const nueva = new Date(fechaCalendario.value)
  nueva.setMonth(nueva.getMonth() + 1)
  fechaCalendario.value = nueva
}

function irAHoy() {
  fechaCalendario.value = new Date()
}

// Selección de fechas en el mini-calendario
function clickDia(dia) {
  const fecha = dia.fechaIso
  if (!formulario.value.fecha_inicio || (formulario.value.fecha_inicio && formulario.value.fecha_fin)) {
    formulario.value.fecha_inicio = fecha
    formulario.value.fecha_fin = fecha
  } else if (formulario.value.fecha_inicio && !formulario.value.fecha_fin) {
    if (fecha < formulario.value.fecha_inicio) {
      formulario.value.fecha_fin = formulario.value.fecha_inicio
      formulario.value.fecha_inicio = fecha
    } else {
      formulario.value.fecha_fin = fecha
    }
  }
}

function esDiaInicio(iso) {
  return formulario.value.fecha_inicio === iso
}

function esDiaFin(iso) {
  return formulario.value.fecha_fin === iso
}

function estaEnRango(iso) {
  if (!formulario.value.fecha_inicio || !formulario.value.fecha_fin) return false
  return iso > formulario.value.fecha_inicio && iso < formulario.value.fecha_fin
}

function esHoy(iso) {
  return iso === new Date().toISOString().split('T')[0]
}

// Botones de presets de duración
function aplicarPreset(dias) {
  const hoy = new Date()
  const inicioIso = hoy.toISOString().split('T')[0]
  const fin = new Date(hoy)
  fin.setDate(fin.getDate() + (dias - 1))
  const finIso = fin.toISOString().split('T')[0]

  formulario.value.fecha_inicio = inicioIso
  formulario.value.fecha_fin = finIso
  fechaCalendario.value = new Date()
}

// Cálculo de días seleccionados
const diasCalculados = computed(() => {
  if (!formulario.value.fecha_inicio || !formulario.value.fecha_fin) return 0
  const d1 = new Date(`${formulario.value.fecha_inicio}T00:00:00`)
  const d2 = new Date(`${formulario.value.fecha_fin}T00:00:00`)
  const diff = Math.round((d2 - d1) / (1000 * 60 * 60 * 24))
  return Math.max(1, diff + 1)
})

// Carga y filtrado de equipos disponibles
async function cargarEquipos() {
  cargando.value = true
  try {
    const { data } = await api.get('/equipos/')
    equipos.value = data.filter((e) => e.estado === 'Operativo')
  } catch {
    error.value = 'No se pudieron cargar los equipos operativos disponibles.'
  } finally {
    cargando.value = false
  }
}

const tiposDisponibles = computed(() => {
  const setTipos = new Set()
  equipos.value.forEach((e) => {
    if (e.tipo?.nombre) setTipos.add(e.tipo.nombre)
  })
  return Array.from(setTipos)
})

const equiposFiltrados = computed(() => {
  const term = busquedaEquipo.value.toLowerCase().trim()
  const tipo = filtroTipo.value
  return equipos.value.filter((e) => {
    if (tipo && e.tipo?.nombre !== tipo) return false
    if (!term) return true
    return [
      e.bien_nacional,
      e.serial,
      e.modelo,
      e.marca?.nombre,
      e.marca_detalle,
      e.tipo?.nombre,
      e.ubicacion?.nombre,
    ].some((v) => String(v || '').toLowerCase().includes(term))
  })
})

const equiposSeleccionadosDetalle = computed(() => {
  return equipos.value.filter((e) => formulario.value.equipos_ids.includes(e.id))
})

function toggleEquipo(id) {
  const idx = formulario.value.equipos_ids.indexOf(id)
  if (idx > -1) {
    formulario.value.equipos_ids.splice(idx, 1)
  } else {
    formulario.value.equipos_ids.push(id)
  }
}

function removerEquipo(id) {
  formulario.value.equipos_ids = formulario.value.equipos_ids.filter((eId) => eId !== id)
}

function limpiarSeleccionEquipos() {
  formulario.value.equipos_ids = []
}

// Sugerencias de actividad
function setActividad(texto) {
  formulario.value.actividad = texto
}

// Envío del formulario
async function enviarSolicitud() {
  if (!formulario.value.fecha_inicio || !formulario.value.fecha_fin) {
    error.value = 'Por favor seleccione los días de uso en el calendario.'
    return
  }
  if (!formulario.value.equipos_ids.length) {
    error.value = 'Debe seleccionar al menos un equipo para el préstamo.'
    return
  }

  error.value = ''
  mensajeExito.value = ''
  enviando.value = true

  try {
    const fechaFin = new Date(`${formulario.value.fecha_fin}T00:00:00`)
    fechaFin.setDate(fechaFin.getDate() + 1)

    const estadoDeseado = formulario.value.aprobarInmediato ? 'Aprobada' : 'Pendiente'

    await api.post('/prestamos', {
      equipos_ids: formulario.value.equipos_ids.map(Number),
      custodio_solicitante: formulario.value.solicitante.trim() || auth.username,
      fecha_inicio: new Date(`${formulario.value.fecha_inicio}T00:00:00`).toISOString(),
      fecha_fin: fechaFin.toISOString(),
      estado_solicitud: estadoDeseado,
      actividad: formulario.value.actividad.trim(),
      motivo_uso: formulario.value.actividad.trim(),
      descripcion: formulario.value.descripcion?.trim() || null,
      observaciones: formulario.value.observaciones?.trim() || null,
    })

    mensajeExito.value = formulario.value.aprobarInmediato
      ? '¡Préstamo registrado y activado con éxito! Los equipos ya figuran como prestados.'
      : 'Solicitud enviada correctamente. Quedó registrada y pendiente de aprobación.'

    // Resetear formulario manteniendo defaults
    formulario.value.equipos_ids = []
    formulario.value.actividad = ''
    formulario.value.descripcion = ''
    formulario.value.observaciones = ''
  } catch (respuesta) {
    error.value = respuesta.response?.data?.detail || 'No se pudo registrar el préstamo. Verifique las fechas.'
  } finally {
    enviando.value = false
  }
}

onMounted(() => {
  cargarEquipos()
  aplicarPreset(1) // Por defecto: hoy
})
</script>

<template>
  <Navbar />
  <main class="contenido prestamo-solicitud-vista">
    <div class="encabezado-vista">
      <div>
        <p class="etiqueta">Control de salidas de equipos</p>
        <h1>Generar Préstamo de Equipos</h1>
      </div>
      <div class="acciones-cabecera">
        <RouterLink class="btn-secundario" to="/prestamos">
          📋 Ver equipos prestados
        </RouterLink>
        <RouterLink class="btn-secundario" to="/prestamos/calendario">
          📅 Ver calendario general
        </RouterLink>
      </div>
    </div>

    <form class="tarjeta-sombra formulario-prestamo-amplio" @submit.prevent="enviarSolicitud">
      <div class="seccion-intro">
        <p class="texto-intro">
          Seleccione los días en el <strong>calendario</strong>, elija los <strong>equipos</strong> a llevar y detalle la <strong>actividad</strong> técnica.
        </p>
      </div>

      <!-- Paso 1: Mini-Calendario para elegir días de uso -->
      <fieldset class="grupo-formulario">
        <legend class="titulo-paso">
          <span class="num-paso">1</span> Días de uso (Elige en el calendario)
        </legend>

        <div class="contenedor-calendario-fechas">
          <!-- Mini Calendario -->
          <div class="mini-calendario tarjeta-sombra">
            <div class="cal-cabecera">
              <button class="cal-nav-btn" type="button" title="Mes anterior" @click="mesAnterior">‹</button>
              <div class="cal-mes-anio" @click="irAHoy">
                <strong>{{ mesActualNombre }}</strong> {{ anioActual }}
              </div>
              <button class="cal-nav-btn" type="button" title="Mes siguiente" @click="mesSiguiente">›</button>
            </div>

            <div class="cal-dias-semana">
              <span v-for="d in nombresDias" :key="d">{{ d }}</span>
            </div>

            <div class="cal-grilla">
              <button
                v-for="(dia, idx) in diasMatriz"
                :key="idx"
                type="button"
                class="cal-dia"
                :class="{
                  'cal-dia-otro-mes': !dia.esMesActual,
                  'cal-dia-hoy': esHoy(dia.fechaIso),
                  'cal-dia-inicio': esDiaInicio(dia.fechaIso),
                  'cal-dia-fin': esDiaFin(dia.fechaIso),
                  'cal-dia-en-rango': estaEnRango(dia.fechaIso),
                }"
                @click="clickDia(dia)"
              >
                {{ dia.numero }}
              </button>
            </div>

            <div class="cal-pie">
              <button type="button" class="btn-cal-hoy" @click="irAHoy">Hoy</button>
              <span class="cal-leyenda">Haz clic en inicio y fin</span>
            </div>
          </div>

          <!-- Panel de selección rápida y resumen de días -->
          <div class="resumen-fechas-panel">
            <div class="presets-fechas">
              <span class="etiqueta-pequena">Duración rápida:</span>
              <div class="botones-presets">
                <button type="button" class="btn-preset" @click="aplicarPreset(1)">Solo hoy (1 día)</button>
                <button type="button" class="btn-preset" @click="aplicarPreset(2)">2 días</button>
                <button type="button" class="btn-preset" @click="aplicarPreset(3)">3 días</button>
                <button type="button" class="btn-preset" @click="aplicarPreset(7)">1 semana</button>
              </div>
            </div>

            <div class="entradas-manuales-fechas">
              <label class="campo-fecha">
                <span>Desde:</span>
                <input v-model="formulario.fecha_inicio" class="input-form" type="date" required />
              </label>
              <label class="campo-fecha">
                <span>Hasta:</span>
                <input v-model="formulario.fecha_fin" class="input-form" type="date" required />
              </label>
            </div>

            <div v-if="formulario.fecha_inicio && formulario.fecha_fin" class="badge-resumen-fechas">
              <div class="icono-resumen">📅</div>
              <div>
                <strong>Duración: {{ diasCalculados }} día{{ diasCalculados > 1 ? 's' : '' }}</strong>
                <div class="sub-fechas">
                  Del {{ formulario.fecha_inicio }} al {{ formulario.fecha_fin }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </fieldset>

      <!-- Paso 2: Selector interactivo de equipos -->
      <fieldset class="grupo-formulario">
        <legend class="titulo-paso">
          <span class="num-paso">2</span> Equipos que se llevarán
          <span v-if="formulario.equipos_ids.length" class="conteo-seleccionados-badge">
            {{ formulario.equipos_ids.length }} seleccionado(s)
          </span>
        </legend>

        <!-- Chips de equipos seleccionados -->
        <div v-if="equiposSeleccionadosDetalle.length" class="bandeja-seleccionados">
          <span class="etiqueta-seleccionados">Equipos a llevar:</span>
          <div class="chips-lista">
            <span
              v-for="eq in equiposSeleccionadosDetalle"
              :key="eq.id"
              class="chip-equipo"
            >
              <strong>{{ eq.bien_nacional }}</strong> · {{ eq.marca?.nombre || '' }} {{ eq.modelo || '' }}
              <button
                type="button"
                class="btn-quitar-chip"
                title="Quitar"
                @click="removerEquipo(eq.id)"
              >
                ×
              </button>
            </span>
          </div>
          <button
            type="button"
            class="btn-limpiar-chips"
            @click="limpiarSeleccionEquipos"
          >
            Limpiar selección
          </button>
        </div>

        <!-- Buscador y filtro para los equipos -->
        <div class="barra-filtro-equipos">
          <input
            v-model="busquedaEquipo"
            type="text"
            class="input-form input-buscar-eq"
            placeholder="🔍 Buscar por Bien Nacional, serial, marca o modelo..."
          />
          <select v-model="filtroTipo" class="input-form select-tipo-eq">
            <option value="">Todos los tipos</option>
            <option v-for="t in tiposDisponibles" :key="t" :value="t">{{ t }}</option>
          </select>
        </div>

        <!-- Lista scrolleable de equipos operativos con casillas -->
        <div class="grilla-equipos-seleccionable">
          <div v-if="cargando" class="estado-mensaje">Cargando equipos disponibles...</div>
          <div v-else-if="!equiposFiltrados.length" class="estado-mensaje">
            No hay equipos disponibles que coincidan con la búsqueda.
          </div>
          <div
            v-for="equipo in equiposFiltrados"
            :key="equipo.id"
            class="tarjeta-equipo-item"
            :class="{ 'equipo-elegido': formulario.equipos_ids.includes(equipo.id) }"
            @click="toggleEquipo(equipo.id)"
          >
            <input
              type="checkbox"
              class="check-equipo"
              :checked="formulario.equipos_ids.includes(equipo.id)"
              @click.stop="toggleEquipo(equipo.id)"
            />
            <div class="detalles-equipo-item">
              <div class="linea-superior-eq">
                <span class="bien-nacional-tag">{{ equipo.bien_nacional }}</span>
                <span v-if="equipo.tipo?.nombre" class="tipo-tag">{{ equipo.tipo.nombre }}</span>
              </div>
              <div class="marca-modelo-eq">
                <strong>{{ equipo.marca?.nombre === 'Otro' ? equipo.marca_detalle : equipo.marca?.nombre }}</strong>
                {{ equipo.modelo || '' }}
              </div>
              <div class="subinfo-eq">
                <span>📍 {{ equipo.ubicacion?.nombre || 'Sin oficina' }}</span>
                <span v-if="equipo.custodio">👤 {{ equipo.custodio }}</span>
              </div>
            </div>
          </div>
        </div>
      </fieldset>

      <!-- Paso 3: Actividad, Descripción y Observaciones -->
      <fieldset class="grupo-formulario">
        <legend class="titulo-paso">
          <span class="num-paso">3</span> Datos de la actividad y observaciones
        </legend>

        <!-- Responsable / Solicitante -->
        <div class="campo-formulario">
          <label for="solicitanteInput">
            <strong>Solicitante / Técnico responsable:</strong>
          </label>
          <input
            id="solicitanteInput"
            v-model="formulario.solicitante"
            class="input-form"
            type="text"
            required
            placeholder="Nombre de la persona o técnico que asume el préstamo"
          />
        </div>

        <!-- Actividad -->
        <div class="campo-formulario">
          <label for="actividadInput">
            <strong>Actividad:</strong>
            <span class="aclaratoria">¿Para qué labor se utilizarán los equipos?</span>
          </label>
          <input
            id="actividadInput"
            v-model="formulario.actividad"
            class="input-form"
            maxlength="200"
            required
            placeholder="Ej. Jornada de capacitación / Mantenimiento en Sede / Evento"
          />
          <div class="chips-sugerencias">
            <span class="sug-label">Sugerencias:</span>
            <button type="button" class="btn-sug" @click="setActividad('Soporte técnico y mantenimiento en sitio')">
              Soporte técnico
            </button>
            <button type="button" class="btn-sug" @click="setActividad('Jornada de capacitación formativa')">
              Capacitación
            </button>
            <button type="button" class="btn-sug" @click="setActividad('Presentación institucional / Evento')">
              Presentación / Evento
            </button>
            <button type="button" class="btn-sug" @click="setActividad('Uso temporal por control técnico')">
              Control técnico
            </button>
          </div>
        </div>

        <!-- Descripción -->
        <div class="campo-formulario">
          <label for="descripcionInput">
            <strong>Descripción del trabajo a realizar:</strong>
          </label>
          <textarea
            id="descripcionInput"
            v-model="formulario.descripcion"
            class="input-form"
            rows="3"
            maxlength="2000"
            placeholder="Describa brevemente la labor a ejecutar y el destino de los equipos..."
          ></textarea>
        </div>

        <!-- Observaciones -->
        <div class="campo-formulario">
          <label for="observacionesInput">
            <strong>Observaciones (accesorios, estado inicial, notas):</strong>
          </label>
          <textarea
            id="observacionesInput"
            v-model="formulario.observaciones"
            class="input-form"
            rows="2"
            maxlength="2000"
            placeholder="Ej. Se entrega con cargador original, cable HDMI y bolso de transporte."
          ></textarea>
        </div>

        <!-- Si es Técnico / Coordinador / Superadmin: Opción de activación inmediata -->
        <div
          v-if="['TECNICO', 'COORDINADOR', 'SUPERADMIN'].includes(auth.rol)"
          class="opcion-auto-aprobacion tarjeta-suave"
        >
          <label class="check-container">
            <input
              v-model="formulario.aprobarInmediato"
              type="checkbox"
            />
            <span class="check-texto">
              <strong>Aprobar y activar préstamo inmediatamente</strong>
              <small class="d-block subtexto">
                Como técnico/coordinador, el préstamo pasará directo a estado <em>En Préstamo (Ocupado)</em> sin requerir aprobación adicional.
              </small>
            </span>
          </label>
        </div>
      </fieldset>

      <!-- Mensajes de feedback -->
      <div v-if="mensajeExito" class="mensaje-alerta alerta-exito">
        <span>✅ {{ mensajeExito }}</span>
        <RouterLink class="btn-enlace-alerta" to="/prestamos">
          Ir a ver equipos prestados →
        </RouterLink>
      </div>

      <div v-if="error" class="mensaje-alerta alerta-error">
        <span>⚠️ {{ error }}</span>
      </div>

      <!-- Botón de acción principal -->
      <div class="pie-formulario">
        <button
          class="btn-primario btn-guardar-prestamo"
          type="submit"
          :disabled="enviando || cargando || !formulario.equipos_ids.length || !formulario.fecha_inicio"
        >
          {{ enviando ? 'Registrando...' : (formulario.aprobarInmediato ? '🚀 Registrar Préstamo en Curso' : '📨 Enviar Solicitud de Préstamo') }}
        </button>
      </div>
    </form>
  </main>
</template>

<style scoped>
.prestamo-solicitud-vista {
  max-width: 900px;
  margin: 0 auto;
}
.acciones-cabecera {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.formulario-prestamo-amplio {
  display: grid;
  gap: 1.5rem;
  padding: 1.75rem;
  background: #ffffff;
  border-radius: 10px;
}
.seccion-intro {
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f1f5f9;
}
.texto-intro {
  margin: 0;
  color: #475569;
  font-size: 0.95rem;
}
.grupo-formulario {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.25rem;
  margin: 0;
  display: grid;
  gap: 1rem;
}
.titulo-paso {
  font-weight: 700;
  color: #0f172a;
  padding: 0 0.5rem;
  font-size: 1.05rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.num-paso {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  width: 1.6rem;
  height: 1.6rem;
  background: var(--azul-institucional, #0284c7);
  color: #fff;
  border-radius: 50%;
  font-size: 0.85rem;
}
.conteo-seleccionados-badge {
  font-size: 0.8rem;
  font-weight: 600;
  background: #dbeafe;
  color: #1e40af;
  padding: 0.15rem 0.6rem;
  border-radius: 12px;
}

/* Mini Calendario */
.contenedor-calendario-fechas {
  display: grid;
  grid-template-columns: 310px 1fr;
  gap: 1.25rem;
  align-items: start;
}
.mini-calendario {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 0.75rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}
.cal-cabecera {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}
.cal-mes-anio {
  cursor: pointer;
  font-size: 0.95rem;
  color: #1e293b;
}
.cal-nav-btn {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  width: 1.8rem;
  height: 1.8rem;
  cursor: pointer;
  font-weight: bold;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
}
.cal-nav-btn:hover {
  background: #e2e8f0;
}
.cal-dias-semana {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  font-weight: 600;
  font-size: 0.78rem;
  color: #64748b;
  margin-bottom: 0.35rem;
}
.cal-grilla {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}
.cal-dia {
  height: 2.1rem;
  border: none;
  background: transparent;
  font-size: 0.85rem;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1e293b;
  transition: all 0.1s ease;
}
.cal-dia:hover:not(.cal-dia-otro-mes) {
  background: #e0f2fe;
}
.cal-dia-otro-mes {
  color: #cbd5e1;
}
.cal-dia-hoy {
  font-weight: 700;
  border: 1px solid #0284c7;
}
.cal-dia-inicio,
.cal-dia-fin {
  background: #0284c7 !important;
  color: #ffffff !important;
  font-weight: 700;
}
.cal-dia-en-rango {
  background: #bae6fd;
  color: #0369a1;
  border-radius: 0;
}
.cal-pie {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.5rem;
  padding-top: 0.4rem;
  border-top: 1px solid #f1f5f9;
}
.btn-cal-hoy {
  background: transparent;
  border: none;
  color: #0284c7;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
}
.cal-leyenda {
  font-size: 0.72rem;
  color: #94a3b8;
}

/* Panel de fechas y presets */
.resumen-fechas-panel {
  display: grid;
  gap: 1rem;
}
.etiqueta-pequena {
  font-size: 0.8rem;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 0.35rem;
  display: block;
}
.botones-presets {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}
.btn-preset {
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 0.35rem 0.7rem;
  font-size: 0.8rem;
  cursor: pointer;
  font-weight: 500;
  color: #334155;
}
.btn-preset:hover {
  background: #f1f5f9;
  border-color: #94a3b8;
}
.entradas-manuales-fechas {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}
.campo-fecha span {
  font-size: 0.8rem;
  color: #475569;
  font-weight: 600;
}
.badge-resumen-fechas {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  color: #166534;
}
.icono-resumen {
  font-size: 1.5rem;
}
.sub-fechas {
  font-size: 0.82rem;
  color: #15803d;
}

/* Chips de selección */
.bandeja-seleccionados {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 0.75rem;
  border-radius: 8px;
}
.etiqueta-seleccionados {
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
  margin-bottom: 0.4rem;
  display: block;
}
.chips-lista {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.4rem;
}
.chip-equipo {
  background: #e0f2fe;
  color: #0369a1;
  padding: 0.25rem 0.6rem;
  border-radius: 14px;
  font-size: 0.82rem;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}
.btn-quitar-chip {
  background: transparent;
  border: none;
  font-weight: bold;
  font-size: 1.1rem;
  cursor: pointer;
  line-height: 1;
  color: #0284c7;
}
.btn-limpiar-chips {
  background: transparent;
  border: none;
  font-size: 0.75rem;
  color: #64748b;
  cursor: pointer;
  text-decoration: underline;
}

/* Filtro y grilla de selección de equipos */
.barra-filtro-equipos {
  display: grid;
  grid-template-columns: 1fr 180px;
  gap: 0.6rem;
}
.grilla-equipos-seleccionable {
  max-height: 250px;
  overflow-y: auto;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.5rem;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 0.5rem;
  background: #fafafa;
}
.tarjeta-equipo-item {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.6rem;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.tarjeta-equipo-item:hover {
  border-color: #0284c7;
  background: #f0f9ff;
}
.equipo-elegido {
  border-color: #0284c7;
  background: #f0f9ff;
  box-shadow: 0 0 0 1px #0284c7;
}
.check-equipo {
  margin-top: 0.2rem;
  cursor: pointer;
}
.detalles-equipo-item {
  font-size: 0.85rem;
  line-height: 1.3;
}
.linea-superior-eq {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.bien-nacional-tag {
  font-weight: 700;
  color: #0f172a;
}
.tipo-tag {
  background: #f1f5f9;
  font-size: 0.72rem;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  color: #475569;
}
.marca-modelo-eq {
  color: #334155;
}
.subinfo-eq {
  font-size: 0.75rem;
  color: #64748b;
  display: flex;
  gap: 0.5rem;
  margin-top: 0.2rem;
}

/* Campos formulario */
.campo-formulario {
  display: grid;
  gap: 0.4rem;
}
.aclaratoria {
  font-size: 0.8rem;
  font-weight: normal;
  color: #64748b;
  margin-left: 0.4rem;
}
.chips-sugerencias {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
  margin-top: 0.2rem;
}
.sug-label {
  font-size: 0.75rem;
  color: #64748b;
}
.btn-sug {
  background: #f1f5f9;
  border: 1px dashed #cbd5e1;
  border-radius: 4px;
  font-size: 0.75rem;
  padding: 0.15rem 0.5rem;
  cursor: pointer;
  color: #334155;
}
.btn-sug:hover {
  background: #e2e8f0;
  border-color: #94a3b8;
}

/* Opción de activación inmediata */
.tarjeta-suave {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 0.75rem 1rem;
  border-radius: 8px;
}
.check-container {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  cursor: pointer;
}
.check-container input[type="checkbox"] {
  margin-top: 0.25rem;
  width: 1.1rem;
  height: 1.1rem;
  cursor: pointer;
}
.check-texto {
  font-size: 0.9rem;
  color: #0f172a;
}
.subtexto {
  color: #64748b;
  margin-top: 0.15rem;
}

/* Alertas */
.mensaje-alerta {
  padding: 0.85rem 1rem;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
}
.alerta-exito {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}
.alerta-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}
.btn-enlace-alerta {
  color: #15803d;
  font-weight: 700;
  text-decoration: underline;
}

/* Pie */
.pie-formulario {
  display: flex;
  justify-content: flex-end;
}
.btn-guardar-prestamo {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 700;
}

@media (max-width: 768px) {
  .contenedor-calendario-fechas {
    grid-template-columns: 1fr;
  }
  .barra-filtro-equipos {
    grid-template-columns: 1fr;
  }
}
</style>
