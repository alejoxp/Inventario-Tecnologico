<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../services/api'

const auth = useAuthStore()
const router = useRouter()
const olvidadosCount = ref(0)

const cerrarSesion = () => {
  auth.cerrarSesion()
  router.push('/login')
}

async function verificarPrestamosOlvidados() {
  if (!auth.autenticado) return
  try {
    const { data } = await api.get('/prestamos')
    olvidadosCount.value = data.filter((p) => p.estado_temporal_equipo === 'Olvidado').length
  } catch {
    // Si falla o no tiene conexión, ignorar silenciosamente
  }
}

onMounted(() => {
  verificarPrestamosOlvidados()
})
</script>

<template>
  <header class="barra-navegacion">
    <div>
      <p class="marca-pequena">Fundacite Sucre</p>
      <strong>Coordinacion de Telematica</strong>
    </div>
    <nav>
      <RouterLink to="/inventario">Inventario</RouterLink>
      <RouterLink to="/prestamos" class="enlace-prestamos">
        Préstamos
        <span
          v-if="olvidadosCount > 0"
          class="badge-nav-alerta"
          :title="`${olvidadosCount} préstamo(s) olvidados o con retraso`"
        >
          {{ olvidadosCount }}
        </span>
      </RouterLink>
      <RouterLink v-if="['TECNICO', 'COORDINADOR', 'SUPERADMIN'].includes(auth.rol)" to="/equipos/nuevo">
        Nuevo equipo
      </RouterLink>
      <RouterLink v-if="['TECNICO', 'COORDINADOR', 'SUPERADMIN'].includes(auth.rol)" to="/equipos/carga-multiple">
        Carga multiple
      </RouterLink>
      <RouterLink v-if="auth.rol === 'SUPERADMIN'" to="/usuarios">
        Usuarios y roles
      </RouterLink>
      <button class="btn-secundario" type="button" @click="cerrarSesion">Cerrar sesión</button>
    </nav>
  </header>
</template>

<style scoped>
.enlace-prestamos {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
.badge-nav-alerta {
  background: #dc2626;
  color: #ffffff;
  font-size: 0.72rem;
  font-weight: 800;
  padding: 0.1rem 0.45rem;
  border-radius: 10px;
  animation: pulso-alerta 2s infinite ease-in-out;
}
@keyframes pulso-alerta {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.15);
    opacity: 0.85;
  }
}
</style>
