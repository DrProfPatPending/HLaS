<template>
  <div class="my-club-container">
    <h2>My Club</h2>

    <div v-if="loading" class="my-club-status">Loading your member information…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>

    <div v-else>
      <div class="member-edit-top-row">
        <div class="member-edit-actions member-edit-actions-top">
          <button v-if="!isEditing" type="button" @click="startEdit">Edit Member Details</button>
          <template v-else>
            <button type="button" class="save-btn" @click="saveEdit">Update Member</button>
            <button type="button" @click="cancelEdit">Cancel</button>
          </template>
          <span v-if="passwordError" style="color: red; margin-left: 15px;">{{ passwordError }}</span>
        </div>

        <div v-if="memberPhotoSrc" class="member-edit-photo-panel">
          <img
            :src="memberPhotoSrc"
            :alt="memberPhotoAlt"
            class="member-edit-photo"
            @error="hideMemberPhoto"
          />
          <div v-if="memberPhotoName" class="member-edit-photo-name">{{ memberPhotoName }}</div>
        </div>
      </div>

      <div v-if="status" class="success-msg">{{ status }}</div>

      <table class="member-detail-table">
        <thead>
          <tr>
            <th>Field</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="editData.username !== undefined">
            <td>{{ formatFieldName('username') }}</td>
            <td>
              <span v-if="!isEditing">{{ formatValue(memberData.username) }}</span>
              <input
                v-else
                v-model="editData.username"
                class="member-detail-input"
              />
            </td>
          </tr>

          <tr>
            <td>New Password</td>
            <td>
              <input
                v-model="newPassword"
                type="password"
                class="member-detail-input"
                :disabled="!isEditing"
                placeholder="Leave blank to keep current password"
              />
            </td>
          </tr>

          <tr>
            <td>Confirm New Password</td>
            <td>
              <input
                v-model="confirmPassword"
                type="password"
                class="member-detail-input"
                :disabled="!isEditing"
              />
            </td>
          </tr>

          <tr v-for="key in orderedFields" :key="key">
            <td>{{ formatFieldName(key) }}</td>
            <td>
              <span v-if="!isEditing">{{ formatMemberFieldValue(key, memberData[key]) }}</span>
              <input
                v-else-if="isDateOfBirthField(key)"
                type="date"
                :value="dateInputValue(editData[key])"
                class="member-detail-input"
                :disabled="isReadOnlyField(key)"
                @input="editData[key] = $event.target.value"
              />
              <input
                v-else
                v-model="editData[key]"
                class="member-detail-input"
                :disabled="isReadOnlyField(key)"
              />
            </td>
          </tr>

          <tr v-if="passwordError">
            <td colspan="2" style="color: red; text-align: center;">{{ passwordError }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { store, formatFieldName, fieldOrderConfig, loadFieldOrderConfig } from '../store.js';

export default {
  name: 'MyClub',
  data() {
    return {
      loading: true,
      error: '',
      status: '',
      passwordError: '',
      isEditing: false,
      photoVisible: true,
      memberData: {},
      editData: {},
      newPassword: '',
      confirmPassword: '',
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
      // Use backend field order if loaded, else fallback to previous logic
      if (fieldOrderConfig.loaded && fieldOrderConfig.order['my_club']) {
        // Only include fields present in memberData
        return fieldOrderConfig.order['my_club'].filter(f => f in this.memberData && f !== 'username' && f !== 'password');
      }
      const keys = Object.keys(this.memberData || {});
      const preferredTop = ['ID', 'id', 'Number', 'Members_Name', 'E_Mail'];
      const topKeys = preferredTop.filter(key => keys.includes(key));
      const remaining = keys.filter(key => !preferredTop.includes(key) && key !== 'username' && key !== 'password');
      return [...topKeys, ...remaining];
    },
    memberId() {
      return this.memberData.id || this.memberData.ID || this.editData.id || this.editData.ID || null;
    },
    memberPhotoName() {
      return this.memberData.Photo_Path || this.editData.Photo_Path || '';
    },
    memberPhotoSrc() {
      if (!this.photoVisible || !this.memberPhotoName) {
        return '';
      }
      return `${this.apiBaseUrl}/member_photo/${this.loggedInClub}/${encodeURIComponent(this.memberPhotoName)}`;
    },
    memberPhotoAlt() {
      return this.memberData.Members_Name || this.memberData.username || 'Member photo';
    },
  },
  created() {
    loadFieldOrderConfig().finally(() => {
      this.fetchMyMemberProfile();
    });
  },
  methods: {
    formatFieldName,
    isDateOfBirthField(field) {
      const normalized = String(field || '').toLowerCase().replace(/[^a-z0-9]/g, '');
      return normalized === 'dob' || normalized.includes('dateofbirth');
    },
    dateInputValue(value) {
      const raw = String(value || '').trim();
      if (!raw) {
        return '';
      }
      if (/^\d{4}-\d{2}-\d{2}/.test(raw)) {
        return raw.slice(0, 10);
      }
      if (/^\d{2}\/\d{2}\/\d{4}$/.test(raw)) {
        const [day, month, year] = raw.split('/');
        return `${year}-${month}-${day}`;
      }
      if (/^\d{2}-\d{2}-\d{4}$/.test(raw)) {
        const [day, month, year] = raw.split('-');
        return `${year}-${month}-${day}`;
      }
      const parsed = new Date(raw);
      if (!Number.isNaN(parsed.getTime())) {
        return parsed.toISOString().slice(0, 10);
      }
      return '';
    },
    normalizeEditableData(payload) {
      const normalized = { ...(payload || {}) };
      Object.keys(normalized).forEach(key => {
        if (this.isDateOfBirthField(key)) {
          normalized[key] = this.dateInputValue(normalized[key]);
        }
      });
      return normalized;
    },
    loadFromSessionUser() {
      const fallbackPayload = this.sanitizeMemberPayload(store.loggedInUser || {});
      if (!Object.keys(fallbackPayload).length) {
        return false;
      }
      this.photoVisible = true;
      this.memberData = fallbackPayload;
      this.editData = this.normalizeEditableData(this.memberData);
      return true;
    },
    hideMemberPhoto() {
      this.photoVisible = false;
    },
    isReadOnlyField(field) {
      return field === 'ID' || field === 'id';
    },
    formatValue(value) {
      if (value === null || value === undefined || value === '') return '-';
      return String(value);
    },
    formatMemberFieldValue(field, value) {
      if (this.isDateOfBirthField(field)) {
        const normalized = this.dateInputValue(value);
        return normalized || '-';
      }
      return this.formatValue(value);
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
          const sanitized = this.sanitizeMemberPayload(payload);
          if (!Object.keys(sanitized).length) {
            const loadedFromSession = this.loadFromSessionUser();
            if (!loadedFromSession) {
              this.error = 'No member information available for this session';
            }
            return;
          }
          this.photoVisible = true;
          this.memberData = sanitized;
          this.editData = this.normalizeEditableData(this.memberData);
        })
        .catch(err => {
          const loadedFromSession = this.loadFromSessionUser();
          if (loadedFromSession) {
            this.error = '';
            return;
          }
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
      this.passwordError = '';
      this.editData = this.normalizeEditableData(this.memberData);
      this.newPassword = '';
      this.confirmPassword = '';
      this.isEditing = true;
    },
    cancelEdit() {
      this.status = '';
      this.error = '';
      this.passwordError = '';
      this.editData = this.normalizeEditableData(this.memberData);
      this.newPassword = '';
      this.confirmPassword = '';
      this.isEditing = false;
    },
    saveEdit() {
      this.status = '';
      this.error = '';
      this.passwordError = '';

      if (!this.memberId) {
        this.error = 'Unable to determine your member ID for update.';
        return;
      }

      if (this.newPassword || this.confirmPassword) {
        if (this.newPassword !== this.confirmPassword) {
          this.passwordError = 'Passwords do not match';
          return;
        }
        if (!this.newPassword.length) {
          this.passwordError = 'Password cannot be empty';
          return;
        }
      }

      const payload = { ...this.editData, club: this.loggedInClub };
      delete payload.ID;
      delete payload.id;
      if (this.newPassword) {
        payload.password = this.newPassword;
      }

      axios
        .put(`${this.apiBaseUrl}/members/${this.memberId}`, payload)
        .then(() => {
          this.memberData = this.sanitizeMemberPayload(this.editData);
          this.editData = this.normalizeEditableData(this.memberData);
          this.newPassword = '';
          this.confirmPassword = '';
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

.success-msg {
  margin: 10px 0;
}
</style>
