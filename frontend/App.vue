<template>
  <div id="app">
    <app-header />
    <login-view v-if="!loggedIn" />
    <div v-else>
      <home-view v-if="activeSection === 'home'" />
    <membership-admin v-else-if="activeSection === 'membership-admin'" />
    <club-information v-else-if="activeSection === 'club-information'" />
    <newsletters v-else-if="activeSection === 'newsletters'" />
    <fishing-beats v-else-if="activeSection === 'fishing-beats'" />
    <member-edit v-else-if="activeSection === 'member-edit'" />
    <div v-else class="section-placeholder">
      <h2>{{ sectionDisplayName(activeSection) }}</h2>
      <p>This section is coming soon.</p>
      <button type="button" @click="goHome">Back to Home</button>
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
import AppHeader from './src/components/AppHeader.vue';
import LoginView from './src/components/LoginView.vue';
import HomeView from './src/components/HomeView.vue';
import MembershipAdmin from './src/components/MembershipAdmin.vue';
import ClubInformation from './src/components/ClubInformation.vue';
import Newsletters from './src/components/Newsletters.vue';
import FishingBeats from './src/components/FishingBeats.vue';
import MemberEdit from './src/components/MemberEdit.vue';
import {
  store,
  restoreMemberSession,
  applyMemberAuthHeader,
  initializeAuthInterceptor,
  teardownAuthInterceptor,
  loadClubs,
  fetchMembers,
  canAccessMembershipAdmin,
  sectionDisplayName,
} from './src/store.js';

export default {
  components: {
    AppHeader,
    LoginView,
    HomeView,
    MembershipAdmin,
    ClubInformation,
    Newsletters,
    FishingBeats,
    MemberEdit,
  },
  computed: {
    loggedIn: () => store.loggedIn,
    activeSection: () => store.activeSection,
  },
  created() {
    restoreMemberSession();
    applyMemberAuthHeader();
    initializeAuthInterceptor();
    loadClubs();
    if (store.loggedIn && canAccessMembershipAdmin.value) {
      fetchMembers();
    }
  },
  beforeUnmount() {
    teardownAuthInterceptor();
  },
  methods: {
    sectionDisplayName,
    goHome() {
      store.activeSection = 'home';
    },
  },
};
/* eslint-disable */
/* ================================================================
 * ORIGINAL App.vue component logic - preserved for reference.
 * This code has been refactored into src/store.js and
 * src/components/*.vue.  Safe to delete after verifying the build.
 * ================================================================
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
      memberAuthToken: '',
      memberRefreshToken: '',
      memberRoles: [],
      memberPermissions: [],
      authInterceptorId: null,
      refreshRequestPromise: null,
      loggedInUsername: '',
      accessError: '',
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
      clubSmtpFromEmail: '',
      clubSmtpFromName: '',
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
    },
    canAccessMembershipAdmin() {
      return this.hasPermission('member.club.list');
    },
    canAccessNewsletters() {
      return this.hasPermission('newsletter.send');
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
    this.restoreMemberSession();
    this.applyMemberAuthHeader();
    this.initializeAuthInterceptor();
    this.loadClubs();
    if (this.loggedIn && this.canAccessMembershipAdmin) {
      this.fetchMembers();
    }
  },
  beforeUnmount() {
    if (this.authInterceptorId !== null) {
      axios.interceptors.response.eject(this.authInterceptorId);
      this.authInterceptorId = null;
    }
    if (this.filterDebounceTimer) {
      clearTimeout(this.filterDebounceTimer);
    }
    if (this.newsletterFilterDebounceTimer) {
      clearTimeout(this.newsletterFilterDebounceTimer);
    }
    this.destroyFishingBeatMap();
  },
  methods: {
    setMemberTokens(accessToken, refreshToken) {
      this.memberAuthToken = accessToken || '';
      this.memberRefreshToken = refreshToken || '';
      this.applyMemberAuthHeader();
      this.persistMemberSession();
    },
    normalizeStringList(values) {
      if (!Array.isArray(values)) {
        return [];
      }
      return values
        .filter(value => typeof value === 'string')
        .map(value => value.trim())
        .filter(Boolean);
    },
    setMemberAuthz(roles, permissions) {
      this.memberRoles = this.normalizeStringList(roles);
      this.memberPermissions = this.normalizeStringList(permissions);
      this.persistMemberSession();
    },
    hasPermission(permissionCode) {
      if (!permissionCode) {
        return false;
      }
      return this.memberPermissions.includes(permissionCode);
    },
    canNavigateToSection(sectionKey) {
      if (sectionKey === 'membership-admin') {
        return this.canAccessMembershipAdmin;
      }
      if (sectionKey === 'newsletters') {
        return this.canAccessNewsletters;
      }
      return true;
    },
    applyMemberAuthHeader() {
      if (this.memberAuthToken) {
        axios.defaults.headers.common.Authorization = `Bearer ${this.memberAuthToken}`;
      } else {
        delete axios.defaults.headers.common.Authorization;
      }
    },
    initializeAuthInterceptor() {
      if (this.authInterceptorId !== null) {
        return;
      }

      this.authInterceptorId = axios.interceptors.response.use(
        response => response,
        async error => {
          const statusCode = error && error.response ? error.response.status : 0;
          const originalRequest = error && error.config ? error.config : null;

          if (!originalRequest || statusCode !== 401) {
            return Promise.reject(error);
          }

          const requestUrl = String(originalRequest.url || '');
          const skipRefresh = Boolean(originalRequest.skipAuthRefresh)
            || requestUrl.includes('/login')
            || requestUrl.includes('/logout')
            || requestUrl.includes('/token/refresh');

          if (skipRefresh || originalRequest._retry || !this.memberRefreshToken || !this.loggedIn) {
            return Promise.reject(error);
          }

          originalRequest._retry = true;

          try {
            await this.refreshMemberAuthToken();
            originalRequest.headers = originalRequest.headers || {};
            originalRequest.headers.Authorization = `Bearer ${this.memberAuthToken}`;
            return axios(originalRequest);
          } catch (refreshError) {
            this.handleAuthSessionExpired();
            return Promise.reject(refreshError);
          }
        }
      );
    },
    async refreshMemberAuthToken() {
      if (!this.memberRefreshToken) {
        throw new Error('Missing refresh token');
      }

      if (this.refreshRequestPromise) {
        return this.refreshRequestPromise;
      }

      this.refreshRequestPromise = axios.post(`${API_BASE_URL}/token/refresh`, {
        refreshToken: this.memberRefreshToken,
      }, {
        skipAuthRefresh: true,
      })
        .then(response => {
          const responseData = response && response.data ? response.data : {};
          if (!responseData.token || !responseData.refreshToken) {
            throw new Error('Invalid refresh response payload');
          }
          this.setMemberTokens(responseData.token, responseData.refreshToken);
        })
        .finally(() => {
          this.refreshRequestPromise = null;
        });

      return this.refreshRequestPromise;
    },
    handleAuthSessionExpired() {
      this.loggedIn = false;
      this.loggedInUser = null;
      this.memberAuthToken = '';
      this.memberRefreshToken = '';
      this.memberRoles = [];
      this.memberPermissions = [];
      this.loggedInUsername = '';
      this.applyMemberAuthHeader();
      this.clearMemberSession();
      this.loginError = 'Session expired. Please log in again.';
      this.accessError = '';
    },
    persistMemberSession() {
      try {
        const payload = {
          loggedIn: Boolean(this.loggedIn),
          loggedInUsername: this.loggedInUsername || '',
          loggedInClub: this.loggedInClub || this.selectedClub || 'GAAFFS',
          loggedInUser: this.loggedInUser || null,
          memberAuthToken: this.memberAuthToken || '',
          memberRefreshToken: this.memberRefreshToken || '',
          memberRoles: this.memberRoles || [],
          memberPermissions: this.memberPermissions || [],
        };
        window.localStorage.setItem(MEMBER_SESSION_STORAGE_KEY, JSON.stringify(payload));
      } catch {
      }
    },
    clearMemberSession() {
      try {
        window.localStorage.removeItem(MEMBER_SESSION_STORAGE_KEY);
      } catch {
      }
    },
    restoreMemberSession() {
      try {
        const raw = window.localStorage.getItem(MEMBER_SESSION_STORAGE_KEY);
        if (!raw) {
          return;
        }

        const payload = JSON.parse(raw);
        if (!payload || payload.loggedIn !== true || !payload.memberAuthToken || !payload.memberRefreshToken) {
          return;
        }

        const restoredClub = typeof payload.loggedInClub === 'string' && payload.loggedInClub.trim()
          ? payload.loggedInClub.trim()
          : 'GAAFFS';

        this.loggedIn = true;
        this.loggedInUsername = typeof payload.loggedInUsername === 'string' ? payload.loggedInUsername : '';
        this.loggedInClub = restoredClub;
        this.selectedClub = restoredClub;
        this.loggedInUser = payload.loggedInUser || null;
        this.memberAuthToken = typeof payload.memberAuthToken === 'string' ? payload.memberAuthToken : '';
        this.memberRefreshToken = typeof payload.memberRefreshToken === 'string' ? payload.memberRefreshToken : '';
        this.memberRoles = this.normalizeStringList(payload.memberRoles);
        this.memberPermissions = this.normalizeStringList(payload.memberPermissions);
      } catch {
        this.clearMemberSession();
      }
    },
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
      }).catch(err => {
        if (err.response?.status === 403) {
          this.members = [];
          this.totalMembers = 0;
          this.accessError = 'You do not have permission to view club members.';
          this.activeSection = 'home';
        }
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
      }).catch(err => {
        if (err.response?.status === 403) {
          this.newsletterMembers = [];
          this.newsletterTotalMembers = 0;
          this.accessError = 'You do not have permission to access newsletters.';
          this.activeSection = 'home';
        }
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
          this.clubSmtpFromEmail = res.data.smtpFromEmail || '';
          this.clubSmtpFromName  = res.data.smtpFromName  || '';
        })
        .catch(() => {
          this.newsletterTemplates = [];
          this.newsletterAvailableTags = [];
          this.clubSmtpFromEmail = '';
          this.clubSmtpFromName  = '';
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
      this.accessError = '';
      if (!this.canNavigateToSection(sectionKey)) {
        this.accessError = 'You do not have permission to access this section.';
        this.activeSection = 'home';
        return;
      }
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
            if (!res.data.token || !res.data.refreshToken) {
              this.loginError = 'Login failed: missing session token';
              return;
            }
            this.loggedIn = true;
            this.loggedInUser = res.data.user;
            this.setMemberTokens(res.data.token, res.data.refreshToken);
            this.setMemberAuthz(res.data.roles, res.data.permissions);
            this.loggedInUsername = this.loginUsername;
            this.loggedInClub = this.selectedClub;
            this.clubLogoLoadFailed = false;
            this.activeSection = 'home';
            this.currentPage = 1;
            this.accessError = '';
            if (this.canAccessMembershipAdmin) {
              this.fetchMembers();
            }
          } else {
            this.loginError = res.data.error || 'Login failed';
          }
        })
        .catch(err => {
          this.loginError = err.response && err.response.data && err.response.data.error ? err.response.data.error : 'Login failed';
        });
    },
    logout() {
      if (this.memberAuthToken) {
        axios.post(`${API_BASE_URL}/logout`, {
          refreshToken: this.memberRefreshToken,
        }, {
          headers: { Authorization: `Bearer ${this.memberAuthToken}` },
          skipAuthRefresh: true,
        }).catch(() => {
        });
      }
      this.loggedIn = false;
      this.loggedInUser = null;
      this.memberAuthToken = '';
      this.memberRefreshToken = '';
      this.memberRoles = [];
      this.memberPermissions = [];
      this.loggedInUsername = '';
      this.applyMemberAuthHeader();
      this.clearMemberSession();
      this.clubLogoLoadFailed = false;
      this.activeSection = 'home';
      this.accessError = '';
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
 * ================================================================
 * End of original App.vue component.
 * ================================================================ */
/* eslint-enable */
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
#app .access-error {
  margin-top: 16px;
  color: #b00020;
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
#app .newsletter-from-indicator {
  font-size: 9pt;
  color: #555;
}
#app .newsletter-from-not-set {
  color: #a94442;
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
#app .login-container .admin-login-link {
  margin-top: 10px;
  text-align: center;
}
#app .login-container .admin-login-link a {
  font-size: 10pt;
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
