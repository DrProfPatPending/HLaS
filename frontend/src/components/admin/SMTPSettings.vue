<template>
  <div class="admin-panel smtp-settings-panel">
    <h1 class="admin-panel-title">Email / SMTP Settings</h1>

    <div class="admin-inline-controls smtp-club-selector">
      <label class="admin-form-label" for="smtp-club-select">Club:</label>
      <select
        id="smtp-club-select"
        v-model="selectedClubShortName"
        class="admin-select"
        @change="fetchSmtpSettings"
      >
        <option v-for="club in clubs" :key="club.shortName" :value="club.shortName">
          {{ club.fullName || club.shortName }}
        </option>
      </select>
    </div>

    <div v-if="loading" class="admin-loading-text">Loading SMTP settings...</div>

    <div v-else class="smtp-form-panel">
      <ul v-if="validationErrors.length" class="smtp-validation-list error-msg">
        <li v-for="(validationError, index) in validationErrors" :key="`smtp-validation-${index}`">
          {{ validationError }}
        </li>
      </ul>

      <div class="admin-form-row">
        <label class="admin-form-label" for="smtp-host">SMTP Host</label>
        <input id="smtp-host" v-model="form.host" class="admin-form-input" type="text" />
      </div>

      <div class="admin-form-row">
        <label class="admin-form-label" for="smtp-port">SMTP Port</label>
        <input id="smtp-port" v-model.number="form.port" class="admin-form-input smtp-port-input" type="number" min="1" max="65535" />
      </div>

      <div class="admin-form-row">
        <label class="admin-form-label" for="smtp-username">Username</label>
        <input id="smtp-username" v-model="form.username" class="admin-form-input" type="text" autocomplete="off" />
      </div>

      <div class="admin-form-row">
        <label class="admin-form-label" for="smtp-password">Password</label>
        <input id="smtp-password" v-model="form.password" class="admin-form-input" type="password" autocomplete="new-password" placeholder="Leave blank to keep existing password" />
      </div>

      <div class="admin-form-row smtp-checkbox-row">
        <label><input v-model="form.useSsl" type="checkbox" /> Use SSL</label>
        <label><input v-model="form.useTls" type="checkbox" /> Use TLS</label>
      </div>

      <div class="admin-form-row">
        <label class="admin-form-label" for="smtp-from-email">From Email</label>
        <input id="smtp-from-email" v-model="form.fromEmail" class="admin-form-input" type="email" />
      </div>

      <div class="admin-form-row">
        <label class="admin-form-label" for="smtp-from-name">From Name</label>
        <input id="smtp-from-name" v-model="form.fromName" class="admin-form-input" type="text" />
      </div>

      <div class="admin-inline-controls smtp-actions">
        <button type="button" class="save-btn" :disabled="saving" @click="saveSmtpSettings">
          {{ saving ? 'Saving…' : 'Save SMTP Settings' }}
        </button>
      </div>

      <div class="smtp-test-panel">
        <h2 class="admin-section-title">Send Test Email</h2>
        <div class="admin-form-row">
          <label class="admin-form-label" for="smtp-test-email">To Email</label>
          <input id="smtp-test-email" v-model="testToEmail" class="admin-form-input" type="email" placeholder="recipient@example.com" />
        </div>
        <div class="admin-inline-controls smtp-actions">
          <button type="button" :disabled="testing" @click="sendTestEmail">
            {{ testing ? 'Sending…' : 'Send Test Email' }}
          </button>
        </div>
      </div>

      <div v-if="statusMsg" :class="statusError ? 'error-msg' : 'success-msg'">{{ statusMsg }}</div>
    </div>
  </div>
</template>

<script>
import { adminGet, adminPost, adminPut } from '../../services/adminApi.js';

export default {
  name: 'SMTPSettings',
  data() {
    return {
      clubs: [],
      selectedClubShortName: '',
      loading: false,
      saving: false,
      testing: false,
      testToEmail: '',
      statusMsg: '',
      statusError: false,
      validationErrors: [],
      form: {
        host: '',
        port: 587,
        username: '',
        password: '',
        fromEmail: '',
        fromName: '',
        useSsl: false,
        useTls: true,
      },
    };
  },
  methods: {
    showStatus(msg, isError = false) {
      this.statusMsg = msg;
      this.statusError = isError;
    },
    fetchClubs() {
      return adminGet('/admin/clubs')
        .then(res => {
          this.clubs = Array.isArray(res.data?.clubs) ? res.data.clubs : [];
          if (this.clubs.length && !this.selectedClubShortName) {
            this.selectedClubShortName = this.clubs[0].shortName;
          }
        })
        .catch(err => {
          this.showStatus(err.response?.data?.error || 'Failed to load clubs', true);
        });
    },
    fetchSmtpSettings() {
      if (!this.selectedClubShortName) return;
      this.loading = true;
      this.statusMsg = '';
      this.validationErrors = [];
      adminGet(`/admin/clubs/${encodeURIComponent(this.selectedClubShortName)}/smtp`)
        .then(res => {
          const smtp = res.data?.smtp || {};
          this.form.host = smtp.host || '';
          this.form.port = Number.isFinite(Number(smtp.port)) ? Number(smtp.port) : 587;
          this.form.username = smtp.username || '';
          this.form.password = '';
          this.form.fromEmail = smtp.fromEmail || '';
          this.form.fromName = smtp.fromName || '';
          this.form.useSsl = !!smtp.useSsl;
          this.form.useTls = !!smtp.useTls;
        })
        .catch(err => {
          this.showStatus(err.response?.data?.error || 'Failed to load SMTP settings', true);
        })
        .finally(() => {
          this.loading = false;
        });
    },
    isValidEmail(emailValue) {
      if (!emailValue) return false;
      const normalized = String(emailValue).trim();
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalized);
    },
    collectValidationErrors(includeTestRecipient = false) {
      const validationErrors = [];
      const host = String(this.form.host || '').trim();
      const fromEmail = String(this.form.fromEmail || '').trim();
      const port = Number(this.form.port);

      if (!host) {
        validationErrors.push('SMTP Host is required.');
      }

      if (!Number.isInteger(port) || port < 1 || port > 65535) {
        validationErrors.push('SMTP Port must be an integer between 1 and 65535.');
      }

      if (!fromEmail) {
        validationErrors.push('From Email is required.');
      } else if (!this.isValidEmail(fromEmail)) {
        validationErrors.push('From Email must be a valid email address.');
      }

      if (this.form.useSsl && this.form.useTls) {
        validationErrors.push('Use SSL and Use TLS cannot both be enabled at the same time.');
      }

      if (!this.form.useSsl && !this.form.useTls) {
        validationErrors.push('Enable either Use SSL or Use TLS for secure SMTP transport.');
      }

      if (includeTestRecipient) {
        const testRecipient = String(this.testToEmail || '').trim();
        if (!testRecipient) {
          validationErrors.push('Test recipient email is required for sending a test email.');
        } else if (!this.isValidEmail(testRecipient)) {
          validationErrors.push('Test recipient email must be a valid email address.');
        }
      }

      return validationErrors;
    },
    saveSmtpSettings() {
      if (!this.selectedClubShortName) return;
      this.validationErrors = this.collectValidationErrors(false);
      if (this.validationErrors.length) {
        this.showStatus('Please fix the validation errors before saving.', true);
        return;
      }
      this.saving = true;
      this.statusMsg = '';
      adminPut(`/admin/clubs/${encodeURIComponent(this.selectedClubShortName)}/smtp`, {
        host: String(this.form.host || '').trim(),
        port: this.form.port,
        username: String(this.form.username || '').trim(),
        password: this.form.password,
        fromEmail: String(this.form.fromEmail || '').trim(),
        fromName: String(this.form.fromName || '').trim(),
        useSsl: this.form.useSsl,
        useTls: this.form.useTls,
      })
        .then(() => {
          this.showStatus(`SMTP settings saved for ${this.selectedClubShortName}.`);
          this.form.password = '';
          this.validationErrors = [];
        })
        .catch(err => {
          this.showStatus(err.response?.data?.error || 'Failed to save SMTP settings', true);
        })
        .finally(() => {
          this.saving = false;
        });
    },
    sendTestEmail() {
      if (!this.selectedClubShortName) return;
      this.validationErrors = this.collectValidationErrors(true);
      if (this.validationErrors.length) {
        this.showStatus('Please fix the validation errors before sending a test email.', true);
        return;
      }
      this.testing = true;
      this.statusMsg = '';
      adminPost(`/admin/clubs/${encodeURIComponent(this.selectedClubShortName)}/smtp/test`, {
        toEmail: this.testToEmail.trim(),
      })
        .then(res => {
          this.showStatus(res.data?.message || 'Test email sent successfully.');
        })
        .catch(err => {
          this.showStatus(err.response?.data?.error || 'Failed to send test email', true);
        })
        .finally(() => {
          this.testing = false;
        });
    },
  },
  mounted() {
    this.fetchClubs().then(() => {
      if (this.selectedClubShortName) this.fetchSmtpSettings();
    });
  },
};
</script>

<style scoped>
.smtp-settings-panel {
  max-width: 900px;
}

.smtp-form-panel {
  margin-top: 10px;
}

.smtp-validation-list {
  margin: 0 0 12px;
  padding-left: 20px;
}

.smtp-validation-list li {
  margin-bottom: 4px;
}

.smtp-port-input {
  max-width: 140px;
}

.smtp-checkbox-row {
  gap: 18px;
}

.smtp-checkbox-row label {
  font-size: 10pt;
}

.smtp-test-panel {
  border-top: 1px solid #ddd;
  margin-top: 14px;
  padding-top: 12px;
}

.smtp-actions {
  margin-bottom: 0;
}
</style>
