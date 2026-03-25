<template>
  <div id="app">
    <!-- Header bar -->
    <table class="logo-table">
      <tbody>
        <tr>
          <td class="logo-cell">
            <a href="/" aria-label="Go to member login">
              <img src="./logos/HLaS.png" alt="HLaS logo" class="app-logo" />
            </a>
          </td>
          <td class="admin-title-cell">
            <span class="admin-title">Club Administration</span>
          </td>
          <td class="logo-spacer"></td>
          <td v-if="loggedIn" class="logout-cell">
            <button type="button" class="logout-button" @click="logout">Log Out</button>
          </td>
        </tr>
      </tbody>
    </table>
    <!-- ...rest of your template code (login, admin-container, tabs, etc.) should go here... -->
  </div>
</template>

<script>
export default {
  // ...existing JS code (data, created, computed, methods, etc.) goes here, wrapped in export default
  // For example:
  // data() { return { ... }; },
  // created() { ... },
  // computed: { ... },
  // methods: { ... }
  // ===== FIELD ORDER TAB METHODS =====
  loadFieldOrder() {
    // Debug: log when called, API_BASE_URL, and Authorization header
    // eslint-disable-next-line no-console
    console.log('[AdminApp.vue] loadFieldOrder() called. API_BASE_URL:', API_BASE_URL);
    const auth = this.authHeaders();
    // eslint-disable-next-line no-console
    console.log('[AdminApp.vue] loadFieldOrder() Authorization header:', auth);
    axios.get(`${API_BASE_URL}/admin/field-order`, { headers: auth })
      .then(res => {
        // eslint-disable-next-line no-console
        console.log('[AdminApp.vue] /admin/field-order response:', res);
        this.fieldOrder = res.data.field_order || {};
        // Force reactivity for fieldOrderContexts
        this.fieldOrderContexts = [];
        this.$nextTick(() => {
          this.fieldOrderContexts = Object.keys(this.fieldOrder);
          this.fieldOrderContext = this.fieldOrderContexts[0] || 'default';
          this.loadFieldOrderContext();
        });
      })
      .catch(err => {
        // eslint-disable-next-line no-console
        console.error('[AdminApp.vue] /admin/field-order error:', err, err?.response);
        this.fieldOrderStatus = err.response?.data?.error || 'Failed to load field order';
        this.fieldOrderStatusError = true;
      });
  },
  loadFieldOrderContext() {
    this.fieldOrderEdit = (this.fieldOrder[this.fieldOrderContext] || []).slice();
  },
  moveField(idx, dir) {
    const newIdx = idx + dir;
    if (newIdx < 0 || newIdx >= this.fieldOrderEdit.length) return;
    const arr = this.fieldOrderEdit;
    [arr[idx], arr[newIdx]] = [arr[newIdx], arr[idx]];
    this.fieldOrderEdit = arr.slice();
  },
  saveFieldOrder() {
    const updated = { ...this.fieldOrder, [this.fieldOrderContext]: this.fieldOrderEdit };
    axios.post(`${API_BASE_URL}/admin/field-order`, updated, { headers: this.authHeaders() })
      .then(() => {
        this.fieldOrderStatus = 'Field order updated.';
        this.fieldOrderStatusError = false;
        this.fieldOrder = updated;
      })
      .catch(err => {
        this.fieldOrderStatus = err.response?.data?.error || 'Failed to update field order';
        this.fieldOrderStatusError = true;
      });
  },
  authHeaders() {
    return { Authorization: `Bearer ${this.adminToken}` };
  },
  showStatus(msg, isError = false) {
    this.statusMsg = msg;
    this.statusMsgError = isError;
    setTimeout(() => { this.statusMsg = ''; }, 4000);
    },
    login() {
      this.loginError = '';
      axios.post(`${API_BASE_URL}/admin/login`, {
        username: this.loginUsername,
        password: this.loginPassword,
      })
        .then(res => {
          if (res.data.success) {
            this.adminToken = res.data.token;
            localStorage.setItem('hlasAdminToken', this.adminToken);
            this.loggedIn = true;
            this.loginPassword = '';
            this.loadClubs();
            // Debug: call loadFieldOrder after login
            // eslint-disable-next-line no-console
            console.log('[AdminApp.vue] login() success, calling loadFieldOrder()');
            this.loadFieldOrder();
          } else {
            this.loginError = res.data.error || 'Login failed';
          }
        })
        .catch(err => {
          this.loginError = err.response?.data?.error || 'Login failed';
        });
    },
    logout() {
      axios.post(`${API_BASE_URL}/admin/logout`, {}, { headers: this.authHeaders() }).catch(() => {});
      this.adminToken = null;
      localStorage.removeItem('hlasAdminToken');
      this.loggedIn = false;
      this.clubs = [];
      this.loginUsername = '';
      this.loginPassword = '';
    },
    loadClubs() {
      axios.get(`${API_BASE_URL}/admin/clubs`, { headers: this.authHeaders() })
        .then(res => { this.clubs = res.data.clubs || []; })
        .catch(err => {
          if (err.response?.status === 401) {
            this.logout();
          }
        });
    },
    startEdit(club) {
      this.editingShortName = club.shortName;
      this.editForm = { ...club };
    },
    cancelEdit() {
      this.editingShortName = null;
      this.editForm = {};
    },
    saveEdit() {
      axios.put(`${API_BASE_URL}/admin/clubs/${encodeURIComponent(this.editingShortName)}`,
        this.editForm,
        { headers: this.authHeaders() })
        .then(() => {
          this.editingShortName = null;
          this.editForm = {};
          this.loadClubs();
          this.showStatus('Club updated successfully.');
        })
        .catch(err => {
          this.showStatus(err.response?.data?.error || 'Update failed', true);
        });
    },
    deleteClub(shortName) {
      if (!window.confirm(`Delete club "${shortName}"? This cannot be undone.`)) return;
      axios.delete(`${API_BASE_URL}/admin/clubs/${encodeURIComponent(shortName)}`,
        { headers: this.authHeaders() })
        .then(() => {
          this.loadClubs();
          this.showStatus(`Club "${shortName}" deleted.`);
        })
        .catch(err => {
          this.showStatus(err.response?.data?.error || 'Delete failed', true);
        });
    },
    onNewClubLogoChange(event) {
      const file = event.target.files && event.target.files.length ? event.target.files[0] : null;
      if (!file) {
        this.newClubLogoFile = null;
        return;
      }
      const isPngType = file.type === 'image/png' || file.name.toLowerCase().endsWith('.png');
      if (!isPngType) {
        this.newClubLogoFile = null;
        event.target.value = '';
        this.showStatus('Logo must be a PNG file.', true);
        return;
      }
      this.newClubLogoFile = file;
    },
    addClub() {
      if (!this.newClub.shortName.trim()) {
        this.showStatus('Short Name is required.', true);
        return;
      }
      const formData = new FormData();
      formData.append('shortName', this.newClub.shortName);
      formData.append('fullName', this.newClub.fullName);
      formData.append('websiteUrl', this.newClub.websiteUrl);
      formData.append('adminEmail', this.newClub.adminEmail);
      formData.append('description', this.newClub.description);
      if (this.newClubLogoFile) {
        formData.append('logoFile', this.newClubLogoFile);
      }

      axios.post(`${API_BASE_URL}/admin/clubs`, formData, { headers: this.authHeaders() })
        .then(() => {
          this.newClub = { shortName: '', fullName: '', websiteUrl: '', adminEmail: '', description: '' };
          this.newClubLogoFile = null;
          if (this.$refs.newClubLogoInput) {
            this.$refs.newClubLogoInput.value = '';
          }
          this.loadClubs();
          this.showStatus('Club added successfully.');
        })
        .catch(err => {
          this.showStatus(err.response?.data?.error || 'Add failed', true);
        });
    },
    loadSmtpConfig() {
      if (!this.smtpSelectedClub) { this.smtpForm = null; return; }
      this.smtpStatusMsg = '';
      axios.get(`${API_BASE_URL}/admin/clubs/${encodeURIComponent(this.smtpSelectedClub)}/smtp`,
        { headers: this.authHeaders() })
        .then(res => {
          this.smtpForm = { ...res.data.smtp };
        })
        .catch(err => {
          this.smtpStatusMsg = err.response?.data?.error || 'Failed to load SMTP config';
          this.smtpStatusError = true;
        });
    },
    saveSmtpConfig() {
      this.smtpStatusMsg = '';
      axios.put(`${API_BASE_URL}/admin/clubs/${encodeURIComponent(this.smtpSelectedClub)}/smtp`,
        this.smtpForm,
        { headers: this.authHeaders() })
        .then(() => {
          this.smtpStatusMsg = 'SMTP settings saved.';
          this.smtpStatusError = false;
          this.loadSmtpConfig(); // Reload to refresh passwordSet
        })
        .catch(err => {
          this.smtpStatusMsg = err.response?.data?.error || 'Save failed';
          this.smtpStatusError = true;
        });
    },
    testSmtpConfig() {
      if (!this.smtpTestEmail.trim()) {
        this.smtpStatusMsg = 'Please enter a recipient email address for the test.';
        this.smtpStatusError = true;
        return;
      }
      this.smtpStatusMsg = 'Sending test email…';
      this.smtpStatusError = false;
      axios.post(`${API_BASE_URL}/admin/clubs/${encodeURIComponent(this.smtpSelectedClub)}/smtp/test`,
        { toEmail: this.smtpTestEmail },
        { headers: this.authHeaders() })
        .then(res => {
          this.smtpStatusMsg = res.data.message || 'Test email sent successfully.';
          this.smtpStatusError = false;
        })
        .catch(err => {
          this.smtpStatusMsg = err.response?.data?.error || 'Test email failed';
          this.smtpStatusError = true;
        });
    },

    // ── User Administration ──────────────────────────────────────────────────
    switchTab(tab) {
      this.activeTab = tab;
      if (tab === 'users' && !this.uaUsers.length && !this.uaLoading) {
        this.loadUserAdmin();
      }
      if (tab !== 'users') {
        this.resetMergeState();
        this.closeGrantModal();
        this.uaGrant.statusMsg = '';
        this.uaGrant.statusError = false;
      }
    },

    loadUserAdmin() {
      this.uaLoading = true;
      this.uaStatusMsg = '';
      Promise.all([
        axios.get(`${API_BASE_URL}/admin/users`,       { headers: this.authHeaders() }),
        axios.get(`${API_BASE_URL}/admin/roles`,       { headers: this.authHeaders() }),
        axios.get(`${API_BASE_URL}/admin/clubs-list`,  { headers: this.authHeaders() }),
      ]).then(([usersRes, rolesRes, clubsRes]) => {
        this.uaUsers          = usersRes.data.users  || [];
        this.uaAvailableRoles = rolesRes.data.roles  || [];
        this.uaClubs          = clubsRes.data.clubs  || [];
      }).catch(err => {
        if (err.response?.status === 401) { this.logout(); return; }
        this.uaStatusMsg  = err.response?.data?.error || 'Failed to load user data';
        this.uaStatusError = true;
      }).finally(() => {
        this.uaLoading = false;
      });
    },

    uaSearchDebounced() {
      clearTimeout(this.uaSearchTimer);
      if (this.uaSearch.length < 2) { this.uaSearchResults = []; return; }
      this.uaSearchTimer = setTimeout(() => {
        axios.get(`${API_BASE_URL}/admin/users/search`,
          { params: { q: this.uaSearch }, headers: this.authHeaders() }
        ).then(res => {
          this.uaSearchResults = res.data.members || [];
        }).catch(() => { this.uaSearchResults = []; });
      }, 300);
    },

    uaMergeSearchDebounced(which) {
      const isSource = which === 'source';
      const query = (isSource ? this.uaMerge.sourceQuery : this.uaMerge.targetQuery) || '';
      const timerKey = isSource ? 'sourceTimer' : 'targetTimer';
      const resultsKey = isSource ? 'sourceResults' : 'targetResults';

      clearTimeout(this.uaMerge[timerKey]);
      if (query.length < 2) {
        this.uaMerge[resultsKey] = [];
        return;
      }

      this.uaMerge[timerKey] = setTimeout(() => {
        axios.get(`${API_BASE_URL}/admin/users/search`, {
          params: { q: query },
          headers: this.authHeaders(),
        }).then(res => {
          const list = res.data.members || [];
          const oppositeUserId = isSource ? this.uaMerge.targetUser?.userId : this.uaMerge.sourceUser?.userId;
          this.uaMerge[resultsKey] = list.filter(u => u.userId !== oppositeUserId);
        }).catch(() => {
          this.uaMerge[resultsKey] = [];
        });
      }, 300);
    },

    selectMergeUser(which, user) {
      if (which === 'source') {
        this.uaMerge.sourceUser = user;
        this.uaMerge.sourceQuery = user.username || '';
        this.uaMerge.sourceResults = [];
      } else {
        this.uaMerge.targetUser = user;
        this.uaMerge.targetQuery = user.username || '';
        this.uaMerge.targetResults = [];
      }
      this.uaMerge.statusMsg = '';
      this.uaMerge.statusError = false;
    },

    resetMergeState() {
      this.uaMerge.sourceQuery = '';
      this.uaMerge.targetQuery = '';
      this.uaMerge.sourceResults = [];
      this.uaMerge.targetResults = [];
      this.uaMerge.sourceUser = null;
      this.uaMerge.targetUser = null;
      this.uaMerge.statusMsg = '';
      this.uaMerge.statusError = false;
      this.uaMerge.busy = false;
      this.uaMergeCleanup.statusMsg = '';
      this.uaMergeCleanup.statusError = false;
      this.uaMergeCleanup.lastResult = null;
      this.uaMergeCleanup.busy = false;
    },

    mergeUsers() {
      if (!this.uaCanMerge) {
        this.uaMerge.statusMsg = 'Select different source and target users.';
        this.uaMerge.statusError = true;
        return;
      }

      const source = this.uaMerge.sourceUser;
      const target = this.uaMerge.targetUser;
      const confirmed = window.confirm(
        `Merge source user "${source.username}" (id ${source.userId}) into target user "${target.username}" (id ${target.userId})?`
      );
      if (!confirmed) return;

      this.uaMerge.busy = true;
      this.uaMerge.statusMsg = '';
      this.uaMerge.statusError = false;

      axios.post(`${API_BASE_URL}/admin/users/merge`, {
        sourceUserId: source.userId,
        targetUserId: target.userId,
      }, {
        headers: this.authHeaders(),
      }).then(res => {
        const summary = res.data.summary || {};
        this.uaMerge.statusMsg = `Merge complete. Links moved: ${summary.movedLinks || 0}, assignments moved: ${summary.movedAssignments || 0}.`;
        this.uaMerge.statusError = false;
        this.loadUserAdmin();
      }).catch(err => {
        this.uaMerge.statusMsg = err.response?.data?.error || 'Merge failed';
        this.uaMerge.statusError = true;
      }).finally(() => {
        this.uaMerge.busy = false;
      });
    },

    runMergeCleanup(dryRun = true) {
      if (!dryRun) {
        const confirmed = window.confirm('Apply merge cleanup now? This will merge eligible duplicate active users.');
        if (!confirmed) return;
      }

      this.uaMergeCleanup.busy = true;
      this.uaMergeCleanup.statusMsg = '';
      this.uaMergeCleanup.statusError = false;

      axios.post(`${API_BASE_URL}/admin/users/merge/cleanup`, {
        dryRun,
      }, {
        headers: this.authHeaders(),
      }).then(res => {
        const payload = res.data || {};
        this.uaMergeCleanup.lastResult = payload;
        this.uaMergeCleanup.statusMsg = dryRun
          ? `Dry run complete. Planned merges: ${payload.mergeCount || 0}.`
          : `Cleanup applied. Merges completed: ${payload.mergeCount || 0}.`;
        this.uaMergeCleanup.statusError = false;
        if (!dryRun) this.loadUserAdmin();
      }).catch(err => {
        this.uaMergeCleanup.statusMsg = err.response?.data?.error || 'Cleanup failed';
        this.uaMergeCleanup.statusError = true;
      }).finally(() => {
        this.uaMergeCleanup.busy = false;
      });
    },

    openGrantModal(member) {
      this.uaGrant = { visible: true, member, roleCode: '', clubId: null, statusMsg: '', statusError: false };
    },

    closeGrantModal() {
      this.uaGrant.visible = false;
    },

    grantRole() {
      if (!this.uaGrant.roleCode) {
        this.uaGrant.statusMsg   = 'Please select a role.';
        this.uaGrant.statusError = true;
        return;
      }
      const selectedRole = this.uaAvailableRoles.find(r => r.code === this.uaGrant.roleCode);
      if (selectedRole?.scopeType === 'club' && !this.uaGrant.clubId) {
        this.uaGrant.statusMsg   = 'Please select a club for this role.';
        this.uaGrant.statusError = true;
        return;
      }
      axios.post(
        `${API_BASE_URL}/admin/users/${this.uaGrant.member.userId}/roles`,
        { roleCode: this.uaGrant.roleCode, clubId: this.uaGrant.clubId || null },
        { headers: this.authHeaders() }
      ).then(() => {
        this.closeGrantModal();
        this.uaSearch = '';
        this.uaSearchResults = [];
        this.uaShowStatus('Role granted successfully.');
        this.loadUserAdmin();
      }).catch(err => {
        this.uaGrant.statusMsg   = err.response?.data?.error || 'Grant failed';
        this.uaGrant.statusError = true;
      });
    },

    revokeRole(user, assignment) {
      const scopeLabel = assignment.roleClubShortName
        ? ` (${assignment.roleClubShortName})`
        : ' (global)';
      if (!window.confirm(`Revoke "${assignment.roleName}"${scopeLabel} from ${user.username}?`)) return;
      axios.delete(
        `${API_BASE_URL}/admin/users/${user.userId}/roles/${assignment.assignmentId}`,
        { headers: this.authHeaders() }
      ).then(() => {
        this.uaShowStatus('Role revoked successfully.');
        this.loadUserAdmin();
      }).catch(err => {
        this.uaStatusMsg  = err.response?.data?.error || 'Revoke failed';
        this.uaStatusError = true;
      });
    },

    uaShowStatus(msg, isError = false) {
      this.uaStatusMsg   = msg;
      this.uaStatusError = isError;
      setTimeout(() => { this.uaStatusMsg = ''; }, 4000);
    },
</script>
  },
}
</script>
</script>

<style>
body {
  margin: 0;
  font-family: Helvetica, Arial, sans-serif;
}
#app .logo-table {
  width: 100%;
  border-collapse: collapse;
  background: #f8f8f8;
  border-bottom: 1px solid #ddd;
  padding: 4px 0;
}
#app .logo-cell {
  padding: 4px 10px;
  vertical-align: middle;
}
#app .app-logo {
  height: 50px;
  cursor: default;
}
#app .admin-title-cell {
  vertical-align: middle;
  padding-left: 12px;
}
#app .admin-title {
  font-size: 18pt;
  font-weight: bold;
  color: #333;
}
#app .logo-spacer {
  width: 100%;
}
#app .logout-cell {
  padding: 4px 12px;
  white-space: nowrap;
  vertical-align: middle;
}
#app .logout-button {
  padding: 6px 14px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 9pt;
  cursor: pointer;
}
#app .login-container {
  max-width: 420px;
  margin: 60px auto;
}
#app .login-container h2 {
  margin-bottom: 20px;
}
#app .form-field {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
#app .form-field label {
  width: 90px;
  font-size: 10pt;
}
#app .form-field input {
  flex: 1;
  padding: 6px;
  font-size: 10pt;
  font-family: Helvetica, Arial, sans-serif;
}
#app .login-container button[type="submit"] {
  margin-top: 10px;
  padding: 7px 20px;
  font-size: 10pt;
  font-family: Helvetica, Arial, sans-serif;
  cursor: pointer;
}
#app .admin-container {
  max-width: 1200px;
  margin: 24px auto;
  padding: 0 16px;
}
#app .admin-container h1 {
  font-size: 16pt;
  margin-bottom: 14px;
}
#app .admin-container h2 {
  font-size: 13pt;
  margin-top: 30px;
  margin-bottom: 10px;
}
#app .clubs-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9pt;
  margin-bottom: 16px;
}
#app .clubs-table th,
#app .clubs-table td {
  border: 1px solid #ccc;
  padding: 7px 9px;
  text-align: left;
  vertical-align: top;
}
#app .clubs-table th {
  background: #f0f0f0;
  font-size: 10pt;
  white-space: nowrap;
}
#app .clubs-table .desc-cell {
  max-width: 280px;
  font-size: 8.5pt;
  color: #444;
}
#app .clubs-table .actions-cell {
  white-space: nowrap;
  text-align: center;
  vertical-align: middle;
}
#app .clubs-table .actions-cell button {
  margin: 2px 3px;
  padding: 4px 10px;
  font-size: 8.5pt;
  font-family: Helvetica, Arial, sans-serif;
  cursor: pointer;
}
#app .delete-btn {
  color: #c00;
}
#app .save-btn {
  background: #2a7;
  color: white;
  border: 1px solid #1a6;
}
#app .edit-row {
  background: #fffbe6;
}
#app .field-input {
  width: 100%;
  box-sizing: border-box;
  padding: 5px;
  font-size: 9pt;
  font-family: Helvetica, Arial, sans-serif;
  border: 1px solid #aaa;
}
#app .short-input {
  width: 90px;
}
#app .desc-textarea {
  resize: vertical;
}
#app .smtp-club-selector {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}
#app .smtp-form-panel {
  background: #fafafa;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 16px 20px;
  margin-bottom: 30px;
  max-width: 860px;
}
#app .smtp-form-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 14px;
}
#app .smtp-form-table td {
  padding: 6px 8px;
  vertical-align: middle;
  font-size: 9pt;
}
#app .smtp-label {
  width: 110px;
  font-weight: 600;
  white-space: nowrap;
  color: #333;
}
#app .smtp-hint {
  color: #666;
  font-size: 8.5pt;
  padding-left: 12px;
}
#app .smtp-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
#app .error-msg {
  color: #c00;
  margin: 8px 0;
  font-size: 10pt;
}
#app .success-msg {
  color: #1a7a3a;
  margin: 8px 0;
  font-size: 10pt;
}
/* ── Tab navigation ───────────────────────────────────────────────────────── */
#app .tab-nav {
  display: flex;
  gap: 4px;
  border-bottom: 2px solid #ccc;
  margin-bottom: 20px;
}
#app .tab-btn {
  padding: 7px 20px;
  font-size: 10pt;
  font-family: Helvetica, Arial, sans-serif;
  background: #f0f0f0;
  border: 1px solid #ccc;
  border-bottom: none;
  cursor: pointer;
  border-radius: 4px 4px 0 0;
  color: #555;
}
#app .tab-btn-active {
  background: #fff;
  border-color: #ccc;
  border-bottom: 2px solid #fff;
  margin-bottom: -2px;
  color: #111;
  font-weight: bold;
}
/* ── User Administration panel ────────────────────────────────────────────── */
#app .ua-panel {
  background: #fafafa;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 16px 20px;
  margin-bottom: 28px;
  max-width: 900px;
}
#app .ua-search-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
#app .ua-hint {
  font-size: 9pt;
  color: #888;
}
#app .ua-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9pt;
  margin-bottom: 10px;
}
#app .ua-table th,
#app .ua-table td {
  border: 1px solid #ccc;
  padding: 6px 9px;
  text-align: left;
  vertical-align: middle;
}
#app .ua-table th {
  background: #f0f0f0;
  font-size: 9.5pt;
  white-space: nowrap;
}
#app .roles-cell {
  min-width: 240px;
}
/* Role badges */
#app .role-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 7px;
  border-radius: 12px;
  font-size: 8pt;
  font-weight: 600;
  margin: 2px 3px 2px 0;
  white-space: nowrap;
}
#app .role-app-owner   { background: #4a1a8a; color: #fff; }
#app .role-app-admin   { background: #1a4a8a; color: #fff; }
#app .role-club-admin   { background: #1a6a3a; color: #fff; }
#app .role-club-manager { background: #7a5a1a; color: #fff; }
#app .role-user         { background: #e0e0e0; color: #333; }
#app .role-revoke-btn {
  background: none;
  border: none;
  color: inherit;
  opacity: 0.7;
  cursor: pointer;
  font-size: 11pt;
  line-height: 1;
  padding: 0 0 0 2px;
}
#app .role-revoke-btn:hover {
  opacity: 1;
}
#app .ua-add-role-btn {
  display: inline-block;
  font-size: 8pt;
  padding: 2px 7px;
  border-radius: 12px;
  border: 1px dashed #999;
  background: none;
  color: #555;
  cursor: pointer;
  margin-left: 2px;
}
#app .ua-add-role-btn:hover {
  border-color: #444;
  color: #222;
}
/* ── Modal ────────────────────────────────────────────────────────────────── */
#app .modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
#app .modal-box {
  background: #fff;
  border-radius: 8px;
  padding: 28px 32px;
  min-width: 420px;
  max-width: 520px;
  box-shadow: 0 8px 32px rgba(0,0,0,.25);
}
#app .modal-actions {
  margin-top: 16px;
  display: flex;
  align-items: center;
}
</style>
