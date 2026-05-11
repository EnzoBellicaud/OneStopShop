import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '../Home.vue'
import Landing from '../Landing.vue'
import Login from '../Login.vue'
import Student from '../components/sections/Student.vue'
import Staff from '../components/sections/Staff.vue'
import External from '../components/sections/External.vue'
import UserProfile from '../components/sections/UserProfile.vue'

const routes = [
  { path: '/home', name: 'home', component: HomeView },
  { path: '/', name: 'landing', component: Landing },
  { path: '/login', name: 'login', component: Login },
  { path: '/student', name: 'student', component: Student },
  { path: '/staff', name: 'staff', component: Staff },
  { path: '/external_user', name: 'externaluser', component: External },
  {
    path: '/user_profile',
    name: 'UserProfile',
    component: UserProfile,
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth && !localStorage.getItem('access_token')) {
    next({ path: '/login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
