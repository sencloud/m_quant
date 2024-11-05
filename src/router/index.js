import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Backtest from '../views/Backtest.vue'
import Stocks from '../views/StockDataView.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/backtest',
    name: 'Backtest',
    component: Backtest
  },
  {
    path: '/stocks',
    name: 'Stocks',
    component: Stocks
  },
  {
    path: '/trading',
    name: 'Trading',
    component: () => import('../views/Trading.vue')
  },
  {
    path: '/ai',
    name: 'AI',
    component: () => import('../views/AI.vue'),
    meta: {
      title: 'nav.ai',
      icon: 'mdi-brain'
    }
  },
  {
    path: '/blog',
    name: 'Blog',
    component: () => import('../views/BlogView.vue')
  },
  {
    path: '/blog/:id',
    name: 'BlogPost',
    component: () => import('../views/BlogPostView.vue')
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('../views/AboutView.vue')
  },
  {
    path: '/category/:id',
    name: 'Category',
    component: () => import('@/views/CategoryView.vue'),
  },
  {
    path: '/blog/create',
    name: 'CreateBlog',
    component: () => import('@/views/CreateBlogView.vue')
  },
]

const router = createRouter({
  history: createWebHistory('/'),
  routes
})

export default router