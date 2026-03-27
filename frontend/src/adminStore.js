// Admin-specific store.js (initial copy from main store.js)
// TODO: Remove club/member logic and tailor for admin-only state/actions.

import { reactive, computed } from 'vue';
import axios from 'axios';

export const API_BASE_URL =
  window.API_BASE_URL ||
  (window.location.origin.includes('localhost')
    ? 'http://localhost:5000/api'
    : '/api');

export const store = reactive({
  loggedIn: false,
  adminToken: localStorage.getItem('hlasAdminToken') || null,
  loggedInUsername: '',
  // ...other admin-specific state
});

// Add admin-specific computed properties and actions here

export function logout() {
  store.loggedIn = false;
  store.adminToken = null;
  store.loggedInUsername = '';
  localStorage.removeItem('hlasAdminToken');
}

// Add admin-specific API calls and logic here
