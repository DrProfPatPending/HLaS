<template>
  <table class="logo-table" style="width:90%; table-layout:fixed;">
    <tbody>
      <tr>
        <td class="logo-cell align-left">
          <img src="../../logos/HLaS.png" alt="HLaS logo" class="app-logo" @click="goHome" />
        </td>
        <td v-if="loggedIn" class="logo-cell align-center">
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
        <td class="logo-cell align-right">
          <app-button v-if="loggedIn" type="button" class="logout-button" inherit-style @click="logout">Log Out</app-button>
        </td>
      </tr>
      <tr>
        <td v-if="loggedIn" class="login-info-cell align-left">
          User: {{ loggedInUsername }}
        </td>
        <td v-if="loggedIn" class="login-info-cell align-center">
          Club: {{ loggedInClub }}
        </td>
        <td class="login-info-admin align-right">
          <span v-if="hasAdminRole" class="login-info-admin">Admin</span>
          <span v-else class="login-info-admin">Normal</span>
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

<style scoped>
.logo-table {
  width: 90%;
  table-layout: fixed;
}
.align-left {
  text-align: left;
}
.align-center {
  text-align: center;
}
.align-right {
  text-align: right;
}
.login-info-cell {
  font-size: 12px;
  color: #222;
  font-weight: 500;
}
.login-info-admin {
  color: #2f7a45;
  font-weight: 700;
  font-size: 12px;
}
</style>
