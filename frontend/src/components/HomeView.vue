<template>
  <div class="home-container">
    <div class="home-page-header">
      <h2>Hello {{ greetingFirstName }},</h2>
      <h3>Welcome to the website for {{ welcomeClubShortName }}</h3>
    </div>

    <section class="home-panels-grid">
      <div class="home-news-card">
        <h4>{{ clubNewsTitle }}</h4>
        <table class="home-news-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Category</th>
              <th>Update</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in newsItems" :key="item.id">
              <td>{{ formatNewsDate(item.date) }}</td>
              <td>{{ item.category }}</td>
              <td>{{ item.message }}</td>
              <td>
                <span class="news-status-badge" :class="`is-${item.status.toLowerCase()}`">
                  {{ item.status }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        <p class="home-news-note">
          Placeholder content only for now. Backend-backed news alerts and club messages can be wired in later.
        </p>
      </div>

      <div class="home-documents-card">
        <h4>{{ clubDocumentsTitle }}</h4>

        <form v-if="canManageDocuments" class="documents-upload-form" @submit.prevent="uploadDocument">
          <div class="documents-upload-fields">
            <input
              v-model="uploadTitle"
              type="text"
              placeholder="Document title (optional)"
              class="documents-input"
            />
            <input
              type="file"
              accept=".pdf,.xls,.xlsx,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              class="documents-input"
              @change="onFileSelected"
            />
          </div>
          <button type="submit" :disabled="uploadBusy" class="documents-upload-button">
            {{ uploadBusy ? 'Uploading...' : 'Upload Document' }}
          </button>
        </form>

        <p v-if="uploadError" class="documents-error">{{ uploadError }}</p>
        <p v-if="documentsError" class="documents-error">{{ documentsError }}</p>

        <table class="home-documents-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>File</th>
              <th>Uploaded</th>
              <th>Size</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="documentsLoading">
              <td colspan="5">Loading documents...</td>
            </tr>
            <tr v-else-if="!documents.length">
              <td colspan="5">No documents uploaded yet.</td>
            </tr>
            <tr v-else v-for="doc in documents" :key="doc.id">
              <td>{{ doc.title || doc.fileName }}</td>
              <td class="documents-file-cell">{{ doc.fileName }}</td>
              <td>{{ formatNewsDate(doc.createdAt) }}</td>
              <td>{{ formatFileSize(doc.fileSize) }}</td>
              <td class="documents-actions-cell">
                <button type="button" class="documents-link-btn" @click="downloadDocument(doc)">Download</button>
                <button
                  v-if="canManageDocuments"
                  type="button"
                  class="documents-delete-btn"
                  @click="deleteDocument(doc)"
                >
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <p v-if="accessError" class="access-error">{{ accessError }}</p>
  </div>
</template>

<script>
import axios from 'axios';
import { store, clubDetails, formatConfiguredDate, API_BASE_URL } from '../store.js';

export default {
  name: 'HomeView',
  data() {
    return {
      documents: [],
      documentsLoading: false,
      documentsError: '',
      uploadTitle: '',
      uploadFile: null,
      uploadBusy: false,
      uploadError: '',
    };
  },
  computed: {
    loggedInUsername: () => store.loggedInUsername,
    loggedInClub: () => store.loggedInClub,
    loggedInUser: () => store.loggedInUser,
    accessError: () => store.accessError,
    canManageDocuments: () => store.memberPermissions.includes('document.club.manage'),
    greetingFirstName() {
      const user = this.loggedInUser || {};
      const candidates = [
        user.First_Name,
        user.first_name,
        user.Preferred_Name,
        user.preferred_name,
        user.display_name,
        user.Members_Name,
        user.members_name,
        this.loggedInUsername,
      ];

      const rawName = candidates.find(value => typeof value === 'string' && value.trim()) || 'Member';
      return String(rawName).trim().split(/\s+/)[0] || 'Member';
    },
    welcomeClubShortName() {
      return clubDetails.value.shortName || this.loggedInClub || 'your club';
    },
    clubNewsTitle: () => `${clubDetails.value.shortName || store.loggedInClub || 'Club'} News and Updates`,
    clubDocumentsTitle: () => `${clubDetails.value.shortName || store.loggedInClub || 'Club'} Documents`,
    newsItems() {
      return [
        {
          id: 'notice-1',
          date: '05 Apr 2026',
          category: 'Club Notice',
          message: 'Season opening briefing will be published here once the news backend is connected.',
          status: 'Draft',
        },
        {
          id: 'notice-2',
          date: '04 Apr 2026',
          category: 'River Conditions',
          message: 'This placeholder row can later show urgent river level alerts or temporary access restrictions.',
          status: 'Planned',
        },
        {
          id: 'notice-3',
          date: '02 Apr 2026',
          category: 'Membership',
          message: 'Member updates, reminders, and general announcements will appear in this central panel.',
          status: 'Queued',
        },
      ];
    },
  },
  methods: {
    formatNewsDate(value) {
      const formatted = formatConfiguredDate(value, 'Date');
      return formatted || value;
    },
    formatFileSize(rawBytes) {
      const bytes = Number(rawBytes || 0);
      if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
      if (bytes < 1024) return `${bytes} B`;
      if (bytes < (1024 * 1024)) return `${(bytes / 1024).toFixed(1)} KB`;
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    },
    fetchDocuments() {
      this.documentsLoading = true;
      this.documentsError = '';
      return axios.get(`${API_BASE_URL}/documents`, {
        params: { club: this.loggedInClub },
      }).then((res) => {
        this.documents = Array.isArray(res.data?.documents) ? res.data.documents : [];
      }).catch((err) => {
        this.documents = [];
        this.documentsError = err?.response?.data?.error || 'Unable to load documents';
      }).finally(() => {
        this.documentsLoading = false;
      });
    },
    onFileSelected(event) {
      const file = event?.target?.files?.[0] || null;
      this.uploadFile = file;
    },
    uploadDocument() {
      this.uploadError = '';
      if (!this.uploadFile) {
        this.uploadError = 'Please choose a file to upload.';
        return Promise.resolve();
      }

      const formData = new FormData();
      formData.append('club', this.loggedInClub);
      formData.append('file', this.uploadFile);
      if (this.uploadTitle.trim()) {
        formData.append('title', this.uploadTitle.trim());
      }

      this.uploadBusy = true;
      return axios.post(`${API_BASE_URL}/documents`, formData)
        .then(() => {
          this.uploadTitle = '';
          this.uploadFile = null;
          this.fetchDocuments();
        })
        .catch((err) => {
          this.uploadError = err?.response?.data?.error || 'Upload failed';
        })
        .finally(() => {
          this.uploadBusy = false;
        });
    },
    downloadDocument(doc) {
      return axios.get(`${API_BASE_URL}/documents/${doc.id}/download`, {
        params: { club: this.loggedInClub },
        responseType: 'blob',
      }).then((res) => {
        const blobUrl = window.URL.createObjectURL(res.data);
        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = doc.fileName || `document-${doc.id}`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(blobUrl);
      }).catch((err) => {
        this.documentsError = err?.response?.data?.error || 'Download failed';
      });
    },
    deleteDocument(doc) {
      this.documentsError = '';
      if (!window.confirm(`Delete document "${doc.fileName}"?`)) {
        return Promise.resolve();
      }
      return axios.delete(`${API_BASE_URL}/documents/${doc.id}`, {
        params: { club: this.loggedInClub },
      }).then(() => {
        this.fetchDocuments();
      }).catch((err) => {
        this.documentsError = err?.response?.data?.error || 'Delete failed';
      });
    },
  },
  mounted() {
    this.fetchDocuments();
  },
  watch: {
    loggedInClub() {
      this.fetchDocuments();
    },
  },
};
</script>

<style scoped>
.home-container {
  width: 100%;
  margin: 0;
  padding: 0 0 24px;
  font-family: Helvetica, Arial, sans-serif;
}

.home-page-header {
  margin-bottom: 22px;
}

.home-page-header h2,
.home-page-header h3 {
  margin: 0;
}

.home-page-header h3 {
  margin-top: 10px;
  font-weight: 500;
  line-height: 1.4;
}

.home-panels-grid {
  min-width: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.home-news-card,
.home-documents-card {
  background: #fff;
  border: 1px solid #d7dce2;
  border-radius: 12px;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
  padding: 18px;
}

.home-news-card h4,
.home-documents-card h4 {
  margin: 0 0 14px;
  font-size: 1.1rem;
  color: #17324d;
}

.home-news-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.home-news-table th,
.home-news-table td {
  padding: 10px 12px;
  border: 1px solid #d7dce2;
  text-align: left;
  vertical-align: top;
  font-size: 10pt;
}

.home-news-table thead th {
  background: #eaf2f8;
  color: #17324d;
}

.home-news-table tbody tr:nth-child(even) {
  background: #f8fbfd;
}

.news-status-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 9pt;
  font-weight: 700;
}

.news-status-badge.is-draft {
  background: #fff2cc;
  color: #7a5a00;
}

.news-status-badge.is-planned {
  background: #dceeff;
  color: #0f4c81;
}

.news-status-badge.is-queued {
  background: #e4f7e7;
  color: #21633a;
}

.home-news-note {
  margin: 14px 0 0;
  color: #475569;
  font-size: 9.5pt;
}

.documents-upload-form {
  margin-bottom: 12px;
}

.documents-upload-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 8px;
}

.documents-input {
  border: 1px solid #d7dce2;
  border-radius: 8px;
  padding: 8px;
}

.documents-upload-button,
.documents-link-btn,
.documents-delete-btn {
  border: 1px solid #c7d2e0;
  border-radius: 8px;
  background: #f8fbfd;
  color: #17324d;
  padding: 7px 12px;
  cursor: pointer;
}

.documents-delete-btn {
  margin-left: 8px;
}

.documents-upload-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.home-documents-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.home-documents-table th,
.home-documents-table td {
  padding: 10px 12px;
  border: 1px solid #d7dce2;
  text-align: left;
  vertical-align: top;
  font-size: 10pt;
}

.home-documents-table thead th {
  background: #eaf2f8;
  color: #17324d;
}

.home-documents-table tbody tr:nth-child(even) {
  background: #f8fbfd;
}

.documents-actions-cell {
  white-space: nowrap;
}

.documents-file-cell {
  overflow-wrap: anywhere;
  word-break: break-word;
}

.documents-error {
  margin: 0 0 10px;
  color: #b42318;
  font-weight: 600;
}


@media (max-width: 1000px) {
  .home-page-header {
    display: none;
  }

  .home-panels-grid {
    grid-template-columns: 1fr;
  }

  .documents-upload-fields {
    grid-template-columns: 1fr;
  }
}
.access-error {
  margin-top: 18px;
  color: #b42318;
  font-weight: 600;
}
</style>
