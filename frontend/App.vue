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
    <h1>Fishing Club Members</h1>
    <form @submit.prevent="addMember">
      <input v-model="newMember.name" placeholder="Name" required />
      <input v-model="newMember.email" placeholder="Email" />
      <input v-model="newMember.phone" placeholder="Phone" />
      <input v-model="newMember.membership_type" placeholder="Membership Type" />
      <button type="submit">Add Member</button>
    </form>
    <ul>
      <li v-for="member in members" :key="member.id">
        {{ member.name }} - {{ member.email }} - {{ member.phone }} - {{ member.membership_type }}
        <button @click="editMember(member)">Edit</button>
        <button @click="deleteMember(member.id)">Delete</button>
      </li>
    </ul>
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
  created() {
    if (this.loggedIn) {
      this.fetchMembers();
    }
  },
  methods: {
    fetchMembers() {
      axios.get('http://localhost:5000/members').then(res => {
        this.members = res.data;
      });
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
