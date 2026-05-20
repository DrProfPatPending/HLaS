<template>
  <div class="newsletters-container">
    <h2>News and Updates</h2>
    <p>Post club news/updates and manage member newsletters from one page.</p>

    <section class="news-updates-post-section">
      <h3>Create News/Update Post</h3>
      <form class="news-updates-post-form" @submit.prevent="createNewsUpdatePost">
        <div class="news-updates-post-top-row">
          <label>
            <span>Date *</span>
            <input v-model="newsPostForm.date" type="date" required :disabled="isNewsUpdatesFieldReadOnly('Date')" />
          </label>
          <label>
            <span>Category</span>
            <input v-model="newsPostForm.category" type="text" maxlength="80" placeholder="e.g. Club Notice" :disabled="isNewsUpdatesFieldReadOnly('Category')" />
          </label>
          <label>
            <span>Status</span>
            <select v-model="newsPostForm.status" :disabled="isNewsUpdatesFieldReadOnly('Status')">
              <option value="Published">Published</option>
              <option value="Draft">Draft</option>
              <option value="Planned">Planned</option>
              <option value="Archived">Archived</option>
            </select>
          </label>
        </div>
        <label class="news-updates-post-message-field">
          <span>Update *</span>
          <textarea
            v-model="newsPostForm.update"
            rows="3"
            maxlength="500"
            placeholder="Write the update to display on the Home page table"
            required
            :disabled="isNewsUpdatesFieldReadOnly('Update')"
          ></textarea>
        </label>
        <div class="news-updates-post-actions">
          <app-button type="submit" :disabled="newsPostBusy || isNewsUpdatesCreateReadOnly" inherit-style>
            {{ newsPostBusy ? 'Posting…' : 'Post Update' }}
          </app-button>
          <app-button type="button" :disabled="newsPostBusy" inherit-style @click="fetchNewsUpdates">Refresh Posts</app-button>
        </div>
      </form>
      <p v-if="newsPostStatus" class="newsletter-status">{{ newsPostStatus }}</p>
      <p v-if="newsPostError" class="newsletter-error">{{ newsPostError }}</p>
    </section>

    <section class="news-updates-list-section">
      <h3>Current Club Posts</h3>
      <table class="newsletter-table">
        <thead>
          <tr>
            <th :style="getColumnStyle('news_updates', 'Date')">Date</th>
            <th :style="getColumnStyle('news_updates', 'Category')">Category</th>
            <th :style="getColumnStyle('news_updates', 'Update')">Update</th>
            <th :style="getColumnStyle('news_updates', 'Status')">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="newsUpdatesLoading">
            <td colspan="4">Loading posts...</td>
          </tr>
          <tr v-else-if="!newsUpdates.length">
            <td colspan="4">No posts yet.</td>
          </tr>
          <tr v-else v-for="post in newsUpdates" :key="post.id">
            <td :style="getColumnStyle('news_updates', 'Date')">{{ formatNewsDate(post.date) }}</td>
            <td :style="getColumnStyle('news_updates', 'Category')">{{ post.category }}</td>
            <td :style="getColumnStyle('news_updates', 'Update')">{{ post.update }}</td>
            <td :style="getColumnStyle('news_updates', 'Status')">{{ post.status }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <h3>Newsletter Distribution</h3>
    <p>Filter members, build a selected list, choose a template, and send club newsletters.</p>
    <div class="newsletter-actions newsletter-toolbar">
      <label class="newsletter-template-label" for="newsletter-template-select">Template</label>
      <select
        id="newsletter-template-select"
        v-model="selectedNewsletterTemplateId"
        class="newsletter-template-select"
      >
        <option value="">Select template</option>
        <option
          v-for="template in newsletterTemplates"
          :key="`newsletter-template-${template.id}`"
          :value="template.id"
        >
          {{ template.name }}
        </option>
      </select>
      <app-button type="button" class="manage-templates-button" inherit-style @click="openTemplateManager">
        Manage Templates
      </app-button>
      <app-button type="button" :disabled="newsletterFilterSelectBusy" inherit-style @click="selectAllNewsletterFiltered">
        {{ newsletterFilterSelectBusy ? 'Selecting…' : 'Select All Filtered' }}
      </app-button>
      <app-button type="button" :disabled="!newsletterSelectedMemberIds.length" inherit-style @click="clearNewsletterSelection">
        Clear Selection
      </app-button>
      <span>Filtered: {{ newsletterTotalMembers }}</span>
    </div>

    <!-- Template Manager Modal -->
    <div v-if="showTemplateManager" class="template-manager-modal">
      <div class="template-manager-content">
        <div class="template-manager-header">
          <h3>Manage Newsletter Templates</h3>
          <app-button type="button" class="close-button" inherit-style @click="closeTemplateManager">×</app-button>
        </div>
        <div class="template-list-section">
          <h4>Existing Templates</h4>
          <div v-if="templateEditError" class="error-message">{{ templateEditError }}</div>
          <div class="template-list">
            <div
              v-for="template in newsletterTemplates"
              :key="template.id"
              class="template-item"
            >
              <div class="template-item-header">
                <span class="template-item-name">{{ template.name }}</span>
                <div class="template-item-actions">
                  <app-button type="button" class="edit-button" inherit-style @click="editTemplate(template)">
                    Edit
                  </app-button>
                  <app-button
                    type="button"
                    class="delete-button"
                    inherit-style
                    :disabled="template.id === 'club-update' || template.id === 'membership-reminder'"
                    @click="deleteTemplate(template.id)"
                  >
                    Delete
                  </app-button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="template-edit-section">
          <h4>{{ templateEditingId ? 'Edit Template' : 'Create New Template' }}</h4>
          <form @submit.prevent="saveTemplate">
            <div v-if="templateCreateError" class="error-message">{{ templateCreateError }}</div>
            <div class="form-group">
              <label for="template-id-input">Template ID:</label>
              <input
                id="template-id-input"
                v-model="templateEditingData.id"
                type="text"
                placeholder="e.g., special-event (lowercase letters, numbers, hyphens)"
                :disabled="templateEditingId !== null"
                required
              />
            </div>
            <div class="form-group">
              <label for="template-name-input">Template Name:</label>
              <input
                id="template-name-input"
                v-model="templateEditingData.name"
                type="text"
                placeholder="e.g., Special Event"
                required
              />
            </div>
            <div class="form-group">
              <label for="template-subject-input">Subject:</label>
              <input
                id="template-subject-input"
                v-model="templateEditingData.subject"
                type="text"
                placeholder="e.g., <Club> Special Event"
                required
              />
            </div>
            <div class="form-group">
              <label for="template-body-input">Body:</label>
              <textarea
                id="template-body-input"
                v-model="templateEditingData.body"
                placeholder="Use tags like <Club>, <Title>, <Last_Name>, <Number>, etc."
                rows="8"
                required
              ></textarea>
            </div>
            <div v-if="newsletterAvailableTags.length" class="available-tags-info">
              <strong>Available tags:</strong>
              <span
                v-for="tag in newsletterAvailableTags"
                :key="tag.tag"
                class="tag-chip"
                :title="tag.description"
              >&lt;{{ tag.tag }}&gt;</span>
            </div>
            <div class="template-form-actions">
              <app-button type="submit" class="save-button" inherit-style>
                {{ templateEditingId ? 'Update Template' : 'Create Template' }}
              </app-button>
              <app-button type="button" class="cancel-button" inherit-style @click="cancelTemplateEdit">
                Cancel
              </app-button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Template Preview -->
    <div v-if="selectedNewsletterTemplate" class="newsletter-template-preview">
      <h3>Template Preview <span class="newsletter-preview-note">(sample values shown)</span></h3>
      <p><strong>Subject:</strong> {{ selectedNewsletterTemplate.previewSubject }}</p>
      <pre class="newsletter-template-preview-body">{{ selectedNewsletterTemplate.previewBody }}</pre>
      <div v-if="newsletterAvailableTags.length" class="newsletter-template-tags-hint">
        <strong>Available tags:</strong>
        <span
          v-for="tag in newsletterAvailableTags"
          :key="tag.tag"
          class="newsletter-tag-chip"
          :title="tag.description"
        >&lt;{{ tag.tag }}&gt;</span>
      </div>
    </div>

    <!-- Member Table -->
    <table class="newsletter-table">
      <thead>
        <tr>
          <th>
            Select
            <input
              type="checkbox"
              :checked="allNewsletterPageSelected"
              @change="toggleSelectAllNewsletterOnPage"
            />
          </th>
          <th v-for="field in orderedNewsletterFields" :key="field">{{ field }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="member in newsletterMembers" :key="`newsletter-${memberIdentity(member)}`">
          <td>
            <input
              type="checkbox"
              :value="String(memberIdentity(member))"
              v-model="newsletterSelectedMemberIds"
            />
          </td>
          <td v-for="field in orderedNewsletterFields" :key="field">
            <span v-if="field === 'E_Mail' && member[field]">
              <a :href="`mailto:${member[field]}`">{{ member[field] }}</a>
            </span>
            <span v-else>{{ member[field] }}</span>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Pagination -->
    <div class="pagination-controls">
      <app-button :disabled="newsletterCurrentPage === 1" inherit-style @click="firstNewsletterPage">First Page</app-button>
      <app-button :disabled="newsletterCurrentPage === 1" inherit-style @click="prevNewsletterPage">Previous Page</app-button>
      <span>Page {{ newsletterCurrentPage }} of {{ newsletterTotalPages }}&nbsp;</span>
      <app-button :disabled="newsletterCurrentPage === newsletterTotalPages" inherit-style @click="nextNewsletterPage">Next Page</app-button>
      <app-button :disabled="newsletterCurrentPage === newsletterTotalPages" inherit-style @click="lastNewsletterPage">Last Page</app-button>
      <select v-model.number="newsletterPageSize" @change="onNewsletterPageSizeChange" class="records-per-page-select">
        <option value="10">10 per page</option>
        <option value="25">25 per page</option>
        <option value="50">50 per page</option>
        <option value="100">100 per page</option>
      </select>
    </div>
    <div class="page-numbers">
      <app-button
        v-for="pageNum in newsletterVisiblePages"
        :key="`newsletter-page-${pageNum}`"
        type="button"
        inherit-style
        :class="{ 'active': pageNum === newsletterCurrentPage }"
        @click="goToNewsletterPage(pageNum)"
      >
        {{ pageNum }}
      </app-button>
    </div>

    <!-- Send actions -->
    <div class="newsletter-actions">
      <app-button
        type="button"
        inherit-style
        :disabled="!selectedNewsletterTemplateId || newsletterSendBusy"
        @click="sendNewsletterToAllMembers"
      >
        {{ newsletterSendBusy ? 'Sending…' : 'Send Newsletter to All' }}
      </app-button>
      <app-button
        type="button"
        inherit-style
        :disabled="!newsletterSelectedMemberIds.length"
        @click="prepareNewsletterRecipients"
      >
        Prepare Selected for Email
      </app-button>
      <span>Selected: {{ newsletterSelectedMemberIds.length }}</span>
      <app-button
        type="button"
        inherit-style
        :disabled="!selectedNewsletterTemplateId || !newsletterSelectedMemberIds.length || newsletterSendBusy"
        @click="sendNewsletterToSelectedMembers"
      >
        {{ newsletterSendBusy ? 'Sending…' : 'Send Newsletter to Selected' }}
      </app-button>
      <span v-if="clubSmtpFromEmail" class="newsletter-from-indicator">
        Sending from: <strong>{{ clubSmtpFromEmail }}</strong>
      </span>
      <span v-else class="newsletter-from-indicator newsletter-from-not-set">
        Sending address not configured
      </span>
    </div>

    <div v-if="newsletterPrepareMessage" class="newsletter-status">{{ newsletterPrepareMessage }}</div>
    <div v-if="newsletterPrepareError" class="newsletter-error">{{ newsletterPrepareError }}</div>
  </div>
</template>

<script>
import axios from 'axios';
import { store, API_BASE_URL, memberIdentity, formatConfiguredDate } from '../store.js';
import { fieldOrderConfig, loadFieldOrderConfig } from '../store.js';
import AppButton from './ui/AppButton.vue';

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

export default {
  name: 'Newsletters',
  components: {
    AppButton,
  },
  data() {
    return {
      newsletterMembers: [],
      newsletterTotalMembers: 0,
      newsletterCurrentPage: 1,
      newsletterPageSize: 10,
      newsletterSelectedMemberIds: [],
      newsletterTemplates: [],
      newsletterAvailableTags: [],
      selectedNewsletterTemplateId: '',
      clubSmtpFromEmail: '',
      clubSmtpFromName: '',
      newsletterFilterSelectBusy: false,
      newsletterSendBusy: false,
      newsletterPrepareMessage: '',
      newsletterPrepareError: '',
      showTemplateManager: false,
      templateEditingId: null,
      templateEditingData: { id: '', name: '', subject: '', body: '' },
      templateCreateError: '',
      templateEditError: '',
      newsletterFilterDebounceTimer: null,
      filterDebounceMs: 250,
      newsletterColumnFilters: {
        ID: '',
        Number: '',
        Members_Name: '',
        E_Mail: '',
        Member_Type: '',
        Paid_Up_2026: '',
      },
      newsUpdates: [],
      newsUpdatesLoading: false,
      newsPostBusy: false,
      newsPostStatus: '',
      newsPostError: '',
      newsPostForm: {
        date: todayIsoDate(),
        category: '',
        update: '',
        status: 'Published',
      },
    };
  },
  computed: {
    newsletterTotalPages() {
      return Math.max(1, Math.ceil(this.newsletterTotalMembers / this.newsletterPageSize));
    },
    newsletterVisiblePages() {
      const current = this.newsletterCurrentPage;
      const total = this.newsletterTotalPages;
      const pageCount = 5;
      let start, end;
      if (current <= 3) {
        start = 1;
        end = Math.min(pageCount, total);
      } else {
        start = current - 2;
        end = current + 2;
        if (end > total) {
          end = total;
          start = Math.max(1, end - pageCount + 1);
        }
      }
      const pages = [];
      for (let i = start; i <= end; i++) pages.push(i);
      return pages;
    },
    selectedNewsletterTemplate() {
      return (
        this.newsletterTemplates.find(t => t.id === this.selectedNewsletterTemplateId) || null
      );
    },
    allNewsletterPageSelected() {
      if (!this.newsletterMembers.length) return false;
      const selectedIds = new Set(this.newsletterSelectedMemberIds.map(id => String(id)));
      return this.newsletterMembers.every(member =>
        selectedIds.has(String(memberIdentity(member)))
      );
    },
    orderedNewsletterFields() {
      if (fieldOrderConfig.loaded && fieldOrderConfig.order['membership_admin']) {
        const sample = this.newsletterMembers[0] || {};
        return fieldOrderConfig.order['membership_admin'].filter(f => f in sample);
      }
      const sample = this.newsletterMembers[0] || {};
      return Object.keys(sample);
    },
    newsUpdatesMinimumWidths() {
      const configured = fieldOrderConfig.order?.minimum_widths?.news_updates;
      return configured && typeof configured === 'object' ? configured : {};
    },
    newsUpdatesWidths() {
      const configured = fieldOrderConfig.order?.widths?.news_updates;
      return configured && typeof configured === 'object' ? configured : {};
    },
    hasAdminRole() {
      const normalizedRoles = (Array.isArray(store.memberRoles) ? store.memberRoles : [])
        .map(role => String(role || '').toLowerCase().replace(/[^a-z0-9]/g, ''));
      return normalizedRoles.includes('clubadmin')
        || normalizedRoles.includes('appadmin')
        || normalizedRoles.includes('appowner');
    },
    newsUpdatesReadOnlyColumns() {
      const configured = fieldOrderConfig.order?.read_only?.news_updates;
      return configured && typeof configured === 'object' ? configured : {};
    },
    isNewsUpdatesCreateReadOnly() {
      return this.isNewsUpdatesFieldReadOnly('Date')
        || this.isNewsUpdatesFieldReadOnly('Category')
        || this.isNewsUpdatesFieldReadOnly('Update')
        || this.isNewsUpdatesFieldReadOnly('Status');
    },
  },
  created() {
    loadFieldOrderConfig();
    this.init();
    this.fetchNewsUpdates();
  },
  beforeUnmount() {
    if (this.newsletterFilterDebounceTimer) clearTimeout(this.newsletterFilterDebounceTimer);
  },
  methods: {
    memberIdentity,
    isNewsUpdatesFieldReadOnly(fieldName) {
      if (this.hasAdminRole) {
        return false;
      }
      return this.newsUpdatesReadOnlyColumns?.[fieldName] === true;
    },
    init() {
      this.newsletterCurrentPage = 1;
      this.newsletterPrepareMessage = '';
      this.newsletterPrepareError = '';
      this.fetchNewsletterTemplates();
      this.fetchNewsletterMembers();
    },
    formatNewsDate(value) {
      const formatted = formatConfiguredDate(value, 'Date');
      return formatted || value;
    },
    getColumnStyle(contextKey, columnKey) {
      // First check if a width is specified in the widths configuration
      const configuredWidth = this.newsUpdatesWidths?.[columnKey];
      if (configuredWidth) {
        const widthStr = String(configuredWidth).trim().toLowerCase();
        
        // Handle 'flex' - return empty and let CSS handle it
        if (widthStr === 'flex' || widthStr === 'auto') {
          return {};
        }
        
        // Return the width value directly (e.g., '80px', '50%')
        return { width: widthStr };
      }
      
      // Fall back to minimum_widths if width is not specified
      const rawMinWidth = this.newsUpdatesMinimumWidths?.[columnKey];
      const minWidth = Number(rawMinWidth);
      if (!Number.isFinite(minWidth) || minWidth <= 0) return {};
      return { minWidth: `${minWidth}px` };
    },
    fetchNewsUpdates() {
      this.newsUpdatesLoading = true;
      this.newsPostError = '';
      return axios
        .get(`${API_BASE_URL}/news-updates`, {
          params: { club: store.loggedInClub, limit: 50 },
        })
        .then((res) => {
          this.newsUpdates = Array.isArray(res?.data?.updates) ? res.data.updates : [];
        })
        .catch((err) => {
          this.newsUpdates = [];
          this.newsPostError = err?.response?.data?.error || 'Failed to load news/updates posts.';
        })
        .finally(() => {
          this.newsUpdatesLoading = false;
        });
    },
    createNewsUpdatePost() {
      this.newsPostStatus = '';
      this.newsPostError = '';

      if (this.isNewsUpdatesCreateReadOnly) {
        this.newsPostError = 'News update fields are read-only for your role.';
        return;
      }

      const payload = {
        club: store.loggedInClub,
        date: this.newsPostForm.date,
        category: String(this.newsPostForm.category || '').trim(),
        update: String(this.newsPostForm.update || '').trim(),
        status: String(this.newsPostForm.status || 'Published').trim(),
      };

      if (!payload.date) {
        this.newsPostError = 'Date is required.';
        return;
      }
      if (!payload.update) {
        this.newsPostError = 'Update is required.';
        return;
      }

      this.newsPostBusy = true;
      return axios
        .post(`${API_BASE_URL}/news-updates`, payload)
        .then(() => {
          this.newsPostStatus = 'News/update post created.';
          this.newsPostForm.update = '';
          this.fetchNewsUpdates();
        })
        .catch((err) => {
          this.newsPostError = err?.response?.data?.error || 'Failed to create post.';
        })
        .finally(() => {
          this.newsPostBusy = false;
        });
    },
    goHome() {
      store.activeSection = 'home';
    },
    buildNewsletterActiveFilters() {
      return Object.fromEntries(
        Object.entries(this.newsletterColumnFilters)
          .filter(([, v]) => v && v.trim() !== '')
          .map(([key, v]) => {
            const trimmed = v.trim();
            if (trimmed === '[BLANK]') return [key, '[BLANK]'];
            const hasWildcard = trimmed.includes('*') || trimmed.includes('?');
            return [key, hasWildcard ? trimmed : `*${trimmed}*`];
          })
      );
    },
    fetchNewsletterMembers() {
      const offset = (this.newsletterCurrentPage - 1) * this.newsletterPageSize;
      axios
        .get(`${API_BASE_URL}/members`, {
          params: {
            club: store.loggedInClub,
            limit: this.newsletterPageSize,
            offset,
            ...this.buildNewsletterActiveFilters(),
          },
        })
        .then(res => {
          this.newsletterMembers = res.data.members || [];
          this.newsletterTotalMembers = res.data.total || 0;
        })
        .catch(err => {
          if (err.response?.status === 403) {
            this.newsletterMembers = [];
            this.newsletterTotalMembers = 0;
            store.accessError = 'You do not have permission to access news and updates.';
            store.activeSection = 'home';
          }
        });
    },
    fetchNewsletterTemplates() {
      axios
        .get(`${API_BASE_URL}/newsletter/templates`, {
          params: { club: store.loggedInClub },
        })
        .then(res => {
          const templates = Array.isArray(res.data && res.data.templates)
            ? res.data.templates
            : [];
          this.newsletterTemplates = templates
            .filter(t => t && t.id)
            .map(t => ({
              id: String(t.id),
              name: t.name || String(t.id),
              subjectTemplate: t.subjectTemplate || '',
              bodyTemplate: t.bodyTemplate || '',
              previewSubject: t.previewSubject || t.subjectTemplate || '',
              previewBody: t.previewBody || t.bodyTemplate || '',
            }));
          this.newsletterAvailableTags = Array.isArray(res.data && res.data.availableTags)
            ? res.data.availableTags
            : [];
          if (!this.selectedNewsletterTemplateId && this.newsletterTemplates.length) {
            this.selectedNewsletterTemplateId = this.newsletterTemplates[0].id;
          }
          this.clubSmtpFromEmail = res.data.smtpFromEmail || '';
          this.clubSmtpFromName = res.data.smtpFromName || '';
        })
        .catch(() => {
          this.newsletterTemplates = [];
          this.newsletterAvailableTags = [];
          this.clubSmtpFromEmail = '';
          this.clubSmtpFromName = '';
        });
    },
    onNewsletterFilterChange() {
      this.newsletterCurrentPage = 1;
      if (this.newsletterFilterDebounceTimer) clearTimeout(this.newsletterFilterDebounceTimer);
      this.newsletterFilterDebounceTimer = setTimeout(
        () => this.fetchNewsletterMembers(),
        this.filterDebounceMs
      );
    },
    nextNewsletterPage() {
      if (this.newsletterCurrentPage < this.newsletterTotalPages) {
        this.newsletterCurrentPage++;
        this.fetchNewsletterMembers();
      }
    },
    prevNewsletterPage() {
      if (this.newsletterCurrentPage > 1) {
        this.newsletterCurrentPage--;
        this.fetchNewsletterMembers();
      }
    },
    firstNewsletterPage() { this.newsletterCurrentPage = 1; this.fetchNewsletterMembers(); },
    lastNewsletterPage() { this.newsletterCurrentPage = this.newsletterTotalPages; this.fetchNewsletterMembers(); },
    goToNewsletterPage(pageNum) { this.newsletterCurrentPage = pageNum; this.fetchNewsletterMembers(); },
    onNewsletterPageSizeChange() { this.newsletterCurrentPage = 1; this.fetchNewsletterMembers(); },
    toggleSelectAllNewsletterOnPage(event) {
      const isChecked = event.target.checked;
      const pageIds = this.newsletterMembers
        .map(m => memberIdentity(m))
        .filter(id => id != null)
        .map(id => String(id));
      if (isChecked) {
        const merged = new Set(this.newsletterSelectedMemberIds);
        pageIds.forEach(id => merged.add(id));
        this.newsletterSelectedMemberIds = Array.from(merged);
      } else {
        const pageIdSet = new Set(pageIds);
        this.newsletterSelectedMemberIds = this.newsletterSelectedMemberIds.filter(
          id => !pageIdSet.has(id)
        );
      }
    },
    selectAllNewsletterFiltered() {
      this.newsletterPrepareMessage = '';
      this.newsletterPrepareError = '';
      this.newsletterFilterSelectBusy = true;
      axios
        .post(`${API_BASE_URL}/newsletter/filtered_member_ids`, {
          club: store.loggedInClub,
          filters: this.newsletterColumnFilters,
        })
        .then(res => {
          const filteredIds = Array.isArray(res.data && res.data.memberIds)
            ? res.data.memberIds.map(id => String(id)).filter(Boolean)
            : [];
          const merged = new Set(this.newsletterSelectedMemberIds);
          filteredIds.forEach(id => merged.add(id));
          this.newsletterSelectedMemberIds = Array.from(merged);
          this.newsletterPrepareMessage = `Selected ${filteredIds.length} members from current filtered results.`;
        })
        .catch(err => {
          this.newsletterPrepareError =
            err.response?.data?.error || 'Failed to select filtered members';
        })
        .finally(() => {
          this.newsletterFilterSelectBusy = false;
        });
    },
    clearNewsletterSelection() {
      this.newsletterSelectedMemberIds = [];
      this.newsletterPrepareMessage = '';
      this.newsletterPrepareError = '';
    },
    prepareNewsletterRecipients() {
      this.newsletterPrepareMessage = '';
      this.newsletterPrepareError = '';
      axios
        .post(`${API_BASE_URL}/newsletter/prepare_recipients`, {
          club: store.loggedInClub,
          memberIds: this.newsletterSelectedMemberIds,
        })
        .then(res => {
          const summary = res.data || {};
          this.newsletterPrepareMessage = `Prepared ${summary.emailableCount || 0} emailable recipients from ${summary.selectedCount || 0} selected members.`;
        })
        .catch(err => {
          this.newsletterPrepareError = err.response?.data?.error || 'Failed to prepare newsletter recipients';
        });
    },
    sendNewsletterToAllMembers() {
      this.newsletterPrepareMessage = '';
      this.newsletterPrepareError = '';
      if (!this.selectedNewsletterTemplateId) {
        this.newsletterPrepareError = 'Please select a newsletter template.';
        return;
      }
      this.newsletterSendBusy = true;
      axios
        .post(`${API_BASE_URL}/newsletter/send`, {
          club: store.loggedInClub,
          templateId: this.selectedNewsletterTemplateId,
          scope: 'all_club',
        })
        .then(res => {
          const summary = res.data || {};
          this.newsletterPrepareMessage = `Sent ${summary.sentCount || 0} emails to ${summary.emailableCount || 0} emailable members in ${store.loggedInClub}.`;
        })
        .catch(err => {
          this.newsletterPrepareError = err.response?.data?.error || 'Failed to send newsletter to all members';
        })
        .finally(() => { this.newsletterSendBusy = false; });
    },
    sendNewsletterToSelectedMembers() {
      this.newsletterPrepareMessage = '';
      this.newsletterPrepareError = '';
      if (!this.selectedNewsletterTemplateId) {
        this.newsletterPrepareError = 'Please select a newsletter template.';
        return;
      }
      if (!this.newsletterSelectedMemberIds.length) {
        this.newsletterPrepareError = 'Please select at least one member.';
        return;
      }
      this.newsletterSendBusy = true;
      axios
        .post(`${API_BASE_URL}/newsletter/send`, {
          club: store.loggedInClub,
          templateId: this.selectedNewsletterTemplateId,
          scope: 'selected',
          memberIds: this.newsletterSelectedMemberIds,
        })
        .then(res => {
          const summary = res.data || {};
          this.newsletterPrepareMessage = `Sent ${summary.sentCount || 0} emails to ${summary.emailableCount || 0} selected emailable members.`;
        })
        .catch(err => {
          this.newsletterPrepareError = err.response?.data?.error || 'Failed to send newsletter to selected members';
        })
        .finally(() => { this.newsletterSendBusy = false; });
    },
    openTemplateManager() {
      this.showTemplateManager = true;
      this.templateEditingId = null;
      this.templateEditingData = { id: '', name: '', subject: '', body: '' };
      this.templateCreateError = '';
      this.templateEditError = '';
    },
    closeTemplateManager() {
      this.showTemplateManager = false;
      this.cancelTemplateEdit();
    },
    editTemplate(template) {
      this.templateEditingId = template.id;
      this.templateEditingData = {
        id: template.id,
        name: template.name,
        subject: template.subjectTemplate,
        body: template.bodyTemplate,
      };
      this.templateCreateError = '';
      this.templateEditError = '';
    },
    cancelTemplateEdit() {
      this.templateEditingId = null;
      this.templateEditingData = { id: '', name: '', subject: '', body: '' };
      this.templateCreateError = '';
      this.templateEditError = '';
    },
    saveTemplate() {
      const { id, name, subject, body } = this.templateEditingData;
      if (!id || !name || !subject || !body) {
        this.templateCreateError = 'All fields are required';
        return;
      }
      if (this.templateEditingId) {
        axios
          .put(`${API_BASE_URL}/newsletter/templates/${this.templateEditingId}`, {
            club: store.loggedInClub,
            name,
            subject,
            body,
          })
          .then(() => { this.fetchNewsletterTemplates(); this.cancelTemplateEdit(); })
          .catch(err => {
            this.templateEditError = err.response?.data?.error || 'Failed to update template';
          });
      } else {
        axios
          .post(`${API_BASE_URL}/newsletter/templates`, {
            club: store.loggedInClub,
            id,
            name,
            subject,
            body,
          })
          .then(() => { this.fetchNewsletterTemplates(); this.cancelTemplateEdit(); })
          .catch(err => {
            this.templateCreateError = err.response?.data?.error || 'Failed to create template';
          });
      }
    },
    deleteTemplate(templateId) {
      if (templateId === 'club-update' || templateId === 'membership-reminder') {
        alert('Cannot delete default templates');
        return;
      }
      if (!confirm(`Delete template "${templateId}"?`)) return;
      axios
        .delete(`${API_BASE_URL}/newsletter/templates/${templateId}`, {
          params: { club: store.loggedInClub },
        })
        .then(() => this.fetchNewsletterTemplates())
        .catch(err => {
          this.templateEditError = err.response?.data?.error || 'Failed to delete template';
        });
    },
  },
};
</script>

<style scoped>
.news-updates-post-section,
.news-updates-list-section {
  margin: 0 0 16px;
  padding: 12px;
  border: 1px solid #d7dce2;
  border-radius: 10px;
  background: #fff;
}

.news-updates-post-section h3,
.news-updates-list-section h3 {
  margin: 0 0 10px;
  color: #17324d;
}

.news-updates-post-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.news-updates-post-top-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  align-items: start;
}

.news-updates-post-form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 0;
}

.news-updates-post-form label span {
  font-size: 9.5pt;
  font-weight: 600;
  color: #1f2937;
}

.news-updates-post-form input,
.news-updates-post-form select,
.news-updates-post-form textarea {
  width: 100%;
  box-sizing: border-box;
  margin-right: 0;
  padding: 9px 10px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
  line-height: 1.35;
  background: #fff;
  color: #111827;
}

.news-updates-post-form textarea {
  min-height: 88px;
  resize: vertical;
}

.news-updates-post-message-field {
  width: 100%;
}

.news-updates-post-actions {
  display: flex;
  gap: 8px;
  margin-top: 2px;
}

@media (max-width: 900px) {
  .news-updates-post-top-row {
    grid-template-columns: 1fr;
  }
}
</style>
