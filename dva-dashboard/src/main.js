import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { OhVueIcon, addIcons } from 'oh-vue-icons'
import * as FaIcons from 'oh-vue-icons/icons/fa'
import VueSidebarMenu from 'vue-sidebar-menu'
import 'vue-sidebar-menu/dist/vue-sidebar-menu.css'

import './style.css'
import App from './App.vue'
import RequestsView from './components/RequestsView.vue'
import PresentationsView from './components/PresentationsView.vue'
import CredentialsView from './components/CredentialsView.vue'

const Fa = Object.values({ ...FaIcons })
addIcons(...Fa)

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/requests' },
    { path: '/requests', component: RequestsView },
    { path: '/verifications', component: PresentationsView },
    { path: '/credentials', component: CredentialsView }
  ]
})

const app = createApp(App)
app.component('v-icon', OhVueIcon)
app.use(router)
app.use(VueSidebarMenu)
app.mount('#app')
