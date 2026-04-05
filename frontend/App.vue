<template>
  <div id="app">
    <app-header />
    <login-view v-if="!loggedIn" />
    <div v-else>
      <home-view v-if="activeSection === 'home'" />
      <membership-admin v-else-if="activeSection === 'membership-admin'" />
      <club-information v-else-if="activeSection === 'club-information'" />
      <my-club v-else-if="activeSection === 'my-club'" />
      <newsletters v-else-if="activeSection === 'newsletters'" />
      <fishing-beats v-else-if="activeSection === 'fishing-beats'" />
      <member-edit v-else-if="activeSection === 'member-edit'" />
    <div v-else class="section-placeholder">
      <h2>{{ sectionDisplayName(activeSection) }}</h2>
      <p>This section is coming soon.</p>
      <button type="button" @click="goHome">Back to Home</button>
    </div>
    </div>
    <footer class="app-footer">
      <span>(c) 2026 - ScoffySoft</span>
      <span class="app-footer-separator">|</span>
      <a href="mailto: robbie.scoff@gmail.com">Contact Us</a>
    </footer>
  </div>
</template>

<script>
import AppHeader from './src/components/AppHeader.vue';
import LoginView from './src/components/LoginView.vue';
import HomeView from './src/components/HomeView.vue';
import MembershipAdmin from './src/components/MembershipAdmin.vue';
import ClubInformation from './src/components/ClubInformation.vue';
import Newsletters from './src/components/Newsletters.vue';
import FishingBeats from './src/components/FishingBeats.vue';
import MemberEdit from './src/components/MemberEdit.vue';
import MyClub from './src/components/MyClub.vue';
import {
  store,
  restoreMemberSession,
  applyMemberAuthHeader,
  initializeAuthInterceptor,
  teardownAuthInterceptor,
  loadClubs,
  fetchMembers,
  canAccessMembershipAdmin,
  sectionDisplayName,
} from './src/store.js';

export default {
  components: {
    AppHeader,
    LoginView,
    HomeView,
    MembershipAdmin,
    ClubInformation,
    MyClub,
    Newsletters,
    FishingBeats,
    MemberEdit,
  },
  computed: {
    loggedIn: () => store.loggedIn,
    activeSection: () => store.activeSection,
  },
  created() {
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
  methods: {
    sectionDisplayName,
    goHome() {
      store.activeSection = 'home';
    },
  },
};

</script>

<style>
#app .home-container {
  max-width: 900px;
  margin: 40px auto;
  font-family: Helvetica, Arial, sans-serif;
}
#app .home-nav-table {
  margin-top: 20px;
  border-collapse: separate;
  border-spacing: 12px;
}
#app .home-nav-button {
  width: 220px;
  padding: 12px 10px;
}
#app .access-error {
  margin-top: 16px;
  color: #b00020;
}
#app .section-placeholder {
  max-width: 900px;
  margin: 40px auto;
  font-family: Helvetica, Arial, sans-serif;
}
#app .club-information-container {
  max-width: 900px;
  margin: 40px auto;
  font-family: Helvetica, Arial, sans-serif;
}
#app .newsletters-container,
#app .fishing-beats-container {
  max-width: 900px;
  margin: 40px auto;
  font-family: Helvetica, Arial, sans-serif;
}
#app .fishing-beats-container {
  max-width: none;
  width: 100%;
  margin: 40px 0;
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
  grid-template-columns: 75% 25%;
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
  max-width: 900px;
  margin: 20px auto;
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
  width: 90%;
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
  max-height: 100px;
  max-width: 100px;
}
#app .club-logo {
  display: block;
  margin: 0;
  max-height: 100px;
  max-width: 100px;
}
#app {
  max-width: none;
  width: 100%;
  margin: 0;
  padding: 70px 12px 12px 12px;
  font-family: Arial, sans-serif;
}
#app .app-footer {
  margin-top: 28px;
  padding-top: 12px;
  border-top: 1px solid #ccc;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 9pt;
  text-align: center;
  color: #444;
}
#app .app-footer-separator {
  margin: 0 8px;
  color: #888;
}
#app h2 {
  font-size: 14pt;
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
</style>
