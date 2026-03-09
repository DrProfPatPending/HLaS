<template>
  <div id="app">
    <table class="logo-table">
      <tbody>
        <tr>
          <td class="logo-cell">
            <img src="./logos/HLaS.png" alt="HLaS logo" class="app-logo" @click="goHome" />
          </td>
          <td class="logo-cell">
            <img v-if="loggedIn" :src="require(`./logos/${loggedInClub}_Logo_50px.png`)" :alt="`${loggedInClub} logo`" class="club-logo" />
          </td>
          <td class="logo-spacer"></td>
          <td v-if="loggedIn" class="login-info-cell">Logged in as: {{ loggedInUsername }} ({{ loggedInClub }})</td>
          <td v-if="loggedIn" class="logout-cell">
            <button type="button" class="logout-button" @click="logout">Log Out</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="!loggedIn" class="login-container">
      <h2>Welcome to HLaS - please provide your credentials to login</h2>
      <form @submit.prevent="login">
        <div class="form-field">
          <label for="club-select">Select Club:</label>
          <select id="club-select" v-model="selectedClub" class="club-select">
            <option
              v-for="club in clubs"
              :key="club.shortName"
              :value="club.shortName"
              :title="club.description"
            >
              {{ club.shortName }} - {{ club.fullName }}
            </option>
          </select>
        </div>
        <input v-model="loginUsername" placeholder="Username" required />
        <input v-model="loginPassword" placeholder="Password" type="password" required />
        <button type="submit">Login</button>
      </form>
      <div v-if="loginError" style="color: red;">{{ loginError }}</div>
    </div>
    <div v-else>
    <div v-if="activeSection === 'home'" class="home-container">
      <h2>Hello {{ loggedInUsername }} [{{ loggedInClub }}]</h2>
      <h3> Welcome to HookLineandSinker your one-stop shop<br>for fishing club management.</h3>
      <table class="home-nav-table">
        <tbody>
          <tr>
            <td><button type="button" class="home-nav-button" @click="navigateToSection('membership-admin')">Membership Admin</button></td>
            <td><button type="button" class="home-nav-button" @click="navigateToSection('club-information')">Club Information</button></td>
          </tr>
          <tr>
            <td><button type="button" class="home-nav-button" @click="navigateToSection('my-club')">My Club</button></td>
            <td><button type="button" class="home-nav-button" @click="navigateToSection('club-store')">Club Store</button></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else-if="activeSection === 'membership-admin'">
    <h1>{{ selectedClub }} Members</h1>
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
            <input v-model="columnFilters.Member_Type" @input="onFilterChange" class="column-filter" placeholder="Filter" />
          </th>
          <th>
            EA_Licence
            <span class="sort-arrow" @click="setSort('EA_Licence', 'asc')">&#8593;</span>
            <span class="sort-arrow" @click="setSort('EA_Licence', 'desc')">&#8595;</span>
            <input v-model="columnFilters.EA_Licence" @input="onFilterChange" class="column-filter" placeholder="Filter" />
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
          <td><a href="#" @click.prevent="lookupMemberByNumber(member.Number)" class="member-link">{{ member.Number }}</a></td>
          <td><a href="#" @click.prevent="openMemberEdit(member)" class="member-link">{{ member.Members_Name }}</a></td>
          <td>{{ member.E_Mail }}</td>
          <td>{{ member.Mobile }}</td>
          <td>{{ member.Car_Reg }}</td>
          <td>{{ member.Member_Type }}</td>
          <td>{{ member.EA_Licence }}</td>
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
      <button v-for="pageNum in visiblePages" :key="pageNum" 
              :class="{ 'active': pageNum === currentPage }" 
              @click="goToPage(pageNum)">
        {{ pageNum }}
      </button>
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
    <div v-else-if="activeSection === 'member-edit'" class="member-edit-container">
      <h2>Edit Member Details</h2>
      <div class="member-edit-actions">
        <button type="button" @click="updateMember">Update Member</button>
        <button type="button" @click="cancelEdit">Cancel</button>
        <span v-if="passwordError" style="color: red; margin-left: 15px;">{{ passwordError }}</span>
      </div>
      <br />
      <table class="member-detail-table">
        <thead>
          <tr>
            <th>Field</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="editMemberData.username !== undefined">
            <td>{{ formatFieldName('username') }}</td>
            <td>
              <input
                v-model="editMemberData.username"
                class="member-detail-input"
              />
            </td>
          </tr>
          <tr>
            <td>New Password</td>
            <td>
              <input
                v-model="newPassword"
                type="password"
                class="member-detail-input"
                placeholder="Leave blank to keep current password"
              />
            </td>
          </tr>
          <tr>
            <td>Confirm New Password</td>
            <td>
              <input
                v-model="confirmPassword"
                type="password"
                class="member-detail-input"
              />
            </td>
          </tr>
          <tr v-for="key in remainingEditMemberKeys" :key="key">
            <td>{{ formatFieldName(key) }}</td>
            <td>
              <input
                v-model="editMemberData[key]"
                :disabled="key === 'ID' || key === 'id'"
                class="member-detail-input"
              />
            </td>
          </tr>
          <tr v-if="passwordError">
            <td colspan="2" style="color: red; text-align: center;">{{ passwordError }}</td>
          </tr>
        </tbody>
      </table>
      <div class="member-edit-actions">
        <button type="button" @click="updateMember">Update Member</button>
        <button type="button" @click="cancelEdit">Cancel</button>
      </div>
    </div>
    <div v-else class="section-placeholder">
      <h2>{{ sectionDisplayName(activeSection) }}</h2>
      <p>This section is coming soon.</p>
      <button type="button" @click="activeSection = 'home'">Back to Home</button>
    </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

const API_BASE_URL = process.env.VUE_APP_BACKEND_URL || `${window.location.protocol}//${window.location.hostname}:5050`;

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
      editMemberData: {},
      editMemberId: null,
      newPassword: '',
      confirmPassword: '',
      passwordError: '',
      lookupNumber: '',
      lookupResult: null,
      lookupError: '',
      loginUsername: '',
      loginPassword: '',
      loginError: '',
      clubs: [],
      loggedIn: false,
      loggedInUser: null,
      loggedInUsername: '',
      activeSection: 'home',
      selectedClub: 'GAAFFS',
      loggedInClub: 'GAAFFS',
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
        EA_Licence: '',
        Resigned: ''
      }
    };
  },
  computed: {
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
    },
    orderedEditMemberKeys() {
      const keys = Object.keys(this.editMemberData);
      const priorityKeys = ['username'];
      const excludeKeys = ['password'];  // Don't show password in regular fields
      const topKeys = priorityKeys.filter(key => keys.includes(key));
      const remainingKeys = keys.filter(key => !priorityKeys.includes(key) && !excludeKeys.includes(key));
      return [...topKeys, ...remainingKeys];
    },
    remainingEditMemberKeys() {
      const keys = Object.keys(this.editMemberData);
      const excludeKeys = ['username', 'password'];
      return keys.filter(key => !excludeKeys.includes(key));
    }
  },
  created() {
    this.loadClubs();
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
    loadClubs() {
      axios.get(`${API_BASE_URL}/clubs`)
        .then(res => {
          const clubs = res.data && Array.isArray(res.data.clubs) ? res.data.clubs : [];
          if (!clubs.length) {
            throw new Error('No clubs in config');
          }

          this.clubs = clubs;
          const hasSelected = clubs.some(club => club.shortName === this.selectedClub);
          if (!hasSelected) {
            this.selectedClub = clubs[0].shortName;
            this.loggedInClub = clubs[0].shortName;
          }
        })
        .catch(() => {
          this.clubs = [
            {
              fullName: 'GAAFFS',
              shortName: 'GAAFFS',
              description: 'GAAFFS fishing club members',
              websiteUrl: '',
              adminEmail: '',
            },
            {
              fullName: 'CTC',
              shortName: 'CTC',
              description: 'CTC fishing club members',
              websiteUrl: '',
              adminEmail: '',
            },
          ];
        });
    },
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
      this.currentPage = 1; // Reset to first page when sorting
      this.fetchMembers();
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

      const params = { club: this.loggedInClub, limit: this.pageSize, offset, ...activeFilters };
      
      // Add sorting parameters if a sort is active
      if (this.sortKey) {
        params.sort_by = this.sortKey;
        params.sort_order = this.sortOrder;
      }

      axios.get(`${API_BASE_URL}/members`, {
        params: params
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
    firstPage() {
      this.currentPage = 1;
      this.fetchMembers();
    },
    lastPage() {
      this.currentPage = this.totalPages;
      this.fetchMembers();
    },
    goToPage(pageNum) {
      this.currentPage = pageNum;
      this.fetchMembers();
    },
    goHome() {
      this.activeSection = 'home';
    },
    onPageSizeChange() {
      this.currentPage = 1;
      this.fetchMembers();
    },
    navigateToSection(sectionKey) {
      if (sectionKey === 'membership-admin') {
        this.activeSection = 'membership-admin';
        this.currentPage = 1;
        this.fetchMembers();
        return;
      }
      this.activeSection = sectionKey;
    },
    sectionDisplayName(sectionKey) {
      if (sectionKey === 'club-information') {
        return 'Club Information';
      }
      if (sectionKey === 'my-club') {
        return 'My Club';
      }
      if (sectionKey === 'club-store') {
        return 'Club Store';
      }
      if (sectionKey === 'member-edit') {
        return 'Edit Member';
      }
      return 'Home';
    },
    login() {
      this.loginError = '';
      axios.post(`${API_BASE_URL}/login`, {
        username: this.loginUsername,
        password: this.loginPassword,
        club: this.selectedClub
      })
        .then(res => {
          if (res.data.success) {
            this.loggedIn = true;
            this.loggedInUser = res.data.user;
            this.loggedInUsername = this.loginUsername;
            this.loggedInClub = this.selectedClub;
            this.activeSection = 'home';
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
    logout() {
      this.loggedIn = false;
      this.loggedInUser = null;
      this.loggedInUsername = '';
      this.activeSection = 'home';
      this.loginPassword = '';
      this.members = [];
      this.totalMembers = 0;
      this.currentPage = 1;
      this.lookupNumber = '';
      this.lookupResult = null;
      this.lookupError = '';
    },
    addMember() {
      const memberData = { ...this.newMember, club: this.loggedInClub };
      axios.post(`${API_BASE_URL}/members`, memberData).then(() => {
        this.fetchMembers();
        this.newMember = { name: '', email: '', phone: '', membership_type: '' };
      });
    },
    openMemberEdit(member) {
      this.editMemberData = { ...member };
      this.editMemberId = member.id || member.ID;
      this.newPassword = '';
      this.confirmPassword = '';
      this.passwordError = '';
      this.activeSection = 'member-edit';
    },
    updateMember() {
      // Validate password if provided
      if (this.newPassword || this.confirmPassword) {
        if (this.newPassword !== this.confirmPassword) {
          this.passwordError = 'Passwords do not match';
          return;
        }
        if (this.newPassword.length === 0) {
          this.passwordError = 'Password cannot be empty';
          return;
        }
      }
      this.passwordError = '';
      
      const memberData = { ...this.editMemberData, club: this.loggedInClub };
      
      // Include password only if a new one was entered
      if (this.newPassword) {
        memberData.password = this.newPassword;
      }
      
      axios.put(`${API_BASE_URL}/members/${this.editMemberId}`, memberData).then(() => {
        this.fetchMembers();
        this.activeSection = 'membership-admin';
        this.editMemberData = {};
        this.editMemberId = null;
        this.newPassword = '';
        this.confirmPassword = '';
        this.passwordError = '';
      }).catch(err => {
        this.passwordError = err.response && err.response.data && err.response.data.error ? err.response.data.error : 'Update failed';
      });
    },
    cancelEdit() {
      this.activeSection = 'membership-admin';
      this.editMemberData = {};
      this.editMemberId = null;
      this.newPassword = '';
      this.confirmPassword = '';
      this.passwordError = '';
    },
    deleteMember(id) {
      axios.delete(`${API_BASE_URL}/members/${id}?club=${this.loggedInClub}`).then(() => {
        this.fetchMembers();
      });
    },
    lookupMember() {
      this.lookupResult = null;
      this.lookupError = '';
      axios.get(`${API_BASE_URL}/member_by_number/${encodeURIComponent(this.lookupNumber)}?club=${this.loggedInClub}`)
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
    formatFieldName(fieldName) {
      // Replace double underscores with double colon, then single underscores with space
      return fieldName.replace(/__/g, '::').replace(/_/g, ' ');
    }
  }
};
</script>

<style>
#app .home-container {
  max-width: 900px;
  margin: 40px auto;
  font-family: Helvetica, Arial, sans-serif;
}
#app .home-nav-table {
  margin-top: 20px;
  border-collapse: separate;
  border-spacing: 12px;
}
#app .home-nav-button {
  width: 220px;
  padding: 12px 10px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
  cursor: pointer;
}
#app .section-placeholder {
  max-width: 900px;
  margin: 40px auto;
  font-family: Helvetica, Arial, sans-serif;
}
#app .member-edit-container {
  max-width: 900px;
  margin: 20px auto;
  font-family: Helvetica, Arial, sans-serif;
}
#app .member-detail-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 14px;
}
#app .member-detail-table th,
#app .member-detail-table td {
  border: 1px solid #ccc;
  padding: 8px;
  font-size: 9pt;
}
#app .member-detail-table th {
  background: #f0f0f0;
  width: 30%;
}
#app .member-detail-input {
  width: 100%;
  box-sizing: border-box;
  padding: 6px;
}
#app .member-edit-actions {
  display: flex;
  gap: 8px;
}
#app .pagination-controls {
  margin-bottom: 20px;
  text-align: center;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 8pt;
}
#app .records-per-page-select {
  margin-left: 12px;
  padding: 4px 6px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 8pt;
  border: 1px solid #ccc;
  border-radius: 3px;
  background-color: white;
  cursor: pointer;
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
#app .member-table th:nth-child(4), #app .member-table td:nth-child(4) { min-width: 160px; } /* E_Mail */
#app .member-table th:nth-child(5), #app .member-table td:nth-child(5) { min-width: 100px; } /* Mobile */
#app .member-table th:nth-child(6), #app .member-table td:nth-child(6) { min-width: 90px; } /* Car_Reg */
#app .member-table th:nth-child(7), #app .member-table td:nth-child(7) { min-width: 100px; } /* Member_Type */
#app .member-table th:nth-child(8), #app .member-table td:nth-child(8) { min-width: 100px; } /* EA_Licence */
#app .member-table th:nth-child(9), #app .member-table td:nth-child(9) { min-width: 90px; } /* Paid_Up_2026 */
#app .member-table th:nth-child(10), #app .member-table td:nth-child(10) { min-width: 70px; } /* Paused */
#app .member-table th:nth-child(11), #app .member-table td:nth-child(11) { min-width: 80px; } /* Resigned */
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
#app .login-container .form-field {
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
}
#app .login-container .form-field label {
  margin-bottom: 5px;
  font-weight: bold;
  font-size: 14px;
}
#app .login-container .club-select {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
  background-color: white;
  cursor: pointer;
}
#app .login-container input {
  margin-bottom: 10px;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  width: 100%;
  box-sizing: border-box;
}
#app .login-container button {
  width: 100%;
  padding: 10px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}
#app .login-container button:hover {
  background-color: #0056b3;
}
#app .logo-table {
  position: fixed;
  top: 10px;
  left: 10px;
  right: 10px;
  border-collapse: collapse;
  z-index: 1000;
  background: white;
}
#app .logo-cell {
  padding: 5px;
  border: none;
}
#app .logo-spacer {
  width: 100%;
}
#app .login-info-cell {
  padding: 5px;
  border: none;
  text-align: right;
  white-space: nowrap;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 8pt;
}
#app .logout-cell {
  padding: 5px;
  border: none;
  text-align: right;
  white-space: nowrap;
}
#app .logout-button {
  margin-right: 0;
  padding: 6px 10px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 8pt;
}
#app .app-logo {
  display: block;
  margin: 0;
  cursor: pointer;
  max-height: 100px;
  max-width: 100px;
}
#app .club-logo {
  display: block;
  margin: 0;
  max-height: 100px;
  max-width: 100px;
}
#app {
  max-width: none;
  width: 100%;
  margin: 0;
  padding: 70px 12px 12px 12px;
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
