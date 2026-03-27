
// Admin-only store for admin UI (no club/member logic)
import { reactive } from 'vue';
import axios from 'axios';

const API_BASE_URL =
  window.API_BASE_URL ||
  (window.location.origin.includes('localhost')
    ? 'http://localhost:5000/api'
    : '/api');

const state = reactive({
  adminToken: localStorage.getItem('hlasAdminToken') || null,
  loginUsername: '',
  loginPassword: '',
  loginError: '',
  loggedIn: !!localStorage.getItem('hlasAdminToken'),
  statusMsg: '',
  statusMsgError: false,
  // Add admin/system-only state here
});

const methods = {
  authHeaders() {
    return { Authorization: `Bearer ${state.adminToken}` };
  },
  showStatus(msg, isError = false) {
    state.statusMsg = msg;
    state.statusMsgError = isError;
    setTimeout(() => { state.statusMsg = ''; }, 4000);
  },
  login() {
    state.loginError = '';
    axios.post(`${API_BASE_URL}/admin/login`, {
      username: state.loginUsername,
      password: state.loginPassword,
    })
      .then(res => {
        if (res.data.success) {
          state.adminToken = res.data.token;
          localStorage.setItem('hlasAdminToken', state.adminToken);
          state.loggedIn = true;
          state.loginPassword = '';
        } else {
          state.loginError = res.data.error || 'Login failed';
        }
      })
      .catch(err => {
        state.loginError = err.response?.data?.error || 'Login failed';
      });
  },
  logout() {
    axios.post(`${API_BASE_URL}/admin/logout`, {}, { headers: methods.authHeaders() }).catch(() => {});
    state.adminToken = null;
    localStorage.removeItem('hlasAdminToken');
    state.loggedIn = false;
  },
  // Add admin/system-only methods here
};

export default {
  state,
  methods,
};
