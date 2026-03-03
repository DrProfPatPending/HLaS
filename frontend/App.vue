<template>
  <div id="app">
    <div v-if="!loggedIn" class="login-container">
      <h2>Login</h2>
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
            Number
            <span class="sort-arrow" @click="setSort('Number', 'desc')">&#8595;</span>
            <span class="sort-arrow" @click="setSort('Number', 'asc')">&#8593;</span>
          </th>
          <th>
            Members_Name
            <span class="sort-arrow" @click="setSort('Members_Name', 'asc')">&#8593;</span>
            <span class="sort-arrow" @click="setSort('Members_Name', 'desc')">&#8595;</span>
          </th>
          <th>
            Member_Type
            <span class="sort-arrow" @click="setSort('Member_Type', 'asc')">&#8593;</span>
            <span class="sort-arrow" @click="setSort('Member_Type', 'desc')">&#8595;</span>
          </th>
          <th>
            Paid_Up_2026
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="member in sortedMembers" :key="member.id || member.Number">
          <td>{{ member.Number }}</td>
          <td>{{ member.Members_Name }}</td>
          <td>{{ member.Member_Type }}</td>
          <td>{{ member.Paid_Up_2026 }}</td>
        </tr>
      </tbody>
    </table>
    <div class="pagination-controls">
      <button :disabled="currentPage === 1" @click="prevPage">Previous Page</button>
      <span>Page {{ currentPage }} of {{ totalPages }}</span>
      <button :disabled="currentPage === totalPages" @click="nextPage">Next Page</button>
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
      <h2>Lookup Member by Number</h2>
      <form @submit.prevent="lookupMember">
        <input v-model="lookupNumber" placeholder="Membership Number" required />
        <button type="submit">Lookup</button>
      </form>
      <div v-if="lookupError" style="color: red;">{{ lookupError }}</div>
      <table v-if="lookupResult">
        <tr>
          <th v-for="(value, key) in lookupResult" :key="key">{{ key }}</th>
        </tr>
        <tr>
          <td v-for="(value, key) in lookupResult" :key="key">{{ value }}</td>
        </tr>
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
      sortKey: 'Number',
      sortOrder: 'desc',
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
      loggedInUser: null
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
    }
  },
  created() {
    if (this.loggedIn) {
      this.fetchMembers();
    }
  },
  methods: {
    setSort(key, order) {
      this.sortKey = key;
      this.sortOrder = order;
    },
    fetchMembers() {
      const offset = (this.currentPage - 1) * this.pageSize;
      axios.get('http://localhost:5000/members', {
        params: { limit: this.pageSize, offset }
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
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
}
#app .member-table th, #app .member-table td {
  border: 1px solid #ccc;
  padding: 8px;
  text-align: left;
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
#app {
  max-width: 600px;
  margin: auto;
  font-family: Arial, sans-serif;
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
</style>
