<template>
  <div class="mini-site-desktop">
    <!-- Navigation Header -->
    <nav class="mini-site-nav">
      <div class="nav-container">
        <!-- Logo Left -->
        <div class="nav-logo">
          <img
            v-if="clubLogoUrl"
            :src="clubLogoUrl"
            :alt="miniSite.title"
            class="logo-image"
          />
          <div v-else class="logo-placeholder">{{ miniSite.title || clubCode }}</div>
        </div>

        <!-- Menu Center -->
        <ul class="nav-links">
          <li v-for="page in enabledPages" :key="page.id">
            <a
              :href="`#${page.id}`"
              :class="{ active: currentPage === page.id }"
              @click.prevent="currentPage = page.id"
            >
              {{ page.title }}
            </a>
          </li>
        </ul>

        <!-- Login Button Right -->
        <a href="#login" class="login-button" @click.prevent="navigateToLogin">
          Log In
        </a>
      </div>
    </nav>

    <!-- Page Content -->
    <main class="mini-site-main">
      <component
        :is="currentPageComponent"
        :key="currentPage"
        :club-name="miniSite.title || clubCode"
        :headline="getPageContent(currentPage, 'headline')"
        :tagline="miniSite.tagline"
        :description="miniSite.description"
        :hero-image="miniSite.hero_image_url"
        :content="getPageContent(currentPage, 'content')"
        :contact-email="miniSite.contact_email"
        :contact-phone="miniSite.contact_phone"
        :contact-address="miniSite.contact_address"
      />
    </main>

    <!-- Footer -->
    <footer class="mini-site-footer">
      <div class="footer-content">
        <p>&copy; 2026 {{ miniSite.title }}. All rights reserved.</p>
        <div v-if="miniSite.social_links && Object.keys(miniSite.social_links).length > 0" class="social-links">
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
import { ref, computed } from 'vue';
import MiniSiteHome from './MiniSiteHome.vue';
import MiniSiteAbout from './MiniSiteAbout.vue';
import MiniSiteWaters from './MiniSiteWaters.vue';
import MiniSiteNews from './MiniSiteNews.vue';
import MiniSiteJoin from './MiniSiteJoin.vue';
import MiniSiteContact from './MiniSiteContact.vue';

const PAGE_COMPONENTS = {
  home: MiniSiteHome,
  about: MiniSiteAbout,
  waters: MiniSiteWaters,
  news: MiniSiteNews,
  join: MiniSiteJoin,
  contact: MiniSiteContact,
};

export default {
  name: 'MiniSiteDesktop',
  components: {
    MiniSiteHome,
    MiniSiteAbout,
    MiniSiteWaters,
    MiniSiteNews,
    MiniSiteJoin,
    MiniSiteContact,
  },
  props: {
    miniSite: {
      type: Object,
      required: true,
    },
    clubCode: {
      type: String,
      required: true,
    },
    clubLogoUrl: {
      type: String,
      default: '',
    },
    initialPage: {
      type: String,
      default: 'home',
    },
  },
  setup(props) {
    const currentPage = ref(props.initialPage);

    // Get enabled pages from the pages array
    const enabledPages = computed(() => {
      if (!props.miniSite.pages || !Array.isArray(props.miniSite.pages)) {
        return [];
      }
      return props.miniSite.pages.filter((page) => page.enabled);
    });

    // Get the current page component
    const currentPageComponent = computed(() => {
      return PAGE_COMPONENTS[currentPage.value] || MiniSiteHome;
    });

    // Get page-specific content
    const getPageContent = (pageId, contentType) => {
      const page = props.miniSite.pages?.find((p) => p.id === pageId);
      if (!page) return '';

      switch (contentType) {
        case 'headline':
          return page.headline || '';
        case 'content':
          return page.content || '';
        default:
          return '';
      }
    };

    const navigateToLogin = () => {
      window.location.href = `/club/${props.clubCode}/login/`;
    };

    return {
      currentPage,
      enabledPages,
      currentPageComponent,
      getPageContent,
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
  min-height: 100vh;
  display: flex;
  flex-direction: column;
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
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
}

/* Logo */
.nav-logo {
  flex-shrink: 0;
}

.logo-image {
  height: 50px;
  width: auto;
  max-width: 150px;
  object-fit: contain;
}

.logo-placeholder {
  font-size: 1.2rem;
  font-weight: bold;
  white-space: nowrap;
  color: white;
}

/* Navigation Links */
.nav-links {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
  gap: 2rem;
  flex: 1;
  justify-content: center;
}

.nav-links a {
  color: white;
  text-decoration: none;
  font-size: 0.95rem;
  font-weight: 500;
  transition: opacity 0.3s, border-bottom 0.3s;
  border-bottom: 2px solid transparent;
  padding: 0.5rem 0;
}

.nav-links a:hover {
  opacity: 0.8;
  border-bottom-color: white;
}

.nav-links a.active {
  border-bottom-color: white;
  opacity: 1;
}

/* Login Button */
.login-button {
  flex-shrink: 0;
  background: #ff6b6b;
  color: white;
  padding: 0.5rem 1.5rem;
  border-radius: 4px;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
  transition: background 0.3s, transform 0.2s;
  display: inline-block;
  white-space: nowrap;
}

.login-button:hover {
  background: #ff5252;
  transform: translateY(-2px);
}

/* Main Content */
.mini-site-main {
  flex: 1;
  width: 100%;
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

.footer-content p {
  margin: 0;
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

/* Responsive Design */
@media (max-width: 1000px) {
  .nav-container {
    gap: 1.5rem;
  }

  .nav-links {
    gap: 1.5rem;
  }

  .nav-links a {
    font-size: 0.9rem;
  }
}

@media (max-width: 768px) {
  .nav-container {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .logo-image {
    height: 40px;
  }

  .nav-links {
    order: 3;
    width: 100%;
    gap: 1rem;
    flex-direction: column;
    justify-content: center;
  }

  .nav-links a {
    padding: 0.75rem;
    text-align: center;
  }

  .login-button {
    order: 2;
    width: 100%;
    text-align: center;
  }
}
</style>
