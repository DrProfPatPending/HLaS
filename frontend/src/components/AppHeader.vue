<template>
  <table class="logo-table">
    <tbody>
      <tr>
        <td class="logo-cell">
          <img src="../../logos/HLaS.png" alt="HLaS logo" class="app-logo" @click="goHome" />
        </td>
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
        <td class="logo-spacer"></td>
        <td v-if="loggedIn" class="login-info-cell">
          Logged in as: {{ loggedInUsername }} ({{ loggedInClub }})
        </td>
        <td v-if="loggedIn" class="logout-cell">
          <button type="button" class="logout-button" @click="logout">Log Out</button>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import { store, clubDetails, clubLogoSrc, logout } from '../store.js';

export default {
  name: 'AppHeader',
  computed: {
    loggedIn: () => store.loggedIn,
    loggedInUsername: () => store.loggedInUsername,
    loggedInClub: () => store.loggedInClub,
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
