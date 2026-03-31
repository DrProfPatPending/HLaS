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

import AppUsers from './src/components/admin/AppUsers.vue';
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
#app .logo-spacer {
  width: 100%;
}
#app .logout-cell {
  padding: 4px 12px;
  white-space: nowrap;
  vertical-align: middle;
}
#app .logout-button {
  padding: 6px 14px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 9pt;
  cursor: pointer;
}
#app .login-container {
  max-width: 420px;
  margin: 60px auto;
}
#app .login-container h2 {
  margin-bottom: 20px;
}
#app .form-field {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
#app .form-field label {
  width: 90px;
  font-size: 10pt;
}
#app .form-field input {
  flex: 1;
  padding: 6px;
  font-size: 10pt;
  font-family: Helvetica, Arial, sans-serif;
}
#app .login-container button[type="submit"] {
  margin-top: 10px;
  padding: 7px 20px;
  font-size: 10pt;
  font-family: Helvetica, Arial, sans-serif;
  cursor: pointer;
}
#app .admin-container {
  max-width: 1200px;
  margin: 24px auto;
  padding: 0 16px;
}
#app .admin-info-box {
  background: #f8f8fc;
  border: 1px solid #bcd;
  border-radius: 7px;
  padding: 18px 22px;
  margin-bottom: 24px;
  font-size: 11pt;
  color: #223;
  box-shadow: 0 2px 8px rgba(180,200,220,0.07);
}
#app .admin-container h1 {
  font-size: 16pt;
  margin-bottom: 14px;
}
#app .admin-container h2 {
  font-size: 13pt;
  margin-top: 30px;
  margin-bottom: 10px;
}
#app .clubs-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9pt;
  margin-bottom: 16px;
}
#app .clubs-table th,
#app .clubs-table td {
  border: 1px solid #ccc;
  padding: 7px 9px;
  text-align: left;
  vertical-align: top;
}
#app .clubs-table th {
  background: #f0f0f0;
  font-size: 10pt;
  white-space: nowrap;
}
#app .clubs-table .desc-cell {
  max-width: 280px;
  font-size: 8.5pt;
  color: #444;
}
#app .clubs-table .actions-cell {
  white-space: nowrap;
  text-align: center;
  vertical-align: middle;
}
#app .clubs-table .actions-cell button {
  margin: 2px 3px;
  padding: 4px 10px;
  font-size: 8.5pt;
  font-family: Helvetica, Arial, sans-serif;
  cursor: pointer;
}
#app .delete-btn {
  color: #c00;
}
#app .save-btn {
  background: #2a7;
  color: white;
  border: 1px solid #1a6;
}
#app .edit-row {
  background: #fffbe6;
}
#app .field-input {
  width: 100%;
  box-sizing: border-box;
  padding: 5px;
  font-size: 9pt;
  font-family: Helvetica, Arial, sans-serif;
  border: 1px solid #aaa;
}
#app .short-input {
  width: 90px;
}
#app .desc-textarea {
  resize: vertical;
}
#app .smtp-club-selector {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}
#app .smtp-form-panel {
  background: #fafafa;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 16px 20px;
  margin-bottom: 30px;
  max-width: 860px;
}
#app .smtp-form-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 14px;
}
#app .smtp-form-table td {
  padding: 6px 8px;
  vertical-align: middle;
  font-size: 9pt;
}
#app .smtp-label {
  width: 110px;
  font-weight: 600;
  white-space: nowrap;
  color: #333;
}
#app .smtp-hint {
  color: #666;
  font-size: 8.5pt;
  padding-left: 12px;
}
#app .smtp-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
#app .error-msg {
  color: #c00;
  margin: 8px 0;
  font-size: 10pt;
}
#app .success-msg {
  color: #1a7a3a;
  margin: 8px 0;
  font-size: 10pt;
}
/* ── Tab navigation ───────────────────────────────────────────────────────── */
#app .tab-nav {
  display: flex;
  gap: 4px;
  border-bottom: 2px solid #ccc;
  margin-bottom: 20px;
}
#app .tab-btn {
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
#app .tab-btn-active {
  background: #fff;
  border-color: #ccc;
  border-bottom: 2px solid #fff;
  margin-bottom: -2px;
  color: #111;
  font-weight: bold;
}
/* ── User Administration panel ────────────────────────────────────────────── */
#app .ua-panel {
  background: #fafafa;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 16px 20px;
  margin-bottom: 28px;
  max-width: 900px;
}
#app .ua-search-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
#app .ua-hint {
  font-size: 9pt;
  color: #888;
}
#app .ua-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9pt;
  margin-bottom: 10px;
}
#app .ua-table th,
#app .ua-table td {
  border: 1px solid #ccc;
  padding: 6px 9px;
  text-align: left;
  vertical-align: middle;
}
#app .ua-table th {
  background: #f0f0f0;
  font-size: 9.5pt;
  white-space: nowrap;
}
#app .roles-cell {
  min-width: 240px;
}
/* Role badges */
#app .role-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 7px;
  border-radius: 12px;
  font-size: 8pt;
  font-weight: 600;
  margin: 2px 3px 2px 0;
  white-space: nowrap;
}
#app .role-app-owner   { background: #4a1a8a; color: #fff; }
#app .role-app-admin   { background: #1a4a8a; color: #fff; }
#app .role-club-admin   { background: #1a6a3a; color: #fff; }
#app .role-club-manager { background: #7a5a1a; color: #fff; }
#app .role-user         { background: #e0e0e0; color: #333; }
#app .role-revoke-btn {
  background: none;
  border: none;
  color: inherit;
  opacity: 0.7;
  cursor: pointer;
  font-size: 11pt;
  line-height: 1;
  padding: 0 0 0 2px;
}
#app .role-revoke-btn:hover {
  opacity: 1;
}
#app .ua-add-role-btn {
  display: inline-block;
  font-size: 8pt;
  padding: 2px 7px;
  border-radius: 12px;
  border: 1px dashed #999;
  background: none;
  color: #555;
  cursor: pointer;
  margin-left: 2px;
}
#app .ua-add-role-btn:hover {
  border-color: #444;
  color: #222;
}
/* ── Modal ────────────────────────────────────────────────────────────────── */
#app .modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
#app .modal-box {
  background: #fff;
  border-radius: 8px;
  padding: 28px 32px;
  min-width: 420px;
  max-width: 520px;
  box-shadow: 0 8px 32px rgba(0,0,0,.25);
}
#app .modal-actions {
  margin-top: 16px;
  display: flex;
  align-items: center;
}
</style>
