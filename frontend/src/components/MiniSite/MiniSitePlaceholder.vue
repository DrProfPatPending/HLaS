<template>
  <div class="mini-site-placeholder">
    <!-- Simple responsive navigation -->
    <nav class="responsive-nav">
      <div class="nav-header">
        <span class="club-name">{{ clubCode }}</span>
        <button class="menu-button" @click="menuOpen = !menuOpen">
          ☰
        </button>
      </div>
      <div v-if="menuOpen" class="nav-menu">
        <a href="#" @click.prevent="navigateToLogin" class="nav-login">Login →</a>
      </div>
    </nav>

    <!-- Placeholder Content -->
    <div class="placeholder-content">
      <div class="placeholder-hero">
        <div class="placeholder-icon">🎣</div>
        <h1>{{ clubCode }}</h1>
        <p class="placeholder-subtitle">Fishing Club Management</p>
      </div>

      <div class="placeholder-message">
        <h2>Mobile View</h2>
        <p>
          The full club mini site is optimized for desktop viewing.
          <strong>Please switch to desktop mode</strong> to explore:
        </p>

        <ul class="feature-list">
          <li>Club information and history</li>
          <li>Fishing beat details and maps</li>
          <li>Gallery and media</li>
          <li>Event calendar</li>
          <li>Contact information</li>
        </ul>

        <div v-if="miniSiteEnabled" class="enabled-notice">
          <p>✓ This club has a mini site available</p>
        </div>
        <div v-else class="info-notice">
          <p>ℹ This club's mini site is not yet configured</p>
        </div>

        <button class="login-button" @click="navigateToLogin">
          Login to Member Portal
        </button>
      </div>

      <footer class="responsive-footer">
        <p>&copy; 2026 {{ clubCode }}. Hook Line and Sinker.</p>
      </footer>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';

export default {
  name: 'MiniSitePlaceholder',
  props: {
    clubCode: {
      type: String,
      required: true,
    },
    miniSiteEnabled: {
      type: Boolean,
      default: false,
    },
  },
  setup(props) {
    const menuOpen = ref(false);

    const navigateToLogin = () => {
      window.location.href = `/club/${props.clubCode}/login/`;
    };

    return {
      menuOpen,
      navigateToLogin,
    };
  },
};
</script>

<style scoped>
.mini-site-placeholder {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f5f5 0%, #ebebeb 100%);
  display: flex;
  flex-direction: column;
}

/* Responsive Navigation */
.responsive-nav {
  background: linear-gradient(135deg, #1a472a 0%, #2d6a45 100%);
  color: white;
  padding: 1rem;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.nav-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 100%;
}

.club-name {
  font-size: 1.25rem;
  font-weight: 600;
}

.menu-button {
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.5rem;
}

.nav-menu {
  margin-top: 1rem;
  padding: 0.5rem 0;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.nav-login {
  display: block;
  padding: 0.75rem 0;
  color: #ff6b6b;
  text-decoration: none;
  font-weight: 500;
}

/* Content */
.placeholder-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 2rem 1rem;
  max-width: 500px;
  margin: 0 auto;
  width: 100%;
}

.placeholder-hero {
  text-align: center;
  margin-bottom: 2rem;
  background: white;
  padding: 2rem 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.placeholder-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.placeholder-hero h1 {
  margin: 0 0 0.5rem 0;
  color: #1a472a;
  font-size: 1.75rem;
}

.placeholder-subtitle {
  margin: 0;
  color: #666;
  font-size: 0.95rem;
}

.placeholder-message {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.placeholder-message h2 {
  margin-top: 0;
  color: #1a472a;
  font-size: 1.25rem;
}

.placeholder-message p {
  color: #555;
  line-height: 1.5;
  margin: 0 0 1rem 0;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 1.5rem 0;
  color: #555;
}

.feature-list li {
  padding: 0.5rem 0 0.5rem 1.5rem;
  position: relative;
}

.feature-list li:before {
  content: "▸";
  position: absolute;
  left: 0;
  color: #ff6b6b;
  font-weight: bold;
}

.enabled-notice {
  background: #e8f5e9;
  border-left: 4px solid #4caf50;
  padding: 0.75rem;
  margin: 1rem 0;
  border-radius: 4px;
}

.enabled-notice p {
  margin: 0;
  color: #2e7d32;
  font-size: 0.9rem;
}

.info-notice {
  background: #e3f2fd;
  border-left: 4px solid #2196f3;
  padding: 0.75rem;
  margin: 1rem 0;
  border-radius: 4px;
}

.info-notice p {
  margin: 0;
  color: #1565c0;
  font-size: 0.9rem;
}

.login-button {
  width: 100%;
  background: #ff6b6b;
  color: white;
  border: none;
  padding: 1rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 1rem;
  transition: background 0.2s;
}

.login-button:active {
  background: #ff5252;
}

/* Footer */
.responsive-footer {
  text-align: center;
  color: #777;
  font-size: 0.85rem;
  padding: 2rem 1rem 1rem;
  margin-top: auto;
}

.responsive-footer p {
  margin: 0;
}
</style>
