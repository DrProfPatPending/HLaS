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
            <span v-for="role in user.roles" :key="role.roleCode">{{ role.roleName }}</span>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="!loading && !users.length" class="admin-empty-state">No app users found.</div>
  </div>
</template>

<script>
import { adminGet } from '../../services/adminApi.js';

export default {
  name: 'AppUsers',
  data() {
    return {
      users: [],
      loading: false,
      clubs: [],
      selectedClubShortName: '',
    };
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
  },
  mounted() {
    this.fetchClubs();
  },
};
</script>

<style scoped>
.app-users-table td {
  vertical-align: top;
}
</style>
