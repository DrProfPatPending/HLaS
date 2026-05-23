<template>
  <div class="login-container">
    <template v-if="isUnknownClub">
      <h2>Club not recognised</h2>
      <p>
        The specific club you requested <strong>{{ unknownClubCode }}</strong> is not recognised on this server,
        please either correct your URL, or click on the link below to go to the main login page for the application.
      </p>
      <p>
        <a :href="mainLoginUrl">{{ mainLoginUrl }}</a>
      </p>
    </template>
    <template v-else>
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
        <div class="remember-me-row">
          <label class="remember-me-label">
            <input type="checkbox" v-model="rememberMe" class="remember-me-checkbox" />
            <span>Remember me</span>
          </label>
        </div>
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
    </template>
  </div>
</template>

<script>
import axios from 'axios';
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
      isUnknownClub: false,
      unknownClubCode: '',
      mainLoginUrl: `${window.location.origin}/`,
      rememberMe: false,
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
  async mounted() {
    await this.checkIfClubSpecificUrl();
    // Prefill username if remembered
    const remembered = window.localStorage.getItem('hlas.rememberedUsername');
    if (remembered) {
      this.loginUsername = remembered;
      this.rememberMe = true;
    }
  },
  methods: {
    login() {
      // Store username if rememberMe checked, else clear
      if (this.rememberMe) {
        window.localStorage.setItem('hlas.rememberedUsername', this.loginUsername);
      } else {
        window.localStorage.removeItem('hlas.rememberedUsername');
      }
      login();
    },
    findClubByCode(clubs, candidateCode) {
      const target = String(candidateCode || '').trim();
      if (!target) return null;
      return (
        clubs.find((club) => club?.shortName === target)
        || clubs.find((club) => String(club?.shortName || '').toLowerCase() === target.toLowerCase())
        || null
      );
    },
    async checkIfClubSpecificUrl() {
      try {
        const match = String(window.location.pathname || '').match(/^\/clubs?\/([^/]+)/i);
        this.isClubSpecificUrl = !!match && !!match[1];
        if (match && match[1]) {
          const requestedClub = decodeURIComponent(match[1]).trim();
          store.selectedClub = requestedClub;

          try {
            const clubsResponse = await axios.get(`${API_BASE_URL}/clubs`);
            const clubs = Array.isArray(clubsResponse?.data?.clubs)
              ? clubsResponse.data.clubs
              : [];
            const matchedClub = this.findClubByCode(clubs, requestedClub);

            if (!matchedClub) {
              this.isUnknownClub = true;
              this.unknownClubCode = requestedClub || 'unknown';
              document.title = 'HLaS - Club not recognised';
              return;
            }

            store.selectedClub = matchedClub.shortName;
          } catch (validationError) {
            console.error('Error validating club code:', validationError);
          }
        }
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

.login-container p {
  margin-bottom: 12px;
}

.remember-me-row {
  display: flex;
  align-items: center;
  margin-top: 6px;
}
.remember-me-label {
  display: flex;
  align-items: center;
  font-weight: normal;
  gap: 6px;
  white-space: nowrap;
}
.remember-me-checkbox {
  margin: 0;
}
</style>
