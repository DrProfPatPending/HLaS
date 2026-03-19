<template>
  <div class="member-edit-container">
    <h2>Edit Member Details</h2>
    <div v-if="editMemberPositionLabel" class="member-edit-position">{{ editMemberPositionLabel }}</div>
    <div class="member-edit-photo-row">
      <img
        v-if="editMemberData.Photo_Path"
        :key="editMemberId"
        :src="`${apiBaseUrl}/member_photo/${loggedInClub}/${encodeURIComponent(editMemberData.Photo_Path)}`"
        :alt="editMemberData.Members_Name || 'Member photo'"
        class="member-edit-photo"
        @error="$event.target.style.display='none'"
      />
      <div v-if="editMemberData.Photo_Path" class="member-edit-photo-name">
        {{ editMemberData.Photo_Path }}
      </div>
    </div>
    <div class="member-edit-actions">
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
        <tr v-for="key in remainingEditMemberKeys" :key="key">
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
  remainingEditMemberKeys,
  navigateEditMember,
  updateMember,
  cancelEdit,
  formatFieldName,
} from '../store.js';

export default {
  name: 'MemberEdit',
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
  },
  methods: {
    navigateEditMember,
    updateMember,
    cancelEdit,
    formatFieldName,
  },
};
</script>
