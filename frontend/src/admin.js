import { createApp } from 'vue';
import AdminApp from '../AdminApp.vue';
import './styles/design-tokens.css';
import './styles/admin-base.css';
import { vuetify } from './plugins/vuetify.js';
import { initializeMobileRuntime } from './mobile/runtime.js';
import { registerThemeDebugHelpers } from './theme-debug.js';

initializeMobileRuntime();
registerThemeDebugHelpers();

createApp(AdminApp).use(vuetify).mount('#app');
