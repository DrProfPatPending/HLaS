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
