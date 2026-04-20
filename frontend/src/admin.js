import { createApp } from 'vue';
import AdminApp from '../AdminApp.vue';
import './styles/design-tokens.css';
import './styles/admin-base.css';
import { vuetify } from './plugins/vuetify.js';
import { initializeMobileRuntime } from './mobile/runtime.js';

initializeMobileRuntime();

createApp(AdminApp).use(vuetify).mount('#app');
