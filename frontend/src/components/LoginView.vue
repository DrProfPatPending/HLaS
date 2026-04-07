<template>
  <div class="login-container">
    <h2>{{ loginHeading }}</h2>
    <div v-if="selectedClubLogoUrl" class="login-club-logo-wrap">
      <img
        :src="selectedClubLogoUrl"
        :alt="`${selectedClubLabel} logo`"
        class="login-club-logo"
      />
    </div>
    <form @submit.prevent="login">
      <div class="form-field">
        <label for="club-select">Select Club:</label>
        <select id="club-select" v-model="selectedClub" class="club-select">
          <option
            v-for="club in clubs"
            :key="club.shortName"
            :value="club.shortName"
            :title="club.description"
          >
            {{ club.shortName }}
          </option>
        </select>
      </div>
      <div class="form-field">
        <label for="login-username">Username:</label>
        <input id="login-username" v-model="loginUsername" placeholder="Username" required />
      </div>
      <div class="form-field">
        <label for="login-password">Password:</label>
        <input id="login-password" v-model="loginPassword" placeholder="Password" type="password" required />
      </div>
      <button type="submit">Login</button>
    </form>
    <div class="admin-login-link">
      <a href="/admin.html">Admin login</a>
    </div>
    <div v-if="loginError" style="color: red;">{{ loginError }}</div>
  </div>
</template>

<script>
import { API_BASE_URL, store, login } from '../store.js';

export default {
  name: 'LoginView',
  computed: {
    clubs: () => store.clubs,
    loginError: () => store.loginError,
    selectedClub: {
      get: () => store.selectedClub,
      set: v => { store.selectedClub = v; },
    },
    loginUsername: {
      get: () => store.loginUsername,
      set: v => { store.loginUsername = v; },
    },
    loginPassword: {
      get: () => store.loginPassword,
      set: v => { store.loginPassword = v; },
    },
    selectedClubRecord() {
      return store.clubs.find(club => club.shortName === store.selectedClub) || null;
    },
    selectedClubLabel() {
      const selected = this.selectedClubRecord;
      return selected?.fullName || selected?.shortName || store.selectedClub || 'your club';
    },
    loginHeading() {
      if (!store.selectedClub) {
        return 'Welcome to HLaS - please provide your credentials to login';
      }
      return `Welcome to ${this.selectedClubLabel} - please provide your credentials to login`;
    },
    selectedClubLogoUrl() {
      const selected = this.selectedClubRecord;
      const logoUrl = String(selected?.logoUrl || '').trim();
      if (!logoUrl) return '';
      if (/^https?:\/\//i.test(logoUrl)) return logoUrl;
      return `${API_BASE_URL}${logoUrl.startsWith('/') ? '' : '/'}${logoUrl}`;
    },
  },
  methods: { login },
};
</script>

<style scoped>
.login-club-logo-wrap {
  margin: 0 auto 14px;
  text-align: center;
}

.login-club-logo {
  max-height: 72px;
  width: auto;
}
</style>
