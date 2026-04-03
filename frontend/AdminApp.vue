<template>
    <div id="admin-app">
      <AdminHeader :loggedIn="loggedIn" @logout="logout" />
      <div v-if="!loggedIn" class="login-container">
        <h2>Admin Login</h2>
        <form @submit.prevent="login">
          <div class="form-field">
            <label>Username:</label>
            <input v-model="loginUsername" type="text" autocomplete="username" required />
          </div>
          <div class="form-field">
            <label>Password:</label>
            <input v-model="loginPassword" type="password" autocomplete="current-password" required />
          </div>
          <div v-if="loginError" class="error-msg" style="margin-bottom:10px;">{{ loginError }}</div>
          <button type="submit" class="save-btn">Login</button>
        </form>
      </div>
      <div v-else class="admin-container">
        <!-- ===== Admin Welcome/Info Box ===== -->
        <div class="admin-info-box">
          <strong>Welcome to the Admin section of 'HookLineAndSinker' (HLaS)</strong><br>
          This page allows you to manage the application itself, configure the available Clubs, and sort out any issues with user logins, roles, and more. Use the tabs below to access different areas of administration.
        </div>
        <!-- ===== Admin Tab Navigation ===== -->
        <div class="tab-nav">
          <button class="tab-btn" :class="{ 'tab-btn-active': activeTab === 'clubs' }" @click="activeTab = 'clubs'">Clubs</button>
          <button class="tab-btn" :class="{ 'tab-btn-active': activeTab === 'adminUsers' }" @click="activeTab = 'adminUsers'">Admin Users</button>
          <button class="tab-btn" :class="{ 'tab-btn-active': activeTab === 'appUsers' }" @click="activeTab = 'appUsers'">App Users</button>
          <button class="tab-btn" :class="{ 'tab-btn-active': activeTab === 'smtp' }" @click="activeTab = 'smtp'">SMTP</button>
          <button class="tab-btn" :class="{ 'tab-btn-active': activeTab === 'fieldOrder' }" @click="activeTab = 'fieldOrder'">Field Order</button>
        </div>
        <!-- ===== ADMIN USER ADMINISTRATION TAB ===== -->
        <div v-show="activeTab === 'adminUsers'">
          <UserAdmin />
          <div v-if="uaStatusMsg" :class="uaStatusError ? 'error-msg' : 'success-msg'">{{ uaStatusMsg }}</div>
        </div>
        <!-- ===== APP USERS TAB ===== -->
        <div v-show="activeTab === 'appUsers'">
          <AppUsers />
        </div>
        <!-- ===== CLUBS TAB ===== -->
        <div v-show="activeTab === 'clubs'">
          <ClubsConfig />
        </div>
        <!-- ===== SMTP TAB ===== -->
        <div v-show="activeTab === 'smtp'">
          <SMTPSettings />
        </div>
        <!-- ===== FIELD ORDER TAB ===== -->
        <div v-show="activeTab === 'fieldOrder'">
          <FieldOrder />
        </div>
      </div>
    </div>
</template>

<script>


import AdminHeader from './src/components/admin/AdminHeader.vue';
import UserAdmin from './src/components/admin/UserAdmin.vue';
import ClubsConfig from './src/components/admin/ClubsConfig.vue';
import SMTPSettings from './src/components/admin/SMTPSettings.vue';
import FieldOrder from './src/components/admin/FieldOrder.vue';
import adminStore from './src/adminStore.js';
import AppUsers from './src/components/admin/AppUsers.vue';
import axios from 'axios';
import config from './server.config.json';
const API_BASE_URL = config.api.backendUrl;

export default {
  components: {
    AdminHeader,
    UserAdmin,
    AppUsers,
    ClubsConfig,
    SMTPSettings,
    FieldOrder,
  },
  data() {
    return {
      ...adminStore.state,
      loginUsername: '',
      loginPassword: '',
      loginError: '',
      loggedIn: false,
      activeTab: 'clubs',
      // Add other state as needed for your admin UI
    };
  },
  methods: {
    ...adminStore.methods,
    // ...existing code...
    login() {
      this.loginError = '';
      axios.post(`${API_BASE_URL}/admin/login`, {
        username: this.loginUsername,
        password: this.loginPassword,
      })
        .then(res => {
          if (res.data.success) {
            this.adminToken = res.data.token;
            localStorage.setItem('hlasAdminToken', this.adminToken);
            this.loggedIn = true;
            this.loginPassword = '';
            this.loginError = '';
            this.activeTab = 'users';
            this.loadClubs();
            // Debug: call loadFieldOrder after login
            // eslint-disable-next-line no-console
            console.log('[AdminApp.vue] login() success, calling loadFieldOrder()');
            this.loadFieldOrder();
          } else {
            this.loginError = res.data.error || 'Login failed';
          }
        })
        .catch(err => {
          this.loginError = err.response?.data?.error || 'Login failed';
        });
    },
    logout() {
      axios.post(`${API_BASE_URL}/admin/logout`, {}, { headers: this.authHeaders() }).catch(() => {});
      this.adminToken = null;
      localStorage.removeItem('hlasAdminToken');
      this.loggedIn = false;
      this.clubs = [];
      this.loginUsername = '';
      this.loginPassword = '';
      this.loginError = '';
    },
    addClub() {
      if (!this.newClub.shortName.trim()) {
        this.showStatus('Short Name is required.', true);
        return;
      }
      const formData = new FormData();
      // ...existing code for adding a club...
      this.uaMerge.statusMsg = '';
      this.uaMerge.statusError = false;
    },
    startEdit(club) {
      this.editingShortName = club.shortName;
      this.editForm = { ...club };
    },
    cancelEdit() {
      this.editingShortName = null;
      this.editForm = {};
    },
    saveEdit() {
      axios.put(`${API_BASE_URL}/admin/clubs/${encodeURIComponent(this.editingShortName)}`,
        this.editForm,
        { headers: this.authHeaders() })
        .then(() => {
          this.editingShortName = null;
          this.editForm = {};
          this.loadClubs();
          this.showStatus('Club updated successfully.');
        })
        .catch(err => {
          this.showStatus(err.response?.data?.error || 'Update failed', true);
        });
    },
    deleteClub(shortName) {
      if (!window.confirm(`Delete club "${shortName}"? This cannot be undone.`)) return;
      axios.delete(`${API_BASE_URL}/admin/clubs/${encodeURIComponent(shortName)}`,
        { headers: this.authHeaders() })
        .then(() => {
          this.loadClubs();
          this.showStatus(`Club "${shortName}" deleted.`);
        })
        .catch(err => {
          this.showStatus(err.response?.data?.error || 'Delete failed', true);
        });
    },
    onNewClubLogoChange(event) {
      const file = event.target.files && event.target.files.length ? event.target.files[0] : null;
      if (!file) {
        this.newClubLogoFile = null;
        return;
      }
      const isPngType = file.type === 'image/png' || file.name.toLowerCase().endsWith('.png');
      if (!isPngType) {
        this.newClubLogoFile = null;
        event.target.value = '';
        this.showStatus('Logo must be a PNG file.', true);
        return;
      }
      this.newClubLogoFile = file;
    },
    // ...existing code...
  },
}
</script>

<style scoped>
.login-container {
  max-width: 420px;
  margin: 60px auto;
}
.login-container h2 {
  margin-bottom: 20px;
}
.form-field {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.form-field label {
  width: 90px;
  font-size: 10pt;
}
.form-field input {
  flex: 1;
  padding: 6px;
  font-size: 10pt;
  font-family: Helvetica, Arial, sans-serif;
}
.login-container button[type="submit"] {
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
/* ── Tab navigation ───────────────────────────────────────────────────────── */
.tab-nav {
  display: flex;
  gap: 4px;
  border-bottom: 2px solid #ccc;
  margin-bottom: 20px;
}
.tab-btn {
  padding: 7px 20px;
  font-size: 10pt;
  font-family: Helvetica, Arial, sans-serif;
  background: #f0f0f0;
  border: 1px solid #ccc;
  border-bottom: none;
  cursor: pointer;
  border-radius: 4px 4px 0 0;
  color: #555;
}
.tab-btn-active {
  background: #fff;
  border-color: #ccc;
  border-bottom: 2px solid #fff;
  margin-bottom: -2px;
  color: #111;
  font-weight: bold;
}
</style>
