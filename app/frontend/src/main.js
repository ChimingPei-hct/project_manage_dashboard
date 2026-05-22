import { createApp } from 'vue'
import App from './App.vue'
import './style.css'
import { tooltipDirective } from './directives/tooltip.js'

const app = createApp(App)
app.directive('tooltip', tooltipDirective)
app.mount('#app')
