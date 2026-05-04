import { createRouter, createWebHistory } from 'vue-router'  // IF IT DOESN'T WORK COPY THIS TO TERMINAL "npm install vue-router"

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
  history: createWebHistory(), 
  routes
})

export default router