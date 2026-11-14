<template>
  <home-view
    content-scope="health-safety"
    news-title="Health and Safety Information"
    documents-title="Health & Safety Documents"
  />
</template>

<script>
import HomeView from './HomeView.vue';

export default {
  name: 'HealthSafetyView',
  components: {
    HomeView,
  },
};
</script>