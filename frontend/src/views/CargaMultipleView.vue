<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '../components/Navbar.vue'
import api from '../services/api'

const router = useRouter()
const marcas = ref([])
const tipos = ref([])
const ubicaciones = ref([])
const error = ref('')
const guardando = ref(false)

function nuevaComputadora() {
  return {
    bien_nacional: '', serial: '', mac: '', modelo: '', marca_id: '', marca_detalle: '',
    tipo_id: '', ubicacion_id: '', custodio: '', estado: 'Operativo', observaciones: '',
    especificaciones: { cpu: '', ram: '' },
  }
}

const equipos = reactive([nuevaComputadora(), nuevaComputadora()])

function esOtro(equipo) {
  return marcas.value.find((marca) => String(marca.id) === String(equipo.marca_id))?.nombre === 'Otro'
}

function requiereEspecificaciones(equipo) {
  const nombre = tipos.value.find((tipo) => String(tipo.id) === String(equipo.tipo_id))?.nombre || ''
  return ['laptop', 'cpu', 'servidor'].includes(nombre.toLowerCase())
}

function ubicacionesDisponibles(equipo) {
  return equipo.estado === 'Desincorporado' ? ubicaciones.value.filter((ubicacion) => ubicacion.nombre === 'Deposito') : ubicaciones.value.filter((ubicacion) => ubicacion.nombre !== 'Deposito')
}

function ajustarUbicacion(equipo) {
  if (equipo.estado === 'Desincorporado') equipo.ubicacion_id = ubicaciones.value.find((ubicacion) => ubicacion.nombre === 'Deposito')?.id || ''
  else if (ubicaciones.value.find((ubicacion) => String(ubicacion.id) === String(equipo.ubicacion_id))?.nombre === 'Deposito') equipo.ubicacion_id = ''
}

function agregarFila() { equipos.push(nuevaComputadora()) }
function quitarFila(index) { if (equipos.length > 1) equipos.splice(index, 1) }

onMounted(async () => {
  try {
    const { data } = await api.get('/catalogos')
    marcas.value = data.marcas
    tipos.value = data.tipos
    ubicaciones.value = data.ubicaciones
  } catch {
    error.value = 'No se pudieron cargar los catalogos.'
  }
})

async function guardarLote() {
  guardando.value = true
  error.value = ''
  const payload = equipos.map((equipo) => {
    const fila = {
      ...equipo,
      marca_id: Number(equipo.marca_id),
      tipo_id: Number(equipo.tipo_id),
      ubicacion_id: Number(equipo.ubicacion_id),
      marca_detalle: esOtro(equipo) ? equipo.marca_detalle : null,
    }
    if (!requiereEspecificaciones(equipo)) delete fila.especificaciones
    return fila
  })
  try {
    await api.post('/equipos/lote', { equipos: payload })
    router.push('/inventario')
  } catch (requestError) {
    error.value = requestError.response?.data?.detail || 'No se pudo registrar el lote completo.'
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <Navbar />
  <main class="contenido">
    <div class="encabezado-vista">
      <div><p class="etiqueta">Carga patrimonial</p><h1>Varias computadoras</h1></div>
      <button class="btn-secundario" type="button" @click="agregarFila">+ Agregar computadora</button>
    </div>
    <p class="ayuda-formulario">Cada fila puede tener una oficina y un custodio diferente. El lote se guarda completo.</p>
    <form @submit.prevent="guardarLote">
      <section v-for="(equipo, index) in equipos" :key="index" class="bloque-lote tarjeta-sombra">
        <div class="fila-lote-titulo"><h2>Computadora {{ index + 1 }}</h2><button v-if="equipos.length > 1" class="btn-peligro btn-pequeno" type="button" @click="quitarFila(index)">Quitar</button></div>
        <div class="formulario formulario-lote">
          <label class="campo-label">Bien nacional<input v-model="equipo.bien_nacional" class="input-form" required /></label>
          <label class="campo-label">Serial<input v-model="equipo.serial" class="input-form" required /></label>
          <label class="campo-label">MAC Address<input v-model="equipo.mac" class="input-form" /></label>
          <label class="campo-label">Modelo<input v-model="equipo.modelo" class="input-form" required /></label>
          <label class="campo-label">Marca<select v-model="equipo.marca_id" class="input-form" required><option value="" disabled>Seleccione</option><option v-for="marca in marcas" :key="marca.id" :value="marca.id">{{ marca.nombre }}</option></select></label>
          <label v-if="esOtro(equipo)" class="campo-label">Nombre de marca<input v-model="equipo.marca_detalle" class="input-form" placeholder="Ejemplo: Djaua" required /></label>
          <label class="campo-label">Oficina<select v-model="equipo.ubicacion_id" class="input-form" required><option value="" disabled>Seleccione</option><option v-for="ubicacion in ubicacionesDisponibles(equipo)" :key="ubicacion.id" :value="ubicacion.id">{{ ubicacion.nombre }}</option></select></label>
          <label class="campo-label">Custodio<input v-model="equipo.custodio" class="input-form" maxlength="150" placeholder="Nombre de la persona" /></label>
          <label class="campo-label">Tipo<select v-model="equipo.tipo_id" class="input-form" required><option value="" disabled>Seleccione</option><option v-for="tipo in tipos" :key="tipo.id" :value="tipo.id">{{ tipo.nombre }}</option></select></label>
          <label class="campo-label">Estado<select v-model="equipo.estado" class="input-form" @change="ajustarUbicacion(equipo)"><option>Operativo</option><option>Dañado</option><option>En Reparación</option><option>Desincorporado</option></select></label>
          <template v-if="requiereEspecificaciones(equipo)"><label class="campo-label">CPU<input v-model="equipo.especificaciones.cpu" class="input-form" required /></label><label class="campo-label">RAM<input v-model="equipo.especificaciones.ram" class="input-form" required /></label></template>
        </div>
      </section>
      <p v-if="error" class="mensaje-error">{{ error }}</p>
      <div class="acciones"><RouterLink class="btn-secundario" to="/inventario">Cancelar</RouterLink><button class="btn-primario" type="submit" :disabled="guardando">{{ guardando ? 'Guardando...' : `Guardar ${equipos.length} computadoras` }}</button></div>
    </form>
  </main>
</template>
