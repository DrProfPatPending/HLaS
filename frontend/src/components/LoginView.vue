<template>
  <div class="login-container">
    <h2>Welcome to HLaS - please provide your credentials to login</h2>
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
      <input v-model="loginUsername" placeholder="Username" required />
      <input v-model="loginPassword" placeholder="Password" type="password" required />
      <button type="submit">Login</button>
    </form>
    <div class="admin-login-link">
      <a href="/admin.html">Admin login</a>
    </div>
    <div v-if="loginError" style="color: red;">{{ loginError }}</div>
  </div>
</template>

<script>
import { store, login } from '../store.js';

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
  },
  methods: { login },
};
</script>
