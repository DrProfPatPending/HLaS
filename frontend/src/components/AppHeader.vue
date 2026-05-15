<template>
  <div class="header-wrapper">
    <!-- Colored accent bar at top -->
    <div class="header-accent-bar" :style="{ backgroundColor: brandColor }"></div>
    
    <!-- Main header content -->
    <div class="header-content">
      <!-- Logo and Club Name -->
      <div v-if="loggedIn" class="logo-name-group">
        <div class="logo-wrapper">
          <a
            v-if="websiteUrl"
            :href="websiteUrl"
            target="_blank"
            rel="noopener noreferrer"
          >
            <img :src="logoSrc" :alt="`${loggedInClub} logo`" class="club-logo" />
          </a>
          <img
            v-else
            :src="logoSrc"
            :alt="`${loggedInClub} logo`"
            class="club-logo"
          />
        </div>
        <div class="club-info">
          <a
            v-if="websiteUrl"
            :href="websiteUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="club-name-link"
          >
            {{ clubDetails.fullName }}
          </a>
          <div v-else class="club-name">{{ clubDetails.fullName }}</div>
        </div>
      </div>
      
      <!-- Spacer to push right section to the right -->
      <div class="header-spacer"></div>
      
      <!-- User Info and Logout together on the right -->
      <div v-if="loggedIn" class="right-section">
        <div class="login-info">
          <div class="login-info-line">{{ loggedInUsername }}</div>
          <div class="login-info-line">
            <span v-if="hasAdminRole" class="login-info-admin">Admin</span><span v-else class="login-info-normal">Member</span>
          </div>
        </div>
        <app-button type="button" class="logout-button" inherit-style @click="logout">Log Out</app-button>
      </div>
    </div>
  </div>
</template>

<script>
import { store, clubDetails, clubLogoSrc, logout } from '../store.js';
import AppButton from './ui/AppButton.vue';

export default {
  name: 'AppHeader',
  components: {
    AppButton,
  },
  computed: {
    loggedIn: () => store.loggedIn,
    loggedInUsername: () => store.loggedInUsername,
    loggedInClub: () => store.loggedInClub,
    clubDetails: () => clubDetails.value,
    hasAdminRole: () => {
      const normalizedRoles = (Array.isArray(store.memberRoles) ? store.memberRoles : [])
        .map(role => String(role || '').toLowerCase().replace(/[^a-z0-9]/g, ''));
      return normalizedRoles.includes('clubadmin') || normalizedRoles.includes('appadmin');
    },
    websiteUrl: () => clubDetails.value.websiteUrl,
    logoSrc: () => clubLogoSrc.value,
    brandColor: () => {
      const color = clubDetails.value.brandColor || '#1f6b4f';
      return color;
    },
  },
  methods: {
    logout,
  },
};
</script>

<style scoped>
.header-wrapper {
  width: 100%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.header-accent-bar {
  height: 10px;
  width: 100%;
  transition: background-color 0.3s ease;
}

.header-content {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 12px;
  padding: 8px 8px;
  box-sizing: border-box;
}

.header-spacer {
  flex: 1 1 auto;
}

.right-section {
  display: flex;
  align-items: center;
  gap: 12px;
  white-space: nowrap;
  flex-shrink: 0;
}

.login-info {
  text-align: right;
}

.logo-name-group {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.logo-wrapper {
  flex-shrink: 0;
}

.club-logo {
  display: block;
  margin: 0;
  max-height: 70px;
  max-width: 70px;
  height: 70px;
  width: 70px;
  object-fit: contain;
}

.club-info {
  flex: 0 1 auto;
}

.club-name-link,
.club-name {
  display: block;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 16pt;
  font-weight: 700;
  color: #17324d;
  line-height: 1.3;
  margin: 0;
  text-decoration: none;
}

.club-name-link:hover {
  color: #0e5d8b;
  text-decoration: underline;
}

.login-info-line {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 8pt;
  color: #222;
  font-weight: 500;
  line-height: 1.4;
}

.login-info-label {
  color: #222;
  font-weight: 500;
}

.login-info-admin {
  color: #2f7a45;
  font-weight: 700;
  font-size: 8pt;
}

.login-info-normal {
  color: #17324d;
  font-weight: 600;
  font-size: 8pt;
}

/* Responsive design for tablets */
@media (max-width: 768px) {
  .header-content {
    padding: 6px 8px;
  }

  .logo-name-group {
    gap: 8px;
  }

  .club-logo {
    max-height: 56px;
    max-width: 56px;
    height: 56px;
    width: 56px;
  }

  .club-name-link,
  .club-name {
    font-size: 14pt;
  }

  .login-info-line {
    font-size: 7pt;
  }

  .right-section {
    gap: 8px;
  }
}

/* Responsive design for mobile */
@media (max-width: 480px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    padding: 6px 8px;
    gap: 8px;
  }

  .header-spacer {
    display: none;
  }

  .logo-name-group {
    gap: 10px;
    width: 100%;
  }

  .club-logo {
    max-height: 52px;
    max-width: 52px;
    height: 52px;
    width: 52px;
  }

  .club-name-link,
  .club-name {
    font-size: 12pt;
  }

  .right-section {
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .login-info {
    text-align: left;
    width: 100%;
  }

  .login-info-line {
    font-size: 7pt;
  }
}
</style>
