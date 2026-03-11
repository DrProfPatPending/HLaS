<template>
  <div id="app">
    <!-- Header bar -->
    <table class="logo-table">
      <tbody>
        <tr>
          <td class="logo-cell">
            <a href="/" aria-label="Go to member login">
              <img src="./logos/HLaS.png" alt="HLaS logo" class="app-logo" />
            </a>
          </td>
          <td class="admin-title-cell">
            <span class="admin-title">Club Administration</span>
          </td>
          <td class="logo-spacer"></td>
          <td v-if="loggedIn" class="logout-cell">
            <button type="button" class="logout-button" @click="logout">Log Out</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Admin login -->
    <div v-if="!loggedIn" class="login-container">
      <h2>Admin Login</h2>
      <form @submit.prevent="login">
        <div class="form-field">
          <label for="admin-username">Username:</label>
          <input id="admin-username" v-model="loginUsername" placeholder="Username" required />
        </div>
        <div class="form-field">
          <label for="admin-password">Password:</label>
          <input id="admin-password" v-model="loginPassword" type="password" placeholder="Password" required />
        </div>
        <button type="submit">Login</button>
      </form>
      <div v-if="loginError" class="error-msg">{{ loginError }}</div>
    </div>

    <!-- Club management -->
    <div v-else class="admin-container">
      <h1>Clubs Configuration</h1>

      <div v-if="statusMsg" :class="statusMsgError ? 'error-msg' : 'success-msg'">{{ statusMsg }}</div>

      <!-- Clubs table -->
      <table class="clubs-table">
        <thead>
          <tr>
            <th>Short Name</th>
            <th>Full Name</th>
            <th>Website URL</th>
            <th>Admin Email</th>
            <th>Description</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="club in clubs" :key="club.shortName">
            <!-- Read-only row -->
            <tr v-if="editingShortName !== club.shortName">
              <td>{{ club.shortName }}</td>
              <td>{{ club.fullName }}</td>
              <td>
                <a v-if="club.websiteUrl" :href="club.websiteUrl" target="_blank" rel="noopener noreferrer">{{ club.websiteUrl }}</a>
                <span v-else>-</span>
              </td>
              <td>
                <a v-if="club.adminEmail" :href="`mailto:${club.adminEmail}`">{{ club.adminEmail }}</a>
                <span v-else>-</span>
              </td>
              <td class="desc-cell">{{ club.description }}</td>
              <td class="actions-cell">
                <button type="button" @click="startEdit(club)">Edit</button>
                <button type="button" class="delete-btn" @click="deleteClub(club.shortName)">Delete</button>
              </td>
            </tr>
            <!-- Inline edit row -->
            <tr v-else class="edit-row">
              <td><input v-model="editForm.shortName" disabled class="field-input short-input" title="Short name cannot be changed" /></td>
              <td><input v-model="editForm.fullName" class="field-input" /></td>
              <td><input v-model="editForm.websiteUrl" class="field-input" /></td>
              <td><input v-model="editForm.adminEmail" class="field-input" /></td>
              <td><textarea v-model="editForm.description" class="field-input desc-textarea" rows="3"></textarea></td>
              <td class="actions-cell">
                <button type="button" class="save-btn" @click="saveEdit">Save</button>
                <button type="button" @click="cancelEdit">Cancel</button>
              </td>
            </tr>
          </template>
        </tbody>
      </table>

      <!-- Add new club -->
      <h2>Add New Club</h2>
      <table class="clubs-table">
        <thead>
          <tr>
            <th>Short Name</th>
            <th>Full Name</th>
            <th>Website URL</th>
            <th>Admin Email</th>
            <th>Description</th>
            <th>Logo (PNG)</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><input v-model="newClub.shortName" class="field-input short-input" placeholder="e.g. ABC" /></td>
            <td><input v-model="newClub.fullName" class="field-input" placeholder="Full club name" /></td>
            <td><input v-model="newClub.websiteUrl" class="field-input" placeholder="https://..." /></td>
            <td><input v-model="newClub.adminEmail" class="field-input" placeholder="admin@example.com" /></td>
            <td><textarea v-model="newClub.description" class="field-input desc-textarea" rows="3" placeholder="Club description"></textarea></td>
            <td>
              <input
                ref="newClubLogoInput"
                type="file"
                accept="image/png"
                class="field-input"
                @change="onNewClubLogoChange"
              />
            </td>
            <td class="actions-cell">
              <button type="button" class="save-btn" @click="addClub">Add Club</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

const API_BASE_URL = process.env.VUE_APP_BACKEND_URL || `${window.location.protocol}//${window.location.hostname}:5050`;

export default {
  data() {
    return {
      loggedIn: false,
      adminToken: null,
      loginUsername: '',
      loginPassword: '',
      loginError: '',
      clubs: [],
      editingShortName: null,
      editForm: {},
      newClub: { shortName: '', fullName: '', websiteUrl: '', adminEmail: '', description: '' },
      newClubLogoFile: null,
      statusMsg: '',
      statusMsgError: false,
    };
  },
  created() {
    // Restore session from localStorage if available
    const saved = localStorage.getItem('hlasAdminToken');
    if (saved) {
      this.adminToken = saved;
      this.loggedIn = true;
      this.loadClubs();
    }
  },
  methods: {
    authHeaders() {
      return { Authorization: `Bearer ${this.adminToken}` };
    },
    showStatus(msg, isError = false) {
      this.statusMsg = msg;
      this.statusMsgError = isError;
      setTimeout(() => { this.statusMsg = ''; }, 4000);
    },
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
            this.loadClubs();
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
    },
    loadClubs() {
      axios.get(`${API_BASE_URL}/admin/clubs`, { headers: this.authHeaders() })
        .then(res => { this.clubs = res.data.clubs || []; })
        .catch(err => {
          if (err.response?.status === 401) {
            this.logout();
          }
        });
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
    addClub() {
      if (!this.newClub.shortName.trim()) {
        this.showStatus('Short Name is required.', true);
        return;
      }
      const formData = new FormData();
      formData.append('shortName', this.newClub.shortName);
      formData.append('fullName', this.newClub.fullName);
      formData.append('websiteUrl', this.newClub.websiteUrl);
      formData.append('adminEmail', this.newClub.adminEmail);
      formData.append('description', this.newClub.description);
      if (this.newClubLogoFile) {
        formData.append('logoFile', this.newClubLogoFile);
      }

      axios.post(`${API_BASE_URL}/admin/clubs`, formData, { headers: this.authHeaders() })
        .then(() => {
          this.newClub = { shortName: '', fullName: '', websiteUrl: '', adminEmail: '', description: '' };
          this.newClubLogoFile = null;
          if (this.$refs.newClubLogoInput) {
            this.$refs.newClubLogoInput.value = '';
          }
          this.loadClubs();
          this.showStatus('Club added successfully.');
        })
        .catch(err => {
          this.showStatus(err.response?.data?.error || 'Add failed', true);
        });
    },
  },
};
</script>

<style>
body {
  margin: 0;
  font-family: Helvetica, Arial, sans-serif;
}
#app .logo-table {
  width: 100%;
  border-collapse: collapse;
  background: #f8f8f8;
  border-bottom: 1px solid #ddd;
  padding: 4px 0;
}
#app .logo-cell {
  padding: 4px 10px;
  vertical-align: middle;
}
#app .app-logo {
  height: 50px;
  cursor: default;
}
#app .admin-title-cell {
  vertical-align: middle;
  padding-left: 12px;
}
#app .admin-title {
  font-size: 18pt;
  font-weight: bold;
  color: #333;
}
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
</style>
