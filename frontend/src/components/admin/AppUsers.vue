<template>
  <div class="app-users-panel">
    <h1>App Users</h1>
    <div class="app-users-header">
      <label for="club-select">Select Club:</label>
      <select id="club-select" v-model="selectedClubShortName" @change="fetchUsers">
        <option v-for="club in clubs" :key="club.shortName" :value="club.shortName">
          {{ club.fullName }}
        </option>
      </select>
    </div>
    <div v-if="loading">Loading users...</div>
    <table v-if="users.length" class="app-users-table">
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
    <div v-if="!loading && !users.length">No app users found.</div>
  </div>
</template>

<script>

import axios from 'axios';
import config from '../../../server.config.json';
const API_BASE_URL = config.api.backendUrl;

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
      axios.get(`${API_BASE_URL}/admin/clubs`, { headers: this.authHeaders() })
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
      axios.get(`${API_BASE_URL}/admin/app-users?club=${encodeURIComponent(this.selectedClubShortName)}`, { headers: this.authHeaders() })
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
    authHeaders() {
      const token = localStorage.getItem('hlasAdminToken');
      return { Authorization: `Bearer ${token}` };
    },
  },
  mounted() {
    this.fetchClubs();
  },
};
</script>

<style scoped>
.app-users-panel {
  background: #fafafa;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 16px 20px;
  margin: 24px 0 28px;
  max-width: 900px;
}

.app-users-panel h1 {
  font-size: 16pt;
  margin-bottom: 14px;
}

.app-users-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.app-users-header select {
  min-width: 240px;
  padding: 6px 8px;
}

.app-users-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9pt;
}

.app-users-table th,
.app-users-table td {
  border: 1px solid #ccc;
  padding: 6px 9px;
  text-align: left;
  vertical-align: top;
}

.app-users-table th {
  background: #f0f0f0;
  white-space: nowrap;
}
</style>
