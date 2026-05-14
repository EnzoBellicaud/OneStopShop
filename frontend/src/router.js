import { createRouter, createWebHistory } from 'vue-router'

import OneStopShop from './OneStopShop.vue'
import Auth from './pages/Auth.vue'
import Dashboard from './pages/Dashboard.vue'

const routes = [
  {
    path: '/',
    component: OneStopShop,
    name: 'Home'
  },
  {
    path: '/auth',
    component: Auth,
    name: 'Auth'
  },
  {
    path: '/dashboard',
    component: Dashboard,
    name: 'Dashboard'
  }
]

export const router = createRouter({
  history: createWebHistory(),
  routes
})