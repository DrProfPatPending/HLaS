<template>
  <v-app id="admin-app">
    <AdminHeader :loggedIn="loggedIn" @logout="logout" />
    <div v-if="!loggedIn" class="admin-login-container">
      <h2>Admin Login</h2>
      <form @submit.prevent="login">
        <div class="admin-form-row">
          <label class="admin-form-label">Username:</label>
          <input v-model="loginUsername" class="admin-form-input" type="text" autocomplete="username" required />
          <div class="remember-me-row">
            <label class="remember-me-label">
              <input type="checkbox" v-model="rememberMe" class="remember-me-checkbox" />
              <span>Remember me</span>
            </label>
          </div>
        </div>
        <div class="admin-form-row">
          <label class="admin-form-label">Password:</label>
          <input v-model="loginPassword" class="admin-form-input" type="password" autocomplete="current-password" required />
        </div>
        <div v-if="loginError" class="error-msg admin-login-error">{{ loginError }}</div>
        <app-button type="submit" class="admin-login-submit" inherit-style>Login</app-button>
      </form>
    </div>
    <div v-else class="admin-container">
      <app-card class="admin-info-box" inherit-style>
        <strong>Welcome to the Admin section of 'HookLineAndSinker' (HLaS)</strong><br>
        This page allows you to manage the application itself, configure the available Clubs, and sort out any issues with user logins, roles, and more. Use the tabs below to access different areas of administration.
      </app-card>
      <div class="admin-tab-nav">
        <app-button
          v-for="tab in tabs"
          :key="tab.key"
          type="button"
          inherit-style
          class="admin-tab-btn"
          :class="{ 'admin-tab-btn-active': activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </app-button>
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
  </v-app>
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
import AppButton from './src/components/ui/AppButton.vue';
import AppCard from './src/components/ui/AppCard.vue';

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
    AppButton,
    AppCard,
  },
  data() {
    return {
      loginUsername: '',
      loginPassword: '',
      loginError: '',
      loggedIn: !!getAdminToken(),
      activeTab: 'appSettings',
      tabs,
      rememberMe: false,
    };
  },
  methods: {
    login() {
      this.loginError = '';
      // Store username if rememberMe checked, else clear
      if (this.rememberMe) {
        window.localStorage.setItem('hlas.adminRememberedUsername', this.loginUsername);
      } else {
        window.localStorage.removeItem('hlas.adminRememberedUsername');
      }
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
      mounted() {
        // Prefill admin username if remembered
        const remembered = window.localStorage.getItem('hlas.adminRememberedUsername');
        if (remembered) {
          this.loginUsername = remembered;
          this.rememberMe = true;
        }
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

:deep(.admin-login-submit.app-button) {
  margin-top: 10px;
  padding: 7px 20px;
  border-radius: 6px;
  border: 1px solid #b7cfe9;
  background: linear-gradient(180deg, #eaf3ff 0%, #dcecff 100%);
  color: #566273;
  font-size: 10pt;
  font-family: Helvetica, Arial, sans-serif;
  font-weight: 600;
}

:deep(.admin-login-submit.app-button .v-btn__content) {
  color: #566273;
}

:deep(.admin-login-submit.app-button:hover) {
  background: linear-gradient(180deg, #e3efff 0%, #d2e6ff 100%);
  box-shadow: 0 5px 14px rgba(92, 128, 168, 0.2);
}

:deep(.admin-tab-btn.app-button) {
  padding: 8px 18px;
  border-radius: 6px;
  border: 1px solid #b7cfe9;
  background: linear-gradient(180deg, #eaf3ff 0%, #dcecff 100%);
  color: #566273;
  font-size: 9pt;
  font-family: Helvetica, Arial, sans-serif;
  font-weight: 600;
  transition: transform 0.12s ease, box-shadow 0.12s ease, background 0.12s ease;
}

:deep(.admin-tab-btn.app-button .v-btn__content) {
  color: #566273;
}

:deep(.admin-tab-btn.app-button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 5px 14px rgba(92, 128, 168, 0.2);
  background: linear-gradient(180deg, #e3efff 0%, #d2e6ff 100%);
}

:deep(.admin-tab-btn.admin-tab-btn-active.app-button) {
  background: linear-gradient(180deg, #d6e8ff 0%, #c2dcff 100%);
  border-color: #8fb5e3;
  box-shadow: 0 5px 14px rgba(83, 123, 170, 0.26), inset 0 0 0 1px rgba(255, 255, 255, 0.35);
  color: #2f4b67;
}

:deep(.admin-tab-btn.admin-tab-btn-active.app-button .v-btn__content) {
  color: #2f4b67;
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

.remember-me-row {
  display: flex;
  align-items: center;
  margin-top: 6px;
}
.remember-me-label {
  display: flex;
  align-items: center;
  font-weight: normal;
  gap: 6px;
}
.remember-me-checkbox {
  margin: 0;
}
</style>
