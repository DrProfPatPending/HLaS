<template>
  <div class="admin-panel app-settings-panel">
    <h1 class="admin-panel-title">App Settings</h1>
    <div class="admin-info-text">
      Configure global application behavior. These settings apply across the app.
    </div>

    <div v-if="loading" class="admin-loading-text">Loading app settings...</div>

    <div v-else>
      <div class="admin-form-row">
        <label class="admin-form-label" for="date-format-select">Date Format</label>
        <select id="date-format-select" v-model="form.dateFormat" class="admin-select">
          <option v-for="option in allowedDateFormats" :key="option" :value="option">{{ option }}</option>
        </select>
      </div>

      <div class="admin-inline-controls">
        <button type="button" class="save-btn" :disabled="saving" @click="saveSettings">
          {{ saving ? 'Saving…' : 'Save App Settings' }}
        </button>
      </div>

      <div v-if="statusMsg" :class="statusError ? 'error-msg' : 'success-msg'">{{ statusMsg }}</div>
    </div>
  </div>
</template>

<script>
import { adminGet, adminPut } from '../../services/adminApi.js';

const FALLBACK_DATE_FORMATS = [
  'DD/MM/YY',
  'DD/MM/YYYY',
  'DD-MMM-YYYY',
  'YYYY-MM-DD',
  'MMM DD, YYYY',
  'DD MMM YYYY',
  'MM/DD/YYYY',
];

export default {
  name: 'AppSettings',
  data() {
    return {
      loading: false,
      saving: false,
      statusMsg: '',
      statusError: false,
      allowedDateFormats: [...FALLBACK_DATE_FORMATS],
      form: {
        dateFormat: 'DD/MM/YY',
      },
    };
  },
  mounted() {
    this.fetchSettings();
  },
  methods: {
    resolveAdminErrorMessage(err, fallbackMessage) {
      const statusCode = err?.response?.status;
      if (statusCode === 401) {
        return 'Session expired. Please log in again, then retry.';
      }
      if (statusCode === 403) {
        return 'You do not have permission to update app settings.';
      }
      return err?.response?.data?.error || fallbackMessage;
    },
    showStatus(message, isError = false) {
      this.statusMsg = message;
      this.statusError = isError;
    },
    fetchSettings() {
      this.loading = true;
      this.statusMsg = '';
      adminGet('/admin/app-settings')
        .then(res => {
          const settings = res.data?.settings || {};
          const allowed = Array.isArray(res.data?.allowedDateFormats)
            ? res.data.allowedDateFormats
            : FALLBACK_DATE_FORMATS;
          this.allowedDateFormats = allowed.length ? allowed : [...FALLBACK_DATE_FORMATS];

          const fromApi = String(settings.dateFormat || '').trim();
          const firstOption = this.allowedDateFormats[0] || 'DD/MM/YY';
          this.form.dateFormat = this.allowedDateFormats.includes(fromApi) ? fromApi : firstOption;
        })
        .catch(err => {
          this.showStatus(err.response?.data?.error || 'Failed to load app settings', true);
        })
        .finally(() => {
          this.loading = false;
        });
    },
    saveSettings() {
      this.saving = true;
      this.statusMsg = '';
      adminPut('/admin/app-settings', {
        settings: {
          dateFormat: this.form.dateFormat,
        },
      })
        .then(() => {
          this.showStatus('App settings saved successfully.');
        })
        .catch(err => {
          this.showStatus(this.resolveAdminErrorMessage(err, 'Failed to save app settings'), true);
        })
        .finally(() => {
          this.saving = false;
        });
    },
  },
};
</script>

<style scoped>
.app-settings-panel {
  max-width: 900px;
}
</style>
