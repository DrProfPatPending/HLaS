<template>
  <div class="mini-site-container">
    <!-- Desktop: Show mini site or placeholder -->
    <mini-site-desktop
      v-if="!isResponsive && miniSiteData"
      :mini-site="miniSiteData"
      :club-code="clubCode"
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
    const loadingMessage = ref('Loading mini site...');
    const isResponsive = ref(false);

    // Check if responsive mode (mobile)
    const updateResponsiveState = () => {
      isResponsive.value = window.innerWidth < 768; // 768px breakpoint
    };

    onMounted(async () => {
      // Setup responsive listener
      updateResponsiveState();
      window.addEventListener('resize', updateResponsiveState);

      // Fetch mini site config
      try {
        const response = await axios.get(
          `${API_BASE_URL}/club/${props.clubCode}/mini-site`
        );
        miniSiteData.value = response.data;
      } catch (error) {
        console.error('Error fetching mini site config:', error);
        loadingMessage.value = 'Mini site not available for this club.';
        miniSiteData.value = { enabled: false };
      }
    });

    return {
      miniSiteData,
      loadingMessage,
      isResponsive,
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
