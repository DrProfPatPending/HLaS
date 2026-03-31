<template>
  <div class="ua-panel">
    <h1>User Administration</h1>
    <!-- Search Bar -->
    <div class="ua-search-row">
      <input v-model="uaSearch" @keyup.enter="searchUsers" placeholder="Search users..." />
      <button @click="searchUsers">Search</button>
      <button @click="resetSearch">Reset</button>
    </div>
    <div v-if="uaLoading">Loading...</div>
    <div v-if="uaStatusMsg" :class="uaStatusError ? 'error-msg' : 'success-msg'">{{ uaStatusMsg }}</div>
    <!-- User Table -->
    <table class="ua-table" v-if="uaSearchResults.length">
      <thead>
        <tr>
          <th>Username</th>
          <th>Email</th>
          <th>Roles</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in uaSearchResults" :key="user.userId">
          <td>{{ user.username }}</td>
          <td>{{ user.email }}</td>
          <td>
            <span v-for="assignment in user.assignments" :key="assignment.assignmentId" class="role-badge">
              {{ assignment.roleName }}
              <button class="role-revoke-btn" @click="revokeRole(user, assignment)">&times;</button>
            </span>
            <button class="ua-add-role-btn" @click="openGrantModal(user)">+ Add Role</button>
          </td>
          <td>
            <button @click="startMerge(user)">Merge</button>
          </td>
        </tr>
      </tbody>
    </table>
    <!-- Grant Role Modal -->
    <div v-if="uaGrant.visible" class="modal-overlay">
      <div class="modal-box">
        <h3>Grant Role to {{ uaGrant.member.username }}</h3>
        <select v-model="uaGrant.roleCode">
          <option value="">Select Role</option>
          <option v-for="role in uaAvailableRoles" :key="role.code" :value="role.code">{{ role.name }}</option>
        </select>
        <div v-if="selectedRole && selectedRole.scopeType === 'club'">
          <select v-model="uaGrant.clubId">
            <option value="">Select Club</option>
            <option v-for="club in uaClubs" :key="club.id" :value="club.id">{{ club.name }}</option>
          </select>
        </div>
        <div v-if="uaGrant.statusMsg" :class="uaGrant.statusError ? 'error-msg' : 'success-msg'">{{ uaGrant.statusMsg }}</div>
        <div class="modal-actions">
          <button @click="grantRole">Grant</button>
          <button @click="closeGrantModal">Cancel</button>
        </div>
      </div>
    </div>
    <!-- Merge/Cleanup Controls -->
    <div class="ua-merge-controls">
      <button @click="runMergeCleanup(true)">Dry Run Merge Cleanup</button>
      <button @click="runMergeCleanup(false)">Apply Merge Cleanup</button>
      <span v-if="uaMergeCleanup.statusMsg" :class="uaMergeCleanup.statusError ? 'error-msg' : 'success-msg'">{{ uaMergeCleanup.statusMsg }}</span>
    </div>
  </div>
</template>

<script>

import axios from 'axios';
import adminStore from '../../adminStore.js';

const API_BASE_URL =
  window.API_BASE_URL ||
  (window.location.origin.includes('localhost')
    ? 'http://localhost:5000/api'
    : '/api');

export default {
  name: 'UserAdmin',
  data() {
    return {
      uaSearch: '',
      uaSearchResults: [],
      uaUsers: [],
      uaLoading: false,
      uaAvailableRoles: [],
      uaClubs: [],
      uaGrant: {
        visible: false,
        member: null,
        roleCode: '',
        clubId: null,
        statusMsg: '',
        statusError: false,
      },
      uaMerge: {
        sourceQuery: '',
        targetQuery: '',
        sourceResults: [],
        targetResults: [],
        sourceUser: null,
        targetUser: null,
        statusMsg: '',
        statusError: false,
        busy: false,
      },
      uaMergeCleanup: {
        statusMsg: '',
        statusError: false,
        lastResult: null,
        busy: false,
      },
      uaMergeCleanupPreview: [],
      uaStatusMsg: '',
      uaStatusError: false,
    };
  },
  computed: {
    selectedRole() {
      return this.uaAvailableRoles.find(r => r.code === this.uaGrant.roleCode) || null;
    }
  },
  methods: {
    searchUsers() {
      this.uaLoading = true;
      axios.get(`${API_BASE_URL}/admin/users`, { params: { q: this.uaSearch }, headers: this.authHeaders() })
        .then(res => {
          this.uaSearchResults = res.data.users || [];
          this.uaStatusMsg = '';
        })
        .catch(err => {
          this.uaStatusMsg = err.response?.data?.error || 'Failed to search users';
          this.uaStatusError = true;
        })
        .finally(() => {
          this.uaLoading = false;
        });
    },
    resetSearch() {
      this.uaSearch = '';
      this.uaSearchResults = [];
      this.uaStatusMsg = '';
    },
    openGrantModal(user) {
      this.uaGrant = { visible: true, member: user, roleCode: '', clubId: null, statusMsg: '', statusError: false };
    },
    closeGrantModal() {
      this.uaGrant.visible = false;
    },
    grantRole() {
      if (!this.uaGrant.roleCode) {
        this.uaGrant.statusMsg = 'Please select a role.';
        this.uaGrant.statusError = true;
        return;
      }
      const selectedRole = this.uaAvailableRoles.find(r => r.code === this.uaGrant.roleCode);
      if (selectedRole?.scopeType === 'club' && !this.uaGrant.clubId) {
        this.uaGrant.statusMsg = 'Please select a club for this role.';
        this.uaGrant.statusError = true;
        return;
      }
      axios.post(
        `${API_BASE_URL}/admin/users/${this.uaGrant.member.userId}/roles`,
        { roleCode: this.uaGrant.roleCode, clubId: this.uaGrant.clubId || null },
        { headers: this.authHeaders() }
      ).then(() => {
        this.closeGrantModal();
        this.uaSearch = '';
        this.uaSearchResults = [];
        this.uaShowStatus('Role granted successfully.');
        this.searchUsers();
      }).catch(err => {
        this.uaGrant.statusMsg = err.response?.data?.error || 'Grant failed';
        this.uaGrant.statusError = true;
      });
    },
    revokeRole(user, assignment) {
      const scopeLabel = assignment.roleClubShortName
        ? ` (${assignment.roleClubShortName})`
        : ' (global)';
      if (!window.confirm(`Revoke "${assignment.roleName}"${scopeLabel} from ${user.username}?`)) return;
      axios.delete(
        `${API_BASE_URL}/admin/users/${user.userId}/roles/${assignment.assignmentId}`,
        { headers: this.authHeaders() }
      ).then(() => {
        this.uaShowStatus('Role revoked successfully.');
        this.searchUsers();
      }).catch(err => {
        this.uaStatusMsg = err.response?.data?.error || 'Revoke failed';
        this.uaStatusError = true;
      });
    },
    runMergeCleanup(dryRun = true) {
      if (!dryRun) {
        const confirmed = window.confirm('Apply merge cleanup now? This will merge eligible duplicate active users.');
        if (!confirmed) return;
      }
      this.uaMergeCleanup.busy = true;
      this.uaMergeCleanup.statusMsg = '';
      this.uaMergeCleanup.statusError = false;
      axios.post(`${API_BASE_URL}/admin/users/merge/cleanup`, {
        dryRun,
      }, {
        headers: this.authHeaders(),
      }).then(res => {
        const payload = res.data || {};
        this.uaMergeCleanup.lastResult = payload;
        this.uaMergeCleanup.statusMsg = dryRun
          ? `Dry run complete. Planned merges: ${payload.mergeCount || 0}.`
          : `Cleanup applied. Merges completed: ${payload.mergeCount || 0}.`;
        this.uaMergeCleanup.statusError = false;
        if (!dryRun) this.searchUsers();
      }).catch(err => {
        this.uaMergeCleanup.statusMsg = err.response?.data?.error || 'Cleanup failed';
        this.uaMergeCleanup.statusError = true;
      }).finally(() => {
        this.uaMergeCleanup.busy = false;
      });
    },
    uaShowStatus(msg, isError = false) {
      this.uaStatusMsg = msg;
      this.uaStatusError = isError;
      setTimeout(() => { this.uaStatusMsg = ''; }, 4000);
    },
    authHeaders() {
      return { Authorization: `Bearer ${adminStore.state.adminToken}` };
    },
    startMerge(user) {
      // Placeholder for merge logic
      alert('Merge logic not yet implemented for user: ' + user.username);
    },
  },
  mounted() {
    // Load roles and clubs for role assignment
    axios.get(`${API_BASE_URL}/admin/roles`, { headers: this.authHeaders() })
      .then(res => { this.uaAvailableRoles = res.data.roles || []; });
    axios.get(`${API_BASE_URL}/admin/clubs`, { headers: this.authHeaders() })
      .then(res => { this.uaClubs = res.data.clubs || []; });
  },
};
</script>

<style scoped>
/* Add styles if needed */
</style>
