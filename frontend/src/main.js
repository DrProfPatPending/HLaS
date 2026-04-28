

import { initializeMobileRuntime } from './mobile/runtime.js';
import { registerThemeDebugHelpers } from './theme-debug.js';
import { Capacitor } from '@capacitor/core';

import { createApp } from 'vue';
import App from '../App.vue';
import { vuetify } from './plugins/vuetify.js';

initializeMobileRuntime();
registerThemeDebugHelpers();

// Redirect to /club/CTC/ on mobile native launch if at root
if (Capacitor.isNativePlatform() && window.location.pathname === '/') {
	window.location.replace('/club/CTC/');
}

createApp(App).use(vuetify).mount('#app');