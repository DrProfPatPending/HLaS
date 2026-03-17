<template>
  <div id="app">
    <table class="logo-table">
      <tbody>
        <tr>
          <td class="logo-cell">
            <img src="./logos/HLaS.png" alt="HLaS logo" class="app-logo" @click="goHome" />
          </td>
          <td class="logo-cell">
            <a v-if="loggedIn && clubDetails.websiteUrl" :href="clubDetails.websiteUrl" target="_blank" rel="noopener noreferrer">
              <img :src="clubLogoSrc" :alt="`${loggedInClub} logo`" class="club-logo" @error="onClubLogoError" />
            </a>
            <img v-else-if="loggedIn" :src="clubLogoSrc" :alt="`${loggedInClub} logo`" class="club-logo" @error="onClubLogoError" />
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
              {{ club.shortName }}
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
            <td><button type="button" class="home-nav-button" @click="navigateToSection('newsletters')">Newsletters</button></td>
          </tr>
          <tr>
            <td><button type="button" class="home-nav-button" @click="navigateToSection('my-club')">My Club</button></td>
            <td><button type="button" class="home-nav-button" @click="navigateToSection('fishing-beats')">Fishing Beats</button></td>
            <td><button type="button" class="home-nav-button" @click="navigateToSection('club-store')">Club Store</button></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else-if="activeSection === 'membership-admin'">
    <div class="membership-admin-header">
      <button type="button" @click="activeSection = 'home'">Back to Home</button>
      <h1>{{ selectedClub }} Members</h1>
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
          <td><a href="#" @click.prevent="lookupMemberByNumber(member.Number)" class="member-link">{{ member.Number }}</a></td>
          <td><a href="#" @click.prevent="openMemberEdit(member)" class="member-link">{{ member.Members_Name }}</a></td>
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
      <button v-for="pageNum in visiblePages" :key="pageNum" 
              :class="{ 'active': pageNum === currentPage }" 
              @click="goToPage(pageNum)">
        {{ pageNum }}
      </button>
    </div>
    <hr />
    <div v-if="showMembershipDetails">
      <div class="membership-details-header">
        <h2>Membership Details</h2>
        <button v-if="lookupResult && !lookupError" type="button" @click="hideLookupDetails">Hide Details</button>
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
    <div v-else-if="activeSection === 'club-information'" class="club-information-container">
      <h2>{{ clubDetails.fullName }}</h2>
      <table class="club-information-table">
        <tbody>
          <tr>
            <th>Short Name</th>
            <td>{{ clubDetails.shortName }}</td>
          </tr>
          <tr>
            <th>URL</th>
            <td>
              <a
                v-if="clubDetails.websiteUrl"
                :href="clubDetails.websiteUrl"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ clubDetails.websiteUrl }}
              </a>
              <span v-else>-</span>
            </td>
          </tr>
          <tr>
            <th>Admin Email</th>
            <td>
              <a v-if="clubDetails.adminEmail" :href="`mailto:${clubDetails.adminEmail}`">{{ clubDetails.adminEmail }}</a>
              <span v-else>-</span>
            </td>
          </tr>
        </tbody>
      </table>
      <textarea
        class="club-description-box"
        :value="clubDetails.description"
        readonly
        rows="6"
      ></textarea>
      <div>
        <button type="button" @click="activeSection = 'home'">Back to Home</button>
      </div>
    </div>
    <div v-else-if="activeSection === 'newsletters'" class="newsletters-container">
      <h2>Newsletters</h2>
      <p>Filter members, build a selected list, choose a template, and send club newsletters.</p>
      <div class="newsletter-actions newsletter-toolbar">
        <label class="newsletter-template-label" for="newsletter-template-select">Template</label>
        <select
          id="newsletter-template-select"
          v-model="selectedNewsletterTemplateId"
          class="newsletter-template-select"
        >
          <option value="">Select template</option>
          <option
            v-for="template in newsletterTemplates"
            :key="`newsletter-template-${template.id}`"
            :value="template.id"
          >
            {{ template.name }}
          </option>
        </select>
        <button type="button" class="manage-templates-button" @click="openTemplateManager">
          Manage Templates
        </button>
        <button type="button" :disabled="newsletterFilterSelectBusy" @click="selectAllNewsletterFiltered">
          {{ newsletterFilterSelectBusy ? 'Selecting…' : 'Select All Filtered' }}
        </button>
        <button type="button" :disabled="!newsletterSelectedMemberIds.length" @click="clearNewsletterSelection">
          Clear Selection
        </button>
        <span>Filtered: {{ newsletterTotalMembers }}</span>
      </div>
      <div v-if="showTemplateManager" class="template-manager-modal">
        <div class="template-manager-content">
          <div class="template-manager-header">
            <h3>Manage Newsletter Templates</h3>
            <button type="button" class="close-button" @click="closeTemplateManager">×</button>
          </div>
          <div class="template-list-section">
            <h4>Existing Templates</h4>
            <div v-if="templateEditError" class="error-message">{{ templateEditError }}</div>
            <div class="template-list">
              <div v-for="template in newsletterTemplates" :key="template.id" class="template-item">
                <div class="template-item-header">
                  <span class="template-item-name">{{ template.name }}</span>
                  <div class="template-item-actions">
                    <button type="button" class="edit-button" @click="editTemplate(template)">Edit</button>
                    <button 
                      type="button" 
                      class="delete-button" 
                      :disabled="template.id === 'club-update' || template.id === 'membership-reminder'"
                      @click="deleteTemplate(template.id)"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="template-edit-section">
            <h4>{{ templateEditingId ? 'Edit Template' : 'Create New Template' }}</h4>
            <form @submit.prevent="saveTemplate">
              <div v-if="templateCreateError" class="error-message">{{ templateCreateError }}</div>
              <div class="form-group">
                <label for="template-id-input">Template ID:</label>
                <input
                  id="template-id-input"
                  v-model="templateEditingData.id"
                  type="text"
                  placeholder="e.g., special-event (lowercase letters, numbers, hyphens)"
                  :disabled="templateEditingId !== null"
                  required
                />
              </div>
              <div class="form-group">
                <label for="template-name-input">Template Name:</label>
                <input
                  id="template-name-input"
                  v-model="templateEditingData.name"
                  type="text"
                  placeholder="e.g., Special Event"
                  required
                />
              </div>
              <div class="form-group">
                <label for="template-subject-input">Subject:</label>
                <input
                  id="template-subject-input"
                  v-model="templateEditingData.subject"
                  type="text"
                  placeholder="e.g., <Club> Special Event"
                  required
                />
              </div>
              <div class="form-group">
                <label for="template-body-input">Body:</label>
                <textarea
                  id="template-body-input"
                  v-model="templateEditingData.body"
                  placeholder="Use tags like <Club>, <Title>, <Last_Name>, <Number>, etc."
                  rows="8"
                  required
                ></textarea>
              </div>
              <div v-if="newsletterAvailableTags.length" class="available-tags-info">
                <strong>Available tags:</strong>
                <span
                  v-for="tag in newsletterAvailableTags"
                  :key="tag.tag"
                  class="tag-chip"
                  :title="tag.description"
                >&lt;{{ tag.tag }}&gt;</span>
              </div>
              <div class="template-form-actions">
                <button type="submit" class="save-button">{{ templateEditingId ? 'Update Template' : 'Create Template' }}</button>
                <button type="button" class="cancel-button" @click="cancelTemplateEdit">Cancel</button>
              </div>
            </form>
          </div>
        </div>
      </div>
      <div v-if="selectedNewsletterTemplate" class="newsletter-template-preview">
        <h3>Template Preview <span class="newsletter-preview-note">(sample values shown)</span></h3>
        <p><strong>Subject:</strong> {{ selectedNewsletterTemplate.previewSubject }}</p>
        <pre class="newsletter-template-preview-body">{{ selectedNewsletterTemplate.previewBody }}</pre>
        <div v-if="newsletterAvailableTags.length" class="newsletter-template-tags-hint">
          <strong>Available tags:</strong>
          <span
            v-for="tag in newsletterAvailableTags"
            :key="tag.tag"
            class="newsletter-tag-chip"
            :title="tag.description"
          >&lt;{{ tag.tag }}&gt;</span>
        </div>
      </div>
      <table class="newsletter-table">
        <thead>
          <tr>
            <th>
              Select
              <input type="checkbox" :checked="allNewsletterPageSelected" @change="toggleSelectAllNewsletterOnPage" />
            </th>
            <th>
              ID
              <input v-model="newsletterColumnFilters.ID" @input="onNewsletterFilterChange" class="column-filter" placeholder="Filter" />
            </th>
            <th>
              Num
              <input v-model="newsletterColumnFilters.Number" @input="onNewsletterFilterChange" class="column-filter" placeholder="Filter" />
            </th>
            <th>
              Name
              <input v-model="newsletterColumnFilters.Members_Name" @input="onNewsletterFilterChange" class="column-filter" placeholder="Filter" />
            </th>
            <th>
              E-Mail
              <input v-model="newsletterColumnFilters.E_Mail" @input="onNewsletterFilterChange" class="column-filter" placeholder="Filter" />
            </th>
            <th>
              Membership Type
              <select v-model="newsletterColumnFilters.Member_Type" @change="onNewsletterFilterChange" class="column-filter">
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
              Paid Up?
              <input v-model="newsletterColumnFilters.Paid_Up_2026" @input="onNewsletterFilterChange" class="column-filter" placeholder="Filter" />
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="member in newsletterMembers" :key="`newsletter-${memberIdentity(member)}`">
            <td>
              <input
                type="checkbox"
                :value="String(memberIdentity(member))"
                v-model="newsletterSelectedMemberIds"
              />
            </td>
            <td>{{ member.ID || member.id }}</td>
            <td>{{ member.Number }}</td>
            <td>{{ member.Members_Name }}</td>
            <td>
              <a v-if="member.E_Mail" :href="`mailto:${member.E_Mail}`">{{ member.E_Mail }}</a>
              <span v-else>-</span>
            </td>
            <td>{{ member.Member_Type }}</td>
            <td>{{ member.Paid_Up_2026 }}</td>
          </tr>
        </tbody>
      </table>
      <div class="pagination-controls">
        <button :disabled="newsletterCurrentPage === 1" @click="firstNewsletterPage">First Page</button>
        <button :disabled="newsletterCurrentPage === 1" @click="prevNewsletterPage">Previous Page</button>
        <span>Page {{ newsletterCurrentPage }} of {{ newsletterTotalPages }}&nbsp;</span>
        <button :disabled="newsletterCurrentPage === newsletterTotalPages" @click="nextNewsletterPage">Next Page</button>
        <button :disabled="newsletterCurrentPage === newsletterTotalPages" @click="lastNewsletterPage">Last Page</button>
        <select v-model.number="newsletterPageSize" @change="onNewsletterPageSizeChange" class="records-per-page-select">
          <option value="10">10 per page</option>
          <option value="25">25 per page</option>
          <option value="50">50 per page</option>
          <option value="100">100 per page</option>
        </select>
      </div>
      <div class="page-numbers">
        <button
          v-for="pageNum in newsletterVisiblePages"
          :key="`newsletter-page-${pageNum}`"
          :class="{ 'active': pageNum === newsletterCurrentPage }"
          @click="goToNewsletterPage(pageNum)"
        >
          {{ pageNum }}
        </button>
      </div>
      <div class="newsletter-actions">
        <button
          type="button"
          :disabled="!selectedNewsletterTemplateId || newsletterSendBusy"
          @click="sendNewsletterToAllMembers"
        >
          {{ newsletterSendBusy ? 'Sending…' : 'Send Newsletter to All' }}
        </button>
        <button type="button" :disabled="!newsletterSelectedMemberIds.length" @click="prepareNewsletterRecipients">
          Prepare Selected for Email
        </button>
        <span>Selected: {{ newsletterSelectedMemberIds.length }}</span>
        <button
          type="button"
          :disabled="!selectedNewsletterTemplateId || !newsletterSelectedMemberIds.length || newsletterSendBusy"
          @click="sendNewsletterToSelectedMembers"
        >
          {{ newsletterSendBusy ? 'Sending…' : 'Send Newsletter to Selected' }}
        </button>
      </div>
      <div v-if="newsletterPrepareMessage" class="newsletter-status">{{ newsletterPrepareMessage }}</div>
      <div v-if="newsletterPrepareError" class="newsletter-error">{{ newsletterPrepareError }}</div>
      <button type="button" @click="activeSection = 'home'">Back to Home</button>
    </div>
    <div v-else-if="activeSection === 'fishing-beats'" class="fishing-beats-container">
      <h2>{{ clubDetails.fullName }} - Fishing Beats</h2>
      <div v-if="clubBeats.length" class="fishing-beats-layout">
        <table class="fishing-beats-table">
          <thead>
            <tr>
              <th>Beat Name</th>
              <th>Beat ID</th>
              <th>River</th>
              <th>Position</th>
              <th>Beat Upstream</th>
              <th>Beat Downstream</th>
              <th>Beat Description</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="beat in clubBeats" :key="`${beat.Beat_ID}-${beat.Beat_Name}`">
              <td>
                <a
                  href="#"
                  class="beat-name-link"
                  :class="{ 'active': selectedFishingBeat && beatKey(selectedFishingBeat) === beatKey(beat) }"
                  @click.prevent="selectFishingBeat(beat)"
                >
                  {{ beat.Beat_Name }}
                </a>
              </td>
              <td>{{ beat.Beat_ID }}</td>
              <td>{{ beat.River }}</td>
              <td>{{ beat.Position }}</td>
              <td>
                <a
                  v-if="beat.Beat_Upstream_W3W"
                  :href="beat.Beat_Upstream_W3W.url"
                  rel="noopener noreferrer"
                  @click.prevent="openReusableMapWindow(beat.Beat_Upstream_W3W.url)"
                >
                  {{ beat.Beat_Upstream_W3W.display }}
                </a>
                <span v-else>{{ beat.Beat_Upstream }}</span>
              </td>
              <td>
                <a
                  v-if="beat.Beat_Downstream_W3W"
                  :href="beat.Beat_Downstream_W3W.url"
                  rel="noopener noreferrer"
                  @click.prevent="openReusableMapWindow(beat.Beat_Downstream_W3W.url)"
                >
                  {{ beat.Beat_Downstream_W3W.display }}
                </a>
                <span v-else>{{ beat.Beat_Downstream }}</span>
              </td>
              <td>{{ beat.Beat_Description }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="selectedFishingBeat" class="fishing-beat-detail-panel">
          <h3>{{ selectedFishingBeat.Beat_Name }}</h3>
          <table class="fishing-beat-detail-table">
            <tbody>
              <tr>
                <th>Beat Name</th>
                <td>{{ selectedFishingBeat.Beat_Name }}</td>
              </tr>
              <tr>
                <th>Beat ID</th>
                <td>{{ selectedFishingBeat.Beat_ID }}</td>
              </tr>
              <tr>
                <th>River</th>
                <td>{{ selectedFishingBeat.River }}</td>
              </tr>
              <tr>
                <th>Position</th>
                <td>{{ selectedFishingBeat.Position }}</td>
              </tr>
              <tr>
                <th>Beat Upstream</th>
                <td>
                  <a
                    v-if="selectedFishingBeat.Beat_Upstream_W3W"
                    :href="selectedFishingBeat.Beat_Upstream_W3W.url"
                    rel="noopener noreferrer"
                    @click.prevent="openReusableMapWindow(selectedFishingBeat.Beat_Upstream_W3W.url)"
                  >
                    {{ selectedFishingBeat.Beat_Upstream_W3W.display }}
                  </a>
                  <span v-else>{{ selectedFishingBeat.Beat_Upstream }}</span>
                </td>
              </tr>
              <tr>
                <th>Beat Downstream</th>
                <td>
                  <a
                    v-if="selectedFishingBeat.Beat_Downstream_W3W"
                    :href="selectedFishingBeat.Beat_Downstream_W3W.url"
                    rel="noopener noreferrer"
                    @click.prevent="openReusableMapWindow(selectedFishingBeat.Beat_Downstream_W3W.url)"
                  >
                    {{ selectedFishingBeat.Beat_Downstream_W3W.display }}
                  </a>
                  <span v-else>{{ selectedFishingBeat.Beat_Downstream }}</span>
                </td>
              </tr>
              <tr>
                <th>Beat Description</th>
                <td>{{ selectedFishingBeat.Beat_Description }}</td>
              </tr>
              <tr>
                <th>Detailed Description</th>
                <td>{{ selectedFishingBeat.Detailed_Description || '-' }}</td>
              </tr>
              <tr>
                <th>Upstream Co-ords</th>
                <td>
                  <span v-if="selectedFishingBeat.Beat_Upstream_Latitude && selectedFishingBeat.Beat_Upstream_Longitude">
                    {{ selectedFishingBeat.Beat_Upstream_Latitude }}, {{ selectedFishingBeat.Beat_Upstream_Longitude }}
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
              <tr>
                <th>Downstream Co-ords</th>
                <td>
                  <span v-if="selectedFishingBeat.Beat_Downstream_Latitude && selectedFishingBeat.Beat_Downstream_Longitude">
                    {{ selectedFishingBeat.Beat_Downstream_Latitude }}, {{ selectedFishingBeat.Beat_Downstream_Longitude }}
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
              <tr>
                <th>Parking</th>
                <td>
                  <ul v-if="selectedFishingBeat.Parking_Locations.length" class="fishing-beat-parking-list">
                    <li v-for="(parking, parkingIndex) in selectedFishingBeat.Parking_Locations" :key="`parking-${parkingIndex}`">
                      <strong>{{ parking.Name || `Parking ${parkingIndex + 1}` }}</strong>
                      <span v-if="parking.Latitude && parking.Longitude"> ({{ parking.Latitude }}, {{ parking.Longitude }})</span>
                      <span v-if="parking.Location_W3W"> &mdash; <a href="#" class="w3w-link" @click.prevent="openReusableMapWindow(parking.Location_W3W.url)">{{ parking.Location_W3W.display }}</a></span>
                      <span v-if="parking.Description"> - {{ parking.Description }}</span>
                    </li>
                  </ul>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
          <div class="fishing-beat-map-wrap">
            <div ref="fishingBeatMap" class="fishing-beat-map"></div>
            <div v-if="fishingBeatMapStatus" class="fishing-beat-map-status">{{ fishingBeatMapStatus }}</div>
          </div>
        </div>
      </div>
      <p v-else>No fishing beats are configured for this club.</p>
      <button type="button" @click="activeSection = 'home'">Back to Home</button>
    </div>
    <div v-else-if="activeSection === 'member-edit'" class="member-edit-container">
      <h2>Edit Member Details</h2>
      <div v-if="editMemberPositionLabel" class="member-edit-position">{{ editMemberPositionLabel }}</div>
      <div class="member-edit-photo-row">
        <img
          v-if="editMemberData.Photo_Path"
          :key="editMemberId"
          :src="`${apiBaseUrl}/member_photo/${loggedInClub}/${encodeURIComponent(editMemberData.Photo_Path)}`"
          :alt="editMemberData.Members_Name || 'Member photo'"
          class="member-edit-photo"
          @error="$event.target.style.display='none'"
        />
        <div v-if="editMemberData.Photo_Path" class="member-edit-photo-name">{{ editMemberData.Photo_Path }}</div>
      </div>
      <div class="member-edit-actions">
        <button type="button" @click="updateMember">Update Member</button>
        <button type="button" :disabled="!hasPreviousEditMember" @click="navigateEditMember(-1)">Previous</button>
        <button type="button" :disabled="!hasNextEditMember" @click="navigateEditMember(1)">Next</button>
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
        <button type="button" :disabled="!hasPreviousEditMember" @click="navigateEditMember(-1)">Previous</button>
        <button type="button" :disabled="!hasNextEditMember" @click="navigateEditMember(1)">Next</button>
        <button type="button" @click="cancelEdit">Cancel</button>
      </div>
    </div>
    <div v-else class="section-placeholder">
      <h2>{{ sectionDisplayName(activeSection) }}</h2>
      <p>This section is coming soon.</p>
      <button type="button" @click="activeSection = 'home'">Back to Home</button>
    </div>
    </div>
    <footer class="app-footer">
      <span>(c) 2026 - ScoffySoft</span>
      <span class="app-footer-separator">|</span>
      <a href="mailto: robbie.scoff@gmail.com">Contact Us</a>
    </footer>
  </div>
</template>

<script>
import axios from 'axios';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const API_BASE_URL = process.env.VUE_APP_BACKEND_URL || `${window.location.protocol}//${window.location.hostname}:5050`;

export default {
  data() {
    return {
      apiBaseUrl: API_BASE_URL,
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
      showMembershipDetails: false,
      loginUsername: '',
      loginPassword: '',
      loginError: '',
      clubs: [],
      loggedIn: false,
      loggedInUser: null,
      loggedInUsername: '',
      clubLogoLoadFailed: false,
      activeSection: 'home',
      selectedClub: 'GAAFFS',
      loggedInClub: 'GAAFFS',
      filterDebounceTimer: null,
      filterDebounceMs: 250,
      newsletterFilterDebounceTimer: null,
      newsletterMembers: [],
      newsletterTotalMembers: 0,
      newsletterCurrentPage: 1,
      newsletterPageSize: 10,
      newsletterSelectedMemberIds: [],
      newsletterTemplates: [],
      newsletterAvailableTags: [],
      selectedNewsletterTemplateId: '',
      newsletterFilterSelectBusy: false,
      newsletterSendBusy: false,
      newsletterPrepareMessage: '',
      newsletterPrepareError: '',
      showTemplateManager: false,
      templateEditingId: null,
      templateEditingData: { id: '', name: '', subject: '', body: '' },
      templateCreateError: '',
      templateEditError: '',
      selectedFishingBeatKey: '',
      fishingBeatMapInstance: null,
      fishingBeatMapLayers: [],
      fishingBeatMapStatus: '',
      fishingBeatMapRequestId: 0,
      newsletterColumnFilters: {
        ID: '',
        Number: '',
        Members_Name: '',
        E_Mail: '',
        Member_Type: '',
        Paid_Up_2026: '',
      },
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
        Licence_Exp: '',
        Resigned: ''
      }
    };
  },
  computed: {
    clubDetails() {
      const activeClubShortName = this.loggedInClub || this.selectedClub;
      const matchedClub =
        this.clubs.find(club => club.shortName === activeClubShortName)
        || this.clubs.find(club => club.shortName === this.selectedClub)
        || {};

      return {
        fullName: matchedClub.fullName || activeClubShortName || 'Club Information',
        shortName: matchedClub.shortName || activeClubShortName || '',
        websiteUrl: matchedClub.websiteUrl || '',
        adminEmail: matchedClub.adminEmail || '',
        description: matchedClub.description || '',
        logoUrl: matchedClub.logoUrl || '',
        beats: Array.isArray(matchedClub.beats) ? matchedClub.beats : [],
      };
    },
    clubBeats() {
      const beats = Array.isArray(this.clubDetails.beats) ? this.clubDetails.beats : [];
      return beats.map(beat => {
        const beatUpstream = beat && beat.Beat_Upstream ? beat.Beat_Upstream : '';
        const beatDownstream = beat && beat.Beat_Downstream ? beat.Beat_Downstream : '';

        return {
          Beat_Name: beat && beat.Beat_Name ? beat.Beat_Name : '',
          Beat_ID: beat && beat.Beat_ID ? beat.Beat_ID : '',
          River: beat && beat.River ? beat.River : '',
          Position: beat && beat.Position ? beat.Position : '',
          Beat_Upstream: beatUpstream,
          Beat_Downstream: beatDownstream,
          Beat_Upstream_W3W: this.parseWhat3Words(beatUpstream),
          Beat_Downstream_W3W: this.parseWhat3Words(beatDownstream),
          Beat_Upstream_Latitude: beat && beat.Beat_Upstream_Latitude ? beat.Beat_Upstream_Latitude : '',
          Beat_Upstream_Longitude: beat && beat.Beat_Upstream_Longitude ? beat.Beat_Upstream_Longitude : '',
          Beat_Downstream_Latitude: beat && beat.Beat_Downstream_Latitude ? beat.Beat_Downstream_Latitude : '',
          Beat_Downstream_Longitude: beat && beat.Beat_Downstream_Longitude ? beat.Beat_Downstream_Longitude : '',
          Parking_Locations: Array.isArray(beat && beat.Parking_Locations)
            ? beat.Parking_Locations
              .filter(location => location && typeof location === 'object')
              .map(location => ({
                Name: location && location.Name ? location.Name : '',
                Location_W3W: this.parseWhat3Words(location && location.Location ? location.Location : ''),
                Description: location && location.Description ? location.Description : '',
                Latitude: location && location.Latitude ? location.Latitude : '',
                Longitude: location && location.Longitude ? location.Longitude : '',
              }))
            : [],
          Beat_Description: beat && beat.Beat_Description ? beat.Beat_Description : '',
          Detailed_Description: beat && beat.Detailed_Description ? beat.Detailed_Description : '',
        };
      });
    },
    selectedFishingBeat() {
      const beats = this.clubBeats;
      if (!beats.length) {
        return null;
      }
      const selected = beats.find(beat => this.beatKey(beat) === this.selectedFishingBeatKey);
      return selected || beats[0];
    },
    clubLogoSrc() {
      if (this.clubDetails.logoUrl && !this.clubLogoLoadFailed) {
        if (/^https?:\/\//i.test(this.clubDetails.logoUrl)) {
          return this.clubDetails.logoUrl;
        }
        return `${API_BASE_URL}${this.clubDetails.logoUrl.startsWith('/') ? '' : '/'}${this.clubDetails.logoUrl}`;
      }
      return this.getBundledClubLogo(this.loggedInClub);
    },
    totalPages() {
      return Math.max(1, Math.ceil(this.totalMembers / this.pageSize));
    },
    newsletterTotalPages() {
      return Math.max(1, Math.ceil(this.newsletterTotalMembers / this.newsletterPageSize));
    },
    newsletterVisiblePages() {
      const current = this.newsletterCurrentPage;
      const total = this.newsletterTotalPages;
      const pageCount = 5;

      let start;
      let end;

      if (current <= 3) {
        start = 1;
        end = Math.min(pageCount, total);
      } else {
        start = current - 2;
        end = current + 2;
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
    selectedNewsletterTemplate() {
      return this.newsletterTemplates.find(template => template.id === this.selectedNewsletterTemplateId) || null;
    },
    allNewsletterPageSelected() {
      if (!this.newsletterMembers.length) {
        return false;
      }
      const selectedIds = new Set(this.newsletterSelectedMemberIds.map(memberId => String(memberId)));
      return this.newsletterMembers.every(member => selectedIds.has(String(this.memberIdentity(member))));
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
    },
    editMemberIndex() {
      if (!this.members.length || this.editMemberId === null || this.editMemberId === undefined) {
        return -1;
      }
      return this.members.findIndex(member => this.memberIdentity(member) === this.editMemberId);
    },
    hasPreviousEditMember() {
      return this.editMemberIndex > 0;
    },
    hasNextEditMember() {
      return this.editMemberIndex >= 0 && this.editMemberIndex < this.members.length - 1;
    },
    editMemberPositionLabel() {
      if (this.editMemberIndex < 0 || !this.members.length) {
        return '';
      }
      return `Member ${this.editMemberIndex + 1} of ${this.members.length}`;
    }
  },
  watch: {
    selectedFishingBeat() {
      if (this.activeSection === 'fishing-beats') {
        this.refreshFishingBeatMap();
      }
    },
    activeSection(newSection) {
      if (newSection === 'fishing-beats') {
        this.refreshFishingBeatMap();
      }
    },
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
    if (this.newsletterFilterDebounceTimer) {
      clearTimeout(this.newsletterFilterDebounceTimer);
    }
    this.destroyFishingBeatMap();
  },
  methods: {
    openReusableMapWindow(url) {
      if (!url) {
        return;
      }

      const popupWindow = window.open(
        url,
        'what3words-map-window',
        'popup=yes,width=980,height=760,resizable=yes,scrollbars=yes'
      );

      if (popupWindow) {
        popupWindow.focus();
        return;
      }

      window.location.href = url;
    },
    parseCoordinateValue(rawValue) {
      const numericValue = Number.parseFloat(String(rawValue || '').trim());
      return Number.isFinite(numericValue) ? numericValue : null;
    },
    async resolveBeatPointCoordinates(wordsValue, latitudeValue, longitudeValue) {
      const latitude = this.parseCoordinateValue(latitudeValue);
      const longitude = this.parseCoordinateValue(longitudeValue);

      if (latitude !== null && longitude !== null) {
        return { lat: latitude, lng: longitude, source: 'coordinates' };
      }

      const parsedW3W = this.parseWhat3Words(wordsValue);
      if (!parsedW3W) {
        return null;
      }

      try {
        const response = await axios.get(`${API_BASE_URL}/w3w/coordinates`, {
          params: {
            words: parsedW3W.display,
          },
        });
        const responseData = response && response.data ? response.data : {};
        const resolvedLat = this.parseCoordinateValue(responseData.lat);
        const resolvedLng = this.parseCoordinateValue(responseData.lng);
        if (resolvedLat !== null && resolvedLng !== null) {
          return { lat: resolvedLat, lng: resolvedLng, source: 'w3w' };
        }
      } catch {
      }

      return null;
    },
    clearFishingBeatMapLayers() {
      if (!this.fishingBeatMapInstance || !Array.isArray(this.fishingBeatMapLayers)) {
        return;
      }
      this.fishingBeatMapLayers.forEach(layer => {
        if (layer && this.fishingBeatMapInstance.hasLayer(layer)) {
          this.fishingBeatMapInstance.removeLayer(layer);
        }
      });
      this.fishingBeatMapLayers = [];
    },
    ensureFishingBeatMap() {
      if (this.fishingBeatMapInstance) {
        return;
      }

      const mapElement = this.$refs.fishingBeatMap;
      if (!mapElement) {
        return;
      }

      this.fishingBeatMapInstance = L.map(mapElement, {
        zoomControl: true,
        attributionControl: true,
      }).setView([54.5, -2.5], 6);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors',
      }).addTo(this.fishingBeatMapInstance);
    },
    async refreshFishingBeatMap() {
      if (this.activeSection !== 'fishing-beats') {
        return;
      }

      const selectedBeat = this.selectedFishingBeat;
      if (!selectedBeat) {
        this.fishingBeatMapStatus = 'No beat selected.';
        this.clearFishingBeatMapLayers();
        return;
      }

      const requestId = ++this.fishingBeatMapRequestId;
      this.fishingBeatMapStatus = 'Loading map...';

      await this.$nextTick();
      this.ensureFishingBeatMap();

      if (!this.fishingBeatMapInstance) {
        this.fishingBeatMapStatus = 'Map is unavailable.';
        return;
      }

      const upstreamCoordinates = await this.resolveBeatPointCoordinates(
        selectedBeat.Beat_Upstream,
        selectedBeat.Beat_Upstream_Latitude,
        selectedBeat.Beat_Upstream_Longitude,
      );
      const downstreamCoordinates = await this.resolveBeatPointCoordinates(
        selectedBeat.Beat_Downstream,
        selectedBeat.Beat_Downstream_Latitude,
        selectedBeat.Beat_Downstream_Longitude,
      );

      if (requestId !== this.fishingBeatMapRequestId) {
        return;
      }

      this.clearFishingBeatMapLayers();

      if (!upstreamCoordinates || !downstreamCoordinates) {
        this.fishingBeatMapStatus = 'Map requires valid W3W lookup support or fallback coordinates for both upstream and downstream limits.';
        return;
      }

      const upstreamLatLng = L.latLng(upstreamCoordinates.lat, upstreamCoordinates.lng);
      const downstreamLatLng = L.latLng(downstreamCoordinates.lat, downstreamCoordinates.lng);
      const allBoundsPoints = [upstreamLatLng, downstreamLatLng];

      const upstreamMarker = L.circleMarker(upstreamLatLng, {
        radius: 7,
        color: '#1f77b4',
        fillColor: '#1f77b4',
        fillOpacity: 0.8,
      }).bindPopup('Upstream limit');

      const downstreamMarker = L.circleMarker(downstreamLatLng, {
        radius: 7,
        color: '#d62728',
        fillColor: '#d62728',
        fillOpacity: 0.8,
      }).bindPopup('Downstream limit');

      const boundaryLine = L.polyline([upstreamLatLng, downstreamLatLng], {
        color: '#2f2f2f',
        weight: 3,
      });

      const parkingLayers = [];
      const parkingLocations = Array.isArray(selectedBeat.Parking_Locations) ? selectedBeat.Parking_Locations : [];
      parkingLocations.forEach((parking, parkingIndex) => {
        const parkingLatitude = this.parseCoordinateValue(parking && parking.Latitude ? parking.Latitude : '');
        const parkingLongitude = this.parseCoordinateValue(parking && parking.Longitude ? parking.Longitude : '');
        if (parkingLatitude === null || parkingLongitude === null) {
          return;
        }

        const parkingLatLng = L.latLng(parkingLatitude, parkingLongitude);
        allBoundsPoints.push(parkingLatLng);

        const label = parking && parking.Name ? parking.Name : `Parking ${parkingIndex + 1}`;
        const description = parking && parking.Description ? parking.Description : '';
        const locationW3W = parking && parking.Location_W3W ? parking.Location_W3W : null;
        let parkingPopup = label;
        if (locationW3W) {
          parkingPopup += `<br><a href="${locationW3W.url}" target="what3words-map-window">${locationW3W.display}</a>`;
        }
        if (description) {
          parkingPopup += `<br>${description}`;
        }

        const parkingMarker = L.marker(parkingLatLng, {
          icon: L.divIcon({
            className: 'parking-pin-marker',
            html: '<div class="parking-pin-dot">P</div>',
            iconSize: [20, 20],
            iconAnchor: [10, 10],
          }),
        }).bindPopup(parkingPopup);

        parkingMarker.addTo(this.fishingBeatMapInstance);
        parkingLayers.push(parkingMarker);
      });

      upstreamMarker.addTo(this.fishingBeatMapInstance);
      downstreamMarker.addTo(this.fishingBeatMapInstance);
      boundaryLine.addTo(this.fishingBeatMapInstance);
      this.fishingBeatMapLayers = [upstreamMarker, downstreamMarker, boundaryLine, ...parkingLayers];

      this.fishingBeatMapInstance.invalidateSize();
      const bounds = L.latLngBounds(allBoundsPoints);
      this.fishingBeatMapInstance.fitBounds(bounds.pad(0.2), { maxZoom: 16 });
      this.fishingBeatMapStatus = parkingLayers.length
        ? `Showing upstream/downstream limits and ${parkingLayers.length} parking marker${parkingLayers.length === 1 ? '' : 's'}.`
        : 'Showing upstream and downstream limits.';
    },
    destroyFishingBeatMap() {
      this.clearFishingBeatMapLayers();
      if (this.fishingBeatMapInstance) {
        this.fishingBeatMapInstance.remove();
        this.fishingBeatMapInstance = null;
      }
      this.fishingBeatMapStatus = '';
    },
    beatKey(beat) {
      const beatId = beat && beat.Beat_ID ? beat.Beat_ID : '';
      const beatName = beat && beat.Beat_Name ? beat.Beat_Name : '';
      return `${beatId}-${beatName}`;
    },
    selectFishingBeat(beat) {
      this.selectedFishingBeatKey = this.beatKey(beat);
      this.refreshFishingBeatMap();
    },
    parseWhat3Words(rawValue) {
      if (typeof rawValue !== 'string') {
        return null;
      }
      const trimmed = rawValue.trim();
      if (!trimmed) {
        return null;
      }

      const withoutSlashes = trimmed.replace(/^\/+/, '');
      const words = withoutSlashes
        .split('.')
        .map(word => word.trim())
        .filter(Boolean);

      if (words.length !== 3) {
        return null;
      }

      const normalizedWords = words.map(word => word.toLowerCase());
      const normalizedPath = normalizedWords.map(word => encodeURIComponent(word)).join('.');

      return {
        display: `///${normalizedWords.join('.')}`,
        url: `https://what3words.com/${normalizedPath}`,
      };
    },
    memberIdentity(member) {
      return member && (member.id || member.ID || member.Number);
    },
    selectMemberForEdit(member) {
      this.editMemberData = { ...member };
      this.editMemberId = this.memberIdentity(member);
      this.newPassword = '';
      this.confirmPassword = '';
      this.passwordError = '';
      this.activeSection = 'member-edit';
    },
    getBundledClubLogo(shortName) {
      try {
        return require(`./logos/${shortName}_Logo_50px.png`);
      } catch {
        return require('./logos/HLaS.png');
      }
    },
    onClubLogoError() {
      this.clubLogoLoadFailed = true;
    },
    loadClubs() {
      axios.get(`${API_BASE_URL}/clubs`)
        .then(res => {
          const clubs = res.data && Array.isArray(res.data.clubs) ? res.data.clubs : [];
          const seenShortNames = new Set();
          const uniqueClubs = clubs.filter(club => {
            const shortName = club && typeof club.shortName === 'string' ? club.shortName.trim() : '';
            if (!shortName || seenShortNames.has(shortName)) {
              return false;
            }
            seenShortNames.add(shortName);
            return true;
          });
          if (!uniqueClubs.length) {
            throw new Error('No clubs in config');
          }

          this.clubs = uniqueClubs;
          this.clubLogoLoadFailed = false;
          const hasSelected = uniqueClubs.some(club => club.shortName === this.selectedClub);
          if (!hasSelected) {
            this.selectedClub = uniqueClubs[0].shortName;
            this.loggedInClub = uniqueClubs[0].shortName;
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
              logoUrl: '',
              beats: [],
            },
            {
              fullName: 'CTC',
              shortName: 'CTC',
              description: 'CTC fishing club members',
              websiteUrl: '',
              adminEmail: '',
              logoUrl: '',
              beats: [],
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
    onNewsletterFilterChange() {
      this.newsletterCurrentPage = 1;
      if (this.newsletterFilterDebounceTimer) {
        clearTimeout(this.newsletterFilterDebounceTimer);
      }
      this.newsletterFilterDebounceTimer = setTimeout(() => {
        this.fetchNewsletterMembers();
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
    fetchNewsletterMembers() {
      const offset = (this.newsletterCurrentPage - 1) * this.newsletterPageSize;
      const activeFilters = this.buildNewsletterActiveFilters();

      axios.get(`${API_BASE_URL}/members`, {
        params: {
          club: this.loggedInClub,
          limit: this.newsletterPageSize,
          offset,
          ...activeFilters,
        }
      }).then(res => {
        this.newsletterMembers = res.data.members || [];
        this.newsletterTotalMembers = res.data.total || 0;
      });
    },
    fetchNewsletterTemplates() {
      axios.get(`${API_BASE_URL}/newsletter/templates`, {
        params: {
          club: this.loggedInClub,
        },
      })
        .then(res => {
          const templates = Array.isArray(res.data && res.data.templates) ? res.data.templates : [];
          this.newsletterTemplates = templates
            .filter(template => template && template.id)
            .map(template => ({
              id: String(template.id),
              name: template.name || String(template.id),
              subjectTemplate: template.subjectTemplate || '',
              bodyTemplate: template.bodyTemplate || '',
              previewSubject: template.previewSubject || template.subjectTemplate || '',
              previewBody: template.previewBody || template.bodyTemplate || '',
            }));

          this.newsletterAvailableTags = Array.isArray(res.data && res.data.availableTags)
            ? res.data.availableTags
            : [];

          if (!this.selectedNewsletterTemplateId && this.newsletterTemplates.length) {
            this.selectedNewsletterTemplateId = this.newsletterTemplates[0].id;
          }
        })
        .catch(() => {
          this.newsletterTemplates = [];
          this.newsletterAvailableTags = [];
        });
    },
    openTemplateManager() {
      this.showTemplateManager = true;
      this.templateEditingId = null;
      this.templateEditingData = { id: '', name: '', subject: '', body: '' };
      this.templateCreateError = '';
      this.templateEditError = '';
    },
    closeTemplateManager() {
      this.showTemplateManager = false;
      this.templateEditingId = null;
      this.templateEditingData = { id: '', name: '', subject: '', body: '' };
      this.templateCreateError = '';
      this.templateEditError = '';
    },
    editTemplate(template) {
      this.templateEditingId = template.id;
      this.templateEditingData = {
        id: template.id,
        name: template.name,
        subject: template.subjectTemplate,
        body: template.bodyTemplate,
      };
      this.templateCreateError = '';
      this.templateEditError = '';
    },
    cancelTemplateEdit() {
      this.templateEditingId = null;
      this.templateEditingData = { id: '', name: '', subject: '', body: '' };
      this.templateCreateError = '';
      this.templateEditError = '';
    },
    saveTemplate() {
      const { id, name, subject, body } = this.templateEditingData;
      if (!id || !name || !subject || !body) {
        this.templateCreateError = 'All fields are required';
        return;
      }

      if (this.templateEditingId) {
        // Update existing template
        axios.put(`${API_BASE_URL}/newsletter/templates/${this.templateEditingId}`, {
          club: this.loggedInClub,
          name,
          subject,
          body,
        })
          .then(() => {
            this.fetchNewsletterTemplates();
            this.cancelTemplateEdit();
          })
          .catch(err => {
            this.templateEditError = err.response?.data?.error || 'Failed to update template';
          });
      } else {
        // Create new template
        axios.post(`${API_BASE_URL}/newsletter/templates`, {
          club: this.loggedInClub,
          id,
          name,
          subject,
          body,
        })
          .then(() => {
            this.fetchNewsletterTemplates();
            this.cancelTemplateEdit();
          })
          .catch(err => {
            this.templateCreateError = err.response?.data?.error || 'Failed to create template';
          });
      }
    },
    deleteTemplate(templateId) {
      if (templateId === 'club-update' || templateId === 'membership-reminder') {
        alert('Cannot delete default templates');
        return;
      }
      if (!confirm(`Delete template "${templateId}"?`)) {
        return;
      }
      axios.delete(`${API_BASE_URL}/newsletter/templates/${templateId}`, {
        params: {
          club: this.loggedInClub,
        },
      })
        .then(() => {
          this.fetchNewsletterTemplates();
        })
        .catch(err => {
          this.templateEditError = err.response?.data?.error || 'Failed to delete template';
        });
    },
    buildNewsletterActiveFilters() {
      return Object.fromEntries(
        Object.entries(this.newsletterColumnFilters)
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
    },
    toggleSelectAllNewsletterOnPage(event) {
      const isChecked = event.target.checked;
      const pageIds = this.newsletterMembers
        .map(member => this.memberIdentity(member))
        .filter(memberId => memberId !== null && memberId !== undefined)
        .map(memberId => String(memberId));

      if (isChecked) {
        const merged = new Set(this.newsletterSelectedMemberIds);
        pageIds.forEach(memberId => merged.add(memberId));
        this.newsletterSelectedMemberIds = Array.from(merged);
      } else {
        const pageIdSet = new Set(pageIds);
        this.newsletterSelectedMemberIds = this.newsletterSelectedMemberIds.filter(memberId => !pageIdSet.has(memberId));
      }
    },
    selectAllNewsletterFiltered() {
      this.newsletterPrepareMessage = '';
      this.newsletterPrepareError = '';
      this.newsletterFilterSelectBusy = true;

      axios.post(`${API_BASE_URL}/newsletter/filtered_member_ids`, {
        club: this.loggedInClub,
        filters: this.newsletterColumnFilters,
      })
        .then(res => {
          const filteredIds = Array.isArray(res.data && res.data.memberIds)
            ? res.data.memberIds.map(memberId => String(memberId)).filter(Boolean)
            : [];

          const merged = new Set(this.newsletterSelectedMemberIds);
          filteredIds.forEach(memberId => merged.add(memberId));
          this.newsletterSelectedMemberIds = Array.from(merged);

          this.newsletterPrepareMessage = `Selected ${filteredIds.length} members from current filtered results.`;
        })
        .catch(err => {
          this.newsletterPrepareError = err.response && err.response.data && err.response.data.error
            ? err.response.data.error
            : 'Failed to select filtered members';
        })
        .finally(() => {
          this.newsletterFilterSelectBusy = false;
        });
    },
    clearNewsletterSelection() {
      this.newsletterSelectedMemberIds = [];
      this.newsletterPrepareMessage = '';
      this.newsletterPrepareError = '';
    },
    prepareNewsletterRecipients() {
      this.newsletterPrepareMessage = '';
      this.newsletterPrepareError = '';
      axios.post(`${API_BASE_URL}/newsletter/prepare_recipients`, {
        club: this.loggedInClub,
        memberIds: this.newsletterSelectedMemberIds,
      })
        .then(res => {
          const summary = res.data || {};
          this.newsletterPrepareMessage = `Prepared ${summary.emailableCount || 0} emailable recipients from ${summary.selectedCount || 0} selected members.`;
        })
        .catch(err => {
          this.newsletterPrepareError = err.response && err.response.data && err.response.data.error
            ? err.response.data.error
            : 'Failed to prepare newsletter recipients';
        });
    },
    sendNewsletterToAllMembers() {
      this.newsletterPrepareMessage = '';
      this.newsletterPrepareError = '';

      if (!this.selectedNewsletterTemplateId) {
        this.newsletterPrepareError = 'Please select a newsletter template.';
        return;
      }

      this.newsletterSendBusy = true;

      axios.post(`${API_BASE_URL}/newsletter/send`, {
        club: this.loggedInClub,
        templateId: this.selectedNewsletterTemplateId,
        scope: 'all_club',
      })
        .then(res => {
          const summary = res.data || {};
          this.newsletterPrepareMessage = `Sent ${summary.sentCount || 0} emails to ${summary.emailableCount || 0} emailable members in ${this.loggedInClub}.`;
        })
        .catch(err => {
          this.newsletterPrepareError = err.response && err.response.data && err.response.data.error
            ? err.response.data.error
            : 'Failed to send newsletter to all members';
        })
        .finally(() => {
          this.newsletterSendBusy = false;
        });
    },
    sendNewsletterToSelectedMembers() {
      this.newsletterPrepareMessage = '';
      this.newsletterPrepareError = '';

      if (!this.selectedNewsletterTemplateId) {
        this.newsletterPrepareError = 'Please select a newsletter template.';
        return;
      }

      if (!this.newsletterSelectedMemberIds.length) {
        this.newsletterPrepareError = 'Please select at least one member.';
        return;
      }

      this.newsletterSendBusy = true;

      axios.post(`${API_BASE_URL}/newsletter/send`, {
        club: this.loggedInClub,
        templateId: this.selectedNewsletterTemplateId,
        scope: 'selected',
        memberIds: this.newsletterSelectedMemberIds,
      })
        .then(res => {
          const summary = res.data || {};
          this.newsletterPrepareMessage = `Sent ${summary.sentCount || 0} emails to ${summary.emailableCount || 0} selected emailable members.`;
        })
        .catch(err => {
          this.newsletterPrepareError = err.response && err.response.data && err.response.data.error
            ? err.response.data.error
            : 'Failed to send newsletter to selected members';
        })
        .finally(() => {
          this.newsletterSendBusy = false;
        });
    },
    nextNewsletterPage() {
      if (this.newsletterCurrentPage < this.newsletterTotalPages) {
        this.newsletterCurrentPage++;
        this.fetchNewsletterMembers();
      }
    },
    prevNewsletterPage() {
      if (this.newsletterCurrentPage > 1) {
        this.newsletterCurrentPage--;
        this.fetchNewsletterMembers();
      }
    },
    firstNewsletterPage() {
      this.newsletterCurrentPage = 1;
      this.fetchNewsletterMembers();
    },
    lastNewsletterPage() {
      this.newsletterCurrentPage = this.newsletterTotalPages;
      this.fetchNewsletterMembers();
    },
    goToNewsletterPage(pageNum) {
      this.newsletterCurrentPage = pageNum;
      this.fetchNewsletterMembers();
    },
    onNewsletterPageSizeChange() {
      this.newsletterCurrentPage = 1;
      this.fetchNewsletterMembers();
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
        this.showMembershipDetails = false;
        this.lookupNumber = '';
        this.lookupResult = null;
        this.lookupError = '';
        this.currentPage = 1;
        this.fetchMembers();
        return;
      }
      if (sectionKey === 'newsletters') {
        this.activeSection = 'newsletters';
        this.newsletterCurrentPage = 1;
        this.newsletterPrepareMessage = '';
        this.newsletterPrepareError = '';
        this.fetchNewsletterTemplates();
        this.fetchNewsletterMembers();
        return;
      }
      if (sectionKey === 'fishing-beats') {
        this.activeSection = 'fishing-beats';
        this.selectedFishingBeatKey = this.clubBeats.length ? this.beatKey(this.clubBeats[0]) : '';
        this.refreshFishingBeatMap();
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
      if (sectionKey === 'newsletters') {
        return 'Newsletters';
      }
      if (sectionKey === 'fishing-beats') {
        return 'Fishing Beats';
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
            this.clubLogoLoadFailed = false;
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
      this.clubLogoLoadFailed = false;
      this.activeSection = 'home';
      this.loginPassword = '';
      this.members = [];
      this.totalMembers = 0;
      this.currentPage = 1;
      this.newsletterMembers = [];
      this.newsletterTotalMembers = 0;
      this.newsletterCurrentPage = 1;
      this.newsletterSelectedMemberIds = [];
      this.newsletterTemplates = [];
      this.newsletterAvailableTags = [];
      this.selectedNewsletterTemplateId = '';
      this.newsletterFilterSelectBusy = false;
      this.newsletterSendBusy = false;
      this.newsletterPrepareMessage = '';
      this.newsletterPrepareError = '';
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
      this.selectMemberForEdit(member);
    },
    navigateEditMember(direction) {
      const targetIndex = this.editMemberIndex + direction;
      if (targetIndex < 0 || targetIndex >= this.members.length) {
        return;
      }
      this.selectMemberForEdit(this.members[targetIndex]);
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
      this.showMembershipDetails = true;
      this.lookupNumber = number;
      this.lookupMember();
    },
    hideLookupDetails() {
      this.showMembershipDetails = false;
      this.lookupNumber = '';
      this.lookupResult = null;
      this.lookupError = '';
    },
    formatFieldName(fieldName) {
      // Replace double underscores with double colon, then single underscores with space
      return fieldName.replace(/__/g, '::').replace(/_/g, ' ');
    },
    getExpiryDateStyle(dateString) {
      if (!dateString) return {};
      
      // Check for n/a or N/A values - render in green
      if (dateString.toLowerCase() === 'n/a') {
        return { color: 'green' };
      }
      
      try {
        // Parse the date (assuming format like YYYY-MM-DD or similar)
        const expiryDate = new Date(dateString);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        expiryDate.setHours(0, 0, 0, 0);
        
        // If expiry date is in the past, return red; otherwise black
        if (expiryDate < today) {
          return { color: 'red' };
        } else {
          return { color: 'black' };
        }
      } catch (e) {
        return {};
      }
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
}
#app .section-placeholder {
  max-width: 900px;
  margin: 40px auto;
  font-family: Helvetica, Arial, sans-serif;
}
#app .club-information-container {
  max-width: 900px;
  margin: 40px auto;
  font-family: Helvetica, Arial, sans-serif;
}
#app .newsletters-container,
#app .fishing-beats-container {
  max-width: 900px;
  margin: 40px auto;
  font-family: Helvetica, Arial, sans-serif;
}
#app .newsletter-table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}
#app .newsletter-table th,
#app .newsletter-table td {
  border: 1px solid #ccc;
  padding: 8px;
  text-align: left;
  font-size: 10pt;
}
#app .newsletter-table th {
  background: #f0f0f0;
  vertical-align: top;
}
#app .newsletter-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin: 10px 0;
}
#app .newsletter-toolbar {
  margin-bottom: 12px;
}
#app .newsletter-template-label {
  font-size: 10pt;
}
#app .newsletter-template-select {
  min-width: 220px;
  padding: 6px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: #fff;
}
#app .newsletter-template-preview {
  margin-bottom: 12px;
  padding: 10px;
  border: 1px solid #ccc;
  background: #fafafa;
}
#app .newsletter-template-preview h3 {
  margin: 0 0 8px 0;
  font-size: 11pt;
}
#app .newsletter-template-preview p {
  margin: 0 0 8px 0;
  font-size: 10pt;
}
#app .newsletter-template-preview-body {
  margin: 0;
  white-space: pre-wrap;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
}
#app .newsletter-preview-note {
  font-size: 8.5pt;
  font-weight: normal;
  color: #888;
}
#app .newsletter-template-tags-hint {
  margin-top: 10px;
  font-size: 9.5pt;
  color: #444;
}
#app .newsletter-tag-chip {
  display: inline-block;
  margin: 3px 4px 0 0;
  padding: 2px 6px;
  background: #e8f0fe;
  border: 1px solid #b3c6f0;
  border-radius: 3px;
  font-family: monospace;
  font-size: 9pt;
  color: #1a3a7a;
  cursor: default;
}
#app .newsletter-status {
  color: #1c6b2a;
  margin-bottom: 8px;
}
#app .newsletter-error {
  color: #c62828;
  margin-bottom: 8px;
}
#app .fishing-beats-table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}
#app .fishing-beats-layout {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}
#app .fishing-beat-detail-panel {
  width: 320px;
  min-width: 280px;
  border: 1px solid #ccc;
  background: #fafafa;
  padding: 10px;
  margin-top: 12px;
}
#app .fishing-beat-detail-panel h3 {
  margin: 0 0 10px 0;
  font-size: 11pt;
}
#app .fishing-beat-detail-table {
  width: 100%;
  border-collapse: collapse;
}
#app .fishing-beat-detail-table th,
#app .fishing-beat-detail-table td {
  border: 1px solid #ccc;
  padding: 6px;
  text-align: left;
  font-size: 10pt;
  vertical-align: top;
}
#app .fishing-beat-detail-table th {
  width: 130px;
  background: #f0f0f0;
}
#app .fishing-beat-map-wrap {
  margin-top: 10px;
}
#app .fishing-beat-map {
  width: 100%;
  height: 230px;
  border: 1px solid #ccc;
  box-sizing: border-box;
}
#app .fishing-beat-map-status {
  margin-top: 6px;
  font-size: 9pt;
  color: #555;
}
#app .fishing-beat-parking-list {
  margin: 0;
  padding-left: 18px;
}
#app .parking-pin-marker {
  background: transparent;
  border: none;
}
#app .parking-pin-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #1c7c3f;
  color: #fff;
  font-size: 10pt;
  font-weight: bold;
  line-height: 20px;
  text-align: center;
  box-shadow: 0 0 0 1px #fff inset;
}
#app .beat-name-link {
  display: inline-block;
  color: #007bff;
  text-decoration: underline;
  cursor: pointer;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
}
#app .beat-name-link.active {
  font-weight: bold;
}
#app .fishing-beats-table th,
#app .fishing-beats-table td {
  border: 1px solid #ccc;
  padding: 8px;
  text-align: left;
  font-size: 10pt;
}
#app .fishing-beats-table th {
  background: #f0f0f0;
}
#app .club-information-table {
  width: 100%;
  max-width: 680px;
  border-collapse: collapse;
  margin: 12px 0;
}
#app .club-information-table th,
#app .club-information-table td {
  border: 1px solid #ccc;
  padding: 8px;
  text-align: left;
  font-size: 10pt;
}
#app .club-information-table th {
  width: 180px;
  background: #f0f0f0;
}
#app .club-description-box {
  width: 100%;
  max-width: 680px;
  box-sizing: border-box;
  padding: 8px;
  margin-bottom: 12px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
  resize: vertical;
}
#app .member-edit-container {
  max-width: 900px;
  margin: 20px auto;
  font-family: Helvetica, Arial, sans-serif;
}
#app .member-edit-photo-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}
#app .member-edit-position {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 9pt;
  color: #555;
  margin-bottom: 8px;
}
#app .member-edit-photo {
  width: 140px;
  height: 140px;
  object-fit: cover;
  border: 2px solid #ccc;
  border-radius: 4px;
  background: #f0f0f0;
}
#app .member-edit-photo-name {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 8pt;
  color: #666;
  align-self: flex-end;
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
#app .membership-admin-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
#app .membership-admin-header h1 {
  margin: 0;
}
#app .membership-details-header {
  display: flex;
  align-items: center;
  gap: 10px;
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
#app .member-table th:nth-child(9), #app .member-table td:nth-child(9) { min-width: 110px; } /* Licence_Expiry */
#app .member-table th:nth-child(10), #app .member-table td:nth-child(10) { min-width: 90px; } /* Paid_Up_2026 */
#app .member-table th:nth-child(11), #app .member-table td:nth-child(11) { min-width: 70px; } /* Paused */
#app .member-table th:nth-child(12), #app .member-table td:nth-child(12) { min-width: 80px; } /* Resigned */
#app .column-filter {
  display: block;
  width: 100%;
  margin-top: 4px;
  box-sizing: border-box;
}
#app .column-filter[type="text"],
#app .column-filter input,
#app .column-filter select {
  padding: 4px;
  border: 1px solid #ccc;
  border-radius: 2px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 8pt;
}
#app .page-numbers {
  margin-top: 15px;
  text-align: center;
}
#app .page-numbers button {
  margin: 0 4px;
  min-width: 36px;
}
#app .page-numbers button:hover {
  background-color: #0069d9;
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
  color: #0056b3;
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
#app .app-footer {
  margin-top: 28px;
  padding-top: 12px;
  border-top: 1px solid #ccc;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 9pt;
  text-align: center;
  color: #444;
}
#app .app-footer-separator {
  margin: 0 8px;
  color: #888;
}
#app h2 {
  font-size: 14pt;
  font-family: Helvetica, Arial, sans-serif;
}
#app form {
  margin-bottom: 20px;
}
#app input {
  margin-right: 10px;
}
#app button {
  margin-right: 5px;
  padding: 8px 12px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
  color: #fff;
  background-color: #007bff;
  border: 1px solid #0056b3;
  border-radius: 4px;
  cursor: pointer;
}
#app button:hover:not(:disabled) {
  background-color: #0069d9;
  border-color: #0056b3;
}
#app button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
#app a,
#app a:visited,
#app .member-link,
#app .beat-name-link,
#app .w3w-link {
  color: #007bff;
}
#app a:hover,
#app a:focus,
#app .member-link:hover,
#app .beat-name-link:hover,
#app .w3w-link:hover,
#app .w3w-link:focus {
  color: #0056b3;
}
#app .manage-templates-button {
  margin-left: 10px;
}
#app .template-manager-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
#app .template-manager-content {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  max-width: 900px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
#app .template-manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid #ddd;
  padding-bottom: 10px;
}
#app .template-manager-header h3 {
  margin: 0;
  font-size: 18px;
}
#app .close-button {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  color: #666;
}
#app .close-button:hover {
  color: #000;
}
#app .template-list-section,
#app .template-edit-section {
  margin-bottom: 20px;
}
#app .template-list-section h4,
#app .template-edit-section h4 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 14px;
  color: #333;
}
#app .template-list {
  border: 1px solid #ddd;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 10px;
}
#app .template-item {
  padding: 10px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
#app .template-item:last-child {
  border-bottom: none;
}
#app .template-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
#app .template-item-name {
  font-weight: 500;
  flex: 1;
}
#app .template-item-actions {
  display: flex;
  gap: 5px;
}
#app .edit-button,
#app .delete-button {
  padding: 4px 8px;
  font-size: 12px;
}
#app .delete-button {
  background-color: #dc3545;
  border-color: #dc3545;
  color: white;
}
#app .delete-button:hover:not(:disabled) {
  background-color: #c82333;
  border-color: #bd2130;
}
#app .form-group {
  margin-bottom: 12px;
}
#app .form-group label {
  display: block;
  margin-bottom: 4px;
  font-weight: 500;
  font-size: 13px;
  color: #333;
}
#app .form-group input,
#app .form-group textarea {
  width: 100%;
  padding: 6px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 13px;
  box-sizing: border-box;
}
#app .form-group textarea {
  resize: vertical;
  font-family: monospace;
}
#app .available-tags-info {
  margin-bottom: 12px;
  padding: 8px;
  background-color: #f9f9f9;
  border-left: 3px solid #007bff;
  font-size: 12px;
}
#app .tag-chip {
  display: inline-block;
  background-color: #e9ecef;
  padding: 2px 6px;
  margin: 2px 2px 2px 0;
  border-radius: 3px;
  font-family: monospace;
  font-size: 11px;
  cursor: help;
}
#app .template-form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
#app .save-button {
  background-color: #28a745;
  border-color: #28a745;
  color: white;
}
#app .save-button:hover:not(:disabled) {
  background-color: #218838;
  border-color: #1e7e34;
}
#app .cancel-button {
  background-color: #6c757d;
  border-color: #6c757d;
  color: white;
}
#app .cancel-button:hover:not(:disabled) {
  background-color: #5a6268;
  border-color: #545b62;
}
#app .error-message {
  padding: 10px;
  margin-bottom: 10px;
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  font-size: 13px;
}
</style>
