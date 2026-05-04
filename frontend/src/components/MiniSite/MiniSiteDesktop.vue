<template>
  <div class="mini-site-desktop">
    <!-- Navigation Header -->
    <nav class="mini-site-nav">
      <div class="nav-container">
        <div class="nav-branding">
          <h1>{{ miniSite.title || clubCode }}</h1>
          <p v-if="miniSite.tagline" class="nav-tagline">{{ miniSite.tagline }}</p>
        </div>
        <ul class="nav-links">
          <li><a href="#home" @click.prevent="currentSection = 'home'">Home</a></li>
          <li><a href="#about" @click.prevent="currentSection = 'about'">About</a></li>
          <li><a href="#beats" @click.prevent="currentSection = 'beats'">Fishing Beats</a></li>
          <li><a href="#contact" @click.prevent="currentSection = 'contact'">Contact</a></li>
          <li><a href="#login" class="login-link">Login</a></li>
        </ul>
      </div>
    </nav>

    <!-- Hero Section -->
    <section v-if="currentSection === 'home'" class="mini-site-hero">
      <img
        v-if="miniSite.hero_image_url"
        :src="miniSite.hero_image_url"
        :alt="miniSite.title"
        class="hero-image"
      />
      <div class="hero-overlay" />
      <div class="hero-content">
        <h2>{{ miniSite.title }}</h2>
        <p v-if="miniSite.description">{{ miniSite.description }}</p>
        <button class="cta-button" @click="navigateToLogin">Join Us</button>
      </div>
    </section>

    <!-- Content Sections -->
    <section v-if="currentSection === 'home'" class="mini-site-content">
      <div class="content-container">
        <div class="featured-card">
          <h3>Welcome to {{ miniSite.title }}</h3>
          <p v-if="miniSite.description">{{ miniSite.description }}</p>
          <p>
            Discover the best fishing opportunities in the region. Manage your fishing activity,
            track your catches, and connect with fellow members.
          </p>
        </div>
      </div>
    </section>

    <!-- About Section (Placeholder) -->
    <section v-if="currentSection === 'about'" class="mini-site-content">
      <div class="content-container">
        <h3>About {{ miniSite.title }}</h3>
        <p>Club information section - coming soon</p>
      </div>
    </section>

    <!-- Beats Section (Placeholder) -->
    <section v-if="currentSection === 'beats'" class="mini-site-content">
      <div class="content-container">
        <h3>Fishing Beats</h3>
        <p>Featured fishing beats - coming soon</p>
      </div>
    </section>

    <!-- Contact Section (Placeholder) -->
    <section v-if="currentSection === 'contact'" class="mini-site-content">
      <div class="content-container">
        <h3>Contact Us</h3>
        <p>Contact information - coming soon</p>
      </div>
    </section>

    <!-- Footer -->
    <footer class="mini-site-footer">
      <div class="footer-content">
        <p>&copy; 2026 {{ miniSite.title }}. All rights reserved.</p>
        <div v-if="miniSite.social_links" class="social-links">
          <a
            v-for="(url, platform) in miniSite.social_links"
            :key="platform"
            :href="url"
            :title="platform"
            target="_blank"
            rel="noopener noreferrer"
          >
            {{ platform }}
          </a>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
import { ref } from 'vue';

export default {
  name: 'MiniSiteDesktop',
  props: {
    miniSite: {
      type: Object,
      required: true,
    },
    clubCode: {
      type: String,
      required: true,
    },
  },
  setup(props) {
    const currentSection = ref('home');

    const navigateToLogin = () => {
      window.location.href = `/club/${props.clubCode}/login/`;
    };

    return {
      currentSection,
      navigateToLogin,
    };
  },
};
</script>

<style scoped>
.mini-site-desktop {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: #fff;
  color: #333;
}

/* Navigation */
.mini-site-nav {
  background: linear-gradient(135deg, #1a472a 0%, #2d6a45 100%);
  color: white;
  padding: 1rem 0;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-branding h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.nav-tagline {
  margin: 0.25rem 0 0 0;
  font-size: 0.9rem;
  opacity: 0.9;
}

.nav-links {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
  gap: 2rem;
}

.nav-links a {
  color: white;
  text-decoration: none;
  font-size: 0.95rem;
  transition: opacity 0.2s;
}

.nav-links a:hover {
  opacity: 0.8;
}

.login-link {
  background: #ff6b6b;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-weight: 500;
}

.login-link:hover {
  background: #ff5252;
  opacity: 1;
}

/* Hero Section */
.mini-site-hero {
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

.hero-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  z-index: 1;
}

.hero-content {
  position: relative;
  z-index: 2;
  text-align: center;
  color: white;
  max-width: 600px;
  padding: 2rem;
}

.hero-content h2 {
  font-size: 2.5rem;
  margin: 0 0 1rem 0;
  font-weight: 700;
}

.hero-content p {
  font-size: 1.1rem;
  margin: 0 0 2rem 0;
  line-height: 1.5;
}

.cta-button {
  background: #ff6b6b;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  font-size: 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s;
}

.cta-button:hover {
  background: #ff5252;
}

/* Content */
.mini-site-content {
  max-width: 1200px;
  margin: 3rem auto;
  padding: 0 2rem;
}

.content-container {
  background: #f9f9f9;
  padding: 2rem;
  border-radius: 8px;
  line-height: 1.6;
}

.featured-card {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  border-left: 4px solid #2d6a45;
}

.featured-card h3 {
  margin-top: 0;
  color: #2d6a45;
}

/* Footer */
.mini-site-footer {
  background: #1a1a1a;
  color: white;
  padding: 3rem 2rem;
  margin-top: 4rem;
  text-align: center;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
}

.social-links {
  margin-top: 1rem;
  display: flex;
  justify-content: center;
  gap: 1.5rem;
}

.social-links a {
  color: #ff6b6b;
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.2s;
}

.social-links a:hover {
  color: #ff8787;
}

@media (max-width: 768px) {
  .nav-container {
    flex-direction: column;
    gap: 1rem;
  }

  .nav-links {
    margin-top: 1rem;
    flex-direction: column;
    gap: 1rem;
  }

  .hero-content h2 {
    font-size: 1.8rem;
  }

  .hero-content p {
    font-size: 0.95rem;
  }
}
</style>
