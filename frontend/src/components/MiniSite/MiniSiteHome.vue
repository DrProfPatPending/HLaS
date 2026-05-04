<template>
  <div class="mini-site-page home-page">
    <div class="home-hero">
      <img
        v-if="heroImage"
        :src="heroImage"
        :alt="clubName"
        class="hero-image"
      />
      <div v-else class="hero-placeholder">
        <div class="river-icon">🌊</div>
      </div>
      
      <div class="hero-overlay" />
      <div class="hero-content">
        <h1>{{ displayHeadline }}</h1>
        <p v-if="tagline" class="hero-tagline">{{ tagline }}</p>
      </div>
    </div>

    <section class="home-welcome">
      <div class="welcome-container">
        <h2>{{ clubName }}</h2>
        <p v-if="description" class="welcome-text">{{ description }}</p>
        <p v-else class="welcome-text">
          A small fishing club which offers access to some of the prettiest rivers and finest fly fishing in the UK.
        </p>
      </div>
    </section>

    <section class="home-features">
      <div class="feature-grid">
        <div class="feature-card">
          <div class="feature-icon">🎣</div>
          <h3>Exclusive Access</h3>
          <p>Premium fly fishing waters for our members</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">👥</div>
          <h3>Community</h3>
          <p>Join a thriving community of passionate anglers</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">📚</div>
          <h3>Learning</h3>
          <p>Expert instruction and mentorship available</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { computed } from 'vue';

export default {
  name: 'MiniSiteHome',
  props: {
    clubName: {
      type: String,
      required: true,
    },
    headline: {
      type: String,
      default: '',
    },
    tagline: {
      type: String,
      default: '',
    },
    description: {
      type: String,
      default: '',
    },
    heroImage: {
      type: String,
      default: '',
    },
  },
  setup(props) {
    const displayHeadline = computed(() => {
      if (props.headline) {
        return props.headline;
      }
      return `Welcome to ${props.clubName} - a small fishing club which offers access to some of the prettiest rivers and finest fly fishing in the UK.`;
    });

    return {
      displayHeadline,
    };
  },
};
</script>

<style scoped>
.home-page {
  width: 100%;
}

/* Hero Section */
.home-hero {
  position: relative;
  height: 400px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hero-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #a8d5d9 0%, #5b9fb4 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.river-icon {
  font-size: 4rem;
  opacity: 0.3;
}

.hero-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.3);
  z-index: 1;
}

.hero-content {
  position: relative;
  z-index: 2;
  text-align: center;
  color: white;
  max-width: 800px;
  padding: 2rem;
}

.hero-content h1 {
  font-size: 2.2rem;
  margin: 0 0 1rem 0;
  font-weight: 700;
  line-height: 1.3;
}

.hero-tagline {
  font-size: 1.1rem;
  margin: 0;
  opacity: 0.9;
}

/* Welcome Section */
.home-welcome {
  padding: 3rem 2rem;
  background: #f9f9f9;
  text-align: center;
}

.welcome-container {
  max-width: 1200px;
  margin: 0 auto;
}

.home-welcome h2 {
  margin: 0 0 1rem 0;
  color: #1a472a;
  font-size: 2rem;
}

.welcome-text {
  margin: 0;
  color: #555;
  font-size: 1.05rem;
  line-height: 1.6;
  max-width: 700px;
  margin: 0 auto;
}

/* Features Section */
.home-features {
  padding: 3rem 2rem;
  background: white;
}

.feature-grid {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
}

.feature-card {
  text-align: center;
  padding: 2rem;
  background: #f9f9f9;
  border-radius: 8px;
  border-left: 4px solid #2d6a45;
  transition: transform 0.2s, box-shadow 0.2s;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.feature-card h3 {
  margin: 0 0 0.75rem 0;
  color: #1a472a;
}

.feature-card p {
  margin: 0;
  color: #666;
  font-size: 0.95rem;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .home-hero {
    height: 250px;
  }

  .hero-content h1 {
    font-size: 1.5rem;
  }

  .home-welcome h2 {
    font-size: 1.5rem;
  }

  .feature-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
}
</style>
