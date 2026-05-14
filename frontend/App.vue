<template>
  <v-app id="app">
    <app-header />
    <login-view v-if="!loggedIn" />
    <div v-else class="app-member-shell">
      <div
        v-if="activeSection === 'home' && VerboseDebug"
        class="mobile-home-greeting"
      >
        <p>Hello {{ loggedInUsername }} [{{ loggedInClub }}]</p>
        <p>Welcome to HookLineandSinker your one-stop shop<br>for fishing club management.</p>
      </div>
      <div class="app-member-sidebar-group">
        <aside class="app-member-sidebar" aria-label="Primary navigation">
          <app-card class="app-member-sidebar-card">
            <div class="app-member-sidebar-title">Navigation</div>
            <button
              type="button"
              class="app-member-nav-button app-member-home-button"
              :class="{ 'is-active': activeSection === 'home' }"
              @click="navigate('home')"
            >
              {{ clubShortName }}
            </button>
            <button
              type="button"
              class="app-member-nav-button"
              :class="{ 'is-active': activeSection === 'my-club' }"
              @click="navigate('my-club')"
            >
              My Club
            </button>
            <button
              type="button"
              class="app-member-nav-button"
              :class="{ 'is-active': activeSection === 'beat-details' }"
              @click="navigate('beat-details')"
            >
              Beat Details
            </button>
            <button
              type="button"
              class="app-member-nav-button"
              :class="{ 'is-active': activeSection === 'fishing-beats' }"
              @click="navigate('fishing-beats')"
            >
              Fishing Beats
            </button>
            <button
              type="button"
              class="app-member-nav-button"
              :class="{ 'is-active': activeSection === 'catch-return' }"
              @click="navigate('catch-return')"
            >
              Catch Return
            </button>
            <button
              type="button"
              class="app-member-nav-button"
              :class="{ 'is-active': activeSection === 'club-information' }"
              @click="navigate('club-information')"
            >
              Club Information
            </button>
            <button
              type="button"
              class="app-member-nav-button"
              :class="{ 'is-active': activeSection === 'club-store' }"
              @click="navigate('club-store')"
            >
              Club Store
            </button>
            <button
              v-if="canAccessNewsletters"
              type="button"
              class="app-member-nav-button"
              :class="{ 'is-active': activeSection === 'newsletters', 'is-admin': true }"
              @click="navigate('newsletters')"
            >
              News/Updates
            </button>
            <button
              v-if="canAccessMembershipAdmin"
              type="button"
              class="app-member-nav-button"
              :class="{ 'is-active': activeSection === 'membership-admin' || activeSection === 'member-edit', 'is-admin': true }"
              @click="navigate('membership-admin')"
            >
              Membership Admin
            </button>
            <button
              v-if="canAccessMembershipAdmin"
              type="button"
              class="app-member-nav-button"
              :class="{ 'is-active': activeSection === 'club-settings', 'is-admin': true }"
              @click="navigate('club-settings')"
            >
              Club Settings
            </button>
          </app-card>
        </aside>

        <aside
          v-if="showMyClubSubnav"
          class="app-member-subnav"
          aria-label="My Club section navigation"
        >
          <app-card class="app-member-subnav-card">
            <div class="app-member-sidebar-title">My Club</div>
            <button
              v-for="tab in myClubTabs"
              :key="tab.id"
              type="button"
              class="app-member-subnav-button"
              :class="{ 'is-active': myClubActiveTab === tab.id }"
              @click="selectMyClubTab(tab.id)"
            >
              {{ tab.label }}
            </button>
          </app-card>
        </aside>
      </div>

      <main class="app-member-content">
        <home-view v-if="activeSection === 'home'" />
        <membership-admin v-else-if="activeSection === 'membership-admin'" />
        <club-information v-else-if="activeSection === 'club-information'" />
        <my-club v-else-if="activeSection === 'my-club'" />
        <newsletters v-else-if="activeSection === 'newsletters'" />
        <fishing-beats v-else-if="activeSection === 'fishing-beats'" />
        <beat-details v-else-if="activeSection === 'beat-details'" />
        <catch-return v-else-if="activeSection === 'catch-return'" />
        <club-settings v-else-if="activeSection === 'club-settings'" />
        <member-edit v-else-if="activeSection === 'member-edit'" />
        <div v-else class="section-placeholder">
          <h2>{{ sectionDisplayName(activeSection) }}</h2>
          <p>This section is coming soon.</p>
        </div>
      </main>
    </div>
    <footer class="app-footer">
      <img src="./logos/HLaS.png" alt="HLaS logo" class="app-footer-logo" />
      <span>(c) 2026 - ScoffySoft</span>
      <span class="app-footer-separator">|</span>
      <a href="mailto: robbie.scoff@gmail.com">Contact Us</a>
    </footer>
  </v-app>
</template>

<script>
import { VerboseDebug } from './src/localConfig.js';
import AppHeader from './src/components/AppHeader.vue';
import LoginView from './src/components/LoginView.vue';
import HomeView from './src/components/HomeView.vue';
import MembershipAdmin from './src/components/MembershipAdmin.vue';
import ClubInformation from './src/components/ClubInformation.vue';
import Newsletters from './src/components/Newsletters.vue';
import FishingBeats from './src/components/FishingBeats.vue';
import BeatDetails from './src/components/BeatDetails.vue';
import CatchReturn from './src/components/CatchReturn.vue';
import MemberEdit from './src/components/MemberEdit.vue';
import MyClub from './src/components/MyClub.vue';
import ClubSettings from './src/components/ClubSettings.vue';
import AppCard from './src/components/ui/AppCard.vue';
import {
  store,
  restoreMemberSession,
  applyMemberAuthHeader,
  initializeAuthInterceptor,
  teardownAuthInterceptor,
  loadClubs,
  fetchMembers,
  canAccessMembershipAdmin,
  canAccessNewsletters,
  clubDetails,
  loadAppSettings,
  syncActiveTheme,
  MY_CLUB_TABS,
  navigateToSection,
  setMyClubActiveTab,
  sectionDisplayName,
} from './src/store.js';

export default {
    data() {
      return {
        VerboseDebug,
      };
    },
  components: {
    AppHeader,
    LoginView,
    HomeView,
    MembershipAdmin,
    ClubInformation,
    MyClub,
    Newsletters,
    FishingBeats,
    BeatDetails,
    CatchReturn,
    MemberEdit,
    ClubSettings,
    AppCard,
  },
  computed: {
    loggedIn: () => store.loggedIn,
    loggedInUsername: () => store.loggedInUsername,
    loggedInClub: () => store.loggedInClub,
    selectedClub: () => store.selectedClub,
    activeSection: () => store.activeSection,
    canAccessMembershipAdmin: () => canAccessMembershipAdmin.value,
    canAccessNewsletters: () => canAccessNewsletters.value,
    clubShortName: () => clubDetails.value.shortName || store.loggedInClub || 'Club',
    myClubTabs: () => MY_CLUB_TABS,
    myClubActiveTab: () => store.myClubActiveTab,
    showMyClubSubnav: () => store.activeSection === 'my-club',
  },
  created() {
    loadAppSettings();
    restoreMemberSession();
    applyMemberAuthHeader();
    initializeAuthInterceptor();
    loadClubs();
    if (store.loggedIn && canAccessMembershipAdmin.value) {
      fetchMembers();
    }
  },
  beforeUnmount() {
    teardownAuthInterceptor();
  },
  watch: {
    loggedInClub: {
      immediate: true,
      handler() {
        this.updateClubFavicon();
        syncActiveTheme();
      },
    },
    selectedClub() {
      this.updateClubFavicon();
      syncActiveTheme();
    },
  },
  methods: {
    sectionDisplayName,
    resolveClubFaviconUrl(clubShortName) {
      const normalizedClub = String(clubShortName || '').trim();
      if (!normalizedClub) return '/favicon.ico';

      const apiBase = String(store.apiBaseUrl || '/api').trim() || '/api';
      const absoluteApiBase = /^https?:\/\//i.test(apiBase)
        ? apiBase
        : `${window.location.origin}${apiBase.startsWith('/') ? '' : '/'}${apiBase}`;

      return `${absoluteApiBase}/club_logo/${encodeURIComponent(normalizedClub)}`;
    },
    updateClubFavicon() {
      try {
        const activeClub = store.loggedIn ? store.loggedInClub : store.selectedClub;
        const faviconHref = this.resolveClubFaviconUrl(activeClub);

        let link = document.getElementById('club-favicon-link');
        if (!link) {
          link = document.createElement('link');
          link.id = 'club-favicon-link';
          link.rel = 'icon';
          link.type = 'image/png';
          document.head.appendChild(link);
        }
        link.href = faviconHref;

        const resolvedClub = String(activeClub || '').trim();
        document.title = resolvedClub ? `HLaS - ${resolvedClub}` : 'HLaS Member login';
      } catch {
      }
    },
    navigate(sectionKey) {
      navigateToSection(sectionKey);
    },
    selectMyClubTab(tabId) {
      setMyClubActiveTab(tabId);
    },
    goHome() {
      store.activeSection = 'home';
    },
  },
};

</script>

<style>
#app .app-member-shell {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 20px;
  align-items: start;
  width: 100%;
  box-sizing: border-box;
  padding: 10px 20px 26px;
}
#app .app-member-sidebar-group {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  min-width: 0;
}
#app .app-member-sidebar {
  min-width: 0;
}
#app .app-member-subnav {
  min-width: 0;
}
#app .app-member-sidebar-card,
#app .app-member-subnav-card {
  position: sticky;
  top: 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid #d7dce2;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
  font-family: Helvetica, Arial, sans-serif;
}
#app .app-member-sidebar-title {
  font-size: 10pt;
  font-weight: 700;
  color: #17324d;
}
#app .app-member-sidebar-club {
  margin-bottom: 4px;
  font-size: 0.8rem;
  font-weight: 700;
  color: #56748f;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
#app .app-member-nav-button {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid #2d5f8b;
  border-radius: 8px;
  background: linear-gradient(180deg, #4b86b4 0%, #2d5f8b 100%);
  color: #fff;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 8pt;
  font-weight: 600;
  text-align: center;
  cursor: pointer;
  transition: transform 0.12s ease, box-shadow 0.12s ease, background 0.12s ease;
}
#app .app-member-nav-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 5px 14px rgba(45, 95, 139, 0.24);
  background: linear-gradient(180deg, #5a97c7 0%, #2f6c9c 100%);
}
#app .app-member-nav-button.is-active {
  border-color: #17324d;
  background: linear-gradient(180deg, #2f6c9c 0%, #17324d 100%);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.15);
}
#app .app-member-home-button {
  color: #3f4852;
  border-color: #b8c0c8;
  background: linear-gradient(180deg, #f1f3f5 0%, #dce1e6 100%);
}
#app .app-member-home-button:hover {
  background: linear-gradient(180deg, #f7f8fa 0%, #e4e8ec 100%);
  box-shadow: 0 5px 14px rgba(88, 96, 105, 0.18);
}
#app .app-member-home-button.is-active {
  color: #2d3338;
  border-color: #9ba5ae;
  background: linear-gradient(180deg, #dce1e6 0%, #c0c8d0 100%);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.4);
}
#app .app-member-nav-button.is-admin {
  border-color: #2f7a45;
  background: linear-gradient(180deg, #49a065 0%, #2f7a45 100%);
}
#app .app-member-nav-button.is-admin:hover {
  background: linear-gradient(180deg, #5ab57a 0%, #368c4f 100%);
  box-shadow: 0 5px 14px rgba(47, 122, 69, 0.24);
}
#app .app-member-nav-button.is-admin.is-active {
  border-color: #215835;
  background: linear-gradient(180deg, #368c4f 0%, #215835 100%);
}
#app .app-member-subnav-button {
  width: 100%;
  min-width: 168px;
  padding: 11px 12px;
  border: 1px solid #9ab0c6;
  border-radius: 8px;
  background: linear-gradient(180deg, #f7f9fc 0%, #e3ebf3 100%);
  color: #17324d;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
  transition: transform 0.12s ease, box-shadow 0.12s ease, background 0.12s ease;
}
#app .app-member-subnav-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 5px 14px rgba(45, 95, 139, 0.18);
  background: linear-gradient(180deg, #ffffff 0%, #eaf1f8 100%);
}
#app .app-member-subnav-button.is-active {
  border-color: #17324d;
  background: linear-gradient(180deg, #2f6c9c 0%, #17324d 100%);
  color: #ffffff;
}
#app .app-member-content {
  min-width: 0;
}
#app .home-container,
#app .section-placeholder,
#app .club-information-container,
#app .newsletters-container,
#app .member-edit-container,
#app .beat-details-container,
#app .catch-return-container,
#app .membership-admin-container,
#app .club-settings-container {
  width: 100%;
  max-width: none;
  margin: 0;
  font-family: Helvetica, Arial, sans-serif;
}
#app .access-error {
  margin-top: 16px;
  color: #b00020;
}
#app .section-placeholder {
  padding: 24px;
  border: 1px solid #d7dce2;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
}
#app .newsletters-container,
#app .fishing-beats-container {
  margin: 0;
  font-family: Helvetica, Arial, sans-serif;
}
#app .fishing-beats-container {
  max-width: none;
  width: 100%;
  margin: 0;
}
#app .fishing-beats-header {
  display: flex;
  align-items: center;
  gap: 12px;
}
#app .fishing-beats-header h2 {
  margin: 0;
}
#app .fishing-beats-back-button {
  white-space: nowrap;
}
#app .newsletter-table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}
#app .newsletter-table th,
#app .newsletter-table td {
  border: 1px solid #ccc;
  padding: 8px;
  text-align: left;
  font-size: 10pt;
}
#app .newsletter-table th {
  background: #f0f0f0;
  vertical-align: top;
}
#app .newsletter-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin: 10px 0;
}
#app .newsletter-from-indicator {
  font-size: 9pt;
  color: #555;
}
#app .newsletter-from-not-set {
  color: #a94442;
}
#app .newsletter-toolbar {
  margin-bottom: 12px;
}
#app .newsletter-template-label {
  font-size: 10pt;
}
#app .newsletter-template-select {
  min-width: 220px;
  padding: 6px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: #fff;
}
#app .newsletter-template-preview {
  margin-bottom: 12px;
  padding: 10px;
  border: 1px solid #ccc;
  background: #fafafa;
}
#app .newsletter-template-preview h3 {
  margin: 0 0 8px 0;
  font-size: 11pt;
}
#app .newsletter-template-preview p {
  margin: 0 0 8px 0;
  font-size: 10pt;
}
#app .newsletter-template-preview-body {
  margin: 0;
  white-space: pre-wrap;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
}
#app .newsletter-preview-note {
  font-size: 8.5pt;
  font-weight: normal;
  color: #888;
}
#app .newsletter-template-tags-hint {
  margin-top: 10px;
  font-size: 9.5pt;
  color: #444;
}
#app .newsletter-tag-chip {
  display: inline-block;
  margin: 3px 4px 0 0;
  padding: 2px 6px;
  background: #e8f0fe;
  border: 1px solid #b3c6f0;
  border-radius: 3px;
  font-family: monospace;
  font-size: 9pt;
  color: #1a3a7a;
  cursor: default;
}
#app .newsletter-status {
  color: #1c6b2a;
  margin-bottom: 8px;
}
#app .newsletter-error {
  color: #c62828;
  margin-bottom: 8px;
}
#app .fishing-beats-table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}
#app .fishing-beats-layout {
  display: grid;
  grid-template-columns: 30% 70%;
  align-items: start;
  gap: 12px;
}
#app .fishing-beat-detail-panel {
  width: 100%;
  min-width: 0;
  border: 1px solid #ccc;
  background: #fafafa;
  padding: 10px;
  margin-top: 12px;
}
#app .fishing-beat-detail-panel h3 {
  margin: 0 0 10px 0;
  font-size: 11pt;
}
#app .fishing-beat-detail-table {
  width: 100%;
  border-collapse: collapse;
}
#app .fishing-beat-detail-table th,
#app .fishing-beat-detail-table td {
  border: 1px solid #ccc;
  padding: 6px;
  text-align: left;
  font-size: 10pt;
  vertical-align: top;
}
#app .fishing-beat-detail-table th {
  width: 130px;
  background: #f0f0f0;
}
#app .fishing-beat-map-wrap {
  margin-top: 10px;
}
#app .fishing-beat-map {
  width: 100%;
  height: 230px;
  border: 1px solid #ccc;
  box-sizing: border-box;
}
#app .fishing-beat-map-status {
  margin-top: 6px;
  font-size: 9pt;
  color: #555;
}
#app .fishing-beat-parking-list {
  margin: 0;
  padding-left: 18px;
}
#app .parking-pin-marker {
  background: transparent;
  border: none;
}
#app .parking-pin-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #1c7c3f;
  color: #fff;
  font-size: 10pt;
  font-weight: bold;
  line-height: 20px;
  text-align: center;
  box-shadow: 0 0 0 1px #fff inset;
}
#app .beat-name-link {
  display: inline-block;
  color: #007bff;
  text-decoration: underline;
  cursor: pointer;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
}
#app .beat-name-link.active {
  font-weight: bold;
}
#app .fishing-beats-table th,
#app .fishing-beats-table td {
  border: 1px solid #ccc;
  padding: 8px;
  text-align: left;
  font-size: 10pt;
}
#app .fishing-beats-table th {
  background: #f0f0f0;
}
#app .fishing-beats-sort-header {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}
#app .fishing-beats-sort-controls {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}
#app .fishing-beats-sort-button {
  margin-right: 0;
  padding: 3px 7px;
  font-size: 8.5pt;
  line-height: 1.2;
}
#app .fishing-beats-sort-button.is-active {
  background-color: #0056b3;
  border-color: #00448f;
  font-weight: bold;
}
#app .club-information-table {
  width: 100%;
  max-width: 680px;
  border-collapse: collapse;
  margin: 12px 0;
}
#app .club-information-table th,
#app .club-information-table td {
  border: 1px solid #ccc;
  padding: 8px;
  text-align: left;
  font-size: 10pt;
}
#app .club-information-table th {
  width: 180px;
  background: #f0f0f0;
}
#app .club-description-box {
  width: 100%;
  max-width: 680px;
  box-sizing: border-box;
  padding: 8px;
  margin-bottom: 12px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
  resize: vertical;
}
#app .member-edit-container {
  margin: 0;
  font-family: Helvetica, Arial, sans-serif;
}
#app .member-edit-top-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
#app .member-edit-actions-top {
  flex: 1;
}
#app .member-edit-photo-panel {
  width: 160px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
#app .member-edit-photo-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}
#app .member-edit-position {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 9pt;
  color: #555;
  margin-bottom: 8px;
}
#app .member-edit-photo {
  width: 140px;
  height: 140px;
  object-fit: cover;
  border: 2px solid #ccc;
  border-radius: 4px;
  background: #f0f0f0;
}
#app .member-edit-photo-name {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 8pt;
  color: #666;
  align-self: flex-end;
}
#app .member-detail-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 14px;
}
#app .member-detail-table th,
#app .member-detail-table td {
  border: 1px solid #ccc;
  padding: 8px;
  font-size: 9pt;
}
#app .member-detail-table th {
  background: #f0f0f0;
  width: 30%;
}
#app .member-detail-input {
  width: 100%;
  box-sizing: border-box;
  padding: 6px;
}
#app .member-edit-actions {
  display: flex;
  gap: 8px;
}
#app .membership-admin-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
#app .membership-admin-header h1 {
  margin: 0;
}
#app .membership-details-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
#app .pagination-controls {
  margin-bottom: 20px;
  text-align: center;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 8pt;
}
#app .records-per-page-select {
  margin-left: 12px;
  padding: 4px 6px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 8pt;
  border: 1px solid #ccc;
  border-radius: 3px;
  background-color: white;
  cursor: pointer;
}
#app .pagination-controls button[disabled] {
  opacity: 0.5;
  cursor: not-allowed;
}
#app .member-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
  font-family: Helvetica, Arial, sans-serif;
}
#app .member-table th, #app .member-table td {
  border: 1px solid #ccc;
  padding: 8px;
  text-align: left;
}
#app .member-table th {
  vertical-align: top;
  font-size: 10pt;
}
#app .member-table td {
  font-size: 8pt;
}
/* Column minimum widths */
#app .member-table th:nth-child(1), #app .member-table td:nth-child(1) { min-width: 60px; } /* ID */
#app .member-table th:nth-child(2), #app .member-table td:nth-child(2) { min-width: 60px; } /* Number */
#app .member-table th:nth-child(3), #app .member-table td:nth-child(3) { min-width: 140px; } /* Members_Name */
#app .member-table th:nth-child(4), #app .member-table td:nth-child(4) { min-width: 160px; } /* E_Mail */
#app .member-table th:nth-child(5), #app .member-table td:nth-child(5) { min-width: 100px; } /* Mobile */
#app .member-table th:nth-child(6), #app .member-table td:nth-child(6) { min-width: 90px; } /* Car_Reg */
#app .member-table th:nth-child(7), #app .member-table td:nth-child(7) { min-width: 100px; } /* Member_Type */
#app .member-table th:nth-child(8), #app .member-table td:nth-child(8) { min-width: 100px; } /* EA_Licence */
#app .member-table th:nth-child(9), #app .member-table td:nth-child(9) { min-width: 110px; } /* Licence_Expiry */
#app .member-table th:nth-child(10), #app .member-table td:nth-child(10) { min-width: 90px; } /* Paid_Up_2026 */
#app .member-table th:nth-child(11), #app .member-table td:nth-child(11) { min-width: 70px; } /* Paused */
#app .member-table th:nth-child(12), #app .member-table td:nth-child(12) { min-width: 80px; } /* Resigned */
#app .column-filter {
  display: block;
  width: 100%;
  margin-top: 4px;
  box-sizing: border-box;
}
#app .column-filter[type="text"],
#app .column-filter input,
#app .column-filter select {
  padding: 4px;
  border: 1px solid #ccc;
  border-radius: 2px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 8pt;
}
#app .page-numbers {
  margin-top: 15px;
  text-align: center;
}
#app .page-numbers button {
  margin: 0 4px;
  min-width: 36px;
}
#app .page-numbers button:hover {
  background-color: #0069d9;
}
#app .page-numbers button.active {
  background-color: #007bff;
  color: white;
  border-color: #0056b3;
}
#app .member-link {
  color: #007bff;
  text-decoration: none;
  cursor: pointer;
}
#app .member-link:hover {
  color: #0056b3;
  text-decoration: underline;
}
#app .lookup-table th,
#app .lookup-table td {
  font-family: "Courier New", Courier, monospace;
  font-size: 8pt;
  border: 2px solid #ccc;
}
#app .lookup-table {
  border-collapse: collapse;
  border: 2px solid #ccc;
}
#app .member-table th {
  background: #f0f0f0;
}
#app .sort-arrow {
  cursor: pointer;
  font-size: 1em;
  margin-left: 2px;
  color: #666;
}
#app .sort-arrow.active {
  color: #0056b3;
  font-weight: bold;
}
#app .login-container {
  max-width: 400px;
  margin: 40px auto;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
  background: #f9f9f9;
}
#app .login-container .form-field {
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
}
#app .login-container .form-field label {
  margin-bottom: 5px;
  font-weight: bold;
  font-size: 14px;
}
#app .login-container .club-select {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
  background-color: white;
  cursor: pointer;
}
#app .login-container input {
  margin-bottom: 10px;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  width: 100%;
  box-sizing: border-box;
}
#app .login-container button {
  width: 100%;
}
#app .login-container .admin-login-link {
  margin-top: 10px;
  text-align: center;
}
#app .login-container .admin-login-link a {
  font-size: 10pt;
}
#app .logo-table {
  position: fixed;
  top: 10px;
  left: 10px;
  right: 10px;
  border-collapse: collapse;
  z-index: 1000;
  background: white;
}
#app .logo-cell {
  padding: 5px;
  border: none;
}
#app .logo-spacer {
  width: 100%;
}
#app .header-menu-cell {
  padding: 0 8px;
  border: none;
  vertical-align: middle;
  white-space: nowrap;
}
#app .login-info-cell {
  padding: 5px;
  border: none;
  text-align: right;
  white-space: nowrap;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 8pt;
}
#app .logout-cell {
  padding: 5px;
  border: none;
  text-align: right;
  white-space: nowrap;
}
#app .logout-button {
  margin-right: 0;
  padding: 6px 10px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 8pt;
}
#app .app-logo {
  display: block;
  margin: 0;
  cursor: pointer;
  max-height: 64px;
  max-width: 64px;
}
#app .club-logo {
  display: block;
  margin: 0;
  max-height: 70px;
  max-width: 70px;
}
#app {
  max-width: none;
  width: 100%;
  margin: 0;
  padding: 56px 12px 12px 12px;
  font-family: Arial, sans-serif;
}
#app .app-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 28px;
  padding-top: 12px;
  border-top: 1px solid #ccc;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 9pt;
  color: #444;
}
#app .app-footer-logo {
  height: 28px;
  width: auto;
  display: block;
}
#app .app-footer-separator {
  margin: 0 8px;
  color: #888;
}

#app .mobile-home-greeting {
  display: none;
}
#app h1 {
  font-size: 16pt;
  font-family: Helvetica, Arial, sans-serif;
}
#app h2 {
  font-size: 12pt;
  font-family: Helvetica, Arial, sans-serif;
}
#app h3 {
  font-size: 10pt;
  font-family: Helvetica, Arial, sans-serif;
}
#app h4 {
  font-size: 9pt;
  font-family: Helvetica, Arial, sans-serif;
}
#app form {
  margin-bottom: 20px;
}
#app input {
  margin-right: 10px;
}
#app button {
  margin-right: 5px;
  padding: 8px 12px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
  color: #fff;
  background-color: #007bff;
  border: 1px solid #0056b3;
  border-radius: 4px;
  cursor: pointer;
}
#app button:hover:not(:disabled) {
  background-color: #0069d9;
  border-color: #0056b3;
}
#app button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
#app .member-top-menu-list button {
  color: #000;
  background-color: #eaf3ff;
  border: none;
  margin-right: 0;
  padding: 8px 14px;
  border-radius: 0;
}
#app .member-top-menu-list button:hover:not(:disabled) {
  background-color: #cce0f8;
  border-color: transparent;
}
#app a,
#app a:visited,
#app .member-link,
#app .beat-name-link,
#app .w3w-link {
  color: #007bff;
}
#app a:hover,
#app a:focus,
#app .member-link:hover,
#app .beat-name-link:hover,
#app .w3w-link:hover,
#app .w3w-link:focus {
  color: #0056b3;
}
#app .manage-templates-button {
  margin-left: 10px;
}
#app .template-manager-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
#app .template-manager-content {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  max-width: 900px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
#app .template-manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid #ddd;
  padding-bottom: 10px;
}
#app .template-manager-header h3 {
  margin: 0;
  font-size: 18px;
}
#app .close-button {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  color: #666;
}
#app .close-button:hover {
  color: #000;
}
#app .template-list-section,
#app .template-edit-section {
  margin-bottom: 20px;
}
#app .template-list-section h4,
#app .template-edit-section h4 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 14px;
  color: #333;
}
#app .template-list {
  border: 1px solid #ddd;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 10px;
}
#app .template-item {
  padding: 10px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
#app .template-item:last-child {
  border-bottom: none;
}
#app .template-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
#app .template-item-name {
  font-weight: 500;
  flex: 1;
}
#app .template-item-actions {
  display: flex;
  gap: 5px;
}
#app .edit-button,
#app .delete-button {
  padding: 4px 8px;
  font-size: 12px;
}
#app .delete-button {
  background-color: #dc3545;
  border-color: #dc3545;
  color: white;
}
#app .delete-button:hover:not(:disabled) {
  background-color: #c82333;
  border-color: #bd2130;
}
#app .form-group {
  margin-bottom: 12px;
}
#app .form-group label {
  display: block;
  margin-bottom: 4px;
  font-weight: 500;
  font-size: 13px;
  color: #333;
}
#app .form-group input,
#app .form-group textarea {
  width: 100%;
  padding: 6px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 13px;
  box-sizing: border-box;
}
#app .form-group textarea {
  resize: vertical;
  font-family: monospace;
}
#app .available-tags-info {
  margin-bottom: 12px;
  padding: 8px;
  background-color: #f9f9f9;
  border-left: 3px solid #007bff;
  font-size: 12px;
}
#app .tag-chip {
  display: inline-block;
  background-color: #e9ecef;
  padding: 2px 6px;
  margin: 2px 2px 2px 0;
  border-radius: 3px;
  font-family: monospace;
  font-size: 11px;
  cursor: help;
}
#app .template-form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
#app .save-button {
  background-color: #28a745;
  border-color: #28a745;
  color: white;
}
#app .save-button:hover:not(:disabled) {
  background-color: #218838;
  border-color: #1e7e34;
}
#app .cancel-button {
  background-color: #6c757d;
  border-color: #6c757d;
  color: white;
}
#app .cancel-button:hover:not(:disabled) {
  background-color: #5a6268;
  border-color: #545b62;
}
#app .error-message {
  padding: 10px;
  margin-bottom: 10px;
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  font-size: 13px;
}

@media (max-width: 1000px) {
  #app .mobile-home-greeting {
    display: block;
    margin: 0 12px 14px;
    font-family: Helvetica, Arial, sans-serif;
  }

  #app .mobile-home-greeting h2,
  #app .mobile-home-greeting h3 {
    margin: 0;
  }

  #app .mobile-home-greeting h3 {
    margin-top: 8px;
    font-weight: 500;
    line-height: 1.35;
  }

  #app .app-member-shell {
    grid-template-columns: 1fr;
  }

  #app .app-member-sidebar-group {
    flex-direction: column;
  }

  #app .app-member-sidebar-card,
  #app .app-member-subnav-card {
    position: static;
  }

  #app .app-member-subnav-button {
    min-width: 0;
  }
}

@media (max-width: 768px) {
  #app .app-member-shell {
    display: flex;
    flex-direction: column;
    width: 100%;
    gap: 20px;
    padding: 8px 0 26px;
  }

  #app .app-member-sidebar-group {
    width: 100%;
    display: flex;
    justify-content: center;
    flex-direction: column;
    align-items: center;
    gap: 14px;
  }

  #app .app-member-sidebar-card {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    width: 80vw;
    padding: 16px 8px;
  }

  #app .app-member-subnav-card {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    width: 80vw;
    padding: 16px 8px;
  }

  #app .app-member-sidebar-title {
    grid-column: 1 / -1;
  }

  #app .app-member-nav-button {
    width: 100%;
    padding: 5px 6px;
    font-size: 7pt;
    text-align: center;
  }

  #app .app-member-subnav-button {
    width: 100%;
    min-width: 0;
    padding: 10px 8px;
    font-size: 9pt;
  }

  #app .app-member-content {
    width: 100%;
    display: flex;
    justify-content: center;
  }

  #app .mobile-home-greeting {
    width: 80vw;
    margin: 0 auto !important;
  }

  #app .home-container,
  #app .section-placeholder,
  #app .club-information-container,
  #app .newsletters-container,
  #app .member-edit-container,
  #app .beat-details-container,
  #app .catch-return-container,
  #app .membership-admin-container,
  #app .club-settings-container {
    width: 80vw;
  }
}

@media (max-width: 400px) {
  #app .mobile-home-greeting {
    margin: 0 8px 10px;
  }

  #app .mobile-home-greeting h2 {
    font-size: 12.5pt;
    line-height: 1.2;
  }

  #app .mobile-home-greeting h3 {
    margin-top: 6px;
    font-size: 10pt;
    line-height: 1.3;
  }
}
</style>
