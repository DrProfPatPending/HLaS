<template>
  <div class="ua-panel">
    <h1>Manage Admin Users</h1>
    <div class="ua-normal">This tab allows you to manage the Admin users for the application itself. The actual users of the app are managed separately on the 'App Users' tab.</div>
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
          <td class="roles-cell">
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
      const params = this.uaSearch ? { q: this.uaSearch } : {};
      axios.get(`${API_BASE_URL}/admin/users`, { params, headers: this.authHeaders() })
        .then(res => {
          this.uaSearchResults = res.data.users || [];
          this.uaStatusMsg = '';
        })
        .catch(err => {
          this.uaStatusMsg = err.response?.data?.error || 'Failed to load users';
          this.uaStatusError = true;
        })
        .finally(() => {
          this.uaLoading = false;
        });
    },
    resetSearch() {
      this.uaSearch = '';
      this.searchUsers();
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
      const token = localStorage.getItem('hlasAdminToken');
      return { Authorization: `Bearer ${token}` };
    },
    startMerge(user) {
      // Begin merge process: set source user and open merge UI (if implemented)
      this.uaMerge.sourceUser = user;
      this.uaMerge.sourceQuery = user.username;
      // For now, just show an alert (UI for merge selection can be added)
      alert('Select a target user to merge into. (UI not yet implemented)');
    },
    mergeUsers() {
      if (!this.uaMerge.sourceUser || !this.uaMerge.targetUser || this.uaMerge.sourceUser.userId === this.uaMerge.targetUser.userId) {
        this.uaMerge.statusMsg = 'Select different source and target users.';
        this.uaMerge.statusError = true;
        return;
      }
      const source = this.uaMerge.sourceUser;
      const target = this.uaMerge.targetUser;
      const confirmed = window.confirm(
        `Merge source user "${source.username}" (id ${source.userId}) into target user "${target.username}" (id ${target.userId})?`
      );
      if (!confirmed) return;
      this.uaMerge.busy = true;
      this.uaMerge.statusMsg = '';
      this.uaMerge.statusError = false;
      axios.post(`${API_BASE_URL}/admin/users/merge`, {
        sourceUserId: source.userId,
        targetUserId: target.userId,
      }, {
        headers: this.authHeaders(),
      }).then(res => {
        const summary = res.data.summary || {};
        this.uaMerge.statusMsg = `Merge complete. Links moved: ${summary.movedLinks || 0}, assignments moved: ${summary.movedAssignments || 0}.`;
        this.uaMerge.statusError = false;
        this.searchUsers();
      }).catch(err => {
        this.uaMerge.statusMsg = err.response?.data?.error || 'Merge failed';
        this.uaMerge.statusError = true;
      }).finally(() => {
        this.uaMerge.busy = false;
      });
    },
    resetMergeState() {
      this.uaMerge.sourceQuery = '';
      this.uaMerge.targetQuery = '';
      this.uaMerge.sourceResults = [];
      this.uaMerge.targetResults = [];
      this.uaMerge.sourceUser = null;
      this.uaMerge.targetUser = null;
      this.uaMerge.statusMsg = '';
      this.uaMerge.statusError = false;
      this.uaMerge.busy = false;
      this.uaMergeCleanup.statusMsg = '';
      this.uaMergeCleanup.statusError = false;
      this.uaMergeCleanup.lastResult = null;
      this.uaMergeCleanup.busy = false;
    },
  },
  mounted() {
    // Load all users by default
    this.searchUsers();
    // Load roles and clubs for role assignment
    axios.get(`${API_BASE_URL}/admin/roles`, { headers: this.authHeaders() })
      .then(res => { this.uaAvailableRoles = res.data.roles || []; });
    axios.get(`${API_BASE_URL}/admin/clubs`, { headers: this.authHeaders() })
      .then(res => { this.uaClubs = res.data.clubs || []; });
  },
};
</script>

<style scoped>
.ua-panel {
  background: #fafafa;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 16px 20px;
  margin: 24px 0 28px;
  max-width: 900px;
}

.ua-panel h1 {
  font-size: 16pt;
  margin-bottom: 14px;
}

.ua-normal {
  margin-bottom: 14px;
  color: #444;
}

.ua-search-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.ua-search-row input {
  min-width: 260px;
  padding: 6px 8px;
  font-size: 9pt;
}

.ua-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9pt;
  margin-bottom: 10px;
}

.ua-table th,
.ua-table td {
  border: 1px solid #ccc;
  padding: 6px 9px;
  text-align: left;
  vertical-align: middle;
}

.ua-table th {
  background: #f0f0f0;
  font-size: 9.5pt;
  white-space: nowrap;
}

.roles-cell {
  min-width: 240px;
}

.role-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 7px;
  border-radius: 12px;
  font-size: 8pt;
  font-weight: 600;
  margin: 2px 3px 2px 0;
  white-space: nowrap;
  background: #e7eef8;
  color: #244;
}

.role-revoke-btn {
  background: none;
  border: none;
  color: inherit;
  opacity: 0.7;
  cursor: pointer;
  font-size: 11pt;
  line-height: 1;
  padding: 0 0 0 2px;
}

.role-revoke-btn:hover {
  opacity: 1;
}

.ua-add-role-btn {
  display: inline-block;
  font-size: 8pt;
  padding: 2px 7px;
  border-radius: 12px;
  border: 1px dashed #999;
  background: none;
  color: #555;
  cursor: pointer;
  margin-left: 2px;
}

.ua-add-role-btn:hover {
  border-color: #444;
  color: #222;
}

.ua-merge-controls {
  margin-top: 16px;
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-box {
  background: #fff;
  border-radius: 8px;
  padding: 28px 32px;
  min-width: 420px;
  max-width: 520px;
  box-shadow: 0 8px 32px rgba(0,0,0,.25);
}

.modal-box h3 {
  margin-top: 0;
}

.modal-box select {
  width: 100%;
  margin-top: 8px;
  padding: 7px 8px;
}

.modal-actions {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>
