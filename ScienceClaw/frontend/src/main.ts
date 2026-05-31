import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './assets/global.css'
import './assets/theme.css'
import 'highlight.js/styles/github-dark.css'  // 代码高亮样式
import 'katex/dist/katex.min.css'  // KaTeX 数学公式样式
import './utils/toast'
import i18n from './composables/useI18n'
import { getStoredToken, getCachedAuthProvider } from './api/auth'
import { configure } from "vue-gtag";

configure({
  tagId: 'G-XCRZ3HH31S' // Replace with your own Google Analytics tag ID
})

// Create router
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/chat',
      component: () => import('./pages/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          component: () => import('./pages/HomePage.vue'),
          alias: ['/', '/home'],
          meta: { requiresAuth: true }
        },
        {
          path: ':sessionId',
          component: () => import('./pages/ChatPage.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'skills',
          component: () => import('./pages/SkillsPage.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'skills/:skillName',
          component: () => import('@/pages/SkillDetailPage.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'tools',
          component: () => import('./pages/ToolsPage.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'tools/:toolName',
          component: () => import('./pages/ToolDetailPage.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'science-tools/:toolName',
          component: () => import('./pages/ScienceToolDetail.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'tasks',
          component: () => import('./pages/TasksPage.vue'),
          meta: { requiresAuth: true }
        }
      ]
    },
    {
      path: '/share',
      component: () => import('./pages/ShareLayout.vue'),
      children: [
        {
          path: ':sessionId',
          component: () => import('./pages/SharePage.vue'),
        }
      ]
    },
    {
      path: '/login',
      component: () => import('./pages/LoginPage.vue')
    }
  ]
})

// Global route guard
router.beforeEach(async (to, _, next) => {
  const requiresAuth = to.matched.some((record: any) => record.meta?.requiresAuth)
  const hasToken = !!getStoredToken()
  
  if (requiresAuth) {
    const authProvider = await getCachedAuthProvider()
    
    if (authProvider === 'none') {
      next()
      return
    }
    
    if (!hasToken) {
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }
  }
  
  if (to.path === '/login' && hasToken) {
    next('/')
  } else {
    next()
  }
})

const app = createApp(App)

app.use(router)
app.use(i18n)
app.mount('#app')
