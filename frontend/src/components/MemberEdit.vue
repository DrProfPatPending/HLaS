<template>
  <div class="member-edit-container">
    <h2>Edit Member Details</h2>
    <div v-if="editMemberPositionLabel" class="member-edit-position">{{ editMemberPositionLabel }}</div>
    <div class="member-edit-top-row">
      <div class="member-edit-actions member-edit-actions-top">
        <button type="button" @click="updateMember">Update Member</button>
        <button type="button" :disabled="!hasPreviousEditMember" @click="navigateEditMember(-1)">
          Previous
        </button>
        <button type="button" :disabled="!hasNextEditMember" @click="navigateEditMember(1)">
          Next
        </button>
        <button type="button" @click="cancelEdit">Cancel</button>
        <span v-if="passwordError" style="color: red; margin-left: 15px;">{{ passwordError }}</span>
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
            <input v-model="editMemberData.username" class="member-detail-input" />
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
              v-model="editMemberData[key]"
              :disabled="key === 'ID' || key === 'id'"
              class="member-detail-input"
            />
          </td>
        </tr>
        <tr v-if="passwordError">
          <td colspan="2" style="color: red; text-align: center;">{{ passwordError }}</td>
        </tr>
      </tbody>
    </table>
    <div class="member-edit-actions">
      <button type="button" @click="updateMember">Update Member</button>
      <button type="button" :disabled="!hasPreviousEditMember" @click="navigateEditMember(-1)">
        Previous
      </button>
      <button type="button" :disabled="!hasNextEditMember" @click="navigateEditMember(1)">
        Next
      </button>
      <button type="button" @click="cancelEdit">Cancel</button>
    </div>
  </div>
</template>

<script>
import {
  store,
  editMemberPositionLabel,
  hasPreviousEditMember,
  hasNextEditMember,
  navigateEditMember,
  updateMember,
  cancelEdit,
  formatFieldName,
  fieldOrderConfig,
  loadFieldOrderConfig,
} from '../store.js';

export default {
  name: 'MemberEdit',
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
    updateMember,
    cancelEdit,
    formatFieldName,
    hideMemberPhoto() {
      this.photoVisible = false;
    },
  },
};
</script>
