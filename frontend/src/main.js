import { createApp } from 'vue';
import App from '../App.vue';
import './styles/design-tokens.css';
import { vuetify } from './plugins/vuetify.js';
import { initializeMobileRuntime } from './mobile/runtime.js';

initializeMobileRuntime();

createApp(App).use(vuetify).mount('#app');