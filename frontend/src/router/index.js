import { createRouter, createWebHistory } from 'vue-router'
// import HomeView from '../App.vue'
import HomeView from '../Home.vue'
import Landing from '../Landing.vue'


const routes = [
  {
    path: '/home',
    name: 'home',
    component: HomeView
  },
  {
    path: '/',
    name: 'landing',
    component: Landing
  },
]

const router = createRouter({
  history: createWebHistory(), // Używa standardowego paska adresu przeglądarki
  routes
})

export default router