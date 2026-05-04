<template>
  <div class="mini-site-page about-page">
    <section class="page-header">
      <h1>About {{ clubName }}</h1>
      <p v-if="subheading" class="subheading">{{ subheading }}</p>
    </section>

    <section class="about-content">
      <div class="about-container">
        <div v-if="content" class="about-text" v-html="content" />
        <div v-else class="about-default">
          <p>
            Welcome to {{ clubName }}. We are a dedicated community of fly fishing enthusiasts with access to
            some of the finest rivers in the UK.
          </p>
          <p>
            Our club offers exclusive membership benefits, including access to premium fishing waters, expert
            tuition, and a welcoming community of like-minded anglers.
          </p>
          <p>
            Founded on principles of conservation and sustainability, we are committed to protecting our rivers
            and ensuring they remain a source of joy for generations to come.
          </p>
          <h3>Our Values</h3>
          <ul>
            <li><strong>Sustainability:</strong> Protecting our rivers and local ecosystems</li>
            <li><strong>Community:</strong> Supporting and mentoring fellow anglers</li>
            <li><strong>Excellence:</strong> Promoting skilled, ethical fly fishing practices</li>
          </ul>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'MiniSiteAbout',
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
.about-page {
  width: 100%;
}

.page-header {
  background: linear-gradient(135deg, #2d6a45 0%, #1a472a 100%);
  color: white;
  padding: 3rem 2rem;
  text-align: center;
}

.page-header h1 {
  margin: 0 0 1rem 0;
  font-size: 2rem;
}

.subheading {
  margin: 0;
  font-size: 1.1rem;
  opacity: 0.9;
}

.about-content {
  padding: 3rem 2rem;
  background: white;
}

.about-container {
  max-width: 900px;
  margin: 0 auto;
}

.about-text {
  color: #333;
  line-height: 1.8;
  font-size: 1rem;
}

.about-default p {
  margin-bottom: 1.5rem;
  color: #555;
  line-height: 1.7;
}

.about-default h3 {
  color: #2d6a45;
  margin-top: 2rem;
  margin-bottom: 1rem;
}

.about-default ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.about-default li {
  margin-bottom: 0.75rem;
  padding-left: 1.5rem;
  position: relative;
  color: #555;
  line-height: 1.6;
}

.about-default li:before {
  content: '✓';
  position: absolute;
  left: 0;
  color: #2d6a45;
  font-weight: bold;
}

@media (max-width: 768px) {
  .page-header {
    padding: 2rem 1.5rem;
  }

  .page-header h1 {
    font-size: 1.5rem;
  }

  .about-content {
    padding: 2rem 1.5rem;
  }
}
</style>
