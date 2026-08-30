<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const cerrarSesion = () => {
  auth.cerrarSesion()
  router.push('/login')
}
</script>

<template>
  <header class="barra-navegacion">
    <div>
      <p class="marca-pequena">Fundacite Sucre</p>
      <strong>Coordinacion de Telematica</strong>
    </div>
    <nav>
      <RouterLink to="/inventario">Inventario</RouterLink>
      <RouterLink v-if="['TECNICO', 'COORDINADOR', 'SUPERADMIN'].includes(auth.rol)" to="/equipos/nuevo">
        Nuevo equipo
      </RouterLink>
      <RouterLink v-if="['TECNICO', 'COORDINADOR', 'SUPERADMIN'].includes(auth.rol)" to="/equipos/carga-multiple">Carga multiple</RouterLink>
      <RouterLink v-if="auth.rol === 'SUPERADMIN'" to="/usuarios">Usuarios y roles</RouterLink>
      <button class="btn-secundario" type="button" @click="cerrarSesion">Cerrar sesión</button>
    </nav>
  </header>
</template>
