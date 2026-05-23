<template>
  <div class="mini-site-view">
    <template v-if="isUnknownClub">
      <div class="login-container unknown-club-container">
        <h2>Club not recognised</h2>
        <p>
          The specific club you requested <strong>{{ unknownClubCode }}</strong> is not recognised on this server,
          please either correct your URL, or click on the link below to go to the main login page for the application.
        </p>
        <p>
          <a :href="mainLoginUrl">{{ mainLoginUrl }}</a>
        </p>
      </div>
    </template>

    <!-- Mini site public pages -->
    <template v-else-if="isLoginPage">
      <login-view />
    </template>
    <template v-else>
      <!-- Show mini site or redirect to login based on config -->
      <mini-site-container :club-code="clubCode" />
    </template>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { API_BASE_URL } from '../store.js';
import MiniSiteContainer from './MiniSite/MiniSiteContainer.vue';
import LoginView from './LoginView.vue';

export default {
  name: 'MiniSiteView',
  components: {
    MiniSiteContainer,
    LoginView,
  },
  setup() {
    const clubCode = ref('');
    const isLoginPage = ref(false);
    const isUnknownClub = ref(false);
    const unknownClubCode = ref('');
    const mainLoginUrl = ref(`${window.location.origin}/`);

    const findClubByCode = (clubs, candidateCode) => {
      const target = String(candidateCode || '').trim();
      if (!target) return null;
      return (
        clubs.find((club) => club?.shortName === target)
        || clubs.find((club) => String(club?.shortName || '').toLowerCase() === target.toLowerCase())
        || null
      );
    };

    onMounted(async () => {
      // Parse the URL to extract club code and page type
      const pathArray = window.location.pathname.split('/');
      // Expected format: /club/{clubCode}/ or /club/{clubCode}/login/

      if (pathArray.length >= 3 && pathArray[1] === 'club') {
        clubCode.value = decodeURIComponent(pathArray[2] || '').trim();

        try {
          const clubsResponse = await axios.get(`${API_BASE_URL}/clubs`);
          const clubs = Array.isArray(clubsResponse?.data?.clubs)
            ? clubsResponse.data.clubs
            : [];
          const matchedClub = findClubByCode(clubs, clubCode.value);

          if (!matchedClub) {
            isUnknownClub.value = true;
            unknownClubCode.value = clubCode.value || 'unknown';
            document.title = 'HLaS - Club not recognised';
            return;
          }

          clubCode.value = matchedClub.shortName;
        } catch (error) {
          console.error('Error validating club code:', error);
        }

        // Check if this is the login page
        if (pathArray[3] === 'login') {
          isLoginPage.value = true;
        } else {
          isLoginPage.value = false;
          
          // Fetch mini-site config to get the club title
          try {
            const response = await axios.get(
              `${API_BASE_URL}/club/${clubCode.value}/mini-site`
            );
            if (response.data?.title) {
              document.title = response.data.title;
            }
          } catch (error) {
            console.error('Error fetching mini site config for title:', error);
          }
        }
      }
    });

    return {
      clubCode,
      isLoginPage,
      isUnknownClub,
      unknownClubCode,
      mainLoginUrl,
    };
  },
};
</script>

<style scoped>
.mini-site-view {
  width: 100%;
  min-height: 100vh;
}

.unknown-club-container p {
  margin-bottom: 12px;
}
</style>
