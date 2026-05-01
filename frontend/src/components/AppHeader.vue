<template>
  <table class="logo-table">
    <tbody>
      <tr>
        <td class="logo-cell">
          <img src="../../logos/HLaS.png" alt="HLaS logo" class="app-logo" @click="goHome" />
        </td>
        <td class="logo-spacer">Spacer 1</td>
        <td class="logo-spacer">Spacer 2</td>
        <td class="logo-cell">
          <a
            v-if="loggedIn && websiteUrl"
            :href="websiteUrl"
            target="_blank"
            rel="noopener noreferrer"
          >
            <img :src="logoSrc" :alt="`${loggedInClub} logo`" class="club-logo" @error="onClubLogoError" />
          </a>
          <img
            v-else-if="loggedIn"
            :src="logoSrc"
            :alt="`${loggedInClub} logo`"
            class="club-logo"
            @error="onClubLogoError"
          />
        </td>
      </tr>
      <tr>
        <td v-if="loggedIn" class="login-info-cell">
          User: {{ loggedInUsername }} ({{ loggedInClub }})
        </td>
        <td class="logo-spacer">Spacer 3</td>
        <td class="login-info-admin">
          <span v-if="hasAdminRole" class="login-info-admin">Admin</span>
        </td>
        <td v-if="loggedIn" class="logout-cell">
          <app-button type="button" class="logout-button" inherit-style @click="logout">Log Out</app-button>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import { store, clubDetails, clubLogoSrc, logout } from '../store.js';
import AppButton from './ui/AppButton.vue';

export default {
  name: 'AppHeader',
  components: {
    AppButton,
  },
  computed: {
    loggedIn: () => store.loggedIn,
    loggedInUsername: () => store.loggedInUsername,
    loggedInClub: () => store.loggedInClub,
    hasAdminRole: () => {
      const normalizedRoles = (Array.isArray(store.memberRoles) ? store.memberRoles : [])
        .map(role => String(role || '').toLowerCase().replace(/[^a-z0-9]/g, ''));
      return normalizedRoles.includes('clubadmin') || normalizedRoles.includes('appadmin');
    },
    websiteUrl: () => clubDetails.value.websiteUrl,
    logoSrc: () => clubLogoSrc.value,
  },
  methods: {
    goHome() {
      store.activeSection = 'home';
    },
    onClubLogoError() {
      store.clubLogoLoadFailed = true;
    },
    logout,
  },
};
</script>

</style>
<style scoped>
.login-info-cell {
  font-size: 15px;
  color: #222;
  font-weight: 500;
}
.login-info-admin {
  color: #2f7a45;
  font-weight: 700;
  font-size: 15px;
}
.logo-spacer {
  font-size: 15px;
}
</style>
</style>
