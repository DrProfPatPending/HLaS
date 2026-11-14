<template>
  <div class="mini-site-page news-page">
    <mini-site-hero
      title="News &amp; Updates"
      :subtitle="subheading"
      :image="heroImage"
      :fallback-image="heroFallbackImage"
    />

    <section class="news-content">
      <div class="news-container">
        <div v-if="content" class="news-text" v-html="content" />
        <div v-else class="news-default">
          <div class="news-item">
            <div class="news-date">Recent Updates</div>
            <h3>Club News</h3>
            <p>
              Stay tuned for the latest news and updates from {{ clubName }}. We share announcements about
              upcoming events, fishing conditions, and club activities here.
            </p>
          </div>
          <div class="news-item">
            <div class="news-date">Updates</div>
            <h3>Water Conditions</h3>
            <p>
              Check back regularly for information about current water levels, fishing reports, and seasonal
              updates from our beats.
            </p>
          </div>
          <div class="news-item">
            <div class="news-date">Announcements</div>
            <h3>Upcoming Events</h3>
            <p>
              Follow this space for information about club meetings, fishing outings, tuition days, and social
              events.
            </p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import MiniSiteHero from './MiniSiteHero.vue';

export default {
  name: 'MiniSiteNews',
  components: { MiniSiteHero },
  props: {
    heroImage: { type: String, default: '' },
    heroFallbackImage: { type: String, default: '' },
    clubName: {
      type: String,
      required: true,
    },
    content: {
      type: String,
      default: '',
    },
    subheading: {
      type: String,
      default: '',
    },
  },
};
</script>

<style scoped>
.news-page {
  width: 100%;
}

.news-content {
  padding: 3rem 2rem;
  background: white;
}

.news-container {
  max-width: 900px;
  margin: 0 auto;
}

.news-text {
  color: #333;
  line-height: 1.8;
  font-size: 1rem;
}

.news-item {
  margin-bottom: 3rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #eee;
}

.news-item:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.news-date {
  display: inline-block;
  background: #2d6a45;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
}

.news-item h3 {
  margin: 0.5rem 0 1rem 0;
  color: #1a472a;
  font-size: 1.3rem;
}

.news-item p {
  margin: 0;
  color: #555;
  line-height: 1.7;
}

@media (max-width: 768px) {
  .news-content {
    padding: 2rem 1.5rem;
  }

  .news-item {
    margin-bottom: 2rem;
  }
}
</style>
