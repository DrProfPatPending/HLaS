<template>
  <div class="member-edit-container">
    <h2>Edit Member Details</h2>
    <div v-if="editMemberPositionLabel" class="member-edit-position">{{ editMemberPositionLabel }}</div>
    <div class="member-edit-top-row">
      <div class="member-edit-actions member-edit-actions-top">
        <app-button type="button" inherit-style @click="updateMember">Update Member</app-button>
        <app-button type="button" inherit-style :disabled="!hasPreviousEditMember" @click="navigateEditMember(-1)">
          Previous
        </app-button>
        <app-button type="button" inherit-style :disabled="!hasNextEditMember" @click="navigateEditMember(1)">
          Next
        </app-button>
        <app-button type="button" inherit-style @click="cancelEdit">Cancel</app-button>
        <span v-if="passwordError" class="member-edit-password-inline-error">{{ passwordError }}</span>
      </div>
      <div v-if="memberPhotoSrc" class="member-edit-photo-panel">
        <img
          :key="`${editMemberId}:${memberPhotoName}`"
          :src="memberPhotoSrc"
          :alt="memberPhotoAlt"
          class="member-edit-photo"
          @error="hideMemberPhoto"
        />
        <div v-if="memberPhotoName" class="member-edit-photo-name">
          {{ memberPhotoName }}
        </div>
      </div>
    </div>
    <br />
    <table class="member-detail-table">
      <thead>
        <tr>
          <th>Field</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="editMemberData.username !== undefined">
          <td>{{ formatFieldName('username') }}</td>
          <td>
            <input
              v-model="editMemberData.username"
              class="member-detail-input"
              :disabled="isReadOnlyField('username')"
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
              placeholder="Leave blank to keep current password"
            />
          </td>
        </tr>
        <tr>
          <td>Confirm New Password</td>
          <td>
            <input v-model="confirmPassword" type="password" class="member-detail-input" />
          </td>
        </tr>
        <tr v-for="key in orderedEditFields" :key="key">
          <td>{{ formatFieldName(key) }}</td>
          <td>
            <input
              v-if="isDateOfBirthField(key)"
              type="date"
              :value="dateInputValue(editMemberData[key])"
                :disabled="isReadOnlyField(key)"
              class="member-detail-input"
              @input="editMemberData[key] = $event.target.value"
            />
            <input
              v-else
              v-model="editMemberData[key]"
                :disabled="isReadOnlyField(key)"
              class="member-detail-input"
            />
          </td>
        </tr>
        <tr v-if="passwordError">
          <td colspan="2" class="member-edit-password-row-error">{{ passwordError }}</td>
        </tr>
      </tbody>
    </table>
    <div class="member-edit-actions">
      <app-button type="button" inherit-style @click="updateMember">Update Member</app-button>
      <app-button type="button" inherit-style :disabled="!hasPreviousEditMember" @click="navigateEditMember(-1)">
        Previous
      </app-button>
      <app-button type="button" inherit-style :disabled="!hasNextEditMember" @click="navigateEditMember(1)">
        Next
      </app-button>
      <app-button type="button" inherit-style @click="cancelEdit">Cancel</app-button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import AppButton from './ui/AppButton.vue';
import {
  API_BASE_URL,
  store,
  editMemberPositionLabel,
  hasPreviousEditMember,
  hasNextEditMember,
  navigateEditMember,
  cancelEdit,
  formatFieldName,
  fieldOrderConfig,
  loadFieldOrderConfig,
  fetchMembers,
  isDateOfBirthField,
  normalizeDateInputValue,
} from '../store.js';

export default {
  name: 'MemberEdit',
  components: {
    AppButton,
  },
  data() {
    return {
      photoVisible: true,
    };
  },
  created() {
    loadFieldOrderConfig();
  },
  watch: {
    editMemberId() {
      this.photoVisible = true;
    },
  },
  computed: {
    apiBaseUrl: () => store.apiBaseUrl,
    loggedInClub: () => store.loggedInClub,
    editMemberData: () => store.editMemberData,
    editMemberId: () => store.editMemberId,
    newPassword: {
      get: () => store.newPassword,
      set: v => { store.newPassword = v; },
    },
    confirmPassword: {
      get: () => store.confirmPassword,
      set: v => { store.confirmPassword = v; },
    },
    passwordError: () => store.passwordError,
    editMemberPositionLabel: () => editMemberPositionLabel.value,
    hasPreviousEditMember: () => hasPreviousEditMember.value,
    hasNextEditMember: () => hasNextEditMember.value,
    remainingEditMemberKeys: () => remainingEditMemberKeys.value,
    orderedEditFields() {
      if (fieldOrderConfig.loaded && fieldOrderConfig.order['membership_admin']) {
        return fieldOrderConfig.order['membership_admin'].filter(f => f in this.editMemberData && f !== 'username' && f !== 'password');
      }
      const keys = Object.keys(this.editMemberData || {});
      return keys.filter(k => k !== 'username' && k !== 'password');
    },
    membershipReadOnlyColumns() {
      const configured = fieldOrderConfig.order?.read_only?.membership_admin;
      return configured && typeof configured === 'object' ? configured : {};
    },
    hasAdminRole() {
      const normalizedRoles = (Array.isArray(store.memberRoles) ? store.memberRoles : [])
        .map(role => String(role || '').toLowerCase().replace(/[^a-z0-9]/g, ''));
      return normalizedRoles.includes('clubadmin')
        || normalizedRoles.includes('appadmin')
        || normalizedRoles.includes('appowner');
    },
    memberPhotoName() {
      return this.editMemberData.Photo_Path || '';
    },
    memberPhotoSrc() {
      if (!this.photoVisible || !this.memberPhotoName || !this.editMemberId) {
        return '';
      }
      return `${this.apiBaseUrl}/member_photo/${this.loggedInClub}/${encodeURIComponent(this.memberPhotoName)}`;
    },
    memberPhotoAlt() {
      return this.editMemberData.Members_Name || this.editMemberData.username || 'Member photo';
    },
  },
  methods: {
    navigateEditMember,
    cancelEdit,
    formatFieldName,
    isDateOfBirthField,
    dateInputValue: normalizeDateInputValue,
    isReadOnlyField(field) {
      if (field === 'ID' || field === 'id') {
        return true;
      }
      if (this.hasAdminRole) {
        return false;
      }
      return this.membershipReadOnlyColumns?.[field] === true;
    },
    stripReadOnlyFields(payload) {
      if (!payload || this.hasAdminRole) {
        return payload;
      }
      const sanitized = { ...payload };
      Object.entries(this.membershipReadOnlyColumns || {}).forEach(([fieldName, isReadOnly]) => {
        if (isReadOnly) {
          delete sanitized[fieldName];
        }
      });
      return sanitized;
    },
    updateMember() {
      if (store.newPassword || store.confirmPassword) {
        if (store.newPassword !== store.confirmPassword) {
          store.passwordError = 'Passwords do not match';
          return;
        }
        if (store.newPassword.length === 0) {
          store.passwordError = 'Password cannot be empty';
          return;
        }
      }
      store.passwordError = '';

      const memberData = this.stripReadOnlyFields({ ...(store.editMemberData || {}), club: store.loggedInClub });
      if (store.newPassword) {
        memberData.password = store.newPassword;
      }

      axios.put(`${API_BASE_URL}/members/${store.editMemberId}`, memberData).then(() => {
        fetchMembers();
        store.activeSection = 'membership-admin';
        store.editMemberData = {};
        store.editMemberId = null;
        store.newPassword = '';
        store.confirmPassword = '';
        store.passwordError = '';
      }).catch(err => {
        store.passwordError =
          err.response && err.response.data && err.response.data.error
            ? err.response.data.error
            : 'Update failed';
      });
    },
    hideMemberPhoto() {
      this.photoVisible = false;
    },
  },
};
</script>

<style scoped>
.member-edit-password-inline-error {
  color: var(--app-color-state-danger);
  margin-left: 15px;
}

.member-edit-password-row-error {
  color: var(--app-color-state-danger);
  text-align: center;
}
</style>
