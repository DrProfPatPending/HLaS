<template>
  <div>
    <div class="membership-admin-header">
      <button type="button" @click="goHome">Back to Home</button>
      <h1>{{ loggedInClub }} Members</h1>
    </div>
    <table class="member-table">
      <thead>
        <tr>
          <th>
            Rank
            <span class="sort-arrow" @click="setSort('ID', 'desc')">&#8595;</span>
            <span class="sort-arrow" @click="setSort('ID', 'asc')">&#8593;</span>
            <input v-model="columnFilters.ID" @input="onFilterChange" class="column-filter" placeholder="Filter" />
          </th>
          <th>
            Num
            <span class="sort-arrow" @click="setSort('Number', 'desc')">&#8595;</span>
            <span class="sort-arrow" @click="setSort('Number', 'asc')">&#8593;</span>
            <input v-model="columnFilters.Number" @input="onFilterChange" class="column-filter" placeholder="Filter" />
          </th>
          <th>
            Name
            <span class="sort-arrow" @click="setSort('Members_Name', 'asc')">&#8593;</span>
            <span class="sort-arrow" @click="setSort('Members_Name', 'desc')">&#8595;</span>
            <input v-model="columnFilters.Members_Name" @input="onFilterChange" class="column-filter" placeholder="Filter" />
          </th>
          <th>
            E-Mail
            <span class="sort-arrow" @click="setSort('E_Mail', 'asc')">&#8593;</span>
            <span class="sort-arrow" @click="setSort('E_Mail', 'desc')">&#8595;</span>
            <input v-model="columnFilters.E_Mail" @input="onFilterChange" class="column-filter" placeholder="Filter" />
          </th>
          <th>
            Mobile
            <span class="sort-arrow" @click="setSort('Mobile', 'asc')">&#8593;</span>
            <span class="sort-arrow" @click="setSort('Mobile', 'desc')">&#8595;</span>
            <input v-model="columnFilters.Mobile" @input="onFilterChange" class="column-filter" placeholder="Filter" />
          </th>
          <th>
            Car_Reg
            <span class="sort-arrow" @click="setSort('Car_Reg', 'asc')">&#8593;</span>
            <span class="sort-arrow" @click="setSort('Car_Reg', 'desc')">&#8595;</span>
            <input v-model="columnFilters.Car_Reg" @input="onFilterChange" class="column-filter" placeholder="Filter" />
          </th>
          <th>
            Type
            <span class="sort-arrow" @click="setSort('Member_Type', 'asc')">&#8593;</span>
            <span class="sort-arrow" @click="setSort('Member_Type', 'desc')">&#8595;</span>
            <select v-model="columnFilters.Member_Type" @change="onFilterChange" class="column-filter">
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
            EA_Licence
            <span class="sort-arrow" @click="setSort('EA_Licence', 'asc')">&#8593;</span>
            <span class="sort-arrow" @click="setSort('EA_Licence', 'desc')">&#8595;</span>
            <input v-model="columnFilters.EA_Licence" @input="onFilterChange" class="column-filter" placeholder="Filter" />
          </th>
          <th>
            Licence Expiry
            <span class="sort-arrow" @click="setSort('Licence_Exp', 'asc')">&#8593;</span>
            <span class="sort-arrow" @click="setSort('Licence_Exp', 'desc')">&#8595;</span>
            <input v-model="columnFilters.Licence_Exp" @input="onFilterChange" class="column-filter" placeholder="Filter" />
          </th>
          <th>
            Paid Up?
            <input v-model="columnFilters.Paid_Up_2026" @input="onFilterChange" class="column-filter" placeholder="Filter" />
          </th>
          <th>
            Paused?
            <input v-model="columnFilters.Paused" @input="onFilterChange" class="column-filter" placeholder="Filter" />
          </th>
          <th>
            Resigned?
            <input v-model="columnFilters.Resigned" @input="onFilterChange" class="column-filter" placeholder="Filter" />
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="member in members" :key="member.id || member.ID || member.Number">
          <td>{{ member.ID }}</td>
          <td>
            <a href="#" @click.prevent="lookupMemberByNumber(member.Number)" class="member-link">
              {{ member.Number }}
            </a>
          </td>
          <td>
            <a href="#" @click.prevent="openMemberEdit(member)" class="member-link">
              {{ member.Members_Name }}
            </a>
          </td>
          <td>
            <a v-if="member.E_Mail" :href="`mailto:${member.E_Mail}`">{{ member.E_Mail }}</a>
            <span v-else>-</span>
          </td>
          <td>{{ member.Mobile }}</td>
          <td>{{ member.Car_Reg }}</td>
          <td>{{ member.Member_Type }}</td>
          <td>{{ member.EA_Licence }}</td>
          <td :style="getExpiryDateStyle(member.Licence_Exp)">{{ member.Licence_Exp }}</td>
          <td>{{ member.Paid_Up_2026 }}</td>
          <td>{{ member.Paused }}</td>
          <td>{{ member.Resigned }}</td>
        </tr>
      </tbody>
    </table>
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
  goToPage,
  onPageSizeChange,
  lookupMember,
  lookupMemberByNumber,
  hideLookupDetails,
  selectMemberForEdit,
  getExpiryDateStyle,
} from '../store.js';

export default {
  name: 'MembershipAdmin',
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
      selectMemberForEdit(member);
    },
    getExpiryDateStyle,
  },
};
</script>
