<template>
  <div id="app">
    <img src="./HLaS_logo_50x50.png" alt="HLaS logo" class="app-logo" />
    <div v-if="!loggedIn" class="login-container">
      <h2>Welcome to HLaS - please provide your credentials to login</h2>
      <form @submit.prevent="login">
        <input v-model="loginUsername" placeholder="Username" required />
        <input v-model="loginPassword" placeholder="Password" type="password" required />
        <button type="submit">Login</button>
      </form>
      <div v-if="loginError" style="color: red;">{{ loginError }}</div>
    </div>
    <div v-else>
    <h1>GAAFFS Members</h1>
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
            Type
            <span class="sort-arrow" @click="setSort('Member_Type', 'asc')">&#8593;</span>
            <span class="sort-arrow" @click="setSort('Member_Type', 'desc')">&#8595;</span>
            <input v-model="columnFilters.Member_Type" @input="onFilterChange" class="column-filter" placeholder="Filter" />
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
            EA_Licence
            <span class="sort-arrow" @click="setSort('EA_Licence', 'asc')">&#8593;</span>
            <span class="sort-arrow" @click="setSort('EA_Licence', 'desc')">&#8595;</span>
            <input v-model="columnFilters.EA_Licence" @input="onFilterChange" class="column-filter" placeholder="Filter" />
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="member in sortedMembers" :key="member.id || member.ID || member.Number">
          <td>{{ member.ID }}</td>
          <td><a href="#" @click.prevent="lookupMemberByNumber(member.Number)" class="member-link">{{ member.Number }}</a></td>
          <td>{{ member.Members_Name }}</td>
          <td>{{ member.Member_Type }}</td>
          <td>{{ member.Paid_Up_2026 }}</td>
          <td>{{ member.Paused }}</td>
          <td>{{ member.E_Mail }}</td>
          <td>{{ member.Mobile }}</td>
          <td>{{ member.Car_Reg }}</td>
          <td>{{ member.EA_Licence }}</td>
        </tr>
      </tbody>
    </table>
    <div class="pagination-controls">
      <button :disabled="currentPage === 1" @click="prevPage">Previous Page</button>
      <span>Page {{ currentPage }} of {{ totalPages }}</span>
      <button :disabled="currentPage === totalPages" @click="nextPage">Next Page</button>
    </div>
    <div class="page-numbers">
      <button v-for="pageNum in visiblePages" :key="pageNum" 
              :class="{ 'active': pageNum === currentPage }" 
              @click="goToPage(pageNum)">
        {{ pageNum }}
      </button>
    </div>
    <div v-if="editing">
      <h2>Edit Member</h2>
      <form @submit.prevent="updateMember">
        <input v-model="editMemberData.name" placeholder="Name" required />
        <input v-model="editMemberData.email" placeholder="Email" />
        <input v-model="editMemberData.phone" placeholder="Phone" />
        <input v-model="editMemberData.membership_type" placeholder="Membership Type" />
        <button type="submit">Save</button>
        <button @click="cancelEdit">Cancel</button>
      </form>
    </div>
    <hr />
    <div>
      <h2>Membership Details</h2>
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
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      members: [],
      totalMembers: 0,
      currentPage: 1,
      pageSize: 10,
      sortKey: 'ID',
      sortOrder: 'asc',
      newMember: { name: '', email: '', phone: '', membership_type: '' },
      editing: false,
      editMemberData: {},
      editMemberId: null,
      lookupNumber: '',
      lookupResult: null,
      lookupError: '',
      loginUsername: '',
      loginPassword: '',
      loginError: '',
      loggedIn: false,
      loggedInUser: null,
      filterDebounceTimer: null,
      filterDebounceMs: 250,
      columnFilters: {
        ID: '',
        Number: '',
        Members_Name: '',
        Member_Type: '',
        Paid_Up_2026: '',
        Paused: '',
        E_Mail: '',
        Mobile: '',
        Car_Reg: '',
        EA_Licence: ''
      }
    };
  },
  computed: {
    sortedMembers() {
      if (!this.members || !this.members.length) return [];

      const key = this.sortKey;
      const order = this.sortOrder;
      return [...this.members].sort((a, b) => {
        let aVal = a[key];
        let bVal = b[key];
        // Try to parse as number if possible
        if (!isNaN(parseFloat(aVal)) && !isNaN(parseFloat(bVal))) {
          aVal = parseFloat(aVal);
          bVal = parseFloat(bVal);
        } else {
          aVal = (aVal || '').toString().toLowerCase();
          bVal = (bVal || '').toString().toLowerCase();
        }
        if (aVal < bVal) return order === 'asc' ? -1 : 1;
        if (aVal > bVal) return order === 'asc' ? 1 : -1;
        return 0;
      });
    },
    totalPages() {
      return Math.max(1, Math.ceil(this.totalMembers / this.pageSize));
    },
    visiblePages() {
      const current = this.currentPage;
      const total = this.totalPages;
      const pageCount = 5;
      
      let start, end;
      
      if (current <= 3) {
        // For pages 1-3, show 1-5 (or fewer if doesn't exist)
        start = 1;
        end = Math.min(pageCount, total);
      } else {
        // Center the current page with 2 on each side
        start = current - 2;
        end = current + 2;
        
        // Adjust if end exceeds total
        if (end > total) {
          end = total;
          start = Math.max(1, end - pageCount + 1);
        }
      }
      
      const pages = [];
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
      return pages;
    }
  },
  created() {
    if (this.loggedIn) {
      this.fetchMembers();
    }
  },
  beforeUnmount() {
    if (this.filterDebounceTimer) {
      clearTimeout(this.filterDebounceTimer);
    }
  },
  methods: {
    onFilterChange() {
      this.currentPage = 1;
      if (this.filterDebounceTimer) {
        clearTimeout(this.filterDebounceTimer);
      }
      this.filterDebounceTimer = setTimeout(() => {
        this.fetchMembers();
      }, this.filterDebounceMs);
    },
    setSort(key, order) {
      this.sortKey = key;
      this.sortOrder = order;
    },
    fetchMembers() {
      const offset = (this.currentPage - 1) * this.pageSize;
      const activeFilters = Object.fromEntries(
        Object.entries(this.columnFilters)
          .filter(([, value]) => value && value.trim() !== '')
          .map(([key, value]) => {
            const trimmed = value.trim();
            if (trimmed === '[BLANK]') {
              return [key, '[BLANK]'];
            }
            const hasWildcard = trimmed.includes('*') || trimmed.includes('?');
            const filterValue = hasWildcard ? trimmed : `*${trimmed}*`;
            return [key, filterValue];
          })
      );

      axios.get('http://localhost:5000/members', {
        params: { limit: this.pageSize, offset, ...activeFilters }
      }).then(res => {
        this.members = res.data.members;
        this.totalMembers = res.data.total;
      });
    },
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
        this.fetchMembers();
      }
    },
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
        this.fetchMembers();
      }
    },
    goToPage(pageNum) {
      this.currentPage = pageNum;
      this.fetchMembers();
    },
    login() {
      this.loginError = '';
      axios.post('http://localhost:5000/login', {
        username: this.loginUsername,
        password: this.loginPassword
      })
        .then(res => {
          if (res.data.success) {
            this.loggedIn = true;
            this.loggedInUser = res.data.user;
            this.currentPage = 1;
            this.fetchMembers();
          } else {
            this.loginError = res.data.error || 'Login failed';
          }
        })
        .catch(err => {
          this.loginError = err.response && err.response.data && err.response.data.error ? err.response.data.error : 'Login failed';
        });
    },
    addMember() {
      axios.post('http://localhost:5000/members', this.newMember).then(() => {
        this.fetchMembers();
        this.newMember = { name: '', email: '', phone: '', membership_type: '' };
      });
    },
    editMember(member) {
      this.editing = true;
      this.editMemberData = { ...member };
      this.editMemberId = member.id;
    },
    updateMember() {
      axios.put(`http://localhost:5000/members/${this.editMemberId}`, this.editMemberData).then(() => {
        this.fetchMembers();
        this.editing = false;
        this.editMemberData = {};
        this.editMemberId = null;
      });
    },
    cancelEdit() {
      this.editing = false;
      this.editMemberData = {};
      this.editMemberId = null;
    },
    deleteMember(id) {
      axios.delete(`http://localhost:5000/members/${id}`).then(() => {
        this.fetchMembers();
      });
    },
    lookupMember() {
      this.lookupResult = null;
      this.lookupError = '';
      axios.get(`http://localhost:5000/member_by_number/${encodeURIComponent(this.lookupNumber)}`)
        .then(res => {
          this.lookupResult = res.data;
        })
        .catch(err => {
          this.lookupError = err.response && err.response.data && err.response.data.error ? err.response.data.error : 'Error retrieving member';
        });
    }
      ,
    lookupMemberByNumber(number) {
      this.lookupNumber = number;
      this.lookupMember();
    },
  }
};
</script>

<style>
#app .pagination-controls {
  margin-bottom: 20px;
  text-align: center;
}
#app .pagination-controls button[disabled] {
  opacity: 0.5;
  cursor: not-allowed;
}
#app .member-table {
  width: 90%;
  border-collapse: collapse;
  margin-bottom: 20px;
  font-family: Helvetica, Arial, sans-serif;
}
#app .member-table th, #app .member-table td {
  border: 1px solid #ccc;
  padding: 8px;
  text-align: left;
}
#app .member-table th {
  vertical-align: top;
  font-size: 10pt;
}
#app .member-table td {
  font-size: 8pt;
}
/* Column minimum widths */
#app .member-table th:nth-child(1), #app .member-table td:nth-child(1) { min-width: 60px; } /* ID */
#app .member-table th:nth-child(2), #app .member-table td:nth-child(2) { min-width: 60px; } /* Number */
#app .member-table th:nth-child(3), #app .member-table td:nth-child(3) { min-width: 140px; } /* Members_Name */
#app .member-table th:nth-child(4), #app .member-table td:nth-child(4) { min-width: 100px; } /* Member_Type */
#app .member-table th:nth-child(5), #app .member-table td:nth-child(5) { min-width: 90px; } /* Paid_Up_2026 */
#app .member-table th:nth-child(6), #app .member-table td:nth-child(6) { min-width: 70px; } /* Paused */
#app .member-table th:nth-child(7), #app .member-table td:nth-child(7) { min-width: 160px; } /* E_Mail */
#app .member-table th:nth-child(8), #app .member-table td:nth-child(8) { min-width: 100px; } /* Mobile */
#app .member-table th:nth-child(9), #app .member-table td:nth-child(9) { min-width: 90px; } /* Car_Reg */
#app .member-table th:nth-child(10), #app .member-table td:nth-child(10) { min-width: 100px; } /* EA_Licence */
#app .column-filter {
  display: block;
  width: 100%;
  margin-top: 4px;
  box-sizing: border-box;
}
#app .page-numbers {
  margin-top: 15px;
  text-align: center;
}
#app .page-numbers button {
  margin: 0 4px;
  padding: 6px 10px;
  border: 1px solid #ccc;
  background-color: #fff;
  cursor: pointer;
  border-radius: 4px;
}
#app .page-numbers button:hover {
  background-color: #f0f0f0;
}
#app .page-numbers button.active {
  background-color: #007bff;
  color: white;
  border-color: #0056b3;
}
#app .member-link {
  color: #007bff;
  text-decoration: none;
  cursor: pointer;
}
#app .member-link:hover {
  text-decoration: underline;
}
#app .lookup-table th,
#app .lookup-table td {
  font-family: "Courier New", Courier, monospace;
  font-size: 8pt;
  border: 2px solid #ccc;
}
#app .lookup-table {
  border-collapse: collapse;
  border: 2px solid #ccc;
}
#app .member-table th {
  background: #f0f0f0;
}
#app .sort-arrow {
  cursor: pointer;
  font-size: 1em;
  margin-left: 2px;
}
#app .login-container {
  max-width: 400px;
  margin: 40px auto;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
  background: #f9f9f9;
}
#app .app-logo {
  display: block;
  margin: 20px auto;
}
#app {
  max-width: 600px;
  margin: auto;
  font-family: Arial, sans-serif;
}
#app h2 {
  font-size: 14pt;
  font-family: Helvetica, Arial, sans-serif;
}
form {
  margin-bottom: 20px;
}
input {
  margin-right: 10px;
}
button {
  margin-right: 5px;
}
#app .member-link {
  color: #007bff;
  text-decoration: none;
  cursor: pointer;
}
#app .member-link:hover {
  text-decoration: underline;
}
</style>
