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
            <th v-for="field in orderedMemberFields" :key="field" :style="getColumnStyle('membership_admin', field)">
              <div class="member-th-label">
                <span>{{ getFieldDisplayName(field) }}</span>
                <span
                  class="sort-arrow"
                  :class="{ active: sortKey === field && sortOrder === 'asc' }"
                  title="Sort ascending"
                  @click="setSort(field, 'asc')"
                >▲</span>
                <span
                  class="sort-arrow"
                  :class="{ active: sortKey === field && sortOrder === 'desc' }"
                  title="Sort descending"
                  @click="setSort(field, 'desc')"
                >▼</span>
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
            <td v-for="field in orderedMemberFields" :key="field" :style="getColumnStyle('membership_admin', field)">
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
              <span v-else-if="isAgeField(field)">
                {{ calculateAgeFromMember(member) }}
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
    <div class="membership-pagination">
      <app-button :disabled="currentPage === 1" @click="firstPage" inherit-style>First</app-button>
      <app-button :disabled="currentPage === 1" @click="prevPage" inherit-style>Previous</app-button>
      <app-button
        v-for="pageNum in visiblePages"
        :key="pageNum"
        type="button"
        inherit-style
        class="membership-page-number"
        :class="{ 'active': pageNum === currentPage }"
        @click="goToPage(pageNum)"
      >
        {{ pageNum }}
      </app-button>
      <app-button :disabled="currentPage === totalPages" @click="nextPage" inherit-style>Next</app-button>
      <app-button :disabled="currentPage === totalPages" @click="lastPage" inherit-style>Last</app-button>
      <span class="membership-page-status">Page {{ currentPage }} of {{ totalPages }}</span>
      <select v-model.number="pageSize" @change="onPageSizeChange" class="records-per-page-select" aria-label="Members per page">
        <option value="10">10 per page</option>
        <option value="25">25 per page</option>
        <option value="50">50 per page</option>
        <option value="100">100 per page</option>
      </select>
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
            <td>{{ isAgeField(key) ? calculateAgeFromMember(lookupResult) : formatMemberFieldValue(key, value) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import AppButton from './ui/AppButton.vue';
import { columnWidthStyle } from '../columnWidth.js';
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
  isAgeField,
  calculateAgeFromDOB,
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
    membershipMinimumWidths() {
      const configured = fieldOrderConfig.order?.minimum_widths?.membership_admin;
      return configured && typeof configured === 'object' ? configured : {};
    },
    membershipWidths() {
      const configured = fieldOrderConfig.order?.widths?.membership_admin;
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
    isAgeField,
    calculateAgeFromDOB,
    dateInputValue: normalizeDateInputValue,
    calculateAgeFromMember(member) {
      const dob = member?.Date_of_Birth;
      const calculated = calculateAgeFromDOB(dob);
      return calculated !== '' ? calculated : (member?.Age ?? '');
    },
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
    getColumnStyle(contextKey, columnKey) {
      return columnWidthStyle(this.membershipWidths?.[columnKey], this.membershipMinimumWidths?.[columnKey]);
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
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  border: 1px solid #d8dde3;
  border-radius: 4px;
}

/* #app prefix: outranks the shared #app .member-table rules in App.vue */
#app .membership-admin-header {
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 8px;
}

#app .membership-admin-header h1 {
  font-size: 1.25rem;
  font-weight: 600;
  line-height: 1.2;
}

#app .membership-export-controls button {
  height: auto;
  margin: 0;
  padding: 3px 10px;
  font-size: 8.5pt;
}

#app .membership-table-scroll .member-table {
  width: 100%;
  min-width: max-content;
  margin: 0;
  border-collapse: collapse;
  border-style: hidden;
}

#app .membership-table-scroll .member-table th,
#app .membership-table-scroll .member-table td {
  min-width: 0;
  border: 1px solid #e3e7eb;
  text-align: left;
}

#app .membership-table-scroll .member-table th {
  padding: 4px 6px 5px;
  font-size: 8pt;
  font-weight: 600;
  color: #334;
  vertical-align: bottom;
  white-space: nowrap;
  background: #f3f5f7;
  border-bottom-color: #cfd5db;
}

#app .membership-table-scroll .member-table td {
  padding: 3px 6px;
  font-size: 8pt;
  line-height: 1.35;
  vertical-align: top;
}

#app .membership-table-scroll .member-table tbody tr:nth-child(even) td {
  background: #fafbfc;
}

#app .membership-table-scroll .member-table tbody tr:hover td {
  background: #eef5ff;
}

.member-th-label {
  display: flex;
  align-items: center;
  gap: 1px;
}

.member-th-label > span:first-child {
  margin-right: 3px;
}

#app .membership-table-scroll .sort-arrow {
  margin: 0;
  padding: 0 1px;
  font-size: 6.5pt;
  line-height: 1;
  color: #a0a8b0;
}

#app .membership-table-scroll .sort-arrow:hover,
#app .membership-table-scroll .sort-arrow.active {
  color: #0056b3;
}

#app .membership-table-scroll .member-table .column-filter {
  min-width: 60px;
  height: 20px;
  margin: 3px 0 0;
  padding: 1px 4px;
  font-size: 7.5pt;
  font-weight: normal;
  border-color: #d0d6dc;
}

#app .membership-pagination {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin: 10px 0 4px;
  font-size: 8pt;
}

#app .membership-pagination button {
  height: auto;
  min-width: 0;
  margin: 0;
  padding: 3px 9px;
  font-size: 8pt;
  line-height: 1.4;
}

#app .membership-pagination .membership-page-number {
  min-width: 26px;
  padding: 3px 6px;
  color: #007bff;
  background: #fff;
  border-color: #b8d4f5;
}

#app .membership-pagination .membership-page-number.active {
  color: #fff;
  background: #007bff;
  border-color: #0056b3;
}

#app .membership-pagination .membership-page-number:hover:not(.active) {
  background: #eef5ff;
}

.membership-page-status {
  margin: 0 6px 0 8px;
  color: var(--app-color-text-muted);
}

#app .membership-pagination .records-per-page-select {
  margin-left: 0;
  padding: 2px 4px;
}

#app .membership-admin-container > hr {
  margin: 12px 0;
}
</style>
