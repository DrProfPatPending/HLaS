<template>
  <div class="app-users-panel">
    <div class="app-users-header">
      <label for="club-select">Select Club:</label>
      <select id="club-select" v-model="selectedClubId" @change="fetchUsers">
        <option v-for="club in clubs" :key="club.clubId" :value="club.clubId">
          {{ club.name }}
        </option>
      </select>
    </div>
    <table v-if="users.length" class="app-users-table">
      <thead>
        <tr>
          <th>User ID</th>
          <th>Username</th>
          <th>Name</th>
          <th>Email</th>
          <th>Roles</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.userId">
          <td>{{ user.userId }}</td>
          <td>{{ user.username }}</td>
          <td>{{ user.name }}</td>
          <td>{{ user.email }}</td>
          <td>
            <span v-for="role in user.roles" :key="role.assignmentId" class="role-badge">
              {{ role.roleName }}<span v-if="role.clubShortName"> ({{ role.clubShortName }})</span>
            </span>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else class="no-users-msg">No users found for this club.</div>
  </div>
</template>

<script>
import axios from 'axios';
import config from '../../server.config.json';

const API_BASE_URL = config.api.backendUrl;

export default {
  name: 'AppUsers',
  data() {
    return {
      clubs: [],
      selectedClubId: '',
      users: [],
    };
  },
  mounted() {
    this.fetchClubs();
  },
  methods: {
    fetchClubs() {
      axios.get(`${API_BASE_URL}/admin/clubs`, { headers: this.authHeaders() })
        .then(res => {
          this.clubs = res.data.clubs || [];
          if (this.clubs.length) {
            this.selectedClubId = this.clubs[0].clubId;
            this.fetchUsers();
          }
        });
    },
    fetchUsers() {
      if (!this.selectedClubId) return;
      axios.get(`${API_BASE_URL}/admin/clubs/${this.selectedClubId}/users`, { headers: this.authHeaders() })
        .then(res => {
          this.users = res.data.users || [];
        });
    },
    authHeaders() {
      const token = localStorage.getItem('hlasAdminToken');
      return { Authorization: `Bearer ${token}` };
    },
  },
};
</script>

<style scoped>
.app-users-panel {
  background: #fafafa;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 18px 22px;
  margin-bottom: 28px;
  max-width: 1100px;
}
.app-users-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}
.app-users-header label {
  font-size: 10pt;
  font-weight: 600;
}
.app-users-header select {
  font-size: 10pt;
  padding: 5px 10px;
  border-radius: 4px;
  border: 1px solid #bbb;
}
.app-users-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9pt;
  margin-bottom: 16px;
}
.app-users-table th,
.app-users-table td {
  border: 1px solid #ccc;
  padding: 7px 9px;
  text-align: left;
  vertical-align: top;
}
.app-users-table th {
  background: #f0f0f0;
  font-size: 10pt;
  white-space: nowrap;
}
.role-badge {
  display: inline-block;
  background: #e0e0e0;
  color: #333;
  border-radius: 10px;
  padding: 2px 8px;
  margin: 2px 3px 2px 0;
  font-size: 8pt;
  font-weight: 600;
}
.no-users-msg {
  color: #888;
  font-size: 10pt;
  margin-top: 12px;
}
</style>
<template>
  <div class="ua-panel">
    <h1>App Users</h1>
    <div v-if="loading">Loading users...</div>
    <table v-if="users.length" class="ua-table">
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
            <span v-for="role in user.roles" :key="role">{{ role }}</span>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="!loading && !users.length">No app users found.</div>
  </div>
</template>

<script>
import axios from 'axios';
const API_BASE_URL =
  window.API_BASE_URL ||
  (window.location.origin.includes('localhost')
    ? 'http://localhost:5000/api'
    : '/api');

export default {
  name: 'AppUsers',
  data() {
    return {
      users: [],
      loading: false,
    };
  },
  methods: {
    isLastClub(user, club) {
      return user.clubs[user.clubs.length - 1] === club;
    },
    fetchUsers() {
      this.loading = true;
      axios.get(`${API_BASE_URL}/admin/app-users`, { headers: { Authorization: `Bearer ${localStorage.getItem('hlasAdminToken')}` } })
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
    this.fetchUsers();
  },
};
</script>

<style scoped>
.ua-panel { margin: 24px 0; }
.ua-table { width: 100%; border-collapse: collapse; }
.ua-table th, .ua-table td { border: 1px solid #ccc; padding: 6px 9px; }
</style>
