import { createRouter, createWebHistory } from 'vue-router'  // IF IT DOESN'T WORK COPY THIS TO TERMINAL "npm install vue-router"

import HomeView from '../Home.vue'
import Landing from '../Landing.vue'
import Student from '../components/sections/Student.vue'
import Staff from '../components/sections/Staff.vue'
import External from '../components/sections/External.vue'

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
  {
    path: '/student',
    name: 'student',
    component: Student
  },
  {
    path: '/staff',
    name: 'staff',
    component: Staff
  },
  {
    path: '/external_user',
    name: 'externaluser',
    component: External
  }
]

const router = createRouter({
  history: createWebHistory(), 
  routes
})

export default router