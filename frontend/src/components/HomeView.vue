<template>
  <div class="home-container">
    <div class="home-page-header" v-if="VerboseDebug">
      <h2>Hello {{ greetingFirstName }},</h2>
      <h3>Welcome to the website for {{ welcomeClubShortName }}</h3>
    </div>

    <section class="home-panels-grid">
      <app-card class="home-news-card">
        <h4>{{ clubNewsTitle }}</h4>
        <table class="home-news-table">
          <thead>
            <tr>
              <th
                v-for="column in visibleNewsColumns"
                :key="`news-head-${column.key}`"
                :class="{ 'sortable-header': isSortableColumn('news', column.key) }"
                :style="getColumnStyle('home_news', column.key)"
                @click.stop="toggleNewsSort(column.key)"
              >
                {{ column.label }}<span class="sort-indicator">{{ getSortIndicator('news', column.key) }}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="newsLoading">
              <td :colspan="newsColumnCount">Loading news/updates...</td>
            </tr>
            <tr v-else-if="!newsItems.length">
              <td :colspan="newsColumnCount">No news/updates posted yet.</td>
            </tr>
            <template v-else v-for="item in sortedNewsItems" :key="item.id">
              <!-- Inline edit row -->
              <tr v-if="editingNewsId === item.id" class="news-edit-row">
                <td :colspan="newsColumnCount">
                  <div class="news-edit-form">
                    <div class="news-edit-fields">
                      <label class="news-edit-label">Date
                        <input v-model="editNewsForm.date" type="date" class="news-edit-input" :disabled="isHomeNewsFieldReadOnly('Date')" />
                      </label>
                      <label class="news-edit-label">Category
                        <input v-model="editNewsForm.category" type="text" class="news-edit-input" placeholder="Category" :disabled="isHomeNewsFieldReadOnly('Category')" />
                      </label>
                      <label class="news-edit-label">Status
                        <select v-model="editNewsForm.status" class="news-edit-input" :disabled="isHomeNewsFieldReadOnly('Status')">
                          <option value="Draft">Draft</option>
                          <option value="Published">Published</option>
                          <option value="Archived">Archived</option>
                        </select>
                      </label>
                    </div>
                    <label class="news-edit-label news-edit-update-label">Update
                      <textarea v-model="editNewsForm.update" rows="3" class="news-edit-textarea" :disabled="isHomeNewsFieldReadOnly('Update')" />
                    </label>
                    <p v-if="editNewsError" class="news-edit-error">{{ editNewsError }}</p>
                    <div class="news-edit-actions">
                      <app-button type="button" size="sm" class="news-edit-save-btn" :disabled="editNewsBusy" @click="saveNewsEdit(item)">{{ editNewsBusy ? 'Saving...' : 'Save' }}</app-button>
                      <app-button type="button" size="sm" variant="secondary" class="news-edit-cancel-btn" :disabled="editNewsBusy" @click="cancelNewsEdit">Cancel</app-button>
                    </div>
                  </div>
                </td>
              </tr>
              <!-- Normal display row -->
              <tr v-else>
                <td
                  v-for="column in visibleNewsColumns"
                  :key="`news-cell-${item.id}-${column.key}`"
                  :class="{
                    'news-actions-cell': column.key === 'Actions',
                  }"
                  :style="getColumnStyle('home_news', column.key)"
                >
                  <template v-if="column.key === 'Date'">
                    <span>{{ formatNewsDate(item.date) }}</span>
                    <div class="news-date-status"><app-status-badge :status="item.status" /></div>
                  </template>
                  <span v-else-if="column.key === 'Category'">{{ item.category }}</span>
                  <span v-else-if="column.key === 'Update'">{{ item.update || item.message }}</span>
                  <template v-else-if="column.key === 'Actions'">
                    <div v-if="canManageNewsActions" class="news-actions-stack">
                      <app-button type="button" size="sm" class="news-edit-btn news-action-btn" inherit-style @click="editNewsItem(item)">Edit</app-button>
                      <app-button type="button" size="sm" class="news-delete-btn news-action-btn news-action-btn-delete" inherit-style :disabled="deleteNewsBusy === item.id" @click="deleteNewsItem(item)">{{ deleteNewsBusy === item.id ? 'Deleting...' : 'Delete' }}</app-button>
                    </div>
                  </template>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
        <p v-if="newsError" class="home-news-note">{{ newsError }}</p>
      </app-card>

      <app-card class="home-documents-card">
        <h4>{{ clubDocumentsTitle }}</h4>

        <form v-if="canManageDocuments" class="documents-upload-form" @submit.prevent="uploadDocument">
          <div class="documents-upload-fields">
            <input
              v-model="uploadTitle"
              type="text"
              placeholder="Document title (optional)"
              class="documents-input"
              :disabled="isHomeDocumentsFieldReadOnly('Title')"
            />
            <input
              type="file"
              accept=".pdf,.xls,.xlsx,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              class="documents-input"
              @change="onFileSelected"
              :disabled="isHomeDocumentsFieldReadOnly('File')"
            />
          </div>
          <app-button type="submit" :disabled="uploadBusy || isDocumentUploadReadOnly" class="documents-upload-button">
            {{ uploadBusy ? 'Uploading...' : 'Upload Document' }}
          </app-button>
        </form>

        <p v-if="uploadError" class="documents-error">{{ uploadError }}</p>
        <p v-if="documentsError" class="documents-error">{{ documentsError }}</p>

        <table class="home-documents-table">
          <thead>
            <tr>
              <th
                v-for="column in visibleDocumentsColumns"
                :key="`docs-head-${column.key}`"
                :class="{ 'sortable-header': isSortableColumn('documents', column.key) }"
                :style="getColumnStyle('home_documents', column.key)"
                @click.stop="toggleDocumentsSort(column.key)"
              >
                {{ column.label }}<span class="sort-indicator">{{ getSortIndicator('documents', column.key) }}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="documentsLoading">
              <td :colspan="documentsColumnCount">Loading documents...</td>
            </tr>
            <tr v-else-if="!documents.length">
              <td :colspan="documentsColumnCount">No documents uploaded yet.</td>
            </tr>
            <tr v-else v-for="doc in sortedDocuments" :key="doc.id">
              <td
                v-for="column in visibleDocumentsColumns"
                :key="`docs-cell-${doc.id}-${column.key}`"
                :class="{
                  'documents-title-cell': column.key === 'Title',
                  'documents-file-cell': column.key === 'File',
                  'documents-actions-cell': column.key === 'Actions',
                }"
                :style="getColumnStyle('home_documents', column.key)"
              >
                <template v-if="column.key === 'Title'">
                  <app-button
                    variant="link"
                    class="documents-title-link"
                    @click="openDocumentPreview(doc)"
                  >
                    {{ doc.title || doc.fileName }}
                  </app-button>
                </template>
                <span v-else-if="column.key === 'File'">{{ doc.fileName }}</span>
                <span v-else-if="column.key === 'Uploaded'">{{ formatNewsDate(doc.createdAt) }}</span>
                <span v-else-if="column.key === 'Size'">{{ formatFileSize(doc.fileSize) }}</span>
                <template v-else-if="column.key === 'Actions'">
                  <div class="documents-actions-stack">
                    <app-button type="button" size="sm" class="documents-link-btn documents-action-btn" inherit-style @click="downloadDocument(doc)">Download</app-button>
                    <app-button
                      v-if="canManageDocuments && !isHomeDocumentsFieldReadOnly('Actions')"
                      type="button"
                      size="sm"
                      class="documents-delete-btn documents-action-btn documents-action-btn-delete"
                      inherit-style
                      @click="deleteDocument(doc)"
                    >
                      Delete
                    </app-button>
                  </div>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </app-card>
    </section>

    <p v-if="accessError" class="access-error">{{ accessError }}</p>
  </div>
</template>

<script>
import axios from 'axios';
import { store, clubDetails, formatConfiguredDate, API_BASE_URL, canAccessNewsletters } from '../store.js';
import { VerboseDebug } from '../localConfig.js';
import AppCard from './ui/AppCard.vue';
import AppButton from './ui/AppButton.vue';
import AppStatusBadge from './ui/AppStatusBadge.vue';

export default {
  name: 'HomeView',
  components: {
    AppCard,
    AppButton,
    AppStatusBadge,
  },
  data() {
    return {
      newsItems: [],
      newsLoading: false,
      newsError: '',
      documents: [],
      documentsLoading: false,
      documentsError: '',
      fieldOrder: {},
      uploadTitle: '',
      uploadFile: null,
      uploadBusy: false,
      uploadError: '',
      VerboseDebug,
      editingNewsId: null,
      editNewsForm: { date: '', category: '', update: '', status: '' },
      editNewsBusy: false,
      editNewsError: '',
      deleteNewsBusy: null,
      newsSortedBy: null,
      newsSortDirection: 'asc',
      documentsSortedBy: null,
      documentsSortDirection: 'asc',
    };
  },
  computed: {
    loggedInUsername: () => store.loggedInUsername,
    loggedInClub: () => store.loggedInClub,
    loggedInUser: () => store.loggedInUser,
    accessError: () => store.accessError,
    canManageDocuments: () => store.memberPermissions.includes('document.club.manage'),
    canManageNews: () => canAccessNewsletters.value,
    hasAdminRole() {
      const normalizedRoles = (Array.isArray(store.memberRoles) ? store.memberRoles : [])
        .map(role => String(role || '').toLowerCase().replace(/[^a-z0-9]/g, ''));
      return normalizedRoles.includes('clubadmin')
        || normalizedRoles.includes('appadmin')
        || normalizedRoles.includes('appowner');
    },
    homeNewsReadOnlyColumns() {
      const configured = this.fieldOrder?.read_only?.home_news;
      return configured && typeof configured === 'object' ? configured : {};
    },
    homeDocumentsReadOnlyColumns() {
      const configured = this.fieldOrder?.read_only?.home_documents;
      return configured && typeof configured === 'object' ? configured : {};
    },
    canManageNewsActions() {
      return this.canManageNews && !this.isHomeNewsFieldReadOnly('Actions');
    },
    isDocumentUploadReadOnly() {
      return this.isHomeDocumentsFieldReadOnly('Title') || this.isHomeDocumentsFieldReadOnly('File');
    },
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
    newsColumns() {
      return [
        { key: 'Date', label: 'Date' },
        { key: 'Category', label: 'Category' },
        { key: 'Update', label: 'Update' },
        { key: 'Actions', label: 'Actions' },
      ];
    },
    documentColumns() {
      // Only show File and Uploaded columns if VerboseDebug is true
      const cols = [
        { key: 'Title', label: 'Title' },
        { key: 'Size', label: 'Size' },
        { key: 'Actions', label: 'Actions' },
      ];
      if (this.VerboseDebug) {
        cols.splice(1, 0, { key: 'File', label: 'File' });
        cols.splice(2, 0, { key: 'Uploaded', label: 'Uploaded' });
      }
      return cols;
    },
    visibleNewsColumns() {
      return this.getVisibleColumns('home_news', this.newsColumns);
    },
    visibleDocumentsColumns() {
      return this.getVisibleColumns('home_documents', this.documentColumns);
    },
    newsColumnCount() {
      return this.visibleNewsColumns.length || 1;
    },
    documentsColumnCount() {
      return this.visibleDocumentsColumns.length || 1;
    },
    sortedNewsItems() {
      if (!this.newsSortedBy) return this.newsItems;
      const sorted = [...this.newsItems];
      const propertyMap = {
        'Date': 'date',
        'Category': 'category',
        'Update': 'update',
      };
      const sortProperty = propertyMap[this.newsSortedBy] || this.newsSortedBy.toLowerCase();
      
      sorted.sort((a, b) => {
        let aVal = a[sortProperty];
        let bVal = b[sortProperty];
        
        if (aVal == null) aVal = '';
        if (bVal == null) bVal = '';
        
        // Convert to string for alphanumeric comparison
        const aStr = String(aVal).toLowerCase();
        const bStr = String(bVal).toLowerCase();
        
        const comparison = aStr.localeCompare(bStr, undefined, { numeric: true });
        return this.newsSortDirection === 'asc' ? comparison : -comparison;
      });
      return sorted;
    },
    sortedDocuments() {
      if (!this.documentsSortedBy) return this.documents;
      const sorted = [...this.documents];
      const propertyMap = {
        'Title': 'title',
        'File': 'fileName',
        'Uploaded': 'createdAt',
        'Size': 'fileSize',
      };
      const sortProperty = propertyMap[this.documentsSortedBy] || this.documentsSortedBy.toLowerCase();
      
      sorted.sort((a, b) => {
        let aVal = a[sortProperty];
        let bVal = b[sortProperty];
        
        if (aVal == null) aVal = '';
        if (bVal == null) bVal = '';
        
        // Convert to string for alphanumeric comparison
        const aStr = String(aVal).toLowerCase();
        const bStr = String(bVal).toLowerCase();
        
        const comparison = aStr.localeCompare(bStr, undefined, { numeric: true });
        return this.documentsSortDirection === 'asc' ? comparison : -comparison;
      });
      return sorted;
    },
  },
  methods: {
    isHomeNewsFieldReadOnly(fieldName) {
      if (this.hasAdminRole) {
        return false;
      }
      return this.homeNewsReadOnlyColumns?.[fieldName] === true;
    },
    isHomeDocumentsFieldReadOnly(fieldName) {
      if (this.hasAdminRole) {
        return false;
      }
      return this.homeDocumentsReadOnlyColumns?.[fieldName] === true;
    },
    sanitizeHomeNewsPayload(basePayload, sourceItem) {
      if (this.hasAdminRole) {
        return basePayload;
      }
      const sanitized = { ...basePayload };
      const source = sourceItem || {};
      const fieldMap = {
        Date: 'date',
        Category: 'category',
        Update: 'update',
        Status: 'status',
      };
      Object.entries(fieldMap).forEach(([columnKey, payloadKey]) => {
        if (!this.isHomeNewsFieldReadOnly(columnKey)) {
          return;
        }
        if (payloadKey === 'update') {
          sanitized[payloadKey] = source.update || source.message || '';
          return;
        }
        sanitized[payloadKey] = source[payloadKey] || '';
      });
      return sanitized;
    },
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
    editNewsItem(item) {
      if (!this.canManageNewsActions) {
        return;
      }
      this.editingNewsId = item.id;
      this.editNewsForm = {
        date: item.date || '',
        category: item.category || '',
        update: item.update || item.message || '',
        status: item.status || 'Published',
      };
      this.editNewsError = '';
    },
    cancelNewsEdit() {
      this.editingNewsId = null;
      this.editNewsError = '';
    },
    saveNewsEdit(item) {
      this.editNewsBusy = true;
      this.editNewsError = '';
      const payload = this.sanitizeHomeNewsPayload({
        club: this.loggedInClub,
        date: this.editNewsForm.date,
        category: this.editNewsForm.category,
        update: this.editNewsForm.update,
        status: this.editNewsForm.status,
      }, item);
      return axios.put(`${API_BASE_URL}/news-updates/${item.id}`, payload).then(() => {
        this.editingNewsId = null;
        this.fetchNewsUpdates();
      }).catch((err) => {
        this.editNewsError = err?.response?.data?.error || 'Failed to save';
      }).finally(() => {
        this.editNewsBusy = false;
      });
    },
    deleteNewsItem(item) {
      if (!this.canManageNewsActions) {
        return Promise.resolve();
      }
      if (!window.confirm(`Delete this news post?`)) return Promise.resolve();
      this.deleteNewsBusy = item.id;
      return axios.delete(`${API_BASE_URL}/news-updates/${item.id}`, {
        params: { club: this.loggedInClub },
      }).then(() => {
        this.fetchNewsUpdates();
      }).catch((err) => {
        this.newsError = err?.response?.data?.error || 'Failed to delete';
      }).finally(() => {
        this.deleteNewsBusy = null;
      });
    },
    fetchNewsUpdates() {
      this.newsLoading = true;
      this.newsError = '';
      return axios.get(`${API_BASE_URL}/news-updates`, {
        params: { club: this.loggedInClub, limit: 20 },
      }).then((res) => {
        this.newsItems = Array.isArray(res.data?.updates) ? res.data.updates : [];
      }).catch((err) => {
        this.newsItems = [];
        this.newsError = err?.response?.data?.error || 'Unable to load news/updates';
      }).finally(() => {
        this.newsLoading = false;
      });
    },
    inferDocumentMimeType(fileName, fallbackType) {
      const extension = String(fileName || '').toLowerCase().split('.').pop();
      const mimeByExtension = {
        pdf: 'application/pdf',
        png: 'image/png',
        jpg: 'image/jpeg',
        jpeg: 'image/jpeg',
        gif: 'image/gif',
        webp: 'image/webp',
        bmp: 'image/bmp',
        svg: 'image/svg+xml',
      };
      return mimeByExtension[extension] || fallbackType || 'application/octet-stream';
    },
    loadFieldOrder() {
      return axios.get(`${API_BASE_URL}/field-order`)
        .then((res) => {
          const loaded = res.data?.field_order;
          this.fieldOrder = loaded && typeof loaded === 'object' ? loaded : {};
        })
        .catch(() => {
          this.fieldOrder = {};
        });
    },
    isColumnVisible(contextKey, columnKey) {
      const configured = this.fieldOrder?.show_columns?.[contextKey]?.[columnKey];
      return configured !== false;
    },
    getVisibleColumns(contextKey, fallbackColumns) {
      const fallbackMap = new Map(fallbackColumns.map(column => [column.key, column]));
      const configuredOrder = Array.isArray(this.fieldOrder?.[contextKey])
        ? this.fieldOrder[contextKey]
        : fallbackColumns.map(column => column.key);

      // Filter out Actions from visibility checks - it's always visible
      const ordered = configuredOrder
        .map(key => fallbackMap.get(key))
        .filter(Boolean)
        .filter(column => column.key !== 'Actions' && this.isColumnVisible(contextKey, column.key));

      // Always include Actions column at the end, regardless of Field Order settings
      const actionsColumn = fallbackMap.get('Actions');
      if (actionsColumn) {
        ordered.push(actionsColumn);
      }

      if (ordered.length) return ordered;
      return fallbackColumns.filter(column => column.key !== 'Actions') || [];
    },
    getColumnStyle(contextKey, columnKey) {
      // First check if a width is specified in the widths configuration
      const configuredWidth = this.fieldOrder?.widths?.[contextKey]?.[columnKey];
      if (configuredWidth) {
        const widthStr = String(configuredWidth).trim().toLowerCase();
        
        // Handle 'flex' - for now return empty and let CSS handle it
        // In a future enhancement, this could calculate proportional widths
        if (widthStr === 'flex' || widthStr === 'auto') {
          return {};
        }
        
        // Return the width value directly (e.g., '80px', '50%')
        return { width: widthStr };
      }
      
      // Fall back to minimum_widths if weight is not specified
      const rawMinWidth = this.fieldOrder?.minimum_widths?.[contextKey]?.[columnKey];
      const minWidth = Number(rawMinWidth);
      if (!Number.isFinite(minWidth) || minWidth <= 0) return {};
      return { minWidth: `${minWidth}px` };
    },
    toggleNewsSort(columnKey) {
      // Don't allow sorting by Actions column
      if (columnKey === 'Actions') return;
      
      if (this.newsSortedBy === columnKey) {
        // Toggle direction
        this.newsSortDirection = this.newsSortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        // Set new sort column
        this.newsSortedBy = columnKey;
        this.newsSortDirection = 'asc';
      }
    },
    toggleDocumentsSort(columnKey) {
      // Don't allow sorting by Actions column
      if (columnKey === 'Actions') return;
      
      if (this.documentsSortedBy === columnKey) {
        // Toggle direction
        this.documentsSortDirection = this.documentsSortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        // Set new sort column
        this.documentsSortedBy = columnKey;
        this.documentsSortDirection = 'asc';
      }
    },
    getSortIndicator(tableName, columnKey) {
      if (tableName === 'news') {
        if (this.newsSortedBy !== columnKey) return '';
        return this.newsSortDirection === 'asc' ? ' ▲' : ' ▼';
      } else if (tableName === 'documents') {
        if (this.documentsSortedBy !== columnKey) return '';
        return this.documentsSortDirection === 'asc' ? ' ▲' : ' ▼';
      }
      return '';
    },
    isSortableColumn(tableName, columnKey) {
      if ((tableName === 'documents' || tableName === 'news') && columnKey === 'Actions') return false;
      return true;
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
      if (this.isHomeDocumentsFieldReadOnly('File')) {
        this.uploadError = 'File uploads are read-only for your role.';
        if (event?.target) {
          event.target.value = '';
        }
        return;
      }
      const file = event?.target?.files?.[0] || null;
      this.uploadFile = file;
    },
    uploadDocument() {
      this.uploadError = '';
      if (this.isDocumentUploadReadOnly) {
        this.uploadError = 'Document upload fields are read-only for your role.';
        return Promise.resolve();
      }
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
    openDocumentPreview(doc) {
      this.documentsError = '';
      return axios.get(`${API_BASE_URL}/documents/${doc.id}/download`, {
        params: { club: this.loggedInClub },
        responseType: 'blob',
      }).then((res) => {
        const inferredMimeType = this.inferDocumentMimeType(doc.fileName, res?.data?.type);
        const previewBlob = new Blob([res.data], { type: inferredMimeType });
        const blobUrl = window.URL.createObjectURL(previewBlob);
        const openedWindow = window.open(blobUrl, '_blank', 'noopener,noreferrer');
        if (!openedWindow) {
          const link = document.createElement('a');
          link.href = blobUrl;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          document.body.appendChild(link);
          link.click();
          link.remove();
        }
        window.setTimeout(() => {
          window.URL.revokeObjectURL(blobUrl);
        }, 60000);
      }).catch((err) => {
        this.documentsError = err?.response?.data?.error || 'Unable to open document preview';
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
      if (this.isHomeDocumentsFieldReadOnly('Actions')) {
        this.documentsError = 'Document actions are read-only for your role.';
        return Promise.resolve();
      }
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
    this.loadFieldOrder();
    this.fetchNewsUpdates();
    this.fetchDocuments();
  },
  watch: {
    loggedInClub() {
      this.loadFieldOrder();
      this.fetchNewsUpdates();
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
  grid-template-columns: 1fr;
  gap: 18px;
  width: 80%;
  max-width: 80%;
}

.home-news-card,
.home-documents-card {
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

.home-news-table thead th.sortable-header {
  cursor: pointer;
  user-select: none;
}

.home-news-table thead th.sortable-header:hover {
  background: #d4e5f0;
}

.sort-indicator {
  font-size: 0.85em;
  margin-left: 4px;
}

.home-news-table th.news-actions-cell,
.home-news-table td.news-actions-cell {
  text-align: center;
  vertical-align: middle;
}

.news-date-status {
  margin-top: 6px;
}

.news-actions-stack {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  max-width: 100%;
}

.home-news-table :deep(.news-edit-btn.app-button.is-sm),
.home-news-table :deep(.news-delete-btn.app-button.is-sm) {
  font-size: 6pt;
  line-height: 1.15;
  padding: 2px 2px;
}

.news-edit-row td {
  padding: 12px;
}

.news-edit-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.news-edit-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.news-edit-label {
  display: flex;
  flex-direction: column;
  font-size: 9pt;
  font-weight: 600;
  color: #17324d;
  gap: 3px;
}

.news-edit-update-label {
  width: 100%;
}

.news-edit-input {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 9pt;
  border: 1px solid #d7dce2;
  border-radius: 6px;
  padding: 5px 8px;
  min-width: 120px;
}

.news-edit-textarea {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 9pt;
  border: 1px solid #d7dce2;
  border-radius: 6px;
  padding: 5px 8px;
  resize: vertical;
  width: 100%;
  box-sizing: border-box;
}

.news-edit-error {
  margin: 0;
  color: #b42318;
  font-size: 9pt;
  font-weight: 600;
}

.news-edit-actions {
  display: flex;
  gap: 8px;
}

.news-edit-save-btn,
.news-edit-cancel-btn {
  font-size: 9pt;
  padding: 5px 14px;
}

.home-news-table tbody tr:nth-child(even) {
  background: #f8fbfd;
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
  border: 1px solid #9ab0c6;
  border-radius: 6px;
  padding: 6px 8px;
  background: #ffffff;
  color: #17324d;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 9pt;
}

.documents-input::placeholder {
  color: #56748f;
}

.documents-input[type="file"] {
  padding: 4px 6px;
}

.documents-input[type="file"]::file-selector-button,
.documents-input[type="file"]::-webkit-file-upload-button {
  border: 1px solid #9ab0c6;
  border-radius: 6px;
  background: linear-gradient(180deg, #f7f9fc 0%, #e3ebf3 100%);
  color: #17324d;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 8pt;
  line-height: 1.1;
  padding: 2px 6px;
  margin-right: 8px;
}

.documents-upload-button {
  margin-left: 0;
}

.documents-upload-form :deep(.documents-upload-button.app-button) {
  border: 1px solid #9ab0c6 !important;
  border-radius: 6px !important;
  background: linear-gradient(180deg, #f7f9fc 0%, #e3ebf3 100%) !important;
  color: #17324d !important;
  font-size: 8pt !important;
  line-height: 1.1 !important;
  padding: 2px 8px !important;
  min-height: 22px !important;
  height: 22px !important;
}

.documents-upload-form :deep(.documents-upload-button.app-button .v-btn__content) {
  color: #17324d !important;
  font-size: 8pt !important;
  line-height: 1.1 !important;
}

.documents-delete-btn {
  margin-left: 0;
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

.home-documents-table th.documents-title-cell,
.home-documents-table td.documents-title-cell {
  text-align: left;
}

.home-documents-table th.documents-actions-cell,
.home-documents-table td.documents-actions-cell {
  text-align: center;
  vertical-align: middle;
}

.home-documents-table thead th {
  background: #eaf2f8;
  color: #17324d;
}

.home-documents-table thead th.sortable-header {
  cursor: pointer;
  user-select: none;
}

.home-documents-table thead th.sortable-header:hover {
  background: #d4e5f0;
}

.home-documents-table tbody tr:nth-child(even) {
  background: #f8fbfd;
}

.documents-actions-cell {
  white-space: normal;
  display: flex;
  justify-content: center;
  align-items: center;
}

.documents-actions-stack {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  max-width: 100%;
}

.documents-title-cell,
.documents-file-cell {
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.home-documents-table :deep(.documents-link-btn.app-button.is-sm),
.home-documents-table :deep(.documents-delete-btn.app-button.is-sm) {
  font-size: 8pt;
  line-height: 1.15;
  padding: 4px 8px;
}

.documents-title-link {
  display: inline-flex;
  width: 100%;
  max-width: 100%;
  justify-content: flex-start;
  text-align: left;
  font-family: inherit !important;
  font-size: inherit !important;
  font-weight: 400;
  line-height: 1.2;
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
  max-width: 100%;
  color: var(--app-color-link) !important;
}

.documents-title-link :deep(.v-btn__content) {
  display: inline;
  width: 100%;
  font-family: inherit !important;
  font-size: inherit !important;
  font-weight: inherit;
  line-height: 1.2;
  white-space: normal !important;
  overflow-wrap: anywhere;
  word-break: break-word;
  text-align: left;
}

.documents-title-link:hover,
.documents-title-link:focus,
.documents-title-link:active {
  color: var(--app-color-link) !important;
}

.documents-empty-title-cell {
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
    width: 100%;
    max-width: 100%;
  }

  .documents-upload-fields {
    grid-template-columns: 1fr;
  }

  .documents-input {
    font-size: 8pt;
  }

  .documents-input[type="file"]::file-selector-button,
  .documents-input[type="file"]::-webkit-file-upload-button {
    font-size: 8pt;
    padding: 2px 5px;
  }

  .home-news-table th,
  .home-news-table td,
  .home-documents-table th,
  .home-documents-table td {
    font-size: 8pt;
  }

  .home-news-table :deep(.app-status-badge) {
    font-size: 6pt;
  }

  .home-news-table .app-status-badge,
  .home-documents-table :deep(.documents-link-btn.app-button.is-sm),
  .home-documents-table :deep(.documents-delete-btn.app-button.is-sm) {
    font-size: 8pt !important;
    padding: 2px 5px !important;
    line-height: 1.1;
    min-height: 20px !important;
    height: 20px !important;
  }

  .home-documents-table :deep(.documents-link-btn.app-button.is-sm .v-btn__content),
  .home-documents-table :deep(.documents-delete-btn.app-button.is-sm .v-btn__content) {
    font-size: 8pt !important;
    line-height: 1.1 !important;
  }

  .home-news-table :deep(.news-edit-btn.app-button.is-sm),
  .home-news-table :deep(.news-delete-btn.app-button.is-sm) {
    font-size: 8pt !important;
    padding: 2px 5px !important;
    line-height: 1.1;
    min-height: 20px !important;
    height: 20px !important;
  }

  .home-news-table :deep(.news-edit-btn.app-button.is-sm .v-btn__content),
  .home-news-table :deep(.news-delete-btn.app-button.is-sm .v-btn__content) {
    font-size: 8pt !important;
    line-height: 1.1 !important;
  }

  .home-news-table :deep(.news-action-btn.app-button),
  .home-documents-table :deep(.documents-action-btn.app-button) {
    border: 1px solid #9ab0c6 !important;
    border-radius: 6px !important;
    background: linear-gradient(180deg, #f7f9fc 0%, #e3ebf3 100%) !important;
    color: #17324d !important;
    font-size: 8pt !important;
    line-height: 1.1 !important;
    padding: 2px 6px !important;
    min-height: 20px !important;
    height: 20px !important;
  }

  .home-news-table :deep(.news-action-btn.app-button .v-btn__content),
  .home-documents-table :deep(.documents-action-btn.app-button .v-btn__content) {
    color: #17324d !important;
    font-size: 8pt !important;
    line-height: 1.1 !important;
  }

  .home-news-table :deep(.news-action-btn-delete.app-button),
  .home-documents-table :deep(.documents-action-btn-delete.app-button) {
    border-color: #c7a5ab !important;
    background: linear-gradient(180deg, #fff6f7 0%, #f6e4e7 100%) !important;
    color: #7a2633 !important;
  }

  .home-news-table :deep(.news-action-btn-delete.app-button .v-btn__content),
  .home-documents-table :deep(.documents-action-btn-delete.app-button .v-btn__content) {
    color: #7a2633 !important;
  }

  .news-admin-actions {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 4px;
  }

  .documents-actions-stack {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 4px;
  }
}
.access-error {
  margin-top: 18px;
  color: #b42318;
  font-weight: 600;
}
</style>
