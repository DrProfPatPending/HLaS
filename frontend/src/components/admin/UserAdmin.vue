<template>
  <div class="admin-panel">
    <h1 class="admin-panel-title">Manage Admin Users</h1>
    <div class="admin-info-text">This tab allows you to manage the Admin users for the application itself. The actual users of the app are managed separately on the 'App Users' tab.</div>
    <div class="admin-inline-controls">
      <input v-model="uaSearch" class="admin-search-input" @keyup.enter="searchUsers" placeholder="Search users..." />
      <button @click="searchUsers">Search</button>
      <button @click="resetSearch">Reset</button>
    </div>
    <div v-if="uaLoading" class="admin-loading-text">Loading...</div>
    <div v-if="uaStatusMsg" :class="uaStatusError ? 'error-msg' : 'success-msg'">{{ uaStatusMsg }}</div>

    <div class="admin-subsection">
      <h3 class="admin-subsection-title">Find User To Grant First Role</h3>
      <div class="admin-inline-controls">
        <input
          v-model="uaLookupQuery"
          class="admin-search-input"
          @keyup.enter="searchAssignableUsers"
          placeholder="Search by username or display name..."
        />
        <button @click="searchAssignableUsers">Find Users</button>
        <button @click="resetAssignableSearch">Reset</button>
      </div>
      <div v-if="uaLookupLoading" class="admin-loading-text">Searching users...</div>
      <div v-if="uaLookupStatusMsg" :class="uaLookupStatusError ? 'error-msg' : 'success-msg'">{{ uaLookupStatusMsg }}</div>

      <table class="admin-table" v-if="uaLookupResults.length">
        <thead>
          <tr>
            <th>Username</th>
            <th>Display Name</th>
            <th>Clubs</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="candidate in uaLookupResults" :key="`lookup-${candidate.userId}`">
            <td>{{ candidate.username }}</td>
            <td>{{ candidate.displayName || '-' }}</td>
            <td>
              <span v-for="(club, index) in candidate.clubs" :key="`${candidate.userId}-${club.id || club.shortName}`">
                {{ club.shortName || club.name || '-' }}<span v-if="index < candidate.clubs.length - 1">, </span>
              </span>
            </td>
            <td>
              <button @click="openGrantModal(candidate)">Grant Role</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <table class="admin-table" v-if="uaSearchResults.length">
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

    <div class="admin-subsection ua-merge-workflow">
      <h3 class="admin-subsection-title">Merge Users</h3>
      <p class="admin-info-text">
        Use merge to combine duplicate app-user identities. Source user will be deactivated after merge.
      </p>

      <div class="admin-inline-controls">
        <strong>Source:</strong>
        <span v-if="uaMerge.sourceUser">{{ uaMerge.sourceUser.username }} (id {{ uaMerge.sourceUser.userId }})</span>
        <span v-else class="admin-muted-text">Click "Merge" on a user row above to set source.</span>
      </div>

      <div class="admin-inline-controls">
        <input
          v-model="uaMerge.targetQuery"
          class="admin-search-input"
          placeholder="Search target user (username/display name)..."
          :disabled="!uaMerge.sourceUser"
          @keyup.enter="searchMergeTargets"
        />
        <button :disabled="!uaMerge.sourceUser" @click="searchMergeTargets">Find Target</button>
        <button :disabled="!uaMerge.sourceUser" @click="clearMergeTarget">Clear Target</button>
      </div>

      <div v-if="uaMerge.targetResults.length" class="ua-merge-target-list">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Username</th>
              <th>Display Name</th>
              <th>Clubs</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="candidate in uaMerge.targetResults" :key="`merge-target-${candidate.userId}`">
              <td>{{ candidate.username }}</td>
              <td>{{ candidate.displayName || '-' }}</td>
              <td>
                <span v-for="(club, index) in candidate.clubs" :key="`${candidate.userId}-club-${club.id || club.shortName}`">
                  {{ club.shortName || '-' }}<span v-if="index < candidate.clubs.length - 1">, </span>
                </span>
              </td>
              <td>
                <button @click="selectMergeTarget(candidate)">Select Target</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="admin-inline-controls">
        <strong>Target:</strong>
        <span v-if="uaMerge.targetUser">{{ uaMerge.targetUser.username }} (id {{ uaMerge.targetUser.userId }})</span>
        <span v-else class="admin-muted-text">No target selected.</span>
      </div>

      <div class="admin-inline-controls">
        <button
          :disabled="!uaMerge.sourceUser || !uaMerge.targetUser || uaMerge.busy"
          @click="mergeUsers"
        >
          {{ uaMerge.busy ? 'Merging...' : 'Run Merge' }}
        </button>
        <button :disabled="uaMerge.busy" @click="resetMergeState">Reset Merge</button>
        <span v-if="uaMerge.statusMsg" :class="uaMerge.statusError ? 'error-msg' : 'success-msg'">{{ uaMerge.statusMsg }}</span>
      </div>
    </div>

    <!-- Grant Role Modal -->
    <div v-if="uaGrant.visible" class="admin-modal-overlay">
      <div class="admin-modal-card user-admin-modal-card">
        <h3>Grant Role to {{ uaGrant.member.username }}</h3>
        <select v-model="uaGrant.roleCode" class="admin-select user-admin-modal-select">
          <option value="">Select Role</option>
          <option v-for="role in uaAvailableRoles" :key="role.code" :value="role.code">{{ role.name }}</option>
        </select>
        <div v-if="selectedRole && selectedRole.scopeType === 'club'">
          <select v-model="uaGrant.clubId" class="admin-select user-admin-modal-select">
            <option value="">Select Club</option>
            <option v-for="club in uaClubs" :key="club.id" :value="club.id">{{ club.shortName }} - {{ club.fullName }}</option>
          </select>
        </div>
        <div v-if="uaGrant.statusMsg" :class="uaGrant.statusError ? 'error-msg' : 'success-msg'">{{ uaGrant.statusMsg }}</div>
        <div class="admin-modal-actions">
          <button @click="grantRole">Grant</button>
          <button @click="closeGrantModal">Cancel</button>
        </div>
      </div>
    </div>
    <div class="ua-merge-controls admin-inline-controls">
      <button @click="runMergeCleanup(true)">Dry Run Merge Cleanup</button>
      <button @click="runMergeCleanup(false)">Apply Merge Cleanup</button>
      <span v-if="uaMergeCleanup.statusMsg" :class="uaMergeCleanup.statusError ? 'error-msg' : 'success-msg'">{{ uaMergeCleanup.statusMsg }}</span>
    </div>
  </div>
</template>

<script>
import { adminDelete, adminGet, adminPost } from '../../services/adminApi.js';

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
      uaLookupQuery: '',
      uaLookupLoading: false,
      uaLookupResults: [],
      uaLookupStatusMsg: '',
      uaLookupStatusError: false,
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
      adminGet('/admin/users', { params })
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
    searchAssignableUsers() {
      const query = String(this.uaLookupQuery || '').trim();
      if (query.length < 2) {
        this.uaLookupStatusMsg = 'Enter at least 2 characters to search users.';
        this.uaLookupStatusError = true;
        this.uaLookupResults = [];
        return;
      }
      this.uaLookupLoading = true;
      this.uaLookupStatusMsg = '';
      this.uaLookupStatusError = false;
      adminGet('/admin/users/search', { params: { q: query, limit: 20 } })
        .then(res => {
          const members = Array.isArray(res.data?.members) ? res.data.members : [];
          this.uaLookupResults = members;
          if (!members.length) {
            this.uaLookupStatusMsg = 'No matching users found.';
            this.uaLookupStatusError = false;
          }
        })
        .catch(err => {
          this.uaLookupResults = [];
          this.uaLookupStatusMsg = err.response?.data?.error || 'Failed to search users';
          this.uaLookupStatusError = true;
        })
        .finally(() => {
          this.uaLookupLoading = false;
        });
    },
    resetAssignableSearch() {
      this.uaLookupQuery = '';
      this.uaLookupResults = [];
      this.uaLookupStatusMsg = '';
      this.uaLookupStatusError = false;
    },
    openGrantModal(user) {
      this.uaGrant = { visible: true, member: user, roleCode: '', clubId: null, statusMsg: '', statusError: false };
    },
    closeGrantModal() {
      this.uaGrant.visible = false;
    },
    grantRole() {
      const grantedUserId = this.uaGrant?.member?.userId;
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
      adminPost(
        `/admin/users/${this.uaGrant.member.userId}/roles`,
        { roleCode: this.uaGrant.roleCode, clubId: this.uaGrant.clubId || null },
        {}
      ).then(() => {
        this.closeGrantModal();
        this.uaSearch = '';
        this.uaSearchResults = [];
        this.uaShowStatus('Role granted successfully.');
        this.uaLookupResults = this.uaLookupResults.filter(user => user.userId !== grantedUserId);
        this.uaLookupStatusMsg = 'Role granted. User will now appear in Manage Admin Users.';
        this.uaLookupStatusError = false;
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
      adminDelete(`/admin/users/${user.userId}/roles/${assignment.assignmentId}`).then(() => {
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
      adminPost('/admin/users/merge/cleanup', {
        dryRun,
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
    startMerge(user) {
      this.uaMerge.sourceUser = user;
      this.uaMerge.sourceQuery = user.username;
      this.uaMerge.targetQuery = '';
      this.uaMerge.targetResults = [];
      this.uaMerge.targetUser = null;
      this.uaMerge.statusMsg = `Source selected: ${user.username}. Find and select a target user.`;
      this.uaMerge.statusError = false;
    },
    searchMergeTargets() {
      if (!this.uaMerge.sourceUser) {
        this.uaMerge.statusMsg = 'Select a source user first.';
        this.uaMerge.statusError = true;
        return;
      }

      const query = String(this.uaMerge.targetQuery || '').trim();
      if (query.length < 2) {
        this.uaMerge.statusMsg = 'Enter at least 2 characters to search for target user.';
        this.uaMerge.statusError = true;
        this.uaMerge.targetResults = [];
        return;
      }

      this.uaMerge.statusMsg = '';
      this.uaMerge.statusError = false;
      adminGet('/admin/users/search', { params: { q: query, limit: 20 } })
        .then(res => {
          const members = Array.isArray(res.data?.members) ? res.data.members : [];
          this.uaMerge.targetResults = members.filter(member => member.userId !== this.uaMerge.sourceUser.userId);
          if (!this.uaMerge.targetResults.length) {
            this.uaMerge.statusMsg = 'No eligible target users found for this query.';
            this.uaMerge.statusError = false;
          }
        })
        .catch(err => {
          this.uaMerge.targetResults = [];
          this.uaMerge.statusMsg = err.response?.data?.error || 'Target search failed';
          this.uaMerge.statusError = true;
        });
    },
    selectMergeTarget(candidate) {
      this.uaMerge.targetUser = candidate;
      this.uaMerge.statusMsg = `Target selected: ${candidate.username}. Ready to run merge.`;
      this.uaMerge.statusError = false;
    },
    clearMergeTarget() {
      this.uaMerge.targetQuery = '';
      this.uaMerge.targetResults = [];
      this.uaMerge.targetUser = null;
      this.uaMerge.statusMsg = '';
      this.uaMerge.statusError = false;
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
      adminPost('/admin/users/merge', {
        sourceUserId: source.userId,
        targetUserId: target.userId,
      }).then(res => {
        const summary = res.data.summary || {};
        this.resetMergeState();
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
    adminGet('/admin/roles')
      .then(res => { this.uaAvailableRoles = res.data.roles || []; });
    adminGet('/admin/clubs-list')
      .then(res => { this.uaClubs = res.data.clubs || []; });
  },
};
</script>

<style scoped>
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

.user-admin-modal-card h3 {
  margin-top: 0;
}

.user-admin-modal-select {
  width: 100%;
  margin-top: 8px;
}

.admin-subsection {
  margin: 14px 0 18px;
}

.admin-subsection-title {
  margin: 0 0 8px;
  font-size: 10pt;
}

.ua-merge-workflow {
  border-top: 1px solid #d7e2f0;
  padding-top: 12px;
}

.ua-merge-target-list {
  margin-top: 8px;
}
</style>
