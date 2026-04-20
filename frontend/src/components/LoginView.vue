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
      <div v-if="!isClubSpecificUrl" class="form-field">
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
      <div v-else class="form-field club-locked-info">
        <label>Club:</label>
        <div class="club-name-display">{{ selectedClubLabel }}</div>
      </div>
      <div class="form-field">
        <label for="login-username">Username:</label>
        <input id="login-username" v-model="loginUsername" placeholder="Username" required />
      </div>
      <div class="form-field">
        <label for="login-password">Password:</label>
        <input id="login-password" v-model="loginPassword" placeholder="Password" type="password" required />
      </div>
      <app-button type="submit" inherit-style>Login</app-button>
    </form>
    <div class="admin-login-link">
      <a href="/admin.html">Admin login</a>
    </div>
    <div v-if="loginError" class="login-error">{{ loginError }}</div>
  </div>
</template>

<script>
import { store, login, API_BASE_URL } from '../store.js';
import AppButton from './ui/AppButton.vue';

export default {
  name: 'LoginView',
  components: {
    AppButton,
  },
  data() {
    return {
      isClubSpecificUrl: false,
    };
  },
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
  mounted() {
    this.checkIfClubSpecificUrl();
  },
  methods: {
    login,
    checkIfClubSpecificUrl() {
      try {
        const match = String(window.location.pathname || '').match(/^\/clubs?\/([^/]+)/i);
        this.isClubSpecificUrl = !!match && !!match[1];
      } catch {
        this.isClubSpecificUrl = false;
      }
    },
  },
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

.club-locked-info {
  pointer-events: none;
  opacity: 0.7;
}

.club-name-display {
  padding: 8px 12px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-weight: 500;
  color: #333;
}

.login-error {
  color: var(--app-color-state-danger);
}
</style>
