<script setup>
import { computed, onMounted, ref } from 'vue'
import Navbar from '../components/Navbar.vue'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

// Estado principal
const equipos = ref([])
const ubicaciones = ref([])
const marcas = ref([])
const tipos = ref([])
const cargando = ref(true)
const error = ref('')

// Pestaña activa del reporte
// 'general' = Reporte general de todas las oficinas
// 'oficina' = Reporte de una sola oficina
// 'custodio' = Reporte de un solo custodio
const tipoReporte = ref('general')

// Selección específica
const oficinaSeleccionadaId = ref('')
const custodioSeleccionado = ref('')

// Filtro secundario de texto o estado dentro del reporte
const busquedaSecundaria = ref('')
const filtroEstadoSecundario = ref('')

// Carga inicial de datos
async function cargarDatos() {
  cargando.value = true
  error.value = ''
  try {
    const [resEquipos, resCatalogos] = await Promise.all([
      api.get('/equipos/'),
      api.get('/catalogos'),
    ])
    equipos.value = resEquipos.data
    ubicaciones.value = resCatalogos.data.ubicaciones || []
    marcas.value = resCatalogos.data.marcas || []
    tipos.value = resCatalogos.data.tipos || []

    // Inicializar selectores por defecto
    if (ubicaciones.value.length) {
      oficinaSeleccionadaId.value = String(ubicaciones.value[0].id)
    }
    if (listaCustodiosUnicos.value.length) {
      custodioSeleccionado.value = listaCustodiosUnicos.value[0].nombre
    }
  } catch (err) {
    error.value = 'No se pudieron cargar los datos para los reportes.'
  } finally {
    cargando.value = false
  }
}

// ==========================================
// 1. CUSTODIOS ÚNICOS DISPONIBLES
// ==========================================
const listaCustodiosUnicos = computed(() => {
  const mapa = new Map()
  equipos.value.forEach((e) => {
    const cust = (e.custodio || '').trim()
    if (cust) {
      if (!mapa.has(cust)) {
        mapa.set(cust, {
          nombre: cust,
          cantidad: 0,
          oficinas: new Set(),
        })
      }
      const item = mapa.get(cust)
      item.cantidad++
      if (e.ubicacion?.nombre) item.oficinas.add(e.ubicacion.nombre)
    }
  })

  return Array.from(mapa.values())
    .map((c) => ({
      nombre: c.nombre,
      cantidad: c.cantidad,
      oficinas: Array.from(c.oficinas).join(', '),
    }))
    .sort((a, b) => a.nombre.localeCompare(b.nombre))
})

// ==========================================
// 2. REPORTE GENERAL (TODAS LAS OFICINAS)
// ==========================================
const metricasGenerales = computed(() => {
  const total = equipos.value.length
  const operativos = equipos.value.filter((e) => e.estado === 'Operativo').length
  const reparacion = equipos.value.filter((e) => e.estado === 'En Reparación').length
  const danados = equipos.value.filter(
    (e) => e.estado === 'Dañado' || e.estado === 'Desincorporado'
  ).length

  return { total, operativos, reparacion, danados }
})

// Desglose por oficinas para la tabla resumen
const desglosePorOficinas = computed(() => {
  return ubicaciones.value.map((ub) => {
    const equiposDeEsta = equipos.value.filter((e) => e.ubicacion?.id === ub.id)
    const operativos = equiposDeEsta.filter((e) => e.estado === 'Operativo').length
    const reparacion = equiposDeEsta.filter((e) => e.estado === 'En Reparación').length
    const danados = equiposDeEsta.filter(
      (e) => e.estado === 'Dañado' || e.estado === 'Desincorporado'
    ).length

    const custodiosSet = new Set()
    equiposDeEsta.forEach((e) => {
      if (e.custodio) custodiosSet.add(e.custodio.trim())
    })

    return {
      id: ub.id,
      nombre: ub.nombre,
      total: equiposDeEsta.length,
      operativos,
      reparacion,
      danados,
      custodiosTotal: custodiosSet.size,
    }
  }).sort((a, b) => b.total - a.total)
})

// Desglose por tipos de equipo
const desglosePorTipos = computed(() => {
  const mapa = {}
  equipos.value.forEach((e) => {
    const tipo = e.tipo?.nombre || 'Sin clasificar'
    mapa[tipo] = (mapa[tipo] || 0) + 1
  })
  return Object.entries(mapa).map(([nombre, cantidad]) => ({ nombre, cantidad }))
})

// ==========================================
// 3. REPORTE POR OFICINA INDIVIDUAL
// ==========================================
const oficinaActualObjeto = computed(() => {
  const idNum = Number(oficinaSeleccionadaId.value)
  return ubicaciones.value.find((ub) => ub.id === idNum) || null
})

const equiposDeOficinaSeleccionada = computed(() => {
  const idNum = Number(oficinaSeleccionadaId.value)
  if (!idNum) return []
  return equipos.value.filter((e) => e.ubicacion?.id === idNum)
})

const metricasOficina = computed(() => {
  const lista = equiposDeOficinaSeleccionada.value
  const total = lista.length
  const operativos = lista.filter((e) => e.estado === 'Operativo').length
  const reparacion = lista.filter((e) => e.estado === 'En Reparación').length
  const danados = lista.filter(
    (e) => e.estado === 'Dañado' || e.estado === 'Desincorporado'
  ).length

  const custodiosSet = new Set()
  lista.forEach((e) => {
    if (e.custodio) custodiosSet.add(e.custodio.trim())
  })

  // Conteo de tipos en la oficina
  const tiposMap = {}
  lista.forEach((e) => {
    const t = e.tipo?.nombre || 'Sin tipo'
    tiposMap[t] = (tiposMap[t] || 0) + 1
  })

  return {
    total,
    operativos,
    reparacion,
    danados,
    custodios: Array.from(custodiosSet),
    tipos: Object.entries(tiposMap).map(([nombre, cantidad]) => ({ nombre, cantidad })),
  }
})

// ==========================================
// 4. REPORTE POR CUSTODIO INDIVIDUAL
// ==========================================
const equiposDeCustodioSeleccionado = computed(() => {
  const custNombre = custodioSeleccionado.value.trim().toLowerCase()
  if (!custNombre) return []
  return equipos.value.filter(
    (e) => String(e.custodio || '').trim().toLowerCase() === custNombre
  )
})

const metricasCustodio = computed(() => {
  const lista = equiposDeCustodioSeleccionado.value
  const total = lista.length
  const operativos = lista.filter((e) => e.estado === 'Operativo').length
  const reparacion = lista.filter((e) => e.estado === 'En Reparación').length
  const danados = lista.filter(
    (e) => e.estado === 'Dañado' || e.estado === 'Desincorporado'
  ).length

  const oficinasSet = new Set()
  lista.forEach((e) => {
    if (e.ubicacion?.nombre) oficinasSet.add(e.ubicacion.nombre)
  })

  return {
    total,
    operativos,
    reparacion,
    danados,
    oficinas: Array.from(oficinasSet).join(', ') || 'Sin oficina asignada',
  }
})

// ==========================================
// 5. LISTA FINAL DE EQUIPOS SEGÚN REPORTE
// ==========================================
const equiposParaReporte = computed(() => {
  let base = []
  if (tipoReporte.value === 'general') {
    base = equipos.value
  } else if (tipoReporte.value === 'oficina') {
    base = equiposDeOficinaSeleccionada.value
  } else if (tipoReporte.value === 'custodio') {
    base = equiposDeCustodioSeleccionado.value
  }

  // Filtrado secundario (búsqueda o estado)
  const term = busquedaSecundaria.value.trim().toLowerCase()
  const est = filtroEstadoSecundario.value

  return base.filter((e) => {
    if (est && e.estado !== est) return false
    if (!term) return true
    return [
      e.bien_nacional,
      e.serial,
      e.mac,
      e.modelo,
      e.marca?.nombre,
      e.marca_detalle,
      e.tipo?.nombre,
      e.ubicacion?.nombre,
      e.custodio,
    ].some((v) => String(v || '').toLowerCase().includes(term))
  })
})

// Atajo para ir a ver reporte de una oficina específica desde la tabla general
function verReporteOficinaEspecifica(oficinaId) {
  oficinaSeleccionadaId.value = String(oficinaId)
  tipoReporte.value = 'oficina'
  busquedaSecundaria.value = ''
  filtroEstadoSecundario.value = ''
}

// ==========================================
// 6. ACCIONES: IMPRESIÓN Y EXPORTACIÓN CSV
// ==========================================
function imprimirReporte() {
  window.print()
}

function exportarCsv() {
  const lista = equiposParaReporte.value
  if (!lista.length) return

  let titulo = 'reporte_equipos'
  if (tipoReporte.value === 'general') titulo = 'reporte_general_todas_las_oficinas'
  if (tipoReporte.value === 'oficina') {
    const nom = (oficinaActualObjeto.value?.nombre || 'oficina').replace(/\s+/g, '_')
    titulo = `reporte_oficina_${nom}`
  }
  if (tipoReporte.value === 'custodio') {
    const nom = (custodioSeleccionado.value || 'custodio').replace(/\s+/g, '_')
    titulo = `reporte_custodio_${nom}`
  }

  const fechaIso = new Date().toISOString().split('T')[0]
  const encabezados = [
    'Bien Nacional',
    'Tipo',
    'Marca',
    'Modelo',
    'Serial',
    'Direccion MAC',
    'Oficina / Ubicacion',
    'Custodio Responsable',
    'Estado',
    'Observaciones',
  ]

  const filas = lista.map((e) => [
    `"${e.bien_nacional || ''}"`,
    `"${e.tipo?.nombre || ''}"`,
    `"${e.marca?.nombre === 'Otro' ? e.marca_detalle : e.marca?.nombre || ''}"`,
    `"${e.modelo || ''}"`,
    `"${e.serial || ''}"`,
    `"${e.mac || ''}"`,
    `"${e.ubicacion?.nombre || ''}"`,
    `"${e.custodio || ''}"`,
    `"${e.estado || ''}"`,
    `"${(e.observaciones || '').replace(/"/g, '""')}"`,
  ])

  const contenidoCsv = '\uFEFF' + [encabezados.join(','), ...filas.map((f) => f.join(','))].join('\r\n')
  const blob = new Blob([contenidoCsv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute('download', `${titulo}_${fechaIso}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

function formatoFechaEmision() {
  return new Date().toLocaleDateString('es-VE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(cargarDatos)
</script>

<template>
  <Navbar />
  <main class="contenido reportes-vista">
    <!-- Encabezado de la Pantalla (Visible en pantalla) -->
    <div class="encabezado-vista no-print">
      <div>
        <p class="etiqueta">Informes y Auditoría Patrimonial</p>
        <h1>Reportes de Equipos e Inventario</h1>
      </div>
      <div class="acciones-cabecera">
        <button
          class="btn-secundario"
          type="button"
          :disabled="cargando || !equiposParaReporte.length"
          title="Descargar datos en formato CSV compatible con Excel"
          @click="exportarCsv"
        >
          📥 Descargar CSV / Excel
        </button>
        <button
          class="btn-primario"
          type="button"
          :disabled="cargando"
          title="Imprimir documento oficial o guardar en PDF"
          @click="imprimirReporte"
        >
          🖨️ Imprimir / Guardar PDF
        </button>
      </div>
    </div>

    <!-- Pestañas de Selección de Reporte (No-print) -->
    <section class="tarjeta-sombra panel-selector-reporte no-print">
      <div class="pestanas-reportes">
        <button
          type="button"
          class="pestana-btn"
          :class="{ 'pestana-activa': tipoReporte === 'general' }"
          @click="tipoReporte = 'general'"
        >
          🏢 1. Reporte General (Todas las Oficinas)
        </button>

        <button
          type="button"
          class="pestana-btn"
          :class="{ 'pestana-activa': tipoReporte === 'oficina' }"
          @click="tipoReporte = 'oficina'"
        >
          📍 2. Equipos en una Sola Oficina
        </button>

        <button
          type="button"
          class="pestana-btn"
          :class="{ 'pestana-activa': tipoReporte === 'custodio' }"
          @click="tipoReporte = 'custodio'"
        >
          👤 3. Equipos de un Solo Custodio
        </button>
      </div>

      <!-- Selectores contextuales según el reporte -->
      <div v-if="tipoReporte === 'oficina'" class="barra-seleccion-contextual">
        <label for="selectOficinaReporte">
          <strong>Seleccione la Oficina a consultar:</strong>
        </label>
        <select
          id="selectOficinaReporte"
          v-model="oficinaSeleccionadaId"
          class="input-form select-filtro-oficina"
        >
          <option
            v-for="ub in ubicaciones"
            :key="ub.id"
            :value="String(ub.id)"
          >
            {{ ub.nombre }} ({{ equipos.filter(e => e.ubicacion?.id === ub.id).length }} equipos)
          </option>
        </select>
      </div>

      <div v-if="tipoReporte === 'custodio'" class="barra-seleccion-contextual">
        <label for="selectCustodioReporte">
          <strong>Seleccione el Custodio / Trabajador responsable:</strong>
        </label>
        <select
          id="selectCustodioReporte"
          v-model="custodioSeleccionado"
          class="input-form select-filtro-custodio"
        >
          <option
            v-for="cust in listaCustodiosUnicos"
            :key="cust.nombre"
            :value="cust.nombre"
          >
            {{ cust.nombre }} ({{ cust.cantidad }} equipos asignados · {{ cust.oficinas }})
          </option>
        </select>
      </div>
    </section>

    <!-- MENSAJES DE ESTADO -->
    <div v-if="cargando" class="tarjeta-sombra estado-carga no-print">
      Cargando información de inventario y oficinas...
    </div>
    <div v-if="error" class="mensaje-error no-print">{{ error }}</div>

    <!-- ================================================================= -->
    <!-- MEMBRETE OFICIAL INSTITUCIONAL (VISIBLE EN IMPRESIÓN Y PANTALLA)  -->
    <!-- ================================================================= -->
    <div class="hoja-reporte tarjeta-sombra">
      <!-- Encabezado Membretado para Impresión -->
      <header class="membrete-oficial">
        <div class="membrete-izq">
          <div class="ente-principal">GOBIERNO BOLIVARIANO DE VENEZUELA</div>
          <div class="ente-secundario">FUNDACITE SUCRE · COORDINACIÓN DE TELEMÁTICA</div>
          <div class="ente-sub">SISTEMA DE CONTROL PATRIMONIAL E INVENTARIO TECNOLÓGICO</div>
        </div>
        <div class="membrete-der">
          <div class="fecha-emision">
            <strong>Fecha de emisión:</strong> {{ formatoFechaEmision() }}
          </div>
          <div class="usuario-emisor">
            <strong>Generado por:</strong> {{ auth.username }} ({{ auth.rol }})
          </div>
        </div>
      </header>

      <!-- TÍTULO DINÁMICO DEL REPORTE -->
      <div class="titulo-documento">
        <h2 v-if="tipoReporte === 'general'">
          INFORME GENERAL DE BIENES TECNOLÓGICOS (TODAS LAS OFICINAS)
        </h2>
        <h2 v-else-if="tipoReporte === 'oficina'">
          INVENTARIO DE EQUIPOS POR OFICINA:
          <span class="subrayado-titulo">{{ oficinaActualObjeto?.nombre || 'Oficina' }}</span>
        </h2>
        <h2 v-else-if="tipoReporte === 'custodio'">
          ACTA Y RESUMEN PATRIMONIAL POR CUSTODIO:
          <span class="subrayado-titulo">{{ custodioSeleccionado || 'Sin custodio' }}</span>
        </h2>
      </div>

      <!-- ============================================================= -->
      <!-- CASO 1: RESUMEN DEL REPORTE GENERAL                           -->
      <!-- ============================================================= -->
      <section v-if="tipoReporte === 'general'" class="seccion-reporte">
        <!-- KPIs Globales -->
        <div class="kpis-resumen-reporte">
          <div class="kpi-mini">
            <span class="kpi-num">{{ metricasGenerales.total }}</span>
            <span class="kpi-lbl">Total Equipos</span>
          </div>
          <div class="kpi-mini kpi-verde">
            <span class="kpi-num">{{ metricasGenerales.operativos }}</span>
            <span class="kpi-lbl">Operativos</span>
          </div>
          <div class="kpi-mini kpi-ambar">
            <span class="kpi-num">{{ metricasGenerales.reparacion }}</span>
            <span class="kpi-lbl">En Reparación</span>
          </div>
          <div class="kpi-mini kpi-rojo">
            <span class="kpi-num">{{ metricasGenerales.danados }}</span>
            <span class="kpi-lbl">Dañados / Bajas</span>
          </div>
          <div class="kpi-mini">
            <span class="kpi-num">{{ ubicaciones.length }}</span>
            <span class="kpi-lbl">Oficinas con bienes</span>
          </div>
        </div>

        <!-- Tabla Desglose: Cuántos equipos tiene cada oficina -->
        <div class="bloque-desglose">
          <h3 class="subtitulo-seccion">
            📊 Desglose de Equipos por Oficina (¿Cuántos equipos tiene cada oficina?)
          </h3>
          <table class="tabla-reporte tabla-oficinas">
            <thead>
              <tr>
                <th>Oficina / Ubicación</th>
                <th class="texto-centro">Total Equipos</th>
                <th class="texto-centro">Operativos</th>
                <th class="texto-centro">En Reparación</th>
                <th class="texto-centro">Dañados</th>
                <th class="texto-centro">Custodios</th>
                <th class="no-print texto-centro">Acción</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ofic in desglosePorOficinas" :key="ofic.id">
                <td>
                  <strong>{{ ofic.nombre }}</strong>
                </td>
                <td class="texto-centro">
                  <span class="badge-total-num">{{ ofic.total }}</span>
                </td>
                <td class="texto-centro">{{ ofic.operativos }}</td>
                <td class="texto-centro">{{ ofic.reparacion }}</td>
                <td class="texto-centro">{{ ofic.danados }}</td>
                <td class="texto-centro">{{ ofic.custodiosTotal }}</td>
                <td class="no-print texto-centro">
                  <button
                    class="btn-secundario btn-pequeno"
                    type="button"
                    title="Ver listado detallado de esta oficina"
                    @click="verReporteOficinaEspecifica(ofic.id)"
                  >
                    Ver detalles →
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Resumen por Tipos -->
        <div class="bloque-tipos">
          <h3 class="subtitulo-seccion">📦 Equipos según su Tipo</h3>
          <div class="badges-tipos-grilla">
            <span
              v-for="t in desglosePorTipos"
              :key="t.nombre"
              class="badge-tipo-item"
            >
              <strong>{{ t.nombre }}:</strong> {{ t.cantidad }} unidad{{ t.cantidad > 1 ? 'es' : '' }}
            </span>
          </div>
        </div>
      </section>

      <!-- ============================================================= -->
      <!-- CASO 2: RESUMEN DEL REPORTE POR OFICINA                       -->
      <!-- ============================================================= -->
      <section v-else-if="tipoReporte === 'oficina'" class="seccion-reporte">
        <div class="ficha-resumen-oficina">
          <div class="kpis-resumen-reporte">
            <div class="kpi-mini">
              <span class="kpi-num">{{ metricasOficina.total }}</span>
              <span class="kpi-lbl">Equipos en esta oficina</span>
            </div>
            <div class="kpi-mini kpi-verde">
              <span class="kpi-num">{{ metricasOficina.operativos }}</span>
              <span class="kpi-lbl">Operativos</span>
            </div>
            <div class="kpi-mini kpi-ambar">
              <span class="kpi-num">{{ metricasOficina.reparacion }}</span>
              <span class="kpi-lbl">En Reparación</span>
            </div>
            <div class="kpi-mini kpi-rojo">
              <span class="kpi-num">{{ metricasOficina.danados }}</span>
              <span class="kpi-lbl">Dañados</span>
            </div>
            <div class="kpi-mini">
              <span class="kpi-num">{{ metricasOficina.custodios.length }}</span>
              <span class="kpi-lbl">Custodios responsables</span>
            </div>
          </div>

          <div class="detalle-custodios-oficina">
            <strong>👤 Custodios en esta oficina:</strong>
            <span v-if="metricasOficina.custodios.length">
              {{ metricasOficina.custodios.join(' · ') }}
            </span>
            <span v-else class="texto-vacio">No hay custodios asignados directamente</span>
          </div>
        </div>
      </section>

      <!-- ============================================================= -->
      <!-- CASO 3: RESUMEN DEL REPORTE POR CUSTODIO                      -->
      <!-- ============================================================= -->
      <section v-else-if="tipoReporte === 'custodio'" class="seccion-reporte">
        <div class="ficha-resumen-custodio">
          <div class="kpis-resumen-reporte">
            <div class="kpi-mini">
              <span class="kpi-num">{{ metricasCustodio.total }}</span>
              <span class="kpi-lbl">Equipos bajo su custodia</span>
            </div>
            <div class="kpi-mini kpi-verde">
              <span class="kpi-num">{{ metricasCustodio.operativos }}</span>
              <span class="kpi-lbl">Operativos</span>
            </div>
            <div class="kpi-mini kpi-ambar">
              <span class="kpi-num">{{ metricasCustodio.reparacion }}</span>
              <span class="kpi-lbl">En Reparación</span>
            </div>
            <div class="kpi-mini kpi-rojo">
              <span class="kpi-num">{{ metricasCustodio.danados }}</span>
              <span class="kpi-lbl">Dañados / Bajas</span>
            </div>
          </div>

          <div class="detalle-custodios-oficina">
            <strong>📍 Ubicación(es) de los bienes:</strong> {{ metricasCustodio.oficinas }}
          </div>
        </div>
      </section>

      <!-- ============================================================= -->
      <!-- TABLA DETALLADA: CUÁLES EQUIPOS TIENE (LISTA COMPLETA)       -->
      <!-- ============================================================= -->
      <section class="seccion-reporte-detalle">
        <div class="cabecera-detalle-reporte">
          <h3 class="subtitulo-seccion">
            📋 Listado Detallado de Equipos ({{ equiposParaReporte.length }} equipos listados)
          </h3>

          <!-- Buscador y filtro secundario en pantalla (No-print) -->
          <div class="filtros-secundarios no-print">
            <input
              v-model="busquedaSecundaria"
              type="text"
              class="input-form input-buscar-sec"
              placeholder="🔍 Filtrar en este reporte..."
            />
            <select
              v-model="filtroEstadoSecundario"
              class="input-form select-estado-sec"
            >
              <option value="">Todos los estados</option>
              <option value="Operativo">Operativos</option>
              <option value="En Reparación">En Reparación</option>
              <option value="Dañado">Dañados</option>
              <option value="Desincorporado">Desincorporados</option>
            </select>
          </div>
        </div>

        <table class="tabla-reporte tabla-equipos-detalle">
          <thead>
            <tr>
              <th style="width: 15%;">Bien Nacional</th>
              <th style="width: 25%;">Equipo & Modelo</th>
              <th style="width: 14%;">Serial / MAC</th>
              <th v-if="tipoReporte !== 'oficina'" style="width: 18%;">Oficina / Ubicación</th>
              <th v-if="tipoReporte !== 'custodio'" style="width: 18%;">Custodio Responsable</th>
              <th style="width: 10%;" class="texto-centro">Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!equiposParaReporte.length">
              <td :colspan="tipoReporte === 'general' ? 6 : 5" class="texto-centro celda-vacia">
                No hay equipos registrados que coincidan con los criterios seleccionados.
              </td>
            </tr>
            <tr
              v-for="equipo in equiposParaReporte"
              :key="equipo.id"
            >
              <!-- Bien Nacional -->
              <td class="col-bn">
                <strong>{{ equipo.bien_nacional }}</strong>
              </td>

              <!-- Equipo y Tipo -->
              <td>
                <div class="nombre-equipo-item">
                  <strong>{{ equipo.marca?.nombre === 'Otro' ? equipo.marca_detalle : (equipo.marca?.nombre || 'S/M') }}</strong>
                  {{ equipo.modelo || '' }}
                </div>
                <span class="tipo-etiqueta-pequena">{{ equipo.tipo?.nombre || 'General' }}</span>
              </td>

              <!-- Serial / MAC -->
              <td class="col-mono">
                <div>SN: {{ equipo.serial || 'S/N' }}</div>
                <div v-if="equipo.mac" class="sub-mac">MAC: {{ equipo.mac }}</div>
              </td>

              <!-- Oficina (si no es reporte de una sola oficina) -->
              <td v-if="tipoReporte !== 'oficina'">
                {{ equipo.ubicacion?.nombre || 'Sin oficina' }}
              </td>

              <!-- Custodio (si no es reporte de un solo custodio) -->
              <td v-if="tipoReporte !== 'custodio'">
                {{ equipo.custodio || 'Sin custodio' }}
              </td>

              <!-- Estado -->
              <td class="texto-centro">
                <span
                  :class="[
                    'estado-badge',
                    `estado-${(equipo.estado || '').toLowerCase().replace(/\s+/g, '-')}`,
                  ]"
                >
                  {{ equipo.estado }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- ============================================================= -->
      <!-- BLOQUE DE FIRMAS FORMALES (PARA IMPRESIÓN Y ACTAS AUDITORÍA) -->
      <!-- ============================================================= -->
      <footer class="bloque-firmas">
        <div class="col-firma">
          <div class="linea-firma"></div>
          <strong>Elaborado por</strong>
          <span>{{ auth.username }} ({{ auth.rol }})</span>
          <small>Técnico / Responsable</small>
        </div>

        <div class="col-firma">
          <div class="linea-firma"></div>
          <strong>Revisado / Custodio</strong>
          <span v-if="tipoReporte === 'custodio'">{{ custodioSeleccionado }}</span>
          <span v-else-if="tipoReporte === 'oficina'">Jefe de {{ oficinaActualObjeto?.nombre }}</span>
          <span v-else>Responsable de Bienes</span>
          <small>Recibí / Conforme</small>
        </div>

        <div class="col-firma">
          <div class="linea-firma"></div>
          <strong>Coordinación de Telemática</strong>
          <span>Fundacite Sucre</span>
          <small>Sello y Validación Oficial</small>
        </div>
      </footer>
    </div>
  </main>
</template>

<style scoped>
.reportes-vista {
  max-width: 1240px;
  margin: 0 auto;
}
.acciones-cabecera {
  display: flex;
  gap: 0.75rem;
}

/* Panel selector de reportes */
.panel-selector-reporte {
  background: #ffffff;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.pestanas-reportes {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.pestana-btn {
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 0.6rem 1rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s ease;
}
.pestana-btn:hover {
  background: #f1f5f9;
  border-color: #94a3b8;
}
.pestana-activa {
  background: var(--azul-institucional, #124e78) !important;
  color: #ffffff !important;
  border-color: transparent !important;
  box-shadow: 0 2px 6px rgba(18, 78, 120, 0.3);
}

.barra-seleccion-contextual {
  background: #f0f7ff;
  border: 1px solid #bae6fd;
  border-radius: 6px;
  padding: 0.75rem 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}
.select-filtro-oficina,
.select-filtro-custodio {
  flex: 1;
  min-width: 280px;
  background: #ffffff;
}

/* Hoja física del reporte */
.hoja-reporte {
  background: #ffffff;
  border-radius: 10px;
  padding: 2.5rem;
  margin-bottom: 2rem;
  border: 1px solid #e2e8f0;
}

/* Membrete oficial */
.membrete-oficial {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1.5rem;
  border-bottom: 2px solid #0f172a;
  padding-bottom: 1rem;
  margin-bottom: 1.5rem;
}
.ente-principal {
  font-size: 0.85rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  color: #0f172a;
}
.ente-secundario {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--azul-institucional, #124e78);
  margin-top: 0.15rem;
}
.ente-sub {
  font-size: 0.72rem;
  color: #64748b;
  margin-top: 0.15rem;
}
.membrete-der {
  text-align: right;
  font-size: 0.8rem;
  color: #475569;
  line-height: 1.4;
}

/* Título de documento */
.titulo-documento {
  text-align: center;
  margin-bottom: 1.75rem;
}
.titulo-documento h2 {
  font-size: 1.25rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: 0.02em;
  margin: 0;
}
.subrayado-titulo {
  color: var(--azul-institucional, #124e78);
  border-bottom: 2px solid var(--azul-institucional, #124e78);
}

/* KPIs de Resumen */
.kpis-resumen-reporte {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}
.kpi-mini {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem;
  text-align: center;
  display: flex;
  flex-direction: column;
}
.kpi-num {
  font-size: 1.6rem;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.1;
}
.kpi-lbl {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 600;
  margin-top: 0.2rem;
}
.kpi-verde {
  background: #f0fdf4;
  border-color: #bbf7d0;
}
.kpi-verde .kpi-num {
  color: #166534;
}
.kpi-ambar {
  background: #fffbeb;
  border-color: #fde68a;
}
.kpi-ambar .kpi-num {
  color: #b45309;
}
.kpi-rojo {
  background: #fef2f2;
  border-color: #fecaca;
}
.kpi-rojo .kpi-num {
  color: #991b1b;
}

/* Bloques de desglose y subtítulos */
.subtitulo-seccion {
  font-size: 1rem;
  font-weight: 700;
  color: #1e293b;
  margin: 1.25rem 0 0.75rem 0;
}
.badges-tipos-grilla {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}
.badge-tipo-item {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 0.3rem 0.65rem;
  font-size: 0.8rem;
  color: #334155;
}
.badge-total-num {
  background: #e0f2fe;
  color: #0369a1;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 12px;
  font-size: 0.85rem;
}

.detalle-custodios-oficina {
  background: #f8fafc;
  border-left: 4px solid var(--azul-institucional, #124e78);
  padding: 0.6rem 0.9rem;
  border-radius: 4px;
  font-size: 0.85rem;
  color: #334155;
  margin-bottom: 1rem;
}
.texto-vacio {
  color: #94a3b8;
  font-style: italic;
}

/* Tabla del reporte */
.cabecera-detalle-reporte {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}
.filtros-secundarios {
  display: flex;
  gap: 0.5rem;
}
.input-buscar-sec {
  width: 220px;
  font-size: 0.85rem;
  padding: 0.35rem 0.6rem;
}
.select-estado-sec {
  font-size: 0.85rem;
  padding: 0.35rem 0.6rem;
}

.tabla-reporte {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
  margin-bottom: 1.5rem;
}
.tabla-reporte th,
.tabla-reporte td {
  border: 1px solid #cbd5e1;
  padding: 0.5rem 0.65rem;
  text-align: left;
}
.tabla-reporte th {
  background: #f1f5f9;
  color: #0f172a;
  font-weight: 700;
}
.tabla-reporte tr:nth-child(even) {
  background: #f8fafc;
}
.texto-centro {
  text-align: center !important;
}
.celda-vacia {
  padding: 2rem;
  color: #64748b;
}

.col-bn {
  font-size: 0.9rem;
  color: #0f172a;
}
.nombre-equipo-item {
  color: #1e293b;
}
.tipo-etiqueta-pequena {
  display: inline-block;
  font-size: 0.72rem;
  background: #e2e8f0;
  color: #475569;
  padding: 0.05rem 0.35rem;
  border-radius: 4px;
  margin-top: 0.15rem;
}
.col-mono {
  font-family: monospace;
  font-size: 0.78rem;
  color: #475569;
}
.sub-mac {
  color: #64748b;
}

/* Firmas formales para impresión */
.bloque-firmas {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  margin-top: 3.5rem;
  padding-top: 1rem;
}
.col-firma {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.linea-firma {
  width: 80%;
  border-top: 1px solid #0f172a;
  margin-bottom: 0.4rem;
}
.col-firma strong {
  font-size: 0.82rem;
  color: #0f172a;
}
.col-firma span {
  font-size: 0.78rem;
  color: #475569;
}
.col-firma small {
  font-size: 0.7rem;
  color: #94a3b8;
}

/* ==========================================================================
   REGLAS PARA IMPRESIÓN OFICIAL (WINDOW.PRINT / PDF)
   ========================================================================== */
@media print {
  @page {
    size: letter portrait;
    margin: 1.2cm;
  }
  :global(body) {
    background: #ffffff !important;
    color: #000000 !important;
  }
  :global(.barra-navegacion),
  .no-print {
    display: none !important;
  }
  .hoja-reporte {
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
    box-shadow: none !important;
  }
  .tabla-reporte {
    font-size: 0.78rem !important;
  }
  .tabla-reporte th {
    background: #e2e8f0 !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .bloque-firmas {
    page-break-inside: avoid;
    margin-top: 2.5rem;
  }
  .kpi-mini {
    border: 1px solid #cbd5e1 !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
}
</style>
