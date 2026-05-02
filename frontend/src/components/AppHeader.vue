<template>
  <table class="logo-table" style="width:80%; table-layout:fixed;">
    <tbody>
      <tr>
        <td class="logo-cell align-left">
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
        <td v-if="loggedIn" class="login-info-cell align-left">
          <div class="login-info-line">User: {{ loggedInUsername }}</div>
          <div class="login-info-line">Club: {{ loggedInClub }}</div>
          <div class="login-info-line">
            <span class="login-info-label">User Type: </span><span v-if="hasAdminRole" class="login-info-admin">Admin</span><span v-else class="login-info-normal">Normal</span>
          </div>
        </td>
        <td class="logout-cell align-right">
          <app-button v-if="loggedIn" type="button" class="logout-button" inherit-style @click="logout">Log Out</app-button>
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
    onClubLogoError() {
      store.clubLogoLoadFailed = true;
    },
    logout,
  },
};
</script>

<style scoped>
.logo-table {
  width: 80%;
  table-layout: fixed;
}
.align-left {
  text-align: left;
  vertical-align: middle;
}
.align-right {
  text-align: right;
  vertical-align: middle;
}
.logo-cell {
  width: 72px;
  padding: 2px 6px;
  border: none;
  vertical-align: middle;
}
.login-info-cell {
  padding: 2px 10px;
  border: none;
  vertical-align: middle;
  text-align: left;
}
.logout-cell {
  padding: 2px 6px;
  border: none;
  white-space: nowrap;
  vertical-align: middle;
}
.login-info-line {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 8pt;
  color: #222;
  font-weight: 500;
  line-height: 1.5;
}
.login-info-label {
  color: #222;
  font-weight: 500;
}
.login-info-admin {
  color: #2f7a45;
  font-weight: 700;
  font-size: 8pt;
}
.login-info-normal {
  color: #17324d;
  font-weight: 600;
  font-size: 8pt;
}
</style>
