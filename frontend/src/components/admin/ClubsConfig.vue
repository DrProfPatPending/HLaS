<template>
  <div class="clubs-panel">
    <h1>Clubs</h1>
    <div v-if="loading">Loading clubs...</div>
    <table v-if="clubs.length" class="clubs-table">
      <thead>
        <tr>
          <th>Short Name</th>
          <th>Full Name</th>
          <th>Description</th>
          <th>Website</th>
          <th>Admin Email</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="club in clubs" :key="club.id || club.shortName">
          <td>{{ club.shortName }}</td>
          <td>{{ club.fullName }}</td>
          <td>{{ club.description }}</td>
          <td><a v-if="club.websiteUrl" :href="club.websiteUrl" target="_blank">{{ club.websiteUrl }}</a></td>
          <td>{{ club.adminEmail }}</td>
        </tr>
      </tbody>
    </table>
    <div v-if="!loading && !clubs.length">No clubs found.</div>
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
  name: 'ClubsConfig',
  data() {
    return {
      clubs: [],
      loading: false,
    };
  },
  methods: {
    fetchClubs() {
      this.loading = true;
      axios.get(`${API_BASE_URL}/admin/clubs`, { headers: { Authorization: `Bearer ${localStorage.getItem('hlasAdminToken')}` } })
        .then(res => {
          this.clubs = res.data.clubs || [];
        })
        .catch(() => {
          this.clubs = [];
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
/* Clubs table styling copied from App.vue */
.clubs-panel { margin: 24px 0; }
.clubs-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9pt;
  margin-bottom: 16px;
}
.clubs-table th,
.clubs-table td {
  border: 1px solid #ccc;
  padding: 7px 9px;
  text-align: left;
  vertical-align: top;
}
.clubs-table th {
  background: #f0f0f0;
  font-size: 10pt;
  white-space: nowrap;
}
.clubs-table .desc-cell {
  max-width: 280px;
  font-size: 8.5pt;
  color: #444;
}
.clubs-table .actions-cell {
  white-space: nowrap;
  text-align: center;
  vertical-align: middle;
}
.clubs-table .actions-cell button {
  margin: 2px 3px;
  padding: 4px 10px;
  font-size: 8.5pt;
  font-family: Helvetica, Arial, sans-serif;
  cursor: pointer;
}
.delete-btn {
  color: #c00;
}
.save-btn {
  background: #2a7;
  color: white;
  border: 1px solid #1a6;
}
.edit-row {
  background: #fffbe6;
}
</style>
