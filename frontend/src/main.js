import { createApp } from 'vue';
import App from '../App.vue';
import MiniSiteView from './components/MiniSiteView.vue';
import './styles/design-tokens.css';
import { vuetify } from './plugins/vuetify.js';
import { initializeMobileRuntime } from './mobile/runtime.js';
import { registerThemeDebugHelpers } from './theme-debug.js';

initializeMobileRuntime();
registerThemeDebugHelpers();

// Check if this is a mini site route (e.g., /club/{clubCode}/)
const isMiniSiteRoute = () => {
  const pathArray = window.location.pathname.split('/');
  return pathArray.length >= 3 && pathArray[1] === 'club';
};

// Mount the appropriate component based on the route
const rootComponent = isMiniSiteRoute() ? MiniSiteView : App;

createApp(rootComponent).use(vuetify).mount('#app');