<template>
  <div class="clubs-panel">
    <h1>Clubs</h1>
    <div v-if="loading">Loading clubs...</div>
    <form @submit.prevent="addClub" class="club-form">
      <h2>Add New Club</h2>
      <div class="form-row">
        <label>Short Name:</label>
        <input v-model="newClub.shortName" required />
      </div>
      <div class="form-row">
        <label>Full Name:</label>
        <input v-model="newClub.fullName" />
      </div>
      <div class="form-row">
        <label>Description:</label>
        <input v-model="newClub.description" />
      </div>
      <div class="form-row">
        <label>Website:</label>
        <input v-model="newClub.websiteUrl" />
      </div>
      <div class="form-row">
        <label>Admin Email:</label>
        <input v-model="newClub.adminEmail" />
      </div>
      <div class="form-row">
        <label>Logo (PNG):</label>
        <input type="file" accept="image/png" @change="onNewClubLogoChange" />
      </div>
      <div v-if="clubLogoPreview" class="form-row">
        <img :src="clubLogoPreview" alt="Logo Preview" style="max-height:40px;max-width:120px;" />
      </div>
      <div class="form-row">
        <button type="submit" class="save-btn">Add Club</button>
      </div>
      <div v-if="statusMsg" :class="statusMsgError ? 'error-msg' : 'success-msg'">{{ statusMsg }}</div>
    </form>
    <table v-if="clubs.length" class="clubs-table">
      <thead>
        <tr>
          <th>Short Name</th>
          <th>Full Name</th>
          <th>Description</th>
          <th>Website</th>
          <th>Admin Email</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="club in clubs" :key="club.id || club.shortName" :class="{ 'edit-row': editingShortName === club.shortName }">
          <template v-if="editingShortName === club.shortName">
            <td><input v-model="editForm.shortName" disabled /></td>
            <td><input v-model="editForm.fullName" /></td>
            <td><input v-model="editForm.description" /></td>
            <td><input v-model="editForm.websiteUrl" /></td>
            <td><input v-model="editForm.adminEmail" /></td>
            <td class="actions-cell">
              <button class="save-btn" @click="saveEdit">Save</button>
              <button @click="cancelEdit">Cancel</button>
            </td>
          </template>
          <template v-else>
            <td>{{ club.shortName }}</td>
            <td>{{ club.fullName }}</td>
            <td class="desc-cell">{{ club.description }}</td>
            <td><a v-if="club.websiteUrl" :href="club.websiteUrl" target="_blank">{{ club.websiteUrl }}</a></td>
            <td>{{ club.adminEmail }}</td>
            <td class="actions-cell">
              <button @click="startEdit(club)">Edit</button>
              <button class="delete-btn" @click="deleteClub(club.shortName)">Delete</button>
            </td>
          </template>
        </tr>
      </tbody>
    </table>
    <div v-if="!loading && !clubs.length">No clubs found.</div>
  </div>
</template>

<script>
import axios from 'axios';
const API_BASE_URL =
  window.API_BASE_URL ||
  (window.location.origin.includes('localhost')
    ? 'http://localhost:5000/api'
    : '/api');

export default {
  name: 'ClubsConfig',
  data() {
    return {
      clubs: [],
      loading: false,
      newClub: { shortName: '', fullName: '', description: '', websiteUrl: '', adminEmail: '' },
      newClubLogoFile: null,
      clubLogoPreview: '',
      editingShortName: null,
      editForm: {},
      statusMsg: '',
      statusMsgError: false,
    };
  },
  methods: {
    fetchClubs() {
      this.loading = true;
      axios.get(`${API_BASE_URL}/admin/clubs`, { headers: { Authorization: `Bearer ${localStorage.getItem('hlasAdminToken')}` } })
        .then(res => {
          this.clubs = res.data.clubs || [];
        })
        .catch(() => {
          this.clubs = [];
        })
        .finally(() => {
          this.loading = false;
        });
    },
    addClub() {
      if (!this.newClub.shortName.trim()) {
        this.showStatus('Short Name is required.', true);
        return;
      }
      const formData = new FormData();
      Object.entries(this.newClub).forEach(([k, v]) => formData.append(k, v));
      if (this.newClubLogoFile) formData.append('logo', this.newClubLogoFile);
      axios.post(`${API_BASE_URL}/admin/clubs`, formData, { headers: { Authorization: `Bearer ${localStorage.getItem('hlasAdminToken')}` } })
        .then(() => {
          this.showStatus('Club added successfully.');
          this.newClub = { shortName: '', fullName: '', description: '', websiteUrl: '', adminEmail: '' };
          this.newClubLogoFile = null;
          this.clubLogoPreview = '';
          this.fetchClubs();
        })
        .catch(err => {
          this.showStatus(err.response?.data?.error || 'Add failed', true);
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
        { headers: { Authorization: `Bearer ${localStorage.getItem('hlasAdminToken')}` } })
        .then(() => {
          this.editingShortName = null;
          this.editForm = {};
          this.fetchClubs();
          this.showStatus('Club updated successfully.');
        })
        .catch(err => {
          this.showStatus(err.response?.data?.error || 'Update failed', true);
        });
    },
    deleteClub(shortName) {
      if (!window.confirm(`Delete club "${shortName}"? This cannot be undone.`)) return;
      axios.delete(`${API_BASE_URL}/admin/clubs/${encodeURIComponent(shortName)}`,
        { headers: { Authorization: `Bearer ${localStorage.getItem('hlasAdminToken')}` } })
        .then(() => {
          this.fetchClubs();
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
        this.clubLogoPreview = '';
        return;
      }
      const isPngType = file.type === 'image/png' || file.name.toLowerCase().endsWith('.png');
      if (!isPngType) {
        this.newClubLogoFile = null;
        event.target.value = '';
        this.showStatus('Logo must be a PNG file.', true);
        this.clubLogoPreview = '';
        return;
      }
      this.newClubLogoFile = file;
      const reader = new FileReader();
      reader.onload = e => { this.clubLogoPreview = e.target.result; };
      reader.readAsDataURL(file);
    },
    showStatus(msg, isError = false) {
      this.statusMsg = msg;
      this.statusMsgError = isError;
      setTimeout(() => { this.statusMsg = ''; }, 4000);
    },
  },
  mounted() {
    this.fetchClubs();
  },
};
</script>

<style scoped>
.clubs-panel {
  background: #fafafa;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 16px 20px;
  margin: 24px 0 28px;
}

.clubs-panel h1 {
  font-size: 16pt;
  margin-bottom: 14px;
}

.clubs-panel h2 {
  font-size: 13pt;
  margin: 0 0 12px;
}

.club-form {
  margin-bottom: 22px;
}

.form-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.form-row label {
  width: 110px;
  font-size: 10pt;
  white-space: nowrap;
}

.form-row input {
  flex: 1;
  max-width: 420px;
  padding: 6px;
  font-size: 10pt;
  font-family: Helvetica, Arial, sans-serif;
}

.clubs-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9pt;
  margin-bottom: 16px;
}
.clubs-table th,
.clubs-table td {
  border: 1px solid #ccc;
  padding: 7px 9px;
  text-align: left;
  vertical-align: top;
}
.clubs-table th {
  background: #f0f0f0;
  font-size: 10pt;
  white-space: nowrap;
}
.clubs-table .desc-cell {
  max-width: 280px;
  font-size: 8.5pt;
  color: #444;
}
.clubs-table .actions-cell {
  white-space: nowrap;
  text-align: center;
  vertical-align: middle;
}
.clubs-table .actions-cell button {
  margin: 2px 3px;
  padding: 4px 10px;
  font-size: 8.5pt;
  font-family: Helvetica, Arial, sans-serif;
  cursor: pointer;
}
.delete-btn {
  color: #c00;
}

.edit-row {
  background: #fffbe6;
}
</style>
