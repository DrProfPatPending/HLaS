<template>
  <div class="club-settings-container">
    <div class="club-settings-header">
      <h2>Club Settings</h2>
      <p>Configure Catch Return field visibility for {{ loggedInClub }}.</p>
    </div>

    <p v-if="status" class="club-settings-status">{{ status }}</p>
    <p v-if="error" class="club-settings-error">{{ error }}</p>

    <section class="club-settings-section">
      <h3>Catch Return Fields</h3>
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

    <div class="club-settings-actions">
      <button type="button" :disabled="loading || saving" @click="loadSettings">
        {{ loading ? 'Loading…' : 'Reload' }}
      </button>
      <button type="button" :disabled="saving || loading" @click="saveSettings">
        {{ saving ? 'Saving…' : 'Save Settings' }}
      </button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { API_BASE_URL, store } from '../store.js';

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

export default {
  name: 'ClubSettings',
  data() {
    return {
      loading: false,
      saving: false,
      status: '',
      error: '',
      visibility: defaultVisibility(),
    };
  },
  computed: {
    loggedInClub: () => store.loggedInClub,
    catchReturnFields: () => CATCH_RETURN_FIELDS,
  },
  created() {
    this.loadSettings();
  },
  methods: {
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

      return axios
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
        })
        .finally(() => {
          this.loading = false;
        });
    },
    saveSettings() {
      this.saving = true;
      this.error = '';
      this.status = '';

      const payload = {
        club: this.loggedInClub,
        settings: {
          catchReturnFieldVisibility: this.normalizeVisibility(this.visibility),
        },
      };

      return axios
        .put(`${API_BASE_URL}/club-settings`, payload)
        .then(() => {
          this.status = 'Club settings saved.';
        })
        .catch(err => {
          this.error = err?.response?.data?.error || 'Unable to save club settings.';
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

.club-settings-section h3 {
  margin: 0 0 10px;
}

.club-settings-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
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
