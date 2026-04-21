<template>
  <div class="club-information-container">
    <h2>{{ isEditing ? editForm.fullName : clubDetails.fullName }}</h2>

    <div v-if="canEditClubInformation" class="club-information-actions">
      <app-button v-if="!isEditing" type="button" inherit-style @click="startEdit">Edit</app-button>
      <template v-else>
        <app-button type="button" inherit-style @click="saveEdit" :disabled="isSaving">{{ isSaving ? 'Saving...' : 'Save' }}</app-button>
        <app-button type="button" inherit-style @click="cancelEdit" :disabled="isSaving">Cancel</app-button>
      </template>
    </div>

    <p v-if="saveError" class="club-information-error">{{ saveError }}</p>
    <p v-if="saveSuccess" class="club-information-success">{{ saveSuccess }}</p>

    <table class="club-information-table">
      <tbody>
        <tr>
          <th>Short Name</th>
          <td>{{ clubDetails.shortName }}</td>
        </tr>
        <tr>
          <th>URL</th>
          <td>
            <template v-if="isEditing">
              <input
                v-model="editForm.websiteUrl"
                type="url"
                class="club-information-input"
                placeholder="https://example.com"
              />
            </template>
            <template v-else>
              <a
                v-if="clubDetails.websiteUrl"
                :href="clubDetails.websiteUrl"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ clubDetails.websiteUrl }}
              </a>
              <span v-else>-</span>
            </template>
          </td>
        </tr>
        <tr>
          <th>Admin Email</th>
          <td>
            <template v-if="isEditing">
              <input
                v-model="editForm.adminEmail"
                type="email"
                class="club-information-input"
                placeholder="admin@club.org"
              />
            </template>
            <template v-else>
              <a v-if="clubDetails.adminEmail" :href="`mailto:${clubDetails.adminEmail}`">
                {{ clubDetails.adminEmail }}
              </a>
              <span v-else>-</span>
            </template>
          </td>
        </tr>
      </tbody>
    </table>
    <textarea
      v-if="isEditing"
      v-model="editForm.description"
      class="club-description-box"
      rows="6"
    ></textarea>
    <textarea
      v-else
      class="club-description-box"
      :value="clubDetails.description"
      readonly
      rows="6"
    ></textarea>
  </div>
</template>

<script>
import axios from 'axios';
import { store, clubDetails, API_BASE_URL, loadClubs } from '../store.js';
import AppButton from './ui/AppButton.vue';

export default {
  name: 'ClubInformation',
  components: {
    AppButton,
  },
  data() {
    return {
      isEditing: false,
      isSaving: false,
      saveError: '',
      saveSuccess: '',
      editForm: {
        fullName: '',
        websiteUrl: '',
        adminEmail: '',
        description: '',
      },
    };
  },
  computed: {
    clubDetails: () => clubDetails.value,
    canEditClubInformation: () => store.memberRoles.includes('club_admin'),
  },
  mounted() {
    this.resetEditForm();
  },
  watch: {
    clubDetails: {
      handler() {
        if (!this.isEditing) {
          this.resetEditForm();
        }
      },
      deep: true,
    },
  },
  methods: {
    resolveClubInformationSaveErrorMessage(err) {
      const statusCode = err?.response?.status;
      if (statusCode === 401) {
        return 'Session expired. Please log in again, then retry.';
      }
      if (statusCode === 403) {
        return 'You do not have permission to update club information.';
      }
      return err?.response?.data?.error || 'Failed to update club information.';
    },
    resetEditForm() {
      this.editForm = {
        fullName: this.clubDetails.fullName || '',
        websiteUrl: this.clubDetails.websiteUrl || '',
        adminEmail: this.clubDetails.adminEmail || '',
        description: this.clubDetails.description || '',
      };
    },
    startEdit() {
      this.saveError = '';
      this.saveSuccess = '';
      this.resetEditForm();
      this.isEditing = true;
    },
    cancelEdit() {
      this.isEditing = false;
      this.saveError = '';
      this.saveSuccess = '';
      this.resetEditForm();
    },
    saveEdit() {
      this.saveError = '';
      this.saveSuccess = '';
      this.isSaving = true;

      const payload = {
        fullName: String(this.editForm.fullName || '').trim(),
        websiteUrl: String(this.editForm.websiteUrl || '').trim(),
        adminEmail: String(this.editForm.adminEmail || '').trim(),
        description: String(this.editForm.description || '').trim(),
        logoUrl: this.clubDetails.logoUrl || '',
        beats: Array.isArray(this.clubDetails.beats) ? this.clubDetails.beats : [],
      };

      return axios.put(
        `${API_BASE_URL}/admin/clubs/${encodeURIComponent(this.clubDetails.shortName)}`,
        payload,
      ).then(() => loadClubs())
        .then(() => {
          this.isEditing = false;
          this.saveSuccess = 'Club information updated.';
        })
        .catch((err) => {
          this.saveError = this.resolveClubInformationSaveErrorMessage(err);
        })
        .finally(() => {
          this.isSaving = false;
        });
    },
    goHome() {
      store.activeSection = 'home';
    },
  },
};
</script>

<style scoped>
.club-information-actions {
  margin: 8px 0 12px;
  display: flex;
  gap: 8px;
}

.club-information-input {
  width: 100%;
  max-width: 520px;
}

.club-information-error {
  color: var(--app-color-state-danger);
  margin: 0 0 8px;
  font-weight: 600;
}

.club-information-success {
  color: var(--app-color-state-success);
  margin: 0 0 8px;
  font-weight: 600;
}
</style>
