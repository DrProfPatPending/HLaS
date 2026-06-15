<template>
  <div class="admin-panel app-users-panel">
    <h1 class="admin-panel-title">App Users</h1>
    <div class="admin-inline-controls app-users-header">
      <label for="club-select">Select Club:</label>
      <select id="club-select" v-model="selectedClubShortName" class="admin-select" @change="fetchUsers">
        <option v-for="club in clubs" :key="club.shortName" :value="club.shortName">
          {{ club.fullName }}
        </option>
      </select>
    </div>
    <div v-if="loading" class="admin-loading-text">Loading users...</div>
    <table v-if="users.length" class="admin-table app-users-table">
      <thead>
        <tr>
          <th>Username</th>
          <th>Email</th>
          <th>Clubs</th>
          <th>Roles</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.userId">
          <td>{{ user.username }}</td>
          <td>{{ user.email }}</td>
          <td>
            <span v-for="club in user.clubs" :key="club.id">{{ club.name }}<span v-if="!isLastClub(user, club)">, </span></span>
          </td>
          <td>
            <span v-for="role in user.roles" :key="`${user.userId}-${role.roleCode}-${role.roleName}`" class="app-user-role-pill">{{ role.roleName }}</span>
          </td>
          <td>
            <button @click="openRoleModal(user)">Manage Roles</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="!loading && !users.length" class="admin-empty-state">No app users found.</div>

    <div v-if="roleModal.visible" class="admin-modal-overlay">
      <div class="admin-modal-card app-users-modal-card">
        <h3>Manage Roles: {{ roleModal.user?.username }}</h3>
        <p class="app-users-modal-context">
          Showing active roles for {{ selectedClubShortName }} and global roles.
        </p>

        <div v-if="roleModal.loading" class="admin-loading-text">Loading role assignments...</div>

        <div v-if="!roleModal.loading" class="app-users-role-list">
          <div v-if="!roleModal.assignments.length" class="admin-empty-state">No active roles in this context.</div>
          <div v-for="assignment in roleModal.assignments" :key="assignment.assignmentId" class="app-users-role-row">
            <span class="app-user-role-pill">
              {{ assignment.roleName }}
              <span v-if="assignment.roleScope === 'global'">(global)</span>
              <span v-else-if="assignment.roleClubShortName">({{ assignment.roleClubShortName }})</span>
            </span>
            <button class="app-users-revoke-btn" @click="revokeRole(roleModal.user, assignment)">Revoke</button>
          </div>
        </div>

        <div class="app-users-grant-box">
          <h4>Grant Role</h4>
          <select v-model="roleModal.roleCode" class="admin-select app-users-modal-select">
            <option value="">Select Role</option>
            <option v-for="role in availableRoles" :key="role.code" :value="role.code">{{ role.name }}</option>
          </select>
          <div v-if="selectedGrantRole && selectedGrantRole.scopeType === 'club'" class="app-users-club-select-wrap">
            <select v-model="roleModal.clubId" class="admin-select app-users-modal-select">
              <option :value="null">Select Club</option>
              <option v-for="club in roleClubs" :key="club.id" :value="club.id">{{ club.shortName }} - {{ club.fullName }}</option>
            </select>
          </div>
          <div v-if="roleModal.statusMsg" :class="roleModal.statusError ? 'error-msg' : 'success-msg'">{{ roleModal.statusMsg }}</div>
          <div class="admin-modal-actions">
            <button @click="grantRole">Grant</button>
            <button @click="closeRoleModal">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { adminDelete, adminGet, adminPost } from '../../services/adminApi.js';

export default {
  name: 'AppUsers',
  data() {
    return {
      users: [],
      loading: false,
      clubs: [],
      selectedClubShortName: '',
      availableRoles: [],
      roleClubs: [],
      roleModal: {
        visible: false,
        user: null,
        loading: false,
        assignments: [],
        roleCode: '',
        clubId: null,
        statusMsg: '',
        statusError: false,
      },
    };
  },
  computed: {
    selectedGrantRole() {
      return this.availableRoles.find(role => role.code === this.roleModal.roleCode) || null;
    },
  },
  methods: {
    isLastClub(user, club) {
      return user.clubs[user.clubs.length - 1] === club;
    },
    fetchClubs() {
      adminGet('/admin/clubs')
        .then(res => {
          this.clubs = res.data.clubs || [];
          if (this.clubs.length && !this.selectedClubShortName) {
            this.selectedClubShortName = this.clubs[0].shortName;
            this.fetchUsers();
          }
        });
    },
    fetchRoleClubs() {
      return adminGet('/admin/clubs-list')
        .then(res => {
          this.roleClubs = res.data.clubs || [];
        })
        .catch(() => {
          this.roleClubs = [];
        });
    },
    fetchAvailableRoles() {
      return adminGet('/admin/roles')
        .then(res => {
          this.availableRoles = res.data.roles || [];
        })
        .catch(() => {
          this.availableRoles = [];
        });
    },
    fetchUsers() {
      if (!this.selectedClubShortName) return;
      this.loading = true;
      adminGet('/admin/app-users', {
        params: { club: this.selectedClubShortName },
      })
        .then(res => {
          this.users = res.data.users || [];
        })
        .catch(() => {
          this.users = [];
        })
        .finally(() => {
          this.loading = false;
        });
    },
    openRoleModal(user) {
      this.roleModal.visible = true;
      this.roleModal.user = user;
      this.roleModal.roleCode = '';
      this.roleModal.statusMsg = '';
      this.roleModal.statusError = false;

      const selectedClub = this.roleClubs.find(club => club.shortName === this.selectedClubShortName);
      this.roleModal.clubId = selectedClub ? selectedClub.id : null;

      this.refreshRoleModalAssignments(user, { clearAssignments: true, clearStatus: false });
    },
    refreshRoleModalAssignments(user, options = {}) {
      const { clearAssignments = false, clearStatus = false } = options;
      if (!user?.userId) return Promise.resolve();
      this.roleModal.loading = true;
      if (clearAssignments) {
        this.roleModal.assignments = [];
      }
      if (clearStatus) {
        this.roleModal.statusMsg = '';
        this.roleModal.statusError = false;
      }

      return adminGet(`/admin/users/${user.userId}/roles`)
        .then(res => {
          const allAssignments = Array.isArray(res.data?.assignments) ? res.data.assignments : [];
          this.roleModal.assignments = allAssignments.filter(assignment => {
            if (!assignment.isActive) return false;
            if (assignment.roleScope === 'global') return true;
            return assignment.roleClubShortName === this.selectedClubShortName;
          });
        })
        .catch(err => {
          this.roleModal.assignments = [];
          this.roleModal.statusMsg = err.response?.data?.error || 'Failed to load role assignments';
          this.roleModal.statusError = true;
        })
        .finally(() => {
          this.roleModal.loading = false;
        });
    },
    closeRoleModal() {
      this.roleModal.visible = false;
      this.roleModal.user = null;
      this.roleModal.loading = false;
      this.roleModal.assignments = [];
      this.roleModal.roleCode = '';
      this.roleModal.clubId = null;
      this.roleModal.statusMsg = '';
      this.roleModal.statusError = false;
    },
    grantRole() {
      const user = this.roleModal.user;
      if (!user) return;
      if (!this.roleModal.roleCode) {
        this.roleModal.statusMsg = 'Select a role to grant.';
        this.roleModal.statusError = true;
        return;
      }

      const selectedRole = this.selectedGrantRole;
      if (selectedRole?.scopeType === 'club' && !this.roleModal.clubId) {
        this.roleModal.statusMsg = 'Select a club for this role.';
        this.roleModal.statusError = true;
        return;
      }

      this.roleModal.statusMsg = '';
      this.roleModal.statusError = false;

      adminPost(`/admin/users/${user.userId}/roles`, {
        roleCode: this.roleModal.roleCode,
        clubId: selectedRole?.scopeType === 'club' ? this.roleModal.clubId : null,
      }).then(() => {
        this.roleModal.statusMsg = 'Role granted successfully.';
        this.roleModal.statusError = false;
        this.refreshRoleModalAssignments(user);
        this.fetchUsers();
      }).catch(err => {
        this.roleModal.statusMsg = err.response?.data?.error || 'Failed to grant role';
        this.roleModal.statusError = true;
      });
    },
    revokeRole(user, assignment) {
      const roleLabel = assignment.roleClubShortName
        ? `${assignment.roleName} (${assignment.roleClubShortName})`
        : `${assignment.roleName} (global)`;
      if (!window.confirm(`Revoke ${roleLabel} from ${user.username}?`)) return;

      adminDelete(`/admin/users/${user.userId}/roles/${assignment.assignmentId}`)
        .then(() => {
          this.roleModal.statusMsg = 'Role revoked successfully.';
          this.roleModal.statusError = false;
          this.refreshRoleModalAssignments(user);
          this.fetchUsers();
        })
        .catch(err => {
          this.roleModal.statusMsg = err.response?.data?.error || 'Failed to revoke role';
          this.roleModal.statusError = true;
        });
    },
  },
  mounted() {
    this.fetchClubs();
    this.fetchRoleClubs();
    this.fetchAvailableRoles();
  },
};
</script>

<style scoped>
.app-users-table td {
  vertical-align: top;
}

.app-user-role-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 7px;
  border-radius: 10px;
  margin: 0 4px 4px 0;
  background: #e7eef8;
  color: #244;
  font-size: 8pt;
  font-weight: 600;
}

.app-users-modal-card {
  max-width: 640px;
  width: min(640px, 94vw);
}

.app-users-modal-context {
  margin: 4px 0 10px;
  color: #445;
  font-size: 9pt;
}

.app-users-role-list {
  max-height: 220px;
  overflow: auto;
  margin-bottom: 12px;
}

.app-users-role-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.app-users-revoke-btn {
  padding: 4px 9px;
}

.app-users-grant-box {
  border-top: 1px solid #d6deea;
  padding-top: 10px;
}

.app-users-grant-box h4 {
  margin: 0 0 8px;
  font-size: 10pt;
}

.app-users-modal-select {
  width: 100%;
  margin-bottom: 8px;
}

.app-users-club-select-wrap {
  margin-bottom: 4px;
}
</style>
