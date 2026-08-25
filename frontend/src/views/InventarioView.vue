<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import Navbar from '../components/Navbar.vue'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const equipos = ref([])
const busqueda = ref('')
const cargando = ref(true)
const error = ref('')
const auth = useAuthStore()

const equiposFiltrados = computed(() => {
  const termino = busqueda.value.toLowerCase().trim()
  return equipos.value.filter((equipo) =>
    [
      equipo.bien_nacional,
      equipo.mac,
      equipo.custodio,
      equipo.modelo,
      equipo.marca?.nombre,
      equipo.marca_detalle,
      equipo.ubicacion?.nombre,
    ].some((valor) => String(valor || '').toLowerCase().includes(termino)),
  )
})

async function cargarEquipos() {
  try {
    equipos.value = (await api.get('/equipos/')).data
  } catch {
    error.value = 'No se pudo cargar el inventario.'
  } finally {
    cargando.value = false
  }
}

onMounted(cargarEquipos)
</script>

<template>
  <Navbar />
  <main class="contenido">
    <div class="encabezado-vista">
      <div>
        <p class="etiqueta">Control patrimonial</p>
        <h1>Inventario de equipos</h1>
      </div>
      <RouterLink class="btn-primario" to="/equipos/nuevo">Registrar equipo</RouterLink>
    </div>
    <input v-model="busqueda" class="input-form buscador" placeholder="Buscar por nombre, oficina, custodio, marca o MAC" />
    <p v-if="error" class="mensaje-error">{{ error }}</p>
    <div class="tabla-contenedor tarjeta-sombra">
      <table>
        <thead><tr><th>Bien nacional</th><th>Equipo</th><th>MAC</th><th>Ubicacion</th><th>Estado</th><th>Acciones</th></tr></thead>
        <tbody>
          <tr v-if="cargando"><td colspan="6">Cargando inventario...</td></tr>
          <tr v-else-if="!equiposFiltrados.length"><td colspan="6">No hay equipos para mostrar.</td></tr>
          <tr v-for="equipo in equiposFiltrados" :key="equipo.id">
            <td>{{ equipo.bien_nacional }}</td>
            <td>{{ equipo.marca.nombre === 'Otro' && equipo.marca_detalle ? equipo.marca_detalle : equipo.marca.nombre }} {{ equipo.modelo || '' }}</td>
            <td>{{ equipo.mac || 'Sin MAC' }}</td>
            <td>{{ equipo.ubicacion.nombre }}{{ equipo.custodio ? ` - ${equipo.custodio}` : '' }}</td>
            <td><span class="estado-tabla">{{ equipo.estado }}</span></td>
            <td class="acciones-tabla">
              <RouterLink v-if="['TECNICO', 'COORDINADOR', 'SUPERADMIN'].includes(auth.rol)" class="btn-secundario btn-pequeno" :to="`/equipos/${equipo.id}/editar`">Editar</RouterLink>
              <RouterLink v-if="equipo.estado !== 'Desincorporado' && auth.rol !== 'TECNICO'" class="btn-peligro btn-pequeno" :to="{ path: `/equipos/${equipo.id}/editar`, query: { desincorporar: '1' } }">Desincorporar</RouterLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </main>
</template>
