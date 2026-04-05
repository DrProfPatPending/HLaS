<template>
  <div id="admin-app">
    <AdminHeader :loggedIn="loggedIn" @logout="logout" />
    <div v-if="!loggedIn" class="admin-login-container">
      <h2>Admin Login</h2>
      <form @submit.prevent="login">
        <div class="admin-form-row">
          <label class="admin-form-label">Username:</label>
          <input v-model="loginUsername" class="admin-form-input" type="text" autocomplete="username" required />
        </div>
        <div class="admin-form-row">
          <label class="admin-form-label">Password:</label>
          <input v-model="loginPassword" class="admin-form-input" type="password" autocomplete="current-password" required />
        </div>
        <div v-if="loginError" class="error-msg admin-login-error">{{ loginError }}</div>
        <button type="submit" class="save-btn">Login</button>
      </form>
    </div>
    <div v-else class="admin-container">
      <div class="admin-info-box">
        <strong>Welcome to the Admin section of 'HookLineAndSinker' (HLaS)</strong><br>
        This page allows you to manage the application itself, configure the available Clubs, and sort out any issues with user logins, roles, and more. Use the tabs below to access different areas of administration.
      </div>
      <div class="admin-tab-nav">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="admin-tab-btn"
          :class="{ 'admin-tab-btn-active': activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>
      <div v-show="activeTab === 'adminUsers'">
        <UserAdmin />
      </div>
      <div v-show="activeTab === 'appSettings'">
        <AppSettings />
      </div>
      <div v-show="activeTab === 'appUsers'">
        <AppUsers />
      </div>
      <div v-show="activeTab === 'clubs'">
        <ClubsConfig />
      </div>
      <div v-show="activeTab === 'smtp'">
        <SMTPSettings />
      </div>
      <div v-show="activeTab === 'fieldOrder'">
        <FieldOrder />
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import AdminHeader from './src/components/admin/AdminHeader.vue';
import UserAdmin from './src/components/admin/UserAdmin.vue';
import ClubsConfig from './src/components/admin/ClubsConfig.vue';
import SMTPSettings from './src/components/admin/SMTPSettings.vue';
import FieldOrder from './src/components/admin/FieldOrder.vue';
import AppUsers from './src/components/admin/AppUsers.vue';
import AppSettings from './src/components/admin/AppSettings.vue';
import { adminUrl, authHeaders, clearAdminToken, getAdminToken, setAdminToken } from './src/services/adminApi.js';

const tabs = [
  { key: 'appSettings', label: 'App Settings' },
  { key: 'clubs', label: 'Clubs' },
  { key: 'adminUsers', label: 'Admin Users' },
  { key: 'appUsers', label: 'App Users' },
  { key: 'smtp', label: 'SMTP' },
  { key: 'fieldOrder', label: 'Field Order' },
];

export default {
  components: {
    AdminHeader,
    UserAdmin,
    AppUsers,
    ClubsConfig,
    SMTPSettings,
    FieldOrder,
    AppSettings,
  },
  data() {
    return {
      loginUsername: '',
      loginPassword: '',
      loginError: '',
      loggedIn: !!getAdminToken(),
      activeTab: 'appSettings',
      tabs,
    };
  },
  methods: {
    login() {
      this.loginError = '';
      axios.post(adminUrl('/admin/login'), {
        username: this.loginUsername,
        password: this.loginPassword,
      })
        .then(res => {
          if (res.data.success) {
            setAdminToken(res.data.token);
            this.loggedIn = true;
            this.loginPassword = '';
            this.loginError = '';
            this.activeTab = 'appSettings';
          } else {
            this.loginError = res.data.error || 'Login failed';
          }
        })
        .catch(err => {
          this.loginError = err.response?.data?.error || 'Login failed';
        });
    },
    logout() {
      axios.post(adminUrl('/admin/logout'), {}, { headers: authHeaders() }).catch(() => {});
      clearAdminToken();
      this.loggedIn = false;
      this.loginUsername = '';
      this.loginPassword = '';
      this.loginError = '';
      this.activeTab = 'appSettings';
    },
  },
};
</script>

<style scoped>
.admin-login-container {
  max-width: 420px;
  margin: 60px auto;
}

.admin-login-container h2 {
  margin-bottom: 20px;
}

.admin-login-error {
  margin-bottom: 10px;
}

.admin-login-container button[type="submit"] {
  margin-top: 10px;
  padding: 7px 20px;
  font-size: 10pt;
  font-family: Helvetica, Arial, sans-serif;
  cursor: pointer;
}
.admin-container {
  max-width: 1200px;
  margin: 24px auto;
  padding: 0 16px;
}
.admin-info-box {
  background: #f8f8fc;
  border: 1px solid #bcd;
  border-radius: 7px;
  padding: 18px 22px;
  margin-bottom: 24px;
  font-size: 11pt;
  color: #223;
  box-shadow: 0 2px 8px rgba(180,200,220,0.07);
}
</style>
