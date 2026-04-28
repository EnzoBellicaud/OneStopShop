import { createRouter, createWebHistory } from 'vue-router'
import OneStopShop from './OneStopShop.vue'
import Auth from './pages/Auth.vue'

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
  }
]

export const router = createRouter({
  history: createWebHistory(),
  routes
})
