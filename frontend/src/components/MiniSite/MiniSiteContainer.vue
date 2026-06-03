<template>
  <div class="mini-site-container">
    <!-- Desktop: Show mini site or placeholder -->
    <mini-site-desktop
      v-if="!isResponsive && miniSiteData"
      :mini-site="miniSiteData"
      :club-code="clubCode"
      :club-logo-url="clubLogoUrl"
      :initial-page="currentPageFromUrl"
    />

    <!-- Responsive: Show placeholder with note about mini site -->
    <mini-site-placeholder
      v-else-if="isResponsive"
      :club-code="clubCode"
      :mini-site-enabled="miniSiteData?.enabled || false"
    />

    <!-- Neither: Show error or loading -->
    <div v-else class="mini-site-error">
      <p>{{ loadingMessage }}</p>
    </div>
  </div>
</template>

<script>
import { computed, ref, onMounted } from 'vue';
import axios from 'axios';
import { API_BASE_URL } from '../../store.js';
import MiniSiteDesktop from './MiniSiteDesktop.vue';
import MiniSitePlaceholder from './MiniSitePlaceholder.vue';

export default {
  name: 'MiniSiteContainer',
  components: {
    MiniSiteDesktop,
    MiniSitePlaceholder,
  },
  props: {
    clubCode: {
      type: String,
      required: true,
    },
  },
  setup(props) {
    const miniSiteData = ref(null);
    const clubLogoUrl = ref('');
    const loadingMessage = ref('Loading mini site...');
    const isResponsive = ref(false);
    const currentPageFromUrl = ref('home');

    // Build club logo URL (same as LoginView)
    const buildLogoUrl = (logoUrlFromClub) => {
      const logoUrl = String(logoUrlFromClub || '').trim();
      if (!logoUrl) return '';
      if (/^https?:\/\//.test(logoUrl)) return logoUrl;
      return `${API_BASE_URL}${logoUrl.startsWith('/') ? '' : '/'}${logoUrl}`;
    };

    // Parse page from URL path
    const parsePageFromUrl = () => {
      const pathMatch = window.location.pathname.match(
        /\/club\/([^/]+)\/([^/]*)\/?$/
      );
      if (pathMatch && pathMatch[2]) {
        const pageName = pathMatch[2].toLowerCase();
        // Validate page name (allow only alphanumeric and hyphens)
        if (/^[a-z0-9-]+$/.test(pageName)) {
          currentPageFromUrl.value = pageName;
          return;
        }
      }
      currentPageFromUrl.value = 'home';
    };

    // Check if responsive mode (mobile)
    const updateResponsiveState = () => {
      isResponsive.value = window.innerWidth < 768; // 768px breakpoint
    };

    onMounted(async () => {
      // Parse initial page from URL
      parsePageFromUrl();

      // Setup responsive listener
      updateResponsiveState();
      window.addEventListener('resize', updateResponsiveState);

      // Fetch clubs data to get logo URL
      try {
        const clubsResponse = await axios.get(`${API_BASE_URL}/clubs`);
        const club = clubsResponse.data.clubs?.find(
          (c) => c.shortName === props.clubCode
        );
        if (club?.logoUrl) {
          clubLogoUrl.value = buildLogoUrl(club.logoUrl);
        }
      } catch (error) {
        console.error('Error fetching clubs data:', error);
      }

      // Fetch mini site config
      try {
        const response = await axios.get(
          `${API_BASE_URL}/club/${props.clubCode}/mini-site`
        );
        miniSiteData.value = response.data;

        // Update page title immediately
        if (miniSiteData.value.title) {
          document.title = miniSiteData.value.title;
        }

        // Validate that requested page is enabled
        if (
          miniSiteData.value.pages &&
          !miniSiteData.value.pages.some(
            (p) => p.id === currentPageFromUrl.value && p.enabled
          )
        ) {
          // If page not enabled, redirect to home
          if (
            !miniSiteData.value.pages.some((p) => p.id === 'home' && p.enabled)
          ) {
            // Home not enabled (shouldn't happen), show error
            loadingMessage.value = 'Home page not available.';
          } else {
            // Redirect to home
            currentPageFromUrl.value = 'home';
          }
        }
      } catch (error) {
        const status = error?.response?.status;
        if (status === 404) {
          // Club no longer exists — redirect to main site
          window.location.replace('/');
          return;
        }
        console.error('Error fetching mini site config:', error);
        loadingMessage.value = 'Mini site not available for this club.';
        miniSiteData.value = null;
      }
    });

    return {
      miniSiteData,
      clubLogoUrl,
      loadingMessage,
      isResponsive,
      currentPageFromUrl,
    };
  },
};
</script>

<style scoped>
.mini-site-container {
  width: 100%;
  min-height: 100vh;
}

.mini-site-error {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  font-size: 1.2rem;
  color: #888;
  background-color: #f5f5f5;
}
</style>
