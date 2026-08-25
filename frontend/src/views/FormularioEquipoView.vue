<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useRoute } from 'vue-router'
import Navbar from '../components/Navbar.vue'
import api from '../services/api'

const router = useRouter()
const route = useRoute()
const tipos = ref([])
const marcas = ref([])
const ubicaciones = ref([])
const error = ref('')
const guardando = ref(false)
const editando = computed(() => Boolean(route.params.id))
const equipo = reactive({ bien_nacional: '', serial: '', mac: '', modelo: '', marca_detalle: '', estado: 'Operativo', marca_id: '', tipo_id: '', ubicacion_id: '', custodio: '', observaciones: '', especificaciones: { cpu: '', ram: '', almacenamiento: '', sistema_operativo: '' } })
const marcaEsOtro = computed(() => marcas.value.find((marca) => String(marca.id) === String(equipo.marca_id))?.nombre === 'Otro')
const ubicacionesDisponibles = computed(() => equipo.estado === 'Desincorporado' ? ubicaciones.value.filter((ubicacion) => ubicacion.nombre === 'Deposito') : ubicaciones.value.filter((ubicacion) => ubicacion.nombre !== 'Deposito'))
const requiereEspecificaciones = computed(() => ['laptop', 'cpu', 'servidor'].includes((tipos.value.find((tipo) => tipo.id === Number(equipo.tipo_id))?.nombre || '').toLowerCase()))

function ajustarUbicacion() {
  if (equipo.estado === 'Desincorporado') equipo.ubicacion_id = ubicaciones.value.find((ubicacion) => ubicacion.nombre === 'Deposito')?.id || ''
  else if (ubicaciones.value.find((ubicacion) => String(ubicacion.id) === String(equipo.ubicacion_id))?.nombre === 'Deposito') equipo.ubicacion_id = ''
}

onMounted(async () => {
  try {
    const { data } = await api.get('/catalogos')
    tipos.value = data.tipos
    marcas.value = data.marcas
    ubicaciones.value = data.ubicaciones
    if (editando.value) {
      const existente = (await api.get(`/equipos/${route.params.id}`)).data
      Object.assign(equipo, existente, {
        marca_id: existente.marca.id,
        tipo_id: existente.tipo.id,
        ubicacion_id: existente.ubicacion.id,
        especificaciones: existente.especificaciones || equipo.especificaciones,
      })
      if (route.query.desincorporar === '1') {
        equipo.estado = 'Desincorporado'
        ajustarUbicacion()
      }
    }
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || (editando.value ? 'No se pudo cargar el equipo.' : 'No se pudieron cargar los catalogos.')
  }
})

async function guardar() {
  guardando.value = true
  error.value = ''
  const payload = {
    bien_nacional: equipo.bien_nacional,
    serial: equipo.serial || null,
    mac: equipo.mac || null,
    modelo: equipo.modelo || null,
    marca_detalle: equipo.marca_detalle || null,
    estado: equipo.estado,
    observaciones: equipo.observaciones || null,
    marca_id: Number(equipo.marca_id),
    tipo_id: Number(equipo.tipo_id),
    ubicacion_id: Number(equipo.ubicacion_id),
    custodio: equipo.custodio || null,
  }
  if (equipo.movimiento_motivo) payload.movimiento_motivo = equipo.movimiento_motivo
  if (requiereEspecificaciones.value) payload.especificaciones = { ...equipo.especificaciones }
  try {
    if (editando.value) await api.put(`/equipos/${route.params.id}`, payload)
    else await api.post('/equipos/nuevo', payload)
    router.push('/inventario')
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || 'No se pudo registrar el equipo.'
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <Navbar />
  <main class="contenido contenido-formulario">
    <h1>Inventario Tecnologico</h1>
    <form class="formulario tarjeta-sombra" @submit.prevent="guardar">
      <label class="campo-label">Bien nacional<input v-model="equipo.bien_nacional" class="input-form" required /></label>
      <label class="campo-label">Serial<input v-model="equipo.serial" class="input-form" /></label>
      <label class="campo-label">MAC Address<input v-model="equipo.mac" class="input-form" /></label>
      <label class="campo-label">Modelo<input v-model="equipo.modelo" class="input-form" /></label>
      <label class="campo-label">Marca<select v-model="equipo.marca_id" class="input-form" required><option value="" disabled>Seleccione</option><option v-for="marca in marcas" :key="marca.id" :value="marca.id">{{ marca.nombre }}</option></select></label>
      <label v-if="marcaEsOtro" class="campo-label">Nombre de la marca<input v-model="equipo.marca_detalle" class="input-form" maxlength="120" placeholder="Ejemplo: Djaua" required /></label>
      <label class="campo-label">Tipo<select v-model="equipo.tipo_id" class="input-form" required><option value="" disabled>Seleccione</option><option v-for="tipo in tipos" :key="tipo.id" :value="tipo.id">{{ tipo.nombre }}</option></select></label>
      <label class="campo-label">Ubicacion<select v-model="equipo.ubicacion_id" class="input-form" required><option value="" disabled>Seleccione</option><option v-for="ubicacion in ubicacionesDisponibles" :key="ubicacion.id" :value="ubicacion.id">{{ ubicacion.nombre }}</option></select></label>
      <label class="campo-label">Custodio<input v-model="equipo.custodio" class="input-form" maxlength="150" placeholder="Nombre de la persona" /></label>
      <label class="campo-label">Estado<select v-model="equipo.estado" class="input-form" @change="ajustarUbicacion"><option>Operativo</option><option>Dañado</option><option>En Reparación</option><option>Desincorporado</option></select></label>
      <template v-if="requiereEspecificaciones"><label class="campo-label">CPU<input v-model="equipo.especificaciones.cpu" class="input-form" /></label><label class="campo-label">RAM<input v-model="equipo.especificaciones.ram" class="input-form" /></label></template>
      <label class="campo-label campo-ancho">Observaciones<textarea v-model="equipo.observaciones" class="input-form" rows="3" /></label>
      <p v-if="error" class="mensaje-error campo-ancho">{{ error }}</p>
      <div class="acciones campo-ancho"><RouterLink class="btn-secundario" to="/inventario">Cancelar</RouterLink><button class="btn-primario" type="submit" :disabled="guardando">{{ editando ? 'Actualizar equipo' : 'Guardar equipo' }}</button></div>
    </form>
  </main>
</template>
