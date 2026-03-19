<template>
  <div class="my-club-container">
    <h2>My Club</h2>

    <div v-if="loading" class="my-club-status">Loading your member information…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>

    <div v-else>
      <div class="my-club-actions">
        <button v-if="!isEditing" type="button" @click="startEdit">Edit</button>
        <template v-else>
          <button type="button" class="save-btn" @click="saveEdit">Save</button>
          <button type="button" @click="cancelEdit">Cancel</button>
        </template>
        <button type="button" @click="goHome">Back to Home</button>
      </div>

      <div v-if="status" class="success-msg">{{ status }}</div>

      <table class="my-club-table">
        <thead>
          <tr>
            <th>Field</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="field in orderedFields" :key="field">
            <td>{{ formatFieldName(field) }}</td>
            <td>
              <span v-if="!isEditing">{{ formatValue(memberData[field]) }}</span>
              <input
                v-else
                v-model="editData[field]"
                class="my-club-input"
                :disabled="isReadOnlyField(field)"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { store, formatFieldName } from '../store.js';

export default {
  name: 'MyClub',
  data() {
    return {
      loading: true,
      error: '',
      status: '',
      isEditing: false,
      memberData: {},
      editData: {},
    };
  },
  computed: {
    loggedInClub() {
      return store.loggedInClub;
    },
    apiBaseUrl() {
      return store.apiBaseUrl;
    },
    orderedFields() {
      const keys = Object.keys(this.memberData || {});
      const preferredTop = ['ID', 'id', 'Number', 'Members_Name', 'username', 'E_Mail'];
      const topKeys = preferredTop.filter(key => keys.includes(key));
      const remaining = keys.filter(key => !preferredTop.includes(key));
      return [...topKeys, ...remaining];
    },
    memberId() {
      return this.memberData.id || this.memberData.ID || this.editData.id || this.editData.ID || null;
    },
  },
  created() {
    this.fetchMyMemberProfile();
  },
  methods: {
    formatFieldName,
    isReadOnlyField(field) {
      return field === 'ID' || field === 'id';
    },
    formatValue(value) {
      if (value === null || value === undefined || value === '') return '-';
      return String(value);
    },
    sanitizeMemberPayload(rawMember) {
      const sanitized = {};
      Object.entries(rawMember || {}).forEach(([key, value]) => {
        if (key === 'password') return;
        sanitized[key] = value === null || value === undefined ? '' : value;
      });
      return sanitized;
    },
    fetchMyMemberProfile() {
      this.loading = true;
      this.error = '';
      this.status = '';
      axios
        .get(`${this.apiBaseUrl}/members/me`, { params: { club: this.loggedInClub } })
        .then(res => {
          const payload = (res.data && res.data.member) || {};
          this.memberData = this.sanitizeMemberPayload(payload);
          this.editData = { ...this.memberData };
        })
        .catch(err => {
          this.error =
            err.response && err.response.data && err.response.data.error
              ? err.response.data.error
              : 'Failed to load member information';
        })
        .finally(() => {
          this.loading = false;
        });
    },
    startEdit() {
      this.status = '';
      this.error = '';
      this.editData = { ...this.memberData };
      this.isEditing = true;
    },
    cancelEdit() {
      this.status = '';
      this.error = '';
      this.editData = { ...this.memberData };
      this.isEditing = false;
    },
    saveEdit() {
      this.status = '';
      this.error = '';

      if (!this.memberId) {
        this.error = 'Unable to determine your member ID for update.';
        return;
      }

      const payload = { ...this.editData, club: this.loggedInClub };
      delete payload.ID;
      delete payload.id;

      axios
        .put(`${this.apiBaseUrl}/members/${this.memberId}`, payload)
        .then(() => {
          this.memberData = this.sanitizeMemberPayload(this.editData);
          this.editData = { ...this.memberData };
          this.isEditing = false;
          this.status = 'Member information updated successfully.';
        })
        .catch(err => {
          this.error =
            err.response && err.response.data && err.response.data.error
              ? err.response.data.error
              : 'Failed to update member information';
        });
    },
    goHome() {
      this.isEditing = false;
      store.activeSection = 'home';
    },
  },
};
</script>

<style scoped>
.my-club-container {
  max-width: 900px;
  margin: 0 auto;
}

.my-club-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.my-club-status {
  margin-bottom: 10px;
}

.my-club-table {
  width: 100%;
  border-collapse: collapse;
}

.my-club-table th,
.my-club-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
  vertical-align: top;
}

.my-club-table th {
  width: 30%;
}

.my-club-input {
  width: 100%;
  box-sizing: border-box;
}
</style>
