<template>
  <div class="newsletters-container">
    <h2>Newsletters</h2>
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
      <button type="button" class="manage-templates-button" @click="openTemplateManager">
        Manage Templates
      </button>
      <button type="button" :disabled="newsletterFilterSelectBusy" @click="selectAllNewsletterFiltered">
        {{ newsletterFilterSelectBusy ? 'Selecting…' : 'Select All Filtered' }}
      </button>
      <button type="button" :disabled="!newsletterSelectedMemberIds.length" @click="clearNewsletterSelection">
        Clear Selection
      </button>
      <span>Filtered: {{ newsletterTotalMembers }}</span>
    </div>

    <!-- Template Manager Modal -->
    <div v-if="showTemplateManager" class="template-manager-modal">
      <div class="template-manager-content">
        <div class="template-manager-header">
          <h3>Manage Newsletter Templates</h3>
          <button type="button" class="close-button" @click="closeTemplateManager">×</button>
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
                  <button type="button" class="edit-button" @click="editTemplate(template)">
                    Edit
                  </button>
                  <button
                    type="button"
                    class="delete-button"
                    :disabled="template.id === 'club-update' || template.id === 'membership-reminder'"
                    @click="deleteTemplate(template.id)"
                  >
                    Delete
                  </button>
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
              <button type="submit" class="save-button">
                {{ templateEditingId ? 'Update Template' : 'Create Template' }}
              </button>
              <button type="button" class="cancel-button" @click="cancelTemplateEdit">
                Cancel
              </button>
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
          <th>
            ID
            <input
              v-model="newsletterColumnFilters.ID"
              @input="onNewsletterFilterChange"
              class="column-filter"
              placeholder="Filter"
            />
          </th>
          <th>
            Num
            <input
              v-model="newsletterColumnFilters.Number"
              @input="onNewsletterFilterChange"
              class="column-filter"
              placeholder="Filter"
            />
          </th>
          <th>
            Name
            <input
              v-model="newsletterColumnFilters.Members_Name"
              @input="onNewsletterFilterChange"
              class="column-filter"
              placeholder="Filter"
            />
          </th>
          <th>
            E-Mail
            <input
              v-model="newsletterColumnFilters.E_Mail"
              @input="onNewsletterFilterChange"
              class="column-filter"
              placeholder="Filter"
            />
          </th>
          <th>
            Membership Type
            <select
              v-model="newsletterColumnFilters.Member_Type"
              @change="onNewsletterFilterChange"
              class="column-filter"
            >
              <option value=""></option>
              <option value="Ordinary">Ordinary</option>
              <option value="Senior Citizen">Senior Citizen</option>
              <option value="Senior 75+">Senior 75+</option>
              <option value="Octagenarian">Octagenarian</option>
              <option value="Junior">Junior</option>
              <option value="Honorary">Honorary</option>
              <option value="Paused">Paused</option>
              <option value="Resigned">Resigned</option>
            </select>
          </th>
          <th>
            Paid Up?
            <input
              v-model="newsletterColumnFilters.Paid_Up_2026"
              @input="onNewsletterFilterChange"
              class="column-filter"
              placeholder="Filter"
            />
          </th>
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
          <td>{{ member.ID || member.id }}</td>
          <td>{{ member.Number }}</td>
          <td>{{ member.Members_Name }}</td>
          <td>
            <a v-if="member.E_Mail" :href="`mailto:${member.E_Mail}`">{{ member.E_Mail }}</a>
            <span v-else>-</span>
          </td>
          <td>{{ member.Member_Type }}</td>
          <td>{{ member.Paid_Up_2026 }}</td>
        </tr>
      </tbody>
    </table>

    <!-- Pagination -->
    <div class="pagination-controls">
      <button :disabled="newsletterCurrentPage === 1" @click="firstNewsletterPage">First Page</button>
      <button :disabled="newsletterCurrentPage === 1" @click="prevNewsletterPage">Previous Page</button>
      <span>Page {{ newsletterCurrentPage }} of {{ newsletterTotalPages }}&nbsp;</span>
      <button :disabled="newsletterCurrentPage === newsletterTotalPages" @click="nextNewsletterPage">Next Page</button>
      <button :disabled="newsletterCurrentPage === newsletterTotalPages" @click="lastNewsletterPage">Last Page</button>
      <select v-model.number="newsletterPageSize" @change="onNewsletterPageSizeChange" class="records-per-page-select">
        <option value="10">10 per page</option>
        <option value="25">25 per page</option>
        <option value="50">50 per page</option>
        <option value="100">100 per page</option>
      </select>
    </div>
    <div class="page-numbers">
      <button
        v-for="pageNum in newsletterVisiblePages"
        :key="`newsletter-page-${pageNum}`"
        :class="{ 'active': pageNum === newsletterCurrentPage }"
        @click="goToNewsletterPage(pageNum)"
      >
        {{ pageNum }}
      </button>
    </div>

    <!-- Send actions -->
    <div class="newsletter-actions">
      <button
        type="button"
        :disabled="!selectedNewsletterTemplateId || newsletterSendBusy"
        @click="sendNewsletterToAllMembers"
      >
        {{ newsletterSendBusy ? 'Sending…' : 'Send Newsletter to All' }}
      </button>
      <button
        type="button"
        :disabled="!newsletterSelectedMemberIds.length"
        @click="prepareNewsletterRecipients"
      >
        Prepare Selected for Email
      </button>
      <span>Selected: {{ newsletterSelectedMemberIds.length }}</span>
      <button
        type="button"
        :disabled="!selectedNewsletterTemplateId || !newsletterSelectedMemberIds.length || newsletterSendBusy"
        @click="sendNewsletterToSelectedMembers"
      >
        {{ newsletterSendBusy ? 'Sending…' : 'Send Newsletter to Selected' }}
      </button>
      <span v-if="clubSmtpFromEmail" class="newsletter-from-indicator">
        Sending from: <strong>{{ clubSmtpFromEmail }}</strong>
      </span>
      <span v-else class="newsletter-from-indicator newsletter-from-not-set">
        Sending address not configured
      </span>
    </div>

    <div v-if="newsletterPrepareMessage" class="newsletter-status">{{ newsletterPrepareMessage }}</div>
    <div v-if="newsletterPrepareError" class="newsletter-error">{{ newsletterPrepareError }}</div>
    <button type="button" @click="goHome">Back to Home</button>
  </div>
</template>

<script>
import axios from 'axios';
import { store, API_BASE_URL, memberIdentity } from '../store.js';

export default {
  name: 'Newsletters',
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
  },
  created() {
    this.init();
  },
  beforeUnmount() {
    if (this.newsletterFilterDebounceTimer) clearTimeout(this.newsletterFilterDebounceTimer);
  },
  methods: {
    memberIdentity,
    init() {
      this.newsletterCurrentPage = 1;
      this.newsletterPrepareMessage = '';
      this.newsletterPrepareError = '';
      this.fetchNewsletterTemplates();
      this.fetchNewsletterMembers();
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
            store.accessError = 'You do not have permission to access newsletters.';
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
