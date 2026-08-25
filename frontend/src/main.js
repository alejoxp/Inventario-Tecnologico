import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import './assets/global.css'

// Monta el componente raiz sobre el nodo definido en index.html.
createApp(App).use(createPinia()).use(router).mount('#app')
