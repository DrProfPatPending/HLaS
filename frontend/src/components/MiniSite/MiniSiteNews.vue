<template>
  <div class="mini-site-page news-page">
    <section class="page-header">
      <h1>News & Updates</h1>
      <p v-if="subheading" class="subheading">{{ subheading }}</p>
    </section>

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
export default {
  name: 'MiniSiteNews',
  props: {
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

.page-header {
  background: linear-gradient(135deg, #2d6a45 0%, #1a472a 100%);
  color: white;
  padding: 1rem;
  text-align: center;
  height: 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.page-header h1 {
  margin: 0;
  font-size: 14pt;
}

.subheading {
  margin: 0;
  font-size: 10pt;
  opacity: 0.9;
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
  .page-header {
    height: 90px;
  }

  .page-header h1 {
    font-size: 12pt;
  }

  .news-content {
    padding: 2rem 1.5rem;
  }

  .news-item {
    margin-bottom: 2rem;
  }
}
</style>
