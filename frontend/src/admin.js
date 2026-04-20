import { createApp } from 'vue';
import AdminApp from '../AdminApp.vue';
import './styles/design-tokens.css';
import './styles/admin-base.css';
import { vuetify } from './plugins/vuetify.js';

createApp(AdminApp).use(vuetify).mount('#app');
