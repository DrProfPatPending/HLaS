<template>
  <div class="home-container">
    <div class="home-page-header">
      <h2>Hello {{ loggedInUsername }} [{{ loggedInClub }}]</h2>
      <h3>Welcome to HookLineandSinker your one-stop shop<br>for fishing club management.</h3>
    </div>

    <section class="home-news-panel">
      <div class="home-news-card">
        <h4>{{ clubNewsTitle }}</h4>
        <table class="home-news-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Category</th>
              <th>Update</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in newsItems" :key="item.id">
              <td>{{ formatNewsDate(item.date) }}</td>
              <td>{{ item.category }}</td>
              <td>{{ item.message }}</td>
              <td>
                <span class="news-status-badge" :class="`is-${item.status.toLowerCase()}`">
                  {{ item.status }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        <p class="home-news-note">
          Placeholder content only for now. Backend-backed news alerts and club messages can be wired in later.
        </p>
      </div>
    </section>

    <p v-if="accessError" class="access-error">{{ accessError }}</p>
  </div>
</template>

<script>
import { store, clubDetails, formatConfiguredDate } from '../store.js';

export default {
  name: 'HomeView',
  computed: {
    loggedInUsername: () => store.loggedInUsername,
    loggedInClub: () => store.loggedInClub,
    accessError: () => store.accessError,
    clubNewsTitle: () => `${clubDetails.value.fullName} News and Updates`,
    newsItems() {
      return [
        {
          id: 'notice-1',
          date: '05 Apr 2026',
          category: 'Club Notice',
          message: 'Season opening briefing will be published here once the news backend is connected.',
          status: 'Draft',
        },
        {
          id: 'notice-2',
          date: '04 Apr 2026',
          category: 'River Conditions',
          message: 'This placeholder row can later show urgent river level alerts or temporary access restrictions.',
          status: 'Planned',
        },
        {
          id: 'notice-3',
          date: '02 Apr 2026',
          category: 'Membership',
          message: 'Member updates, reminders, and general announcements will appear in this central panel.',
          status: 'Queued',
        },
      ];
    },
  },
  methods: {
    formatNewsDate(value) {
      const formatted = formatConfiguredDate(value, 'Date');
      return formatted || value;
    },
  },
};
</script>

<style scoped>
.home-container {
  width: 100%;
  margin: 0;
  padding: 0 0 24px;
  font-family: Helvetica, Arial, sans-serif;
}

.home-page-header {
  margin-bottom: 22px;
}

.home-page-header h2,
.home-page-header h3 {
  margin: 0;
}

.home-page-header h3 {
  margin-top: 10px;
  font-weight: 500;
  line-height: 1.4;
}

.home-news-panel {
  min-width: 0;
}

.home-news-card {
  background: #fff;
  border: 1px solid #d7dce2;
  border-radius: 12px;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
  padding: 18px;
}

.home-news-card h4 {
  margin: 0 0 14px;
  font-size: 1.1rem;
  color: #17324d;
}

.home-news-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.home-news-table th,
.home-news-table td {
  padding: 10px 12px;
  border: 1px solid #d7dce2;
  text-align: left;
  vertical-align: top;
  font-size: 10pt;
}

.home-news-table thead th {
  background: #eaf2f8;
  color: #17324d;
}

.home-news-table tbody tr:nth-child(even) {
  background: #f8fbfd;
}

.news-status-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 9pt;
  font-weight: 700;
}

.news-status-badge.is-draft {
  background: #fff2cc;
  color: #7a5a00;
}

.news-status-badge.is-planned {
  background: #dceeff;
  color: #0f4c81;
}

.news-status-badge.is-queued {
  background: #e4f7e7;
  color: #21633a;
}

.home-news-note {
  margin: 14px 0 0;
  color: #475569;
  font-size: 9.5pt;
}


@media (max-width: 1000px) {
  .home-page-header {
    display: none;
  }
}
.access-error {
  margin-top: 18px;
  color: #b42318;
  font-weight: 600;
}
</style>
