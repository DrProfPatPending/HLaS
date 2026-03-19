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

    <!-- Admin login -->
    <div v-if="!loggedIn" class="login-container">
      <h2>Admin Login</h2>
      <form @submit.prevent="login">
        <div class="form-field">
          <label for="admin-username">Username:</label>
          <input id="admin-username" v-model="loginUsername" placeholder="Username" required />
        </div>
        <div class="form-field">
          <label for="admin-password">Password:</label>
          <input id="admin-password" v-model="loginPassword" type="password" placeholder="Password" required />
        </div>
        <button type="submit">Login</button>
      </form>
      <div v-if="loginError" class="error-msg">{{ loginError }}</div>
    </div>

    <!-- Club management & user admin -->
    <div v-else class="admin-container">
      <!-- Tab navigation -->
      <div class="tab-nav">
        <button :class="['tab-btn', activeTab === 'clubs' ? 'tab-btn-active' : '']" @click="switchTab('clubs')">Clubs Configuration</button>
        <button :class="['tab-btn', activeTab === 'users' ? 'tab-btn-active' : '']" @click="switchTab('users')">User Administration</button>
      </div>

      <!-- ===== CLUBS TAB ===== -->
      <div v-show="activeTab === 'clubs'">
      <h1>Clubs Configuration</h1>

      <div v-if="statusMsg" :class="statusMsgError ? 'error-msg' : 'success-msg'">{{ statusMsg }}</div>

      <!-- Clubs table -->
      <table class="clubs-table">
        <thead>
          <tr>
            <th>Short Name</th>
            <th>Full Name</th>
            <th>Website URL</th>
            <th>Admin Email</th>
            <th>Description</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="club in clubs" :key="club.shortName">
            <!-- Read-only row -->
            <tr v-if="editingShortName !== club.shortName">
              <td>{{ club.shortName }}</td>
              <td>{{ club.fullName }}</td>
              <td>
                <a v-if="club.websiteUrl" :href="club.websiteUrl" target="_blank" rel="noopener noreferrer">{{ club.websiteUrl }}</a>
                <span v-else>-</span>
              </td>
              <td>
                <a v-if="club.adminEmail" :href="`mailto:${club.adminEmail}`">{{ club.adminEmail }}</a>
                <span v-else>-</span>
              </td>
              <td class="desc-cell">{{ club.description }}</td>
              <td class="actions-cell">
                <button type="button" @click="startEdit(club)">Edit</button>
                <button type="button" class="delete-btn" @click="deleteClub(club.shortName)">Delete</button>
              </td>
            </tr>
            <!-- Inline edit row -->
            <tr v-else class="edit-row">
              <td><input v-model="editForm.shortName" disabled class="field-input short-input" title="Short name cannot be changed" /></td>
              <td><input v-model="editForm.fullName" class="field-input" /></td>
              <td><input v-model="editForm.websiteUrl" class="field-input" /></td>
              <td><input v-model="editForm.adminEmail" class="field-input" /></td>
              <td><textarea v-model="editForm.description" class="field-input desc-textarea" rows="3"></textarea></td>
              <td class="actions-cell">
                <button type="button" class="save-btn" @click="saveEdit">Save</button>
                <button type="button" @click="cancelEdit">Cancel</button>
              </td>
            </tr>
          </template>
        </tbody>
      </table>

      <!-- SMTP / Email Settings per club -->
      <h2>Email / SMTP Settings</h2>
      <p style="font-size:9pt;color:#555;">Configure the outgoing mail account for each club's newsletters. Leave Host empty to fall back to server-level environment variables.</p>
      <div class="smtp-club-selector">
        <label for="smtp-club-select"><strong>Club:</strong></label>
        <select id="smtp-club-select" v-model="smtpSelectedClub" class="field-input short-input" style="width:160px;margin-left:8px;" @change="loadSmtpConfig">
          <option value="">Select club…</option>
          <option v-for="c in clubs" :key="c.shortName" :value="c.shortName">{{ c.shortName }} – {{ c.fullName }}</option>
        </select>
      </div>
      <div v-if="smtpSelectedClub && smtpForm" class="smtp-form-panel">
        <div v-if="smtpStatusMsg" :class="smtpStatusError ? 'error-msg' : 'success-msg'">{{ smtpStatusMsg }}</div>
        <table class="smtp-form-table">
          <tbody>
            <tr>
              <td class="smtp-label">SMTP Host</td>
              <td><input v-model="smtpForm.host" class="field-input" placeholder="e.g. smtp.gmail.com" /></td>
              <td class="smtp-hint">Hostname of your outgoing mail server</td>
            </tr>
            <tr>
              <td class="smtp-label">Port</td>
              <td><input v-model.number="smtpForm.port" type="number" class="field-input" placeholder="587" style="width:90px;" /></td>
              <td class="smtp-hint">587 (STARTTLS) or 465 (SSL)</td>
            </tr>
            <tr>
              <td class="smtp-label">Username</td>
              <td><input v-model="smtpForm.username" class="field-input" placeholder="user@example.com" autocomplete="off" /></td>
              <td class="smtp-hint">Login username for the mail server</td>
            </tr>
            <tr>
              <td class="smtp-label">Password</td>
              <td><input v-model="smtpForm.password" type="password" class="field-input" placeholder="Leave blank to keep current" autocomplete="new-password" /></td>
              <td class="smtp-hint"><span v-if="smtpForm.passwordSet" style="color:#1a7a3a;">✓ Password is set</span><span v-else style="color:#888;">No password stored</span> — leave blank to keep existing</td>
            </tr>
            <tr>
              <td class="smtp-label">From Email</td>
              <td><input v-model="smtpForm.fromEmail" class="field-input" placeholder="e.g. committee@gaaffs.org" /></td>
              <td class="smtp-hint">The email address newsletters are sent <em>from</em></td>
            </tr>
            <tr>
              <td class="smtp-label">From Name</td>
              <td><input v-model="smtpForm.fromName" class="field-input" placeholder="e.g. GAAFFS Newsletter" /></td>
              <td class="smtp-hint">Friendly name shown to recipients</td>
            </tr>
            <tr>
              <td class="smtp-label">Encryption</td>
              <td>
                <label style="margin-right:14px;"><input type="checkbox" v-model="smtpForm.useTls" /> STARTTLS (port 587)</label>
                <label><input type="checkbox" v-model="smtpForm.useSsl" /> SSL/TLS (port 465)</label>
              </td>
              <td class="smtp-hint">Enable STARTTLS or direct SSL – enable one, not both</td>
            </tr>
          </tbody>
        </table>
        <div class="smtp-actions">
          <button type="button" class="save-btn" @click="saveSmtpConfig">Save SMTP Settings</button>
          <span style="margin:0 10px;">|</span>
          <label for="smtp-test-to">Test to:</label>
          <input id="smtp-test-to" v-model="smtpTestEmail" class="field-input" style="width:220px;display:inline-block;margin:0 6px;" placeholder="your@email.com" />
          <button type="button" @click="testSmtpConfig">Send Test Email</button>
        </div>
      </div>

      <!-- Add new club -->
      <h2>Add New Club</h2>
      <table class="clubs-table">
        <thead>
          <tr>
            <th>Short Name</th>
            <th>Full Name</th>
            <th>Website URL</th>
            <th>Admin Email</th>
            <th>Description</th>
            <th>Logo (PNG)</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><input v-model="newClub.shortName" class="field-input short-input" placeholder="e.g. ABC" /></td>
            <td><input v-model="newClub.fullName" class="field-input" placeholder="Full club name" /></td>
            <td><input v-model="newClub.websiteUrl" class="field-input" placeholder="https://..." /></td>
            <td><input v-model="newClub.adminEmail" class="field-input" placeholder="admin@example.com" /></td>
            <td><textarea v-model="newClub.description" class="field-input desc-textarea" rows="3" placeholder="Club description"></textarea></td>
            <td>
              <input
                ref="newClubLogoInput"
                type="file"
                accept="image/png"
                class="field-input"
                @change="onNewClubLogoChange"
              />
            </td>
            <td class="actions-cell">
              <button type="button" class="save-btn" @click="addClub">Add Club</button>
            </td>
          </tr>
        </tbody>
      </table>
      </div><!-- end clubs tab -->

      <!-- ===== USER ADMINISTRATION TAB ===== -->
      <div v-show="activeTab === 'users'">
        <h1>User Administration</h1>
        <p style="font-size:9pt;color:#555;">Manage role assignments for members across all clubs. Changes take effect immediately.</p>

        <div v-if="uaStatusMsg" :class="uaStatusError ? 'error-msg' : 'success-msg'">{{ uaStatusMsg }}</div>

        <!-- Search panel to find a member and grant a role -->
        <div class="ua-panel">
          <h2>Grant Role to Member</h2>
          <div class="ua-search-row">
            <input
              v-model="uaSearch"
              @input="uaSearchDebounced"
              placeholder="Search by username or name (min 2 chars)…"
              class="field-input"
              style="width:340px;"
            />
            <span v-if="uaSearch.length >= 2 && !uaSearchResults.length" class="ua-hint">No results.</span>
          </div>
          <div v-if="uaSearchResults.length" style="margin-top:8px;">
            <table class="ua-table">
              <thead><tr><th>Username</th><th>Name</th><th>Club</th><th></th></tr></thead>
              <tbody>
                <tr v-for="m in uaSearchResults" :key="m.userId">
                  <td>{{ m.username }}</td>
                  <td>{{ m.displayName }}</td>
                  <td>{{ m.clubs && m.clubs.map(c => c.shortName).join(', ') }}</td>
                  <td><button type="button" class="save-btn" style="white-space:nowrap;" @click="openGrantModal(m)">Grant Role…</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="uaCanAccessMerge" class="ua-panel">
          <h2>Merge Users</h2>
          <p style="font-size:9pt;color:#555;margin-top:0;">Merge a duplicate source user into a target user. This requires global admin permission.</p>

          <div class="ua-search-row" style="margin-bottom:8px;">
            <label style="width:70px;">Source:</label>
            <input
              v-model="uaMerge.sourceQuery"
              @input="uaMergeSearchDebounced('source')"
              placeholder="Search source user (min 2 chars)…"
              class="field-input"
              style="width:340px;"
            />
          </div>
          <div v-if="uaMerge.sourceResults.length" style="margin:0 0 10px 70px;max-width:720px;">
            <table class="ua-table">
              <thead><tr><th>Username</th><th>Name</th><th>Clubs</th><th></th></tr></thead>
              <tbody>
                <tr v-for="u in uaMerge.sourceResults" :key="'src-' + u.userId">
                  <td>{{ u.username }}</td>
                  <td>{{ u.displayName }}</td>
                  <td>{{ (u.clubs || []).map(c => c.shortName).join(', ') }}</td>
                  <td><button type="button" @click="selectMergeUser('source', u)">Select</button></td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="ua-search-row" style="margin-bottom:8px;">
            <label style="width:70px;">Target:</label>
            <input
              v-model="uaMerge.targetQuery"
              @input="uaMergeSearchDebounced('target')"
              placeholder="Search target user (min 2 chars)…"
              class="field-input"
              style="width:340px;"
            />
          </div>
          <div v-if="uaMerge.targetResults.length" style="margin:0 0 10px 70px;max-width:720px;">
            <table class="ua-table">
              <thead><tr><th>Username</th><th>Name</th><th>Clubs</th><th></th></tr></thead>
              <tbody>
                <tr v-for="u in uaMerge.targetResults" :key="'tgt-' + u.userId">
                  <td>{{ u.username }}</td>
                  <td>{{ u.displayName }}</td>
                  <td>{{ (u.clubs || []).map(c => c.shortName).join(', ') }}</td>
                  <td><button type="button" @click="selectMergeUser('target', u)">Select</button></td>
                </tr>
              </tbody>
            </table>
          </div>

          <div style="font-size:9pt;color:#444;margin:8px 0;">
            <div><strong>Selected Source:</strong> <span v-if="uaMerge.sourceUser">{{ uaMerge.sourceUser.username }} — {{ uaMerge.sourceUser.displayName }} (id {{ uaMerge.sourceUser.userId }})</span><span v-else>None</span></div>
            <div><strong>Selected Target:</strong> <span v-if="uaMerge.targetUser">{{ uaMerge.targetUser.username }} — {{ uaMerge.targetUser.displayName }} (id {{ uaMerge.targetUser.userId }})</span><span v-else>None</span></div>
          </div>

          <div v-if="uaMerge.statusMsg" :class="uaMerge.statusError ? 'error-msg' : 'success-msg'">{{ uaMerge.statusMsg }}</div>
          <div class="ua-search-row">
            <button type="button" class="save-btn" :disabled="!uaCanMerge || uaMerge.busy" @click="mergeUsers">{{ uaMerge.busy ? 'Merging…' : 'Merge Users' }}</button>
            <button type="button" @click="resetMergeState">Reset</button>
          </div>

          <hr style="margin:14px 0;border:none;border-top:1px solid #ddd;" />
          <div class="ua-search-row" style="gap:8px;">
            <button type="button" :disabled="uaMergeCleanup.busy" @click="runMergeCleanup(true)">
              {{ uaMergeCleanup.busy ? 'Working…' : 'Cleanup Dry Run' }}
            </button>
            <button type="button" class="save-btn" :disabled="uaMergeCleanup.busy" @click="runMergeCleanup(false)">
              {{ uaMergeCleanup.busy ? 'Working…' : 'Apply Cleanup' }}
            </button>
            <span style="font-size:9pt;color:#666;">Auto-merges safe duplicates by email + username/display-name match.</span>
          </div>
          <div v-if="uaMergeCleanup.statusMsg" :class="uaMergeCleanup.statusError ? 'error-msg' : 'success-msg'" style="margin-top:8px;">
            {{ uaMergeCleanup.statusMsg }}
          </div>
          <div v-if="uaMergeCleanup.lastResult" style="font-size:9pt;color:#444;margin-top:4px;">
            Planned: {{ uaMergeCleanup.lastResult.mergeCount || 0 }}, Skipped: {{ (uaMergeCleanup.lastResult.skipped || []).length }}
          </div>
          <div v-if="uaMergeCleanupPreview.length" style="margin-top:8px;max-width:520px;">
            <table class="ua-table" style="margin-bottom:4px;">
              <thead>
                <tr>
                  <th style="width:220px;">Source</th>
                  <th style="width:220px;">Target</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(m, idx) in uaMergeCleanupPreview" :key="'cleanup-preview-' + idx">
                  <td>
                    <div><strong>{{ m.sourceUsername || '(no username)' }}</strong> (id {{ m.sourceUserId }})</div>
                    <div style="font-size:8.5pt;color:#666;">{{ m.sourceDisplayName || '(no name)' }}</div>
                  </td>
                  <td>
                    <div><strong>{{ m.targetUsername || '(no username)' }}</strong> (id {{ m.targetUserId }})</div>
                    <div style="font-size:8.5pt;color:#666;">{{ m.targetDisplayName || '(no name)' }}</div>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-if="uaMergeCleanupRemaining > 0" style="font-size:8.5pt;color:#666;">
              +{{ uaMergeCleanupRemaining }} more planned merge{{ uaMergeCleanupRemaining === 1 ? '' : 's' }}
            </div>
          </div>
        </div>
        <p v-else style="font-size:9pt;color:#777;margin:-8px 0 20px;">Merge Users is available only to app owners.</p>

        <!-- Role assignment table -->
        <h2>Current Role Assignments</h2>
        <div v-if="uaLoading" style="padding:12px;color:#666;">Loading…</div>
        <p v-else-if="!uaUsers.length" style="font-size:9pt;color:#888;">No members with role assignments found.</p>
        <table v-else class="ua-table" style="margin-bottom:30px;">
          <thead>
            <tr>
              <th style="width:180px;">Username</th>
              <th style="width:180px;">Name</th>
              <th style="width:110px;">Home Club</th>
              <th>Roles</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in uaUsers" :key="u.userId">
              <td>{{ u.username }}</td>
              <td>{{ u.displayName }}</td>
              <td>{{ u.homeClub || '—' }}</td>
              <td class="roles-cell">
                <span
                  v-for="a in u.assignments"
                  :key="a.assignmentId"
                  :class="['role-badge', 'role-' + a.roleCode.replace(/_/g, '-')]"
                >
                  {{ a.roleName }}<span v-if="a.roleClubShortName" style="opacity:.75;"> / {{ a.roleClubShortName }}</span>
                  <button type="button" class="role-revoke-btn" @click="revokeRole(u, a)" title="Revoke this role">×</button>
                </span>
                <button type="button" class="ua-add-role-btn" @click="openGrantModal(u)" title="Grant additional role">+ Role</button>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Grant role modal -->
        <div v-if="uaGrant.visible" class="modal-overlay" @click.self="closeGrantModal">
          <div class="modal-box">
            <h3 style="margin-top:0;">Grant Role</h3>
            <p style="margin:0 0 14px;">User: <strong>{{ uaGrant.member && uaGrant.member.username }}</strong> — {{ uaGrant.member && uaGrant.member.displayName }}</p>
            <div class="form-field">
              <label style="width:70px;">Role:</label>
              <select v-model="uaGrant.roleCode" class="field-input" style="width:220px;">
                <option value="">Select role…</option>
                <option v-for="r in uaAvailableRoles" :key="r.code" :value="r.code">
                  {{ r.name }} ({{ r.scopeType === 'global' ? 'global' : 'club-scoped' }})
                </option>
              </select>
            </div>
            <div v-if="uaGrantNeedsClub" class="form-field">
              <label style="width:70px;">Club:</label>
              <select v-model="uaGrant.clubId" class="field-input" style="width:220px;">
                <option :value="null">Select club…</option>
                <option v-for="c in uaClubs" :key="c.id" :value="c.id">{{ c.shortName }} – {{ c.fullName }}</option>
              </select>
            </div>
            <div v-if="uaGrant.statusMsg" :class="uaGrant.statusError ? 'error-msg' : 'success-msg'" style="margin:8px 0;">{{ uaGrant.statusMsg }}</div>
            <div class="modal-actions">
              <button type="button" class="save-btn" @click="grantRole">Grant Role</button>
              <button type="button" style="margin-left:8px;" @click="closeGrantModal">Cancel</button>
            </div>
          </div>
        </div>

      </div><!-- end users tab -->
    </div><!-- end admin-container -->
  </div><!-- end app -->
</template>

<script>
import axios from 'axios';

const API_BASE_URL = process.env.VUE_APP_BACKEND_URL || `${window.location.protocol}//${window.location.hostname}:5050`;

export default {
  data() {
    return {
      loggedIn: false,
      adminToken: null,
      loginUsername: '',
      loginPassword: '',
      loginError: '',
      clubs: [],
      editingShortName: null,
      editForm: {},
      newClub: { shortName: '', fullName: '', websiteUrl: '', adminEmail: '', description: '' },
      newClubLogoFile: null,
      statusMsg: '',
      statusMsgError: false,
      smtpSelectedClub: '',
      smtpForm: null,
      smtpStatusMsg: '',
      smtpStatusError: false,
      smtpTestEmail: '',
      // User administration tab
      activeTab: 'clubs',
      uaUsers: [],
      uaAvailableRoles: [],
      uaClubs: [],
      uaLoading: false,
      uaStatusMsg: '',
      uaStatusError: false,
      uaSearch: '',
      uaSearchResults: [],
      uaSearchTimer: null,
      uaGrant: { visible: false, member: null, roleCode: '', clubId: null, statusMsg: '', statusError: false },
      uaMerge: {
        sourceQuery: '',
        targetQuery: '',
        sourceResults: [],
        targetResults: [],
        sourceTimer: null,
        targetTimer: null,
        sourceUser: null,
        targetUser: null,
        statusMsg: '',
        statusError: false,
        busy: false,
      },
      uaMergeCleanup: {
        busy: false,
        statusMsg: '',
        statusError: false,
        lastResult: null,
      },
    };
  },
  created() {
    // Restore session from localStorage if available
    const saved = localStorage.getItem('hlasAdminToken');
    if (saved) {
      this.adminToken = saved;
      this.loggedIn = true;
      this.loadClubs();
    }
  },
  computed: {
    uaGrantNeedsClub() {
      if (!this.uaGrant.roleCode) return false;
      const role = this.uaAvailableRoles.find(r => r.code === this.uaGrant.roleCode);
      return role ? role.scopeType === 'club' : false;
    },
    uaCanAccessMerge() {
      return this.uaAvailableRoles.some(r => r.code === 'app_owner');
    },
    uaCanMerge() {
      const sourceId = this.uaMerge.sourceUser?.userId;
      const targetId = this.uaMerge.targetUser?.userId;
      return !!sourceId && !!targetId && sourceId !== targetId;
    },
    uaMergeCleanupPreview() {
      const planned = (this.uaMergeCleanup.lastResult && this.uaMergeCleanup.lastResult.plannedMerges) || [];
      return planned.slice(0, 10);
    },
    uaMergeCleanupRemaining() {
      const planned = (this.uaMergeCleanup.lastResult && this.uaMergeCleanup.lastResult.plannedMerges) || [];
      return Math.max(0, planned.length - 10);
    },
  },
  methods: {
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
  },
};
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
