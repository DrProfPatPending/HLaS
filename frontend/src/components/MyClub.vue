<template>
  <div class="my-club-container">
    <h2>{{ activeTabTitle }}</h2>

    <div v-if="loading" class="my-club-status">Loading your member information…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>

    <div v-else>
      <div class="member-edit-top-row">
        <div class="member-edit-actions member-edit-actions-top">
          <app-button v-if="!isEditing" type="button" class="my-club-edit-btn" inherit-style @click="startEdit">Edit Member Details</app-button>
          <template v-else>
            <app-button type="button" class="save-btn" inherit-style @click="saveEdit">Update Member</app-button>
            <app-button type="button" inherit-style @click="cancelEdit">Cancel</app-button>
          </template>
          <span v-if="passwordError" class="my-club-password-inline-error">{{ passwordError }}</span>
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
          <tr v-if="showUsernameSection">
            <td>{{ formatFieldName('username') }}</td>
            <td>
              <span v-if="!isEditing">{{ formatValue(memberData.username) }}</span>
              <input
                v-else
                v-model="editData.username"
                class="member-detail-input"
                :disabled="isReadOnlyField('username')"
              />
            </td>
          </tr>

          <tr v-if="showPasswordSection">
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

          <tr v-if="showPasswordSection">
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

          <tr v-for="key in activeTabFields" :key="key">
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
            <td colspan="2" class="my-club-password-row-error">{{ passwordError }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import AppButton from './ui/AppButton.vue';
import {
  store,
  MY_CLUB_TABS,
  formatFieldName,
  fieldOrderConfig,
  loadFieldOrderConfig,
  isDateOfBirthField,
  formatConfiguredDate,
  normalizeDateInputValue,
} from '../store.js';

export default {
  name: 'MyClub',
  components: {
    AppButton,
  },
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
    myClubShowColumns() {
      const configured = fieldOrderConfig.order?.show_columns?.my_club;
      return configured && typeof configured === 'object' ? configured : {};
    },
    myClubReadOnlyColumns() {
      const configured = fieldOrderConfig.order?.read_only?.my_club;
      return configured && typeof configured === 'object' ? configured : {};
    },
    hasAdminRole() {
      const normalizedRoles = (Array.isArray(store.memberRoles) ? store.memberRoles : [])
        .map(role => String(role || '').toLowerCase().replace(/[^a-z0-9]/g, ''));
      return normalizedRoles.includes('clubadmin')
        || normalizedRoles.includes('appadmin')
        || normalizedRoles.includes('appowner');
    },
    orderedFields() {
      // Use backend field order if loaded, else fallback to previous logic
      if (fieldOrderConfig.loaded && fieldOrderConfig.order['my_club']) {
        // Only include fields present in memberData and honouring show_columns visibility flags
        return fieldOrderConfig.order['my_club'].filter(
          f => f in this.memberData && f !== 'username' && f !== 'password' && this.isFieldVisible(f)
        );
      }
      const keys = Object.keys(this.memberData || {});
      const preferredTop = ['ID', 'id', 'Number', 'Members_Name', 'E_Mail'];
      const topKeys = preferredTop.filter(key => keys.includes(key));
      const remaining = keys.filter(key => !preferredTop.includes(key) && key !== 'username' && key !== 'password');
      return [...topKeys, ...remaining];
    },
    groupedFields() {
      const personalFields = new Set([
        'ID',
        'id',
        'Number',
        'Members_Name',
        'Title',
        'First_Name',
        'Last_Name',
        'Preferred_Name',
        'First_Names',
        'Photo_Path',
        'Date_of_Birth',
        'Age',
        'Car_Reg',
        'Member_Type',
        'EA_Licence',
        'Licence_Exp',
        'Phone',
        'Mobile',
        'E_Mail',
      ]);
      const addressFields = new Set([
        'Full_Address',
        'Address___Street_Address',
        'Address___Address_Line_2',
        'Address___City',
        'County',
        'Address___State/Prov/Region',
        'Address___ZIP/Postal',
        'Address___Country',
      ]);
      const statusFields = new Set([
        'Paused',
        'Resigned',
        'Subs_Expected',
        'Subs_paid',
        'Join_Fee',
        'Paid_Up_2026',
        'Photo_Received',
        'In_WhatsApp',
        'In_FB',
        'New_Member_2026',
        'Paid_up_Card_Sent',
        'CR2023',
        'CR2024',
        'CR2025',
        'Details_Confirmed_2026',
      ]);

      const grouped = {
        personal: [],
        address: [],
        security: [],
        status: [],
      };

      this.orderedFields.forEach(key => {
        if (statusFields.has(key)) {
          grouped.status.push(key);
          return;
        }
        if (addressFields.has(key)) {
          grouped.address.push(key);
          return;
        }
        if (personalFields.has(key)) {
          grouped.personal.push(key);
          return;
        }
        grouped.personal.push(key);
      });

      return grouped;
    },
    activeTabFields() {
      return this.groupedFields[store.myClubActiveTab] || [];
    },
    activeTabTitle() {
      const activeTabId = store.myClubActiveTab;
      const matchedTab = MY_CLUB_TABS.find(tab => tab.id === activeTabId);
      return matchedTab?.label || 'My Club';
    },
    showUsernameSection() {
      return store.myClubActiveTab === 'security' && this.editData.username !== undefined;
    },
    showPasswordSection() {
      return store.myClubActiveTab === 'security';
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
    isDateOfBirthField,
    dateInputValue: normalizeDateInputValue,
    isFieldVisible(field) {
      const configured = this.myClubShowColumns?.[field];
      return configured !== false;
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
      if (field === 'ID' || field === 'id') {
        return true;
      }
      if (this.hasAdminRole) {
        return false;
      }
      return this.myClubReadOnlyColumns?.[field] === true;
    },
    removeReadOnlyFieldsFromPayload(payload) {
      if (!payload || this.hasAdminRole) {
        return payload;
      }
      const sanitized = { ...payload };
      Object.entries(this.myClubReadOnlyColumns || {}).forEach(([fieldName, isReadOnly]) => {
        if (isReadOnly) {
          delete sanitized[fieldName];
        }
      });
      return sanitized;
    },
    formatValue(value) {
      if (value === null || value === undefined || value === '') return '-';
      return String(value);
    },
    formatMemberFieldValue(field, value) {
      const formatted = formatConfiguredDate(value, field);
      if (formatted !== value) {
        return formatted || '-';
      }
      if (this.isDateOfBirthField(field)) {
        return formatted || '-';
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

      const payload = this.removeReadOnlyFieldsFromPayload({ ...this.editData, club: this.loggedInClub });
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

.my-club-container h2 {
  margin: 0 0 12px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
  font-weight: 700;
  color: #17324d;
}

.my-club-container :deep(.my-club-edit-btn.app-button) {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 8pt !important;
  line-height: 1.2;
  padding: 4px 8px !important;
}

.my-club-password-inline-error {
  color: var(--app-color-state-danger);
  margin-left: 15px;
}

.my-club-password-row-error {
  color: var(--app-color-state-danger);
  text-align: center;
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
