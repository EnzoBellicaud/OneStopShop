import { createRouter, createWebHistory } from 'vue-router'
import OneStopShop from './OneStopShop.vue'
import Auth from './pages/Auth.vue'

const routes = [
  { path: '/', component: OneStopShop, name: 'Home' },
  { path: '/auth', component: Auth, name: 'Auth', meta: { guestOnly: true } },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.guestOnly && token) return '/'
})
