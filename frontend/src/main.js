
import { Capacitor } from '@capacitor/core';

initializeMobileRuntime();
registerThemeDebugHelpers();

// Redirect to /club/CTC/ on mobile native launch if at root
if (Capacitor.isNativePlatform() && window.location.pathname === '/') {
	window.location.replace('/club/CTC/');
}

createApp(App).use(vuetify).mount('#app');