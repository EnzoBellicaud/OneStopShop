import { createRouter, createWebHistory } from 'vue-router'
import OneStopShop from './OneStopShop.vue'
import Auth from './pages/Auth.vue'

const routes = [
  { path: '/', component: OneStopShop, name: 'Home' },
  { path: '/auth', component: Auth, name: 'Auth', meta: { guestOnly: true } },
  {
    path: '/offers',
    component: () => import('./pages/OffersPage.vue'),
    name: 'Offers',
  },
  {
    path: '/offers/:id',
    component: () => import('./pages/OfferDetailPage.vue'),
    name: 'OfferDetail',
  },
  {
    path: '/profile',
    component: () => import('./pages/ProfilePage.vue'),
    name: 'Profile',
    meta: { requiresAuth: true },
  },
  {
    path: '/:pathMatch(.*)*',
    component: () => import('./pages/NotFoundPage.vue'),
    name: 'NotFound',
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  // Presence-only check — expiry is handled by api/client.js (401 → refresh → clearAuth).
  // A stale token here keeps guestOnly routes blocked until the next API call fails.
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth && !token) {
    return { name: 'Auth', query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && token) {
    return { name: 'Home' }
  }
})
