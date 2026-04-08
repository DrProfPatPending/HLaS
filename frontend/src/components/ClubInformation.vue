<template>
  <div class="club-information-container">
    <h2>{{ isEditing ? editForm.fullName : clubDetails.fullName }}</h2>

    <div v-if="canEditClubInformation" class="club-information-actions">
      <button v-if="!isEditing" type="button" @click="startEdit">Edit</button>
      <template v-else>
        <button type="button" @click="saveEdit" :disabled="isSaving">{{ isSaving ? 'Saving...' : 'Save' }}</button>
        <button type="button" @click="cancelEdit" :disabled="isSaving">Cancel</button>
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

export default {
  name: 'ClubInformation',
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
          this.saveError = err?.response?.data?.error || 'Failed to update club information.';
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
  color: #b42318;
  margin: 0 0 8px;
  font-weight: 600;
}

.club-information-success {
  color: #21633a;
  margin: 0 0 8px;
  font-weight: 600;
}
</style>
