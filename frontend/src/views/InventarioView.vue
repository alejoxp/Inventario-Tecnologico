<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import Navbar from '../components/Navbar.vue'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const equipos = ref([])
const marcas = ref([])
const ubicaciones = ref([])

const busqueda = ref('')
const filtroOficina = ref('')
const filtroCustodio = ref('')
const filtroEstado = ref('')
const filtroMarca = ref('')
const paginaActual = ref(1)
const equiposPorPagina = ref(20)

const cargando = ref(true)
const error = ref('')
const auth = useAuthStore()

const estadosDisponibles = ['Operativo', 'Dañado', 'En Reparación', 'Desincorporado']

const hayFiltrosActivos = computed(() => {
  return Boolean(
    busqueda.value.trim() ||
    filtroOficina.value ||
    filtroCustodio.value.trim() ||
    filtroEstado.value ||
    filtroMarca.value
  )
})

function limpiarFiltros() {
  busqueda.value = ''
  filtroOficina.value = ''
  filtroCustodio.value = ''
  filtroEstado.value = ''
  filtroMarca.value = ''
  reiniciarPagina()
}

const equiposFiltrados = computed(() => {
  const termino = busqueda.value.toLowerCase().trim()
  const oficinaId = filtroOficina.value ? Number(filtroOficina.value) : null
  const marcaId = filtroMarca.value ? Number(filtroMarca.value) : null
  const estado = filtroEstado.value
  const custodio = filtroCustodio.value.toLowerCase().trim()

  return equipos.value.filter((equipo) => {
    // Filtro por Oficina
    if (oficinaId !== null && equipo.ubicacion?.id !== oficinaId) {
      return false
    }

    // Filtro por Estado
    if (estado && equipo.estado !== estado) {
      return false
    }

    // Filtro por Marca
    if (marcaId !== null && equipo.marca?.id !== marcaId) {
      return false
    }

    // Filtro por Custodio específico
    if (custodio && !String(equipo.custodio || '').toLowerCase().includes(custodio)) {
      return false
    }

    // Búsqueda general (Bien Nacional, Serial, MAC, Modelo, Marca detalle, etc.)
    if (termino) {
      const coincide = [
        equipo.bien_nacional,
        equipo.serial,
        equipo.mac,
        equipo.custodio,
        equipo.modelo,
        equipo.marca?.nombre,
        equipo.marca_detalle,
        equipo.ubicacion?.nombre,
      ].some((valor) => String(valor || '').toLowerCase().includes(termino))

      if (!coincide) return false
    }

    return true
  })
})

const totalPaginas = computed(() => Math.max(1, Math.ceil(equiposFiltrados.value.length / equiposPorPagina.value)))
const indiceInicio = computed(() => (paginaActual.value - 1) * equiposPorPagina.value)
const indiceFin = computed(() => Math.min(indiceInicio.value + equiposPorPagina.value, equiposFiltrados.value.length))

const equiposPaginados = computed(() => {
  return equiposFiltrados.value.slice(indiceInicio.value, indiceFin.value)
})

const paginasPaginador = computed(() => {
  const total = totalPaginas.value
  const actual = paginaActual.value
  if (total <= 7) {
    return Array.from({ length: total }, (_, indice) => indice + 1)
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

function reiniciarPagina() {
  paginaActual.value = 1
}

async function cargarDatos() {
  cargando.value = true
  error.value = ''
  try {
    const [equiposRes, catalogosRes] = await Promise.all([
      api.get('/equipos/'),
      api.get('/catalogos'),
    ])
    equipos.value = equiposRes.data
    marcas.value = catalogosRes.data.marcas || []
    ubicaciones.value = catalogosRes.data.ubicaciones || []
  } catch {
    error.value = 'No se pudo cargar el inventario o los catálogos.'
  } finally {
    cargando.value = false
  }
}

onMounted(cargarDatos)
</script>

<template>
  <Navbar />
  <main class="contenido">
    <div class="encabezado-vista">
      <div>
        <p class="etiqueta">Control patrimonial</p>
        <h1>Inventario de equipos</h1>
      </div>
      <RouterLink v-if="['TECNICO', 'COORDINADOR', 'SUPERADMIN'].includes(auth.rol)" class="btn-primario" to="/equipos/nuevo">
        + Registrar equipo
      </RouterLink>
    </div>

    <!-- Panel de Filtros Avanzados -->
    <section class="panel-filtros tarjeta-sombra">
      <div class="encabezado-filtros">
        <div class="titulo-filtros">
          <span class="icono-filtro">🔍</span>
          <strong>Filtros de búsqueda avanzada</strong>
        </div>
        <button
          v-if="hayFiltrosActivos"
          class="btn-limpiar-filtros"
          type="button"
          @click="limpiarFiltros"
        >
          Limpiar filtros
        </button>
      </div>

      <div class="grilla-filtros">
        <!-- Búsqueda General -->
        <label class="campo-filtro">
          <span>Búsqueda rápida (Bien Nal / MAC / Modelo)</span>
          <input
            v-model="busqueda"
            class="input-form"
            placeholder="Escriba para buscar..."
            @input="reiniciarPagina"
          />
        </label>

        <!-- Filtro por Oficina -->
        <label class="campo-filtro">
          <span>Oficina / Ubicación</span>
            <select v-model="filtroOficina" class="input-form" @change="reiniciarPagina">
            <option value="">Todas las oficinas</option>
            <option v-for="ubicacion in ubicaciones" :key="ubicacion.id" :value="ubicacion.id">
              {{ ubicacion.nombre }}
            </option>
          </select>
        </label>

        <!-- Filtro por Custodio -->
        <label class="campo-filtro">
          <span>Custodio / Responsable</span>
          <input
            v-model="filtroCustodio"
            class="input-form"
            placeholder="Filtrar por custodio..."
            @input="reiniciarPagina"
          />
        </label>

        <!-- Filtro por Estado -->
        <label class="campo-filtro">
          <span>Estado del equipo</span>
            <select v-model="filtroEstado" class="input-form" @change="reiniciarPagina">
            <option value="">Todos los estados</option>
            <option v-for="est in estadosDisponibles" :key="est" :value="est">
              {{ est }}
            </option>
          </select>
        </label>

        <!-- Filtro por Marca -->
        <label class="campo-filtro">
          <span>Marca</span>
            <select v-model="filtroMarca" class="input-form" @change="reiniciarPagina">
            <option value="">Todas las marcas</option>
            <option v-for="marca in marcas" :key="marca.id" :value="marca.id">
              {{ marca.nombre }}
            </option>
          </select>
        </label>
      </div>

      <!-- Resumen de resultados y selector de equipos por página -->
      <div class="barra-conteo-filtros">
        <div class="conteo-izq">
          <span class="badge-conteo">
            Mostrando <strong>{{ equiposFiltrados.length ? indiceInicio + 1 : 0 }} - {{ indiceFin }}</strong> de <strong>{{ equiposFiltrados.length }}</strong> equipos
          </span>
          <span v-if="hayFiltrosActivos" class="aviso-filtros-activos">
            (Filtros aplicados)
          </span>
        </div>
        <div class="selector-por-pagina">
          <label for="selectPorPagina">Mostrar por página:</label>
          <select id="selectPorPagina" v-model="equiposPorPagina" class="select-tamano-pagina" @change="reiniciarPagina">
            <option :value="10">10 equipos</option>
            <option :value="20">20 equipos</option>
            <option :value="50">50 equipos</option>
            <option :value="100">100 equipos</option>
          </select>
        </div>
      </div>
    </section>

    <p v-if="error" class="mensaje-error">{{ error }}</p>

    <!-- Tabla de Equipos -->
    <div class="tabla-contenedor tarjeta-sombra">
      <table>
        <thead>
          <tr>
            <th>Bien nacional</th>
            <th>Equipo</th>
            <th>MAC</th>
            <th>Ubicación y Custodio</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="cargando">
            <td colspan="6" class="celda-centrada">Cargando inventario...</td>
          </tr>
          <tr v-else-if="!equiposFiltrados.length">
            <td colspan="6" class="celda-centrada">
              No se encontraron equipos con los criterios de búsqueda seleccionados.
            </td>
          </tr>
          <tr v-for="equipo in equiposPaginados" :key="equipo.id">
            <td class="col-bien-nacional"><strong>{{ equipo.bien_nacional }}</strong></td>
            <td>
              {{ equipo.marca?.nombre === 'Otro' && equipo.marca_detalle ? equipo.marca_detalle : (equipo.marca?.nombre || 'Sin marca') }}
              {{ equipo.modelo || '' }}
              <span v-if="equipo.tipo?.nombre" class="tipo-etiqueta">({{ equipo.tipo.nombre }})</span>
            </td>
            <td class="col-mono">{{ equipo.mac || 'Sin MAC' }}</td>
            <td>
              <div><strong>{{ equipo.ubicacion?.nombre || 'Sin asignar' }}</strong></div>
              <div v-if="equipo.custodio" class="subtexto-custodio">👤 {{ equipo.custodio }}</div>
            </td>
            <td>
              <span :class="['estado-badge', `estado-${(equipo.estado || '').toLowerCase().replace(/\s+/g, '-')}`]">
                {{ equipo.estado }}
              </span>
            </td>
            <td class="acciones-tabla">
              <RouterLink
                v-if="['TECNICO', 'COORDINADOR', 'SUPERADMIN'].includes(auth.rol)"
                class="btn-secundario btn-pequeno"
                :to="`/equipos/${equipo.id}/editar`"
              >
                Editar
              </RouterLink>
              <RouterLink
                v-if="equipo.estado !== 'Desincorporado' && ['COORDINADOR', 'SUPERADMIN'].includes(auth.rol)"
                class="btn-peligro btn-pequeno"
                :to="{ path: `/equipos/${equipo.id}/editar`, query: { desincorporar: '1' } }"
              >
                Desincorporar
              </RouterLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Paginación completa con navegación y elipsis: 1...2...3..4..5...6... -> -->
    <nav v-if="totalPaginas > 1" class="paginacion" aria-label="Paginación del inventario">
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
        Pág. <strong>{{ paginaActual }}</strong> de <strong>{{ totalPaginas }}</strong>
      </span>
    </nav>
  </main>
</template>

<style scoped>
.barra-conteo-filtros {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: #f8fafc;
  border-radius: 8px;
  margin-top: 1rem;
}
.conteo-izq {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}
.selector-por-pagina {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.88rem;
  color: #475569;
}
.select-tamano-pagina {
  padding: 0.25rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.85rem;
  background: #fff;
  cursor: pointer;
}
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
@media (max-width: 640px) {
  .barra-conteo-filtros {
    flex-direction: column;
    align-items: stretch;
  }
  .info-pagina-actual {
    width: 100%;
    text-align: center;
    margin-left: 0;
    margin-top: 0.5rem;
  }
}
</style>
