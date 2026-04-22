<template>
  <div class="membership-admin-container">
    <div class="membership-admin-header">
      <h1>{{ loggedInClub }} Members</h1>
      <div class="membership-export-controls">
        <label for="member-export-format" class="membership-export-label">Export as</label>
        <select id="member-export-format" v-model="exportFormat">
          <option value="csv">CSV</option>
          <option value="json">JSON</option>
        </select>
        <app-button type="button" :disabled="exportBusy" @click="exportMembers" inherit-style>
          {{ exportBusy ? 'Exporting…' : exportButtonLabel }}
        </app-button>
      </div>
    </div>
    <div v-if="exportError" class="membership-export-error">{{ exportError }}</div>
    <div v-if="orderedMemberFields.length" class="membership-table-scroll" aria-label="Membership table horizontal scroll region">
      <table class="member-table">
        <thead>
          <tr>
            <th v-for="field in orderedMemberFields" :key="field">
              <div>
                <span>{{ getFieldDisplayName(field) }}</span>
                <span
                  class="sort-arrow"
                  :class="{ active: sortKey === field && sortOrder === 'asc' }"
                  @click="setSort(field, 'asc')"
                >
                  ▲
                </span>
                <span
                  class="sort-arrow"
                  :class="{ active: sortKey === field && sortOrder === 'desc' }"
                  @click="setSort(field, 'desc')"
                >
                  ▼
                </span>
              </div>
              <input
                v-model="columnFilters[field]"
                class="column-filter"
                type="text"
                :placeholder="`Filter ${getFieldDisplayName(field)}`"
                @input="onFilterChange"
              />
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="member in members" :key="member.id || member.ID || member.Number">
            <td v-for="field in orderedMemberFields" :key="field">
              <span v-if="field === 'Members_Name' && member[field]">
                <a href="#" class="member-link" @click.prevent="openMemberEdit(member)">
                  {{ member[field] }}
                </a>
              </span>
              <span v-else-if="field === 'Number' && member[field]">
                <a href="#" class="member-link" @click.prevent="lookupMemberByNumber(member[field])">
                  {{ member[field] }}
                </a>
              </span>
              <span v-else-if="field === 'E_Mail' && member[field]">
                <a :href="`mailto:${member[field]}`">{{ member[field] }}</a>
              </span>
              <span v-else :style="getMemberFieldStyle(field, member[field])">
                {{ formatMemberFieldValue(field, member[field]) }}
              </span>
            </td>
          </tr>
          <tr v-if="!members.length">
            <td :colspan="orderedMemberFields.length" class="membership-empty-state">
              No members found.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="membership-no-columns">No member columns configured.</div>
    <div class="pagination-controls">
      <app-button :disabled="currentPage === 1" @click="firstPage" inherit-style>First Page</app-button>
      <app-button :disabled="currentPage === 1" @click="prevPage" inherit-style>Previous Page</app-button>
      <span>Page {{ currentPage }} of {{ totalPages }}&nbsp;</span>
      <app-button :disabled="currentPage === totalPages" @click="nextPage" inherit-style>Next Page</app-button>
      <app-button :disabled="currentPage === totalPages" @click="lastPage" inherit-style>Last Page</app-button>
      <select v-model.number="pageSize" @change="onPageSizeChange" class="records-per-page-select">
        <option value="10">10 per page</option>
        <option value="25">25 per page</option>
        <option value="50">50 per page</option>
        <option value="100">100 per page</option>
      </select>
    </div>
    <div class="page-numbers">
      <app-button
        v-for="pageNum in visiblePages"
        :key="pageNum"
        type="button"
        inherit-style
        :class="{ 'active': pageNum === currentPage }"
        @click="goToPage(pageNum)"
      >
        {{ pageNum }}
      </app-button>
    </div>
    <hr />
    <div v-if="showMembershipDetails">
      <div class="membership-details-header">
        <h2>Membership Details</h2>
        <app-button v-if="lookupResult && !lookupError" type="button" @click="hideLookupDetails" inherit-style>
          Hide Details
        </app-button>
      </div>
      <form @submit.prevent="lookupMember">
        <input v-model="lookupNumber" placeholder="Membership Number" required />
        <app-button type="submit" inherit-style>Lookup</app-button>
      </form>
      <div v-if="lookupError" class="membership-lookup-error">{{ lookupError }}</div>
      <table v-if="lookupResult" class="lookup-table">
        <thead>
          <tr>
            <th>Field</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(value, key) in lookupResult" :key="key">
            <td>{{ key }}</td>
            <td>{{ formatMemberFieldValue(key, value) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import AppButton from './ui/AppButton.vue';
import {
  API_BASE_URL,
  store,
  totalPages,
  visiblePages,
  setSort,
  onFilterChange,
  nextPage,
  prevPage,
  firstPage,
  lastPage,
  fieldOrderConfig,
  loadFieldOrderConfig,
  onPageSizeChange,
  goToPage,
  lookupMember,
  lookupMemberByNumber,
  hideLookupDetails,
  openMemberForEdit,
  formatConfiguredDate,
  getExpiryDateStyle,
  isDateOfBirthField,
  normalizeDateInputValue,
} from '../store.js';

export default {
  name: 'MembershipAdmin',
  components: {
    AppButton,
  },
  data() {
    return {
      exportFormat: 'csv',
      exportBusy: false,
      exportError: '',
    };
  },
  created() {
    loadFieldOrderConfig();
  },
  computed: {
    loggedInClub: () => store.loggedInClub,
    members: () => store.members,
    currentPage: {
      get: () => store.currentPage,
      set: v => { store.currentPage = v; },
    },
    pageSize: {
      get: () => store.pageSize,
      set: v => { store.pageSize = v; },
    },
    totalPages: () => totalPages.value,
    visiblePages: () => visiblePages.value,
    columnFilters: () => store.columnFilters,
    sortKey: () => store.sortKey,
    sortOrder: () => store.sortOrder,
    showMembershipDetails: () => store.showMembershipDetails,
    lookupNumber: {
      get: () => store.lookupNumber,
      set: v => { store.lookupNumber = v; },
    },
    lookupResult: () => store.lookupResult,
    lookupError: () => store.lookupError,
    hasActiveFilters() {
      return Object.values(this.columnFilters || {}).some(
        value => value && String(value).trim() !== ''
      );
    },
    exportButtonLabel() {
      return this.hasActiveFilters ? 'Export Filtered' : 'Export All';
    },
    membershipDisplayNames() {
      const configured = fieldOrderConfig.order?.display_names?.membership_admin;
      return configured && typeof configured === 'object' ? configured : {};
    },
    membershipShowColumns() {
      const configured = fieldOrderConfig.order?.show_columns?.membership_admin;
      return configured && typeof configured === 'object' ? configured : {};
    },
    orderedMemberFields() {
      const configured = fieldOrderConfig.order['membership_admin'];
      if (fieldOrderConfig.loaded && Array.isArray(configured) && configured.length) {
        if (this.members && this.members.length) {
          const sample = this.members[0] || {};
          const filtered = configured
            .filter(f => f in sample)
            .filter(f => this.isFieldVisible(f));
          if (filtered.length) return filtered;
        }
        return configured.filter(f => this.isFieldVisible(f));
      }
      if (this.members && this.members.length) {
        const sample = this.members[0] || {};
        return Object.keys(sample).filter(f => this.isFieldVisible(f));
      }
      return Object.keys(this.columnFilters || {}).filter(f => this.isFieldVisible(f));
    },
  },
  methods: {
    goHome() {
      store.activeSection = 'home';
    },
    setSort,
    onFilterChange,
    nextPage,
    prevPage,
    firstPage,
    lastPage,
    goToPage,
    onPageSizeChange,
    lookupMember,
    lookupMemberByNumber,
    hideLookupDetails,
    openMemberEdit(member) {
      openMemberForEdit(member);
    },
    isDateOfBirthField,
    dateInputValue: normalizeDateInputValue,
    formatMemberFieldValue(field, value) {
      if (value === null || value === undefined || value === '') {
        return value;
      }
      const formatted = formatConfiguredDate(value, field);
      if (formatted !== value) {
        return formatted;
      }
      if (this.isDateOfBirthField(field)) {
        return this.dateInputValue(value) || value;
      }
      return value;
    },
    getMemberFieldStyle(field, value) {
      if (field === 'Licence_Exp' || field === 'Licence_Expiry') {
        return getExpiryDateStyle(value);
      }
      return {};
    },
    getExpiryDateStyle,
    isFieldVisible(field) {
      const configured = this.membershipShowColumns?.[field];
      return configured !== false;
    },
    getFieldDisplayName(field) {
      const configured = this.membershipDisplayNames?.[field];
      if (typeof configured === 'string' && configured.trim()) {
        return configured.trim();
      }
      return field;
    },
    buildActiveMemberFilters() {
      return Object.fromEntries(
        Object.entries(this.columnFilters || {})
          .filter(([, value]) => value && String(value).trim() !== '')
          .map(([key, value]) => {
            const trimmed = String(value).trim();
            if (trimmed === '[BLANK]') return [key, '[BLANK]'];
            const hasWildcard = trimmed.includes('*') || trimmed.includes('?');
            return [key, hasWildcard ? trimmed : `*${trimmed}*`];
          })
      );
    },
    parseDownloadFilename(contentDisposition, fallbackName) {
      const disposition = String(contentDisposition || '');
      const match = disposition.match(/filename\*?=(?:UTF-8''|\")?([^";]+)/i);
      if (!match || !match[1]) return fallbackName;
      try {
        return decodeURIComponent(match[1].replace(/\"/g, '').trim());
      } catch {
        return match[1].replace(/\"/g, '').trim() || fallbackName;
      }
    },
    exportMembers() {
      this.exportBusy = true;
      this.exportError = '';

      const params = {
        club: this.loggedInClub,
        format: this.exportFormat,
        ...this.buildActiveMemberFilters(),
      };

      if (this.sortKey) {
        params.sort_by = this.sortKey;
        params.sort_order = this.sortOrder;
      }

      return axios.get(`${API_BASE_URL}/members/export`, {
        params,
        responseType: 'blob',
      }).then(res => {
        const fallbackName = `${this.loggedInClub}_members.${this.exportFormat}`;
        const fileName = this.parseDownloadFilename(res.headers?.['content-disposition'], fallbackName);
        const blob = new Blob([res.data], {
          type: this.exportFormat === 'json' ? 'application/json' : 'text/csv;charset=utf-8;',
        });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', fileName);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }).catch(err => {
        this.exportError = err?.response?.data?.error || 'Export failed';
      }).finally(() => {
        this.exportBusy = false;
      });
    },
  },
};
</script>

<style scoped>
.membership-export-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.membership-export-label {
  display: inline-flex;
  align-items: center;
  font-size: 10pt;
  line-height: 1;
  color: var(--app-color-text-muted);
}

.membership-admin-header {
  align-items: center;
}

#member-export-format,
#member-export-format option {
  font-size: 10pt;
}

.membership-export-error {
  margin: 8px 0;
  color: var(--app-color-state-danger);
}

.membership-empty-state {
  text-align: center;
  color: #888;
}

.membership-no-columns {
  margin: 24px 0;
  color: #888;
}

.membership-lookup-error {
  color: var(--app-color-state-danger);
}

.membership-table-scroll {
  width: 100%;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}

.membership-table-scroll .member-table {
  min-width: 100%;
}

.membership-table-scroll .member-table th {
  font-size: 8pt;
}

.membership-table-scroll .member-table td {
  font-size: 6pt;
}

@media (max-width: 1000px) {
  .membership-table-scroll {
    overflow-x: visible;
  }

  .membership-table-scroll .member-table {
    min-width: 100%;
  }

  .membership-table-scroll .member-table th {
    font-size: 8pt;
    min-width: 0 !important;
    white-space: normal;
    overflow-wrap: anywhere;
  }

  .membership-table-scroll .member-table td {
    font-size: 6pt;
    min-width: 0 !important;
    white-space: normal;
    overflow-wrap: anywhere;
  }
}

@media (min-width: 1001px) {
  .membership-table-scroll {
    overflow-x: auto;
  }

  .membership-table-scroll .member-table {
    min-width: max-content;
  }
}
</style>
