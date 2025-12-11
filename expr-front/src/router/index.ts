import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import ChatDetail from '../views/ChatDetail.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: ChatView,
    },
    {
      path: '/chat',
      name: 'chat-new',
      component: ChatDetail,
    },
    {
      path: '/chat/:id',
      name: 'chat-detail',
      component: ChatDetail,
    }
  ],
})

export default router
