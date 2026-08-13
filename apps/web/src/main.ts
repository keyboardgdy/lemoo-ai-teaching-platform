import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query'
import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import { i18n } from './app/i18n'
import { router } from './app/router'
import './style.css'

const app = createApp(App)
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      staleTime: 30_000,
    },
  },
})

app.use(createPinia())
app.use(i18n)
app.use(router)
app.use(VueQueryPlugin, { queryClient })
app.mount('#app')
