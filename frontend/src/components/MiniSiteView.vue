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

    const getFaviconLinkElement = () => {
      let link = document.getElementById('club-favicon-link');
      if (!link) {
        link = document.createElement('link');
        link.id = 'club-favicon-link';
        link.rel = 'icon';
        document.head.appendChild(link);
      }
      return link;
    };

    const setAppFavicon = () => {
      try {
        const link = getFaviconLinkElement();
        link.type = 'image/x-icon';
        link.href = '/favicon.ico';
      } catch {
      }
    };

    const resolveClubLogoUrl = (clubShortName) => {
      const normalizedClub = String(clubShortName || '').trim();
      if (!normalizedClub) return '';

      const apiBase = String(API_BASE_URL || '/api').trim() || '/api';
      const absoluteApiBase = /^https?:\/\//i.test(apiBase)
        ? apiBase
        : `${window.location.origin}${apiBase.startsWith('/') ? '' : '/'}${apiBase}`;

      return `${absoluteApiBase}/club_logo/${encodeURIComponent(normalizedClub)}`;
    };

    const canLoadImage = (url) => new Promise((resolve) => {
      if (!url) {
        resolve(false);
        return;
      }

      const image = new Image();
      image.onload = () => resolve(true);
      image.onerror = () => resolve(false);
      image.src = url;
    });

    const ensureClubOrAppFavicon = async (clubShortName) => {
      const clubLogoUrl = resolveClubLogoUrl(clubShortName);
      const hasClubLogo = await canLoadImage(clubLogoUrl);

      if (!hasClubLogo) {
        setAppFavicon();
        return;
      }

      try {
        const link = getFaviconLinkElement();
        link.type = 'image/png';
        link.href = clubLogoUrl;
      } catch {
        setAppFavicon();
      }
    };

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
      setAppFavicon();

      // Parse the URL to extract club code and page type
      const pathArray = window.location.pathname.split('/');
      // Expected format: /club/{clubCode}/ or /club/{clubCode}/login/

      if (pathArray.length >= 3 && pathArray[1] === 'club') {
        clubCode.value = decodeURIComponent(pathArray[2] || '').trim();
        await ensureClubOrAppFavicon(clubCode.value);

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
          await ensureClubOrAppFavicon(clubCode.value);
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
