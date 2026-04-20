import { createApp } from 'vue';
import App from '../App.vue';
import './styles/design-tokens.css';
import { vuetify } from './plugins/vuetify.js';
import { initializeMobileRuntime } from './mobile/runtime.js';
import { registerThemeDebugHelpers } from './theme-debug.js';

initializeMobileRuntime();
registerThemeDebugHelpers();

createApp(App).use(vuetify).mount('#app');