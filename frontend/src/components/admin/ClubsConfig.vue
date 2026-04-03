<template>
  <div class="admin-panel">
    <h1 class="admin-panel-title">Clubs</h1>
    <div v-if="loading" class="admin-loading-text">Loading clubs...</div>
    <form @submit.prevent="addClub" class="club-form">
      <h2 class="admin-section-title">Add New Club</h2>
      <div class="admin-form-row">
        <label class="admin-form-label">Short Name:</label>
        <input v-model="newClub.shortName" class="admin-form-input" required />
      </div>
      <div class="admin-form-row">
        <label class="admin-form-label">Full Name:</label>
        <input v-model="newClub.fullName" class="admin-form-input" />
      </div>
      <div class="admin-form-row">
        <label class="admin-form-label">Description:</label>
        <input v-model="newClub.description" class="admin-form-input" />
      </div>
      <div class="admin-form-row">
        <label class="admin-form-label">Website:</label>
        <input v-model="newClub.websiteUrl" class="admin-form-input" />
      </div>
      <div class="admin-form-row">
        <label class="admin-form-label">Admin Email:</label>
        <input v-model="newClub.adminEmail" class="admin-form-input" />
      </div>
      <div class="admin-form-row">
        <label class="admin-form-label">Logo (PNG):</label>
        <input type="file" accept="image/png" @change="onNewClubLogoChange" />
      </div>
      <div v-if="clubLogoPreview" class="admin-form-row">
        <img :src="clubLogoPreview" alt="Logo Preview" class="club-logo-preview" />
      </div>
      <div class="admin-form-row">
        <button type="submit" class="save-btn">Add Club</button>
      </div>
      <div v-if="statusMsg" :class="statusMsgError ? 'error-msg' : 'success-msg'">{{ statusMsg }}</div>
    </form>
    <table v-if="clubs.length" class="admin-table clubs-table">
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
        <tr v-for="club in clubs" :key="club.id || club.shortName" :class="{ 'admin-edit-row': editingShortName === club.shortName }">
          <template v-if="editingShortName === club.shortName">
            <td><input v-model="editForm.shortName" class="clubs-table-input" disabled /></td>
            <td><input v-model="editForm.fullName" class="clubs-table-input" /></td>
            <td><input v-model="editForm.description" class="clubs-table-input" /></td>
            <td><input v-model="editForm.websiteUrl" class="clubs-table-input" /></td>
            <td><input v-model="editForm.adminEmail" class="clubs-table-input" /></td>
            <td class="admin-actions-cell">
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
            <td class="admin-actions-cell">
              <button @click="startEdit(club)">Edit</button>
              <button class="delete-btn" @click="deleteClub(club.shortName)">Delete</button>
            </td>
          </template>
        </tr>
      </tbody>
    </table>
    <div v-if="!loading && !clubs.length" class="admin-empty-state">No clubs found.</div>
  </div>
</template>

<script>
import { adminDelete, adminGet, adminPost, adminPut } from '../../services/adminApi.js';

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
      adminGet('/admin/clubs')
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
      adminPost('/admin/clubs', formData)
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
      adminPut(`/admin/clubs/${encodeURIComponent(this.editingShortName)}`,
        this.editForm)
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
      adminDelete(`/admin/clubs/${encodeURIComponent(shortName)}`)
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
.club-form {
  margin-bottom: 22px;
}

.club-logo-preview {
  max-height: 40px;
  max-width: 120px;
}

.clubs-table th {
  font-size: 10pt;
}

.clubs-table td {
  vertical-align: top;
}

.desc-cell {
  max-width: 280px;
  font-size: 8.5pt;
  color: #444;
}

.clubs-table-input {
  width: 100%;
  box-sizing: border-box;
  padding: 5px;
  font-size: 9pt;
  font-family: Helvetica, Arial, sans-serif;
  border: 1px solid #aaa;
}

.delete-btn {
  color: #c00;
}
</style>
