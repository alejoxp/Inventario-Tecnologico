import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import LoginView from '../views/LoginView.vue'
import InventarioView from '../views/InventarioView.vue'
import FormularioEquipoView from '../views/FormularioEquipoView.vue'
import UsuariosView from '../views/UsuariosView.vue'
import CargaMultipleView from '../views/CargaMultipleView.vue'
import SolicitudPrestamoView from '../views/SolicitudPrestamoView.vue'
import CalendarioPrestamosView from '../views/CalendarioPrestamosView.vue'
import PrestamosView from '../views/PrestamosView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView, meta: { publico: true } },
    { path: '/', redirect: '/inventario' },
    { path: '/inventario', component: InventarioView },
    { path: '/equipos/nuevo', component: FormularioEquipoView, meta: { roles: ['TECNICO', 'COORDINADOR', 'SUPERADMIN'] } },
    { path: '/equipos/carga-multiple', component: CargaMultipleView, meta: { roles: ['TECNICO', 'COORDINADOR', 'SUPERADMIN'] } },
    { path: '/equipos/:id/editar', component: FormularioEquipoView, meta: { roles: ['TECNICO', 'COORDINADOR', 'SUPERADMIN'] } },
    { path: '/usuarios', component: UsuariosView, meta: { roles: ['SUPERADMIN'] } },
    { path: '/prestamos/nuevo', component: SolicitudPrestamoView },
    { path: '/prestamos/calendario', component: CalendarioPrestamosView },
    { path: '/prestamos', component: PrestamosView },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.publico && !auth.autenticado) return '/login'
  if (to.meta.roles && !to.meta.roles.includes(auth.rol)) return '/inventario'
  if (to.path === '/login' && auth.autenticado) return '/inventario'
})

export default router
