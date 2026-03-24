<template>
  <div>
    <div class="membership-admin-header">
      <button type="button" @click="goHome">Back to Home</button>
      <h1>{{ loggedInClub }} Members</h1>
    </div>
    <table v-if="orderedMemberFields.length && members.length" class="member-table">
      <thead>
        <tr>
          <th v-for="field in orderedMemberFields" :key="field">{{ field }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="member in members" :key="member.id || member.ID || member.Number">
          <td v-for="field in orderedMemberFields" :key="field">
            <span v-if="field === 'E_Mail' && member[field]">
              <a :href="`mailto:${member[field]}`">{{ member[field] }}</a>
            </span>
            <span v-else>{{ member[field] }}</span>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else style="margin: 24px 0; color: #888;">No members found.</div>
    <div class="pagination-controls">
      <button :disabled="currentPage === 1" @click="firstPage">First Page</button>
      <button :disabled="currentPage === 1" @click="prevPage">Previous Page</button>
      <span>Page {{ currentPage }} of {{ totalPages }}&nbsp;</span>
      <button :disabled="currentPage === totalPages" @click="nextPage">Next Page</button>
      <button :disabled="currentPage === totalPages" @click="lastPage">Last Page</button>
      <select v-model.number="pageSize" @change="onPageSizeChange" class="records-per-page-select">
        <option value="10">10 per page</option>
        <option value="25">25 per page</option>
        <option value="50">50 per page</option>
        <option value="100">100 per page</option>
      </select>
    </div>
    <div class="page-numbers">
      <button
        v-for="pageNum in visiblePages"
        :key="pageNum"
        :class="{ 'active': pageNum === currentPage }"
        @click="goToPage(pageNum)"
      >
        {{ pageNum }}
      </button>
    </div>
    <hr />
    <div v-if="showMembershipDetails">
      <div class="membership-details-header">
        <h2>Membership Details</h2>
        <button v-if="lookupResult && !lookupError" type="button" @click="hideLookupDetails">
          Hide Details
        </button>
      </div>
      <form @submit.prevent="lookupMember">
        <input v-model="lookupNumber" placeholder="Membership Number" required />
        <button type="submit">Lookup</button>
      </form>
      <div v-if="lookupError" style="color: red;">{{ lookupError }}</div>
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
            <td>{{ value }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import {
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
} from '../store.js';

export default {
  name: 'MembershipAdmin',
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
    showMembershipDetails: () => store.showMembershipDetails,
    lookupNumber: {
      get: () => store.lookupNumber,
      set: v => { store.lookupNumber = v; },
    },
    lookupResult: () => store.lookupResult,
    lookupError: () => store.lookupError,
    orderedMemberFields() {
      if (!this.members || !this.members.length) return [];
      if (fieldOrderConfig.loaded && fieldOrderConfig.order['membership_admin']) {
        const sample = this.members[0] || {};
        return fieldOrderConfig.order['membership_admin'].filter(f => f in sample);
      }
      const sample = this.members[0] || {};
      return Object.keys(sample);
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
    goToPage(pageNum) {
      store.currentPage = pageNum;
    },
    onPageSizeChange,
    lookupMember,
    lookupMemberByNumber,
    hideLookupDetails,
    openMemberEdit(member) {
      selectMemberForEdit(member);
    },
    getExpiryDateStyle,
  },
};
</script>
