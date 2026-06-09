import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '../Home.vue'
import Landing from '../Landing.vue'
import Login from '../Login.vue'
import Student from '../components/sections/Student.vue'
import Staff from '../components/sections/Staff.vue'
import External from '../components/sections/External.vue'
import UserProfile from '../components/sections/UserProfile.vue'
import Dashboard from '../Dashboard.vue'
import ForumPage from '../pages/ForumPage.vue'
import QuestionDetailPage from '../pages/QuestionDetailPage.vue'
import NewQuestionPage from '../pages/NewQuestionPage.vue'
import VerifyEmail from '../pages/VerifyEmail.vue'

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
  {
    path: '/dashboard',
    name: 'dashboard',
    component: Dashboard,
    meta: { requiresAuth: true },
  },
  { path: '/forum', name: 'Forum', component: ForumPage },
  { path: '/forum/new', name: 'NewQuestion', component: NewQuestionPage, meta: { requiresAuth: true } },
  { path: '/forum/:id', name: 'QuestionDetail', component: QuestionDetailPage },
  { path: '/verify-email', name: 'VerifyEmail', component: VerifyEmail },
  // /admin redirects to dashboard — admin functionality lives in the Angular portal
  { path: '/admin', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth && !token) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }
  next()
})

export default router
