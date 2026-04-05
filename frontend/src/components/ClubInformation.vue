<template>
  <div class="club-information-container">
    <h2>{{ clubDetails.fullName }}</h2>
    <table class="club-information-table">
      <tbody>
        <tr>
          <th>Short Name</th>
          <td>{{ clubDetails.shortName }}</td>
        </tr>
        <tr>
          <th>URL</th>
          <td>
            <a
              v-if="clubDetails.websiteUrl"
              :href="clubDetails.websiteUrl"
              target="_blank"
              rel="noopener noreferrer"
            >
              {{ clubDetails.websiteUrl }}
            </a>
            <span v-else>-</span>
          </td>
        </tr>
        <tr>
          <th>Admin Email</th>
          <td>
            <a v-if="clubDetails.adminEmail" :href="`mailto:${clubDetails.adminEmail}`">
              {{ clubDetails.adminEmail }}
            </a>
            <span v-else>-</span>
          </td>
        </tr>
      </tbody>
    </table>
    <textarea
      class="club-description-box"
      :value="clubDetails.description"
      readonly
      rows="6"
    ></textarea>
  </div>
</template>

<script>
import { store, clubDetails } from '../store.js';

export default {
  name: 'ClubInformation',
  computed: {
    clubDetails: () => clubDetails.value,
  },
  methods: {
    goHome() {
      store.activeSection = 'home';
    },
  },
};
</script>
