<template>
  <div class="mini-site-view">
    <!-- Mini site public pages -->
    <template v-if="isLoginPage">
      <login-view />
    </template>
    <template v-else>
      <!-- Show mini site or redirect to login based on config -->
      <mini-site-container :club-code="clubCode" />
    </template>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
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

    onMounted(async () => {
      // Parse the URL to extract club code and page type
      const pathArray = window.location.pathname.split('/');
      // Expected format: /club/{clubCode}/ or /club/{clubCode}/login/

      if (pathArray.length >= 3 && pathArray[1] === 'club') {
        clubCode.value = pathArray[2] || '';

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
    };
  },
};
</script>

<style scoped>
.mini-site-view {
  width: 100%;
  min-height: 100vh;
}
</style>
