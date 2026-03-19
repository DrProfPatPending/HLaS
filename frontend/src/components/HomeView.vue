<template>
  <div class="home-container">
    <h2>Hello {{ loggedInUsername }} [{{ loggedInClub }}]</h2>
    <h3>Welcome to HookLineandSinker your one-stop shop<br>for fishing club management.</h3>
    <table class="home-nav-table">
      <tbody>
        <tr>
          <td>
            <button
              v-if="canAccessMembershipAdmin"
              type="button"
              class="home-nav-button"
              @click="navigateToSection('membership-admin')"
            >
              Membership Admin
            </button>
          </td>
          <td>
            <button
              type="button"
              class="home-nav-button"
              @click="navigateToSection('club-information')"
            >
              Club Information
            </button>
          </td>
          <td>
            <button
              v-if="canAccessNewsletters"
              type="button"
              class="home-nav-button"
              @click="navigateToSection('newsletters')"
            >
              Newsletters
            </button>
          </td>
        </tr>
        <tr>
          <td>
            <button type="button" class="home-nav-button" @click="navigateToSection('my-club')">
              My Club
            </button>
          </td>
          <td>
            <button
              type="button"
              class="home-nav-button"
              @click="navigateToSection('fishing-beats')"
            >
              Fishing Beats
            </button>
          </td>
          <td>
            <button type="button" class="home-nav-button" @click="navigateToSection('club-store')">
              Club Store
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="accessError" class="access-error">{{ accessError }}</p>
  </div>
</template>

<script>
import {
  store,
  canAccessMembershipAdmin,
  canAccessNewsletters,
  navigateToSection,
} from '../store.js';

export default {
  name: 'HomeView',
  computed: {
    loggedInUsername: () => store.loggedInUsername,
    loggedInClub: () => store.loggedInClub,
    accessError: () => store.accessError,
    canAccessMembershipAdmin: () => canAccessMembershipAdmin.value,
    canAccessNewsletters: () => canAccessNewsletters.value,
  },
  methods: { navigateToSection },
};
</script>
