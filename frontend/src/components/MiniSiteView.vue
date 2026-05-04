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

    onMounted(() => {
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
