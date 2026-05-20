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

    <!-- Core fields table -->
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
              <input v-model="editForm.websiteUrl" type="url" class="club-information-input" placeholder="https://example.com" />
            </template>
            <template v-else>
              <a v-if="clubDetails.websiteUrl" :href="clubDetails.websiteUrl" target="_blank" rel="noopener noreferrer">{{ clubDetails.websiteUrl }}</a>
              <span v-else>-</span>
            </template>
          </td>
        </tr>
        <tr>
          <th>Admin Email</th>
          <td>
            <template v-if="isEditing">
              <input v-model="editForm.adminEmail" type="email" class="club-information-input" placeholder="admin@club.org" />
            </template>
            <template v-else>
              <a v-if="clubDetails.adminEmail" :href="`mailto:${clubDetails.adminEmail}`">{{ clubDetails.adminEmail }}</a>
              <span v-else>-</span>
            </template>
          </td>
        </tr>
        <tr>
          <th>WhatsApp Group(s)</th>
          <td>
            <template v-if="isEditing">
              <input v-model="editForm.whatsappGroups" type="text" class="club-information-input" placeholder="https://chat.whatsapp.com/..." />
            </template>
            <template v-else>
              <a v-if="clubDetails.whatsappGroups" :href="clubDetails.whatsappGroups" target="_blank" rel="noopener noreferrer">{{ clubDetails.whatsappGroups }}</a>
              <span v-else>-</span>
            </template>
          </td>
        </tr>
        <tr>
          <th>Social Media</th>
          <td>
            <template v-if="isEditing">
              <div class="social-media-edit">
                <div v-for="(entry, idx) in editForm.socialMedia" :key="idx" class="social-media-row">
                  <input v-model="entry.platform" type="text" class="club-information-input social-media-platform" placeholder="e.g. Instagram" />
                  <input v-model="entry.url" type="url" class="club-information-input social-media-url" placeholder="https://instagram.com/club" />
                  <app-button type="button" size="sm" inherit-style @click="removeSocialMedia(idx)">Remove</app-button>
                </div>
                <app-button type="button" size="sm" inherit-style @click="addSocialMedia">+ Add Link</app-button>
              </div>
            </template>
            <template v-else>
              <span v-if="!clubDetails.socialMedia.length">-</span>
              <div v-else class="social-media-links">
                <a v-for="entry in clubDetails.socialMedia" :key="entry.platform" :href="entry.url" target="_blank" rel="noopener noreferrer" class="social-media-link">{{ entry.platform }}</a>
              </div>
            </template>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Description -->
    <textarea v-if="isEditing" v-model="editForm.description" class="club-description-box" rows="6"></textarea>
    <textarea v-else class="club-description-box" :value="clubDetails.description" readonly rows="6"></textarea>

    <!-- Officers & Committee table -->
    <div class="officers-section">
      <div class="officers-header">
        <h3>{{ clubDetails.shortName }} Officers and Committee</h3>
      </div>

      <table class="officers-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Mobile</th>
            <th>Committee Role</th>
            <th v-if="isEditing">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!editForm.officers.length && !isEditing">
            <td colspan="4" class="officers-empty">No officers or committee members listed.</td>
          </tr>
          <template v-for="(officer, idx) in editForm.officers" :key="idx">
            <tr v-if="isEditing && editingOfficerIdx === idx" class="officer-edit-row">
              <td><input v-model="officerEditBuf.name" type="text" class="club-information-input" placeholder="Name" /></td>
              <td><input v-model="officerEditBuf.email" type="email" class="club-information-input" placeholder="email@club.org" /></td>
              <td><input v-model="officerEditBuf.mobile" type="text" class="club-information-input" placeholder="+44 7xxx" /></td>
              <td><input v-model="officerEditBuf.role" type="text" class="club-information-input" placeholder="e.g. Chairman" /></td>
              <td class="officer-actions-cell">
                <app-button type="button" size="sm" inherit-style @click="saveOfficerRow(idx)">Save</app-button>
                <app-button type="button" size="sm" inherit-style @click="cancelOfficerEdit">Cancel</app-button>
              </td>
            </tr>
            <tr v-else>
              <td>{{ officer.name }}</td>
              <td>
                <a v-if="officer.email" :href="`mailto:${officer.email}`">{{ officer.email }}</a>
                <span v-else>-</span>
              </td>
              <td>{{ officer.mobile || '-' }}</td>
              <td>{{ officer.role }}</td>
              <td v-if="isEditing" class="officer-actions-cell">
                <app-button type="button" size="sm" inherit-style @click="editOfficerRow(idx)">Edit</app-button>
                <app-button type="button" size="sm" inherit-style @click="deleteOfficerRow(idx)">Delete</app-button>
              </td>
            </tr>
          </template>
          <!-- New officer input row -->
          <tr v-if="isEditing && editingOfficerIdx === -1" class="officer-edit-row">
            <td><input v-model="officerEditBuf.name" type="text" class="club-information-input" placeholder="Name" /></td>
            <td><input v-model="officerEditBuf.email" type="email" class="club-information-input" placeholder="email@club.org" /></td>
            <td><input v-model="officerEditBuf.mobile" type="text" class="club-information-input" placeholder="+44 7xxx" /></td>
            <td><input v-model="officerEditBuf.role" type="text" class="club-information-input" placeholder="e.g. Chairman" /></td>
            <td class="officer-actions-cell">
              <app-button type="button" size="sm" inherit-style @click="saveNewOfficerRow">Add</app-button>
              <app-button type="button" size="sm" inherit-style @click="cancelOfficerEdit">Cancel</app-button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="isEditing && editingOfficerIdx !== -1" class="officers-add-row">
        <app-button type="button" size="sm" inherit-style @click="startAddOfficer">+ Add Row</app-button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { store, clubDetails, API_BASE_URL, loadClubs } from '../store.js';
import AppButton from './ui/AppButton.vue';

export default {
  name: 'ClubInformation',
  components: { AppButton },
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
        whatsappGroups: '',
        socialMedia: [],
        officers: [],
      },
      editingOfficerIdx: null,
      officerEditBuf: { name: '', email: '', mobile: '', role: '' },
    };
  },
  computed: {
    clubDetails: () => clubDetails.value,
    canEditClubInformation() {
      const roles = Array.isArray(store.memberRoles) ? store.memberRoles : [];
      return roles.includes('club_admin') || roles.includes('app_admin') || roles.includes('app_owner');
    },
  },
  mounted() {
    this.resetEditForm();
  },
  watch: {
    clubDetails: {
      handler() {
        if (!this.isEditing) this.resetEditForm();
      },
      deep: true,
    },
  },
  methods: {
    resolveClubInformationSaveErrorMessage(err) {
      const statusCode = err?.response?.status;
      if (statusCode === 401) return 'Session expired. Please log in again, then retry.';
      if (statusCode === 403) return 'You do not have permission to update club information.';
      return err?.response?.data?.error || 'Failed to update club information.';
    },
    resetEditForm() {
      this.editForm = {
        fullName: this.clubDetails.fullName || '',
        websiteUrl: this.clubDetails.websiteUrl || '',
        adminEmail: this.clubDetails.adminEmail || '',
        description: this.clubDetails.description || '',
        whatsappGroups: this.clubDetails.whatsappGroups || '',
        socialMedia: (this.clubDetails.socialMedia || []).map(e => ({ ...e })),
        officers: (this.clubDetails.officers || []).map(o => ({ ...o })),
      };
      this.editingOfficerIdx = null;
      this.officerEditBuf = { name: '', email: '', mobile: '', role: '' };
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
      if (this.editingOfficerIdx !== null) {
        this.saveError = 'Please finish editing the current officer row first.';
        return;
      }
      this.saveError = '';
      this.saveSuccess = '';
      this.isSaving = true;

      const payload = {
        fullName: String(this.editForm.fullName || '').trim(),
        websiteUrl: String(this.editForm.websiteUrl || '').trim(),
        adminEmail: String(this.editForm.adminEmail || '').trim(),
        description: String(this.editForm.description || '').trim(),
        whatsappGroups: String(this.editForm.whatsappGroups || '').trim(),
        socialMedia: this.editForm.socialMedia
          .filter(e => e.platform || e.url)
          .map(e => ({ platform: String(e.platform || '').trim(), url: String(e.url || '').trim() })),
        officers: this.editForm.officers.map(o => ({
          name: String(o.name || '').trim(),
          email: String(o.email || '').trim(),
          mobile: String(o.mobile || '').trim(),
          role: String(o.role || '').trim(),
        })),
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
    addSocialMedia() {
      this.editForm.socialMedia.push({ platform: '', url: '' });
    },
    removeSocialMedia(idx) {
      this.editForm.socialMedia.splice(idx, 1);
    },
    startAddOfficer() {
      this.editingOfficerIdx = -1;
      this.officerEditBuf = { name: '', email: '', mobile: '', role: '' };
    },
    editOfficerRow(idx) {
      this.editingOfficerIdx = idx;
      this.officerEditBuf = { ...this.editForm.officers[idx] };
    },
    saveOfficerRow(idx) {
      this.editForm.officers[idx] = { ...this.officerEditBuf };
      this.editingOfficerIdx = null;
      this.officerEditBuf = { name: '', email: '', mobile: '', role: '' };
    },
    saveNewOfficerRow() {
      if (!this.officerEditBuf.name && !this.officerEditBuf.role) return;
      this.editForm.officers.push({ ...this.officerEditBuf });
      this.editingOfficerIdx = null;
      this.officerEditBuf = { name: '', email: '', mobile: '', role: '' };
    },
    cancelOfficerEdit() {
      this.editingOfficerIdx = null;
      this.officerEditBuf = { name: '', email: '', mobile: '', role: '' };
    },
    deleteOfficerRow(idx) {
      this.editForm.officers.splice(idx, 1);
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
  border: 1px solid #9ab0c6;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 10pt;
  font-family: inherit;
  box-sizing: border-box;
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

.club-information-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 12px;
  font-size: 10pt;
}

.club-information-table th,
.club-information-table td {
  padding: 7px 10px;
  border: 1px solid #d7dce2;
  text-align: left;
  vertical-align: middle;
}

.club-information-table th {
  background: #eaf2f8;
  color: #17324d;
  width: 160px;
  font-weight: 600;
}

.club-description-box {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #9ab0c6;
  border-radius: 4px;
  padding: 8px;
  font-size: 10pt;
  font-family: inherit;
  resize: vertical;
  margin-bottom: 16px;
}

.social-media-edit {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.social-media-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.social-media-platform {
  max-width: 140px;
}

.social-media-url {
  max-width: 340px;
}

.social-media-links {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.social-media-link {
  color: #0e5d8b;
  text-decoration: none;
  font-weight: 500;
}

.social-media-link:hover {
  text-decoration: underline;
}

.officers-section {
  margin-top: 8px;
}

.officers-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.officers-header h3 {
  margin: 0;
  font-size: 11pt;
  color: #17324d;
}

.officers-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 10pt;
  margin-bottom: 8px;
}

.officers-table th,
.officers-table td {
  padding: 7px 10px;
  border: 1px solid #d7dce2;
  text-align: left;
  vertical-align: middle;
}

.officers-table thead th {
  background: #eaf2f8;
  color: #17324d;
  font-weight: 600;
}

.officers-table tbody tr:nth-child(even) {
  background: #f8fbfd;
}

.officer-edit-row td {
  background: #fffbe6;
  padding: 6px 8px;
}

.officer-actions-cell {
  white-space: nowrap;
  display: flex;
  gap: 4px;
}

.officers-empty {
  color: #666;
  font-style: italic;
}

.officers-add-row {
  margin-top: 6px;
}
</style>
