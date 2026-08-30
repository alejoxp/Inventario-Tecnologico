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
          />
        </label>

        <!-- Filtro por Oficina -->
        <label class="campo-filtro">
          <span>Oficina / Ubicación</span>
          <select v-model="filtroOficina" class="input-form">
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
          />
        </label>

        <!-- Filtro por Estado -->
        <label class="campo-filtro">
          <span>Estado del equipo</span>
          <select v-model="filtroEstado" class="input-form">
            <option value="">Todos los estados</option>
            <option v-for="est in estadosDisponibles" :key="est" :value="est">
              {{ est }}
            </option>
          </select>
        </label>

        <!-- Filtro por Marca -->
        <label class="campo-filtro">
          <span>Marca</span>
          <select v-model="filtroMarca" class="input-form">
            <option value="">Todas las marcas</option>
            <option v-for="marca in marcas" :key="marca.id" :value="marca.id">
              {{ marca.nombre }}
            </option>
          </select>
        </label>
      </div>

      <!-- Resumen de resultados -->
      <div class="barra-conteo-filtros">
        <span class="badge-conteo">
          Mostrando <strong>{{ equiposFiltrados.length }}</strong> de <strong>{{ equipos.length }}</strong> equipos
        </span>
        <span v-if="hayFiltrosActivos" class="aviso-filtros-activos">
          (Filtros aplicados)
        </span>
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
          <tr v-for="equipo in equiposFiltrados" :key="equipo.id">
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
  </main>
</template>
