<template>
  <div class="club-settings-container">
    <div class="club-settings-header">
      <h2>Club Settings</h2>
      <p>Configure settings for {{ loggedInClub }}.</p>
    </div>

    <p v-if="status" class="club-settings-status">{{ status }}</p>
    <p v-if="error" class="club-settings-error">{{ error }}</p>

    <!-- Catch Return Fields Section -->
    <section class="club-settings-section">
      <h3>Catch Return Fields</h3>
      <p class="section-description">Show/hide fields in the Catch Return form for club members.</p>
      <table class="club-settings-table">
        <thead>
          <tr>
            <th>Field</th>
            <th>Visible</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="field in catchReturnFields" :key="field.key">
            <td>{{ field.label }}</td>
            <td>
              <label class="club-settings-toggle">
                <input v-model="visibility[field.key]" type="checkbox" />
                <span>{{ visibility[field.key] ? 'Yes' : 'No' }}</span>
              </label>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Mini Site Section -->
    <section class="club-settings-section">
      <h3>Club Mini Site</h3>
      <p class="section-description">Create a public-facing marketing website for your club.</p>
      
      <div class="mini-site-config">
        <label class="mini-site-toggle">
          <input v-model="miniSite.enabled" type="checkbox" />
          <span class="toggle-label">{{ miniSite.enabled ? 'Enable' : 'Disable' }} Mini Site</span>
        </label>
        <p class="mini-site-hint">
          {{ miniSite.enabled ? 'Your mini site is enabled and accessible.' : 'Enable to create a public marketing page.' }}
        </p>

        <template v-if="miniSite.enabled">
          <div class="form-group">
            <label for="mini-site-title">Site Title</label>
            <input
              id="mini-site-title"
              v-model="miniSite.title"
              type="text"
              placeholder="e.g., Cambridge Trout Club"
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="mini-site-tagline">Tagline</label>
            <input
              id="mini-site-tagline"
              v-model="miniSite.tagline"
              type="text"
              placeholder="e.g., Premier fly fishing destination"
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="mini-site-description">Description</label>
            <textarea
              id="mini-site-description"
              v-model="miniSite.description"
              placeholder="Brief description of your club"
              class="form-input"
              rows="4"
            />
          </div>

          <div class="form-group">
            <label for="mini-site-hero">Hero Image URL</label>
            <input
              id="mini-site-hero"
              v-model="miniSite.hero_image_url"
              type="url"
              placeholder="https://..."
              class="form-input"
            />
            <p class="form-hint">URL to an image for the hero section (desktop view)</p>
          </div>

          <div class="mini-site-preview">
            <strong>Mini Site URL:</strong>
            <code>{{ miniSiteUrl }}</code>
            <p class="form-hint">
              Desktop users: Full mini site<br />
              Mobile/Responsive: Shows placeholder with redirect to login
            </p>
          </div>
        </template>
      </div>
    </section>

    <div class="club-settings-actions">
      <app-button type="button" inherit-style :disabled="loading || saving" @click="loadSettings">
        {{ loading ? 'Loading…' : 'Reload' }}
      </app-button>
      <app-button type="button" inherit-style :disabled="saving || loading" @click="saveSettings">
        {{ saving ? 'Saving…' : 'Save Settings' }}
      </app-button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { API_BASE_URL, store } from '../store.js';
import AppButton from './ui/AppButton.vue';

const CATCH_RETURN_FIELDS = [
  { key: 'sessionDate', label: 'Date' },
  { key: 'beatId', label: 'Beat ID' },
  { key: 'smallTrout', label: 'Small Trout' },
  { key: 'mediumTrout', label: 'Medium Trout' },
  { key: 'largeTrout', label: 'Large Trout' },
  { key: 'smallGrayling', label: 'Small Grayling' },
  { key: 'mediumGrayling', label: 'Medium Grayling' },
  { key: 'largeGrayling', label: 'Large Grayling' },
  { key: 'otherFish', label: 'Other Fish' },
  { key: 'fliesUsed', label: 'Flies Used' },
  { key: 'weatherConditions', label: 'Weather Conditions' },
  { key: 'predatorDamage', label: 'Predator Damage' },
];

function defaultVisibility() {
  return Object.fromEntries(CATCH_RETURN_FIELDS.map(field => [field.key, true]));
}

function defaultMiniSite() {
  return {
    enabled: false,
    title: '',
    tagline: '',
    description: '',
    hero_image_url: '',
  };
}

export default {
  name: 'ClubSettings',
  components: {
    AppButton,
  },
  data() {
    return {
      loading: false,
      saving: false,
      status: '',
      error: '',
      visibility: defaultVisibility(),
      miniSite: defaultMiniSite(),
    };
  },
  computed: {
    loggedInClub: () => store.loggedInClub,
    catchReturnFields: () => CATCH_RETURN_FIELDS,
    miniSiteUrl() {
      const domain = window.location.origin;
      return `${domain}/club/${this.loggedInClub}/`;
    },
  },
  created() {
    this.loadSettings();
  },
  methods: {
    resolveClubSettingsSaveErrorMessage(err) {
      const statusCode = err?.response?.status;
      if (statusCode === 401) {
        return 'Session expired. Please log in again, then retry.';
      }
      if (statusCode === 403) {
        return 'You do not have permission to update club settings.';
      }
      return err?.response?.data?.error || 'Unable to save club settings.';
    },
    normalizeVisibility(rawVisibility) {
      const source = rawVisibility && typeof rawVisibility === 'object' ? rawVisibility : {};
      const normalized = defaultVisibility();
      for (const field of CATCH_RETURN_FIELDS) {
        if (Object.prototype.hasOwnProperty.call(source, field.key)) {
          normalized[field.key] = Boolean(source[field.key]);
        }
      }
      return normalized;
    },
    loadSettings() {
      this.loading = true;
      this.error = '';
      this.status = '';
      this.miniSite = defaultMiniSite();

      // Load catch return settings
      axios
        .get(`${API_BASE_URL}/club-settings`, {
          params: { club: this.loggedInClub },
        })
        .then(res => {
          const visibility = res?.data?.settings?.catchReturnFieldVisibility;
          this.visibility = this.normalizeVisibility(visibility);
        })
        .catch(err => {
          this.visibility = defaultVisibility();
          this.error = err?.response?.data?.error || 'Unable to load club settings.';
        });

      // Load mini site settings
      axios
        .get(`${API_BASE_URL}/mini-site`, {
          params: { club: this.loggedInClub },
        })
        .then(res => {
          this.miniSite = {
            enabled: res?.data?.enabled || false,
            title: res?.data?.title || '',
            tagline: res?.data?.tagline || '',
            description: res?.data?.description || '',
            hero_image_url: res?.data?.hero_image_url || '',
          };
        })
        .catch(err => {
          // Mini site endpoint not available or not configured, that's ok
          this.miniSite = defaultMiniSite();
        })
        .finally(() => {
          this.loading = false;
        });
    },
    saveSettings() {
      this.saving = true;
      this.error = '';
      this.status = '';

      const catchReturnPayload = {
        club: this.loggedInClub,
        settings: {
          catchReturnFieldVisibility: this.normalizeVisibility(this.visibility),
        },
      };

      const miniSitePayload = {
        club: this.loggedInClub,
        enabled: this.miniSite.enabled,
        title: this.miniSite.title,
        tagline: this.miniSite.tagline,
        description: this.miniSite.description,
        hero_image_url: this.miniSite.hero_image_url,
      };

      // Save both settings in parallel
      Promise.all([
        axios.put(`${API_BASE_URL}/club-settings`, catchReturnPayload),
        axios.put(`${API_BASE_URL}/mini-site`, miniSitePayload),
      ])
        .then(() => {
          this.status = 'Club settings saved.';
        })
        .catch(err => {
          this.error = this.resolveClubSettingsSaveErrorMessage(err);
        })
        .finally(() => {
          this.saving = false;
        });
    },
  },
};
</script>

<style scoped>
.club-settings-header {
  margin-bottom: 12px;
}

.club-settings-header h2 {
  margin: 0;
}

.club-settings-header p {
  margin: 8px 0 0;
  color: #475569;
}

.club-settings-section {
  margin-bottom: 2rem;
}

.club-settings-section h3 {
  margin: 0 0 10px;
  color: #1a472a;
}

.section-description {
  margin: 0 0 1rem 0;
  color: #666;
  font-size: 0.95rem;
}

.club-settings-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  margin-bottom: 1rem;
}

.club-settings-table th,
.club-settings-table td {
  border: 1px solid #d7dce2;
  padding: 9px 10px;
  text-align: left;
}

.club-settings-table thead th {
  background: #eaf2f8;
  color: #17324d;
}

.club-settings-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.club-settings-toggle input[type="checkbox"] {
  cursor: pointer;
}

/* Mini Site Styles */
.mini-site-config {
  background: #f9f9f9;
  padding: 1rem;
  border-radius: 4px;
  border-left: 4px solid #2d6a45;
}

.mini-site-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 1rem;
  cursor: pointer;
}

.mini-site-toggle input[type="checkbox"] {
  cursor: pointer;
  width: 20px;
  height: 20px;
}

.toggle-label {
  font-weight: 600;
  color: #1a472a;
  font-size: 1rem;
}

.mini-site-hint {
  margin: 0 0 1rem 0;
  color: #666;
  font-size: 0.9rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #17324d;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  font-family: inherit;
  font-size: 1rem;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #2d6a45;
  box-shadow: 0 0 4px rgba(45, 106, 69, 0.2);
}

.form-hint {
  margin: 0.5rem 0 0 0;
  color: #999;
  font-size: 0.85rem;
}

.mini-site-preview {
  background: white;
  padding: 1rem;
  border-radius: 4px;
  margin-top: 1rem;
  border: 1px solid #d0d0d0;
}

.mini-site-preview strong {
  display: block;
  margin-bottom: 0.5rem;
  color: #17324d;
}

.mini-site-preview code {
  background: #f0f0f0;
  padding: 0.5rem;
  border-radius: 4px;
  display: block;
  word-break: break-all;
  font-family: monospace;
  color: #2d6a45;
}

.club-settings-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.club-settings-status {
  margin: 0 0 10px;
  color: #21633a;
  font-weight: 600;
}

.club-settings-error {
  margin: 0 0 10px;
  color: #b42318;
  font-weight: 600;
}
</style>
