<template>
  <div class="fishing-beats-container">
    <div class="fishing-beats-header">
      <h2>{{ clubFullName }} - Fishing Beats</h2>
    </div>
    <div v-if="clubBeats.length" class="fishing-beats-layout">
      <table class="fishing-beats-table">
        <thead>
          <tr>
            <th
              v-for="column in orderedTableColumns"
              :key="`header-${column.key}`"
              :style="columnMinWidthStyle(column.key)"
            >
              <div class="fishing-beats-sort-header">
                <span>{{ column.label }}</span>
                <span class="fishing-beats-sort-controls">
                  <app-button
                    type="button"
                    inherit-style
                    class="fishing-beats-sort-button"
                    :class="{ 'is-active': isSortActive(column.key, 'asc') }"
                    @click="setSort(column.key, 'asc')"
                  >
                    Asc. ↑
                  </app-button>
                  <app-button
                    type="button"
                    inherit-style
                    class="fishing-beats-sort-button"
                    :class="{ 'is-active': isSortActive(column.key, 'desc') }"
                    @click="setSort(column.key, 'desc')"
                  >
                    Desc. ↓
                  </app-button>
                </span>
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="beat in sortedClubBeats" :key="`${beat.Beat_ID}-${beat.Beat_Name}`">
            <td
              v-for="column in orderedTableColumns"
              :key="`${beatKey(beat)}-${column.key}`"
              :style="columnMinWidthStyle(column.key)"
            >
              <template v-if="column.key === 'Beat_Name'">
                <a
                  href="#"
                  class="beat-name-link"
                  :class="{ 'active': selectedFishingBeat && beatKey(selectedFishingBeat) === beatKey(beat) }"
                  @click.prevent="selectFishingBeat(beat)"
                >
                  {{ beat.Beat_Name }}
                </a>
              </template>
              <template v-else-if="column.key === 'Beat_Upstream'">
                <a
                  v-if="beat.Beat_Upstream_W3W"
                  :href="beat.Beat_Upstream_W3W.url"
                  rel="noopener noreferrer"
                  @click.prevent="openReusableMapWindow(beat.Beat_Upstream_W3W.url)"
                >
                  {{ beat.Beat_Upstream_W3W.display }}
                </a>
                <span v-else>{{ beat.Beat_Upstream }}</span>
              </template>
              <template v-else-if="column.key === 'Beat_Downstream'">
                <a
                  v-if="beat.Beat_Downstream_W3W"
                  :href="beat.Beat_Downstream_W3W.url"
                  rel="noopener noreferrer"
                  @click.prevent="openReusableMapWindow(beat.Beat_Downstream_W3W.url)"
                >
                  {{ beat.Beat_Downstream_W3W.display }}
                </a>
                <span v-else>{{ beat.Beat_Downstream }}</span>
              </template>
              <template v-else>
                {{ beat[column.key] }}
              </template>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="selectedFishingBeat" class="fishing-beat-detail-panel">
        <h3>{{ selectedFishingBeat.Beat_Name }}</h3>
        <table class="fishing-beat-detail-table">
          <tbody>
            <tr v-for="column in orderedDetailColumns" :key="`detail-${column.key}`">
              <th>{{ column.label }}</th>
              <td>
                <template v-if="column.key === 'Beat_Upstream'">
                  <a
                    v-if="selectedFishingBeat.Beat_Upstream_W3W"
                    :href="selectedFishingBeat.Beat_Upstream_W3W.url"
                    rel="noopener noreferrer"
                    @click.prevent="openReusableMapWindow(selectedFishingBeat.Beat_Upstream_W3W.url)"
                  >
                    {{ selectedFishingBeat.Beat_Upstream_W3W.display }}
                  </a>
                  <span v-else>{{ selectedFishingBeat.Beat_Upstream || '-' }}</span>
                </template>
                <template v-else-if="column.key === 'Beat_Downstream'">
                  <a
                    v-if="selectedFishingBeat.Beat_Downstream_W3W"
                    :href="selectedFishingBeat.Beat_Downstream_W3W.url"
                    rel="noopener noreferrer"
                    @click.prevent="openReusableMapWindow(selectedFishingBeat.Beat_Downstream_W3W.url)"
                  >
                    {{ selectedFishingBeat.Beat_Downstream_W3W.display }}
                  </a>
                  <span v-else>{{ selectedFishingBeat.Beat_Downstream || '-' }}</span>
                </template>
                <template v-else-if="column.key === 'Detailed_Description'">
                  {{ selectedFishingBeat.Detailed_Description || '-' }}
                </template>
                <template v-else-if="column.key === 'Beat_Upstream_Coords'">
                  <a
                    v-if="selectedFishingBeat.Beat_Upstream_Latitude && selectedFishingBeat.Beat_Upstream_Longitude"
                    :href="googleMapsUrl(selectedFishingBeat.Beat_Upstream_Latitude, selectedFishingBeat.Beat_Upstream_Longitude)"
                    rel="noopener noreferrer"
                    @click.prevent="openGoogleMapsWindow(selectedFishingBeat.Beat_Upstream_Latitude, selectedFishingBeat.Beat_Upstream_Longitude)"
                  >
                    {{ selectedFishingBeat.Beat_Upstream_Latitude }}, {{ selectedFishingBeat.Beat_Upstream_Longitude }}
                  </a>
                  <span v-else>-</span>
                </template>
                <template v-else-if="column.key === 'Beat_Downstream_Coords'">
                  <a
                    v-if="selectedFishingBeat.Beat_Downstream_Latitude && selectedFishingBeat.Beat_Downstream_Longitude"
                    :href="googleMapsUrl(selectedFishingBeat.Beat_Downstream_Latitude, selectedFishingBeat.Beat_Downstream_Longitude)"
                    rel="noopener noreferrer"
                    @click.prevent="openGoogleMapsWindow(selectedFishingBeat.Beat_Downstream_Latitude, selectedFishingBeat.Beat_Downstream_Longitude)"
                  >
                    {{ selectedFishingBeat.Beat_Downstream_Latitude }}, {{ selectedFishingBeat.Beat_Downstream_Longitude }}
                  </a>
                  <span v-else>-</span>
                </template>
                <template v-else-if="column.key === 'Parking_Locations'">
                  <ul
                    v-if="selectedFishingBeat.Parking_Locations.length"
                    class="fishing-beat-parking-list"
                  >
                    <li
                      v-for="(parking, parkingIndex) in selectedFishingBeat.Parking_Locations"
                      :key="`parking-${parkingIndex}`"
                    >
                      <strong>{{ parking.Name || `Parking ${parkingIndex + 1}` }}</strong>
                      <span v-if="parking.Latitude && parking.Longitude">
                        ({{ parking.Latitude }}, {{ parking.Longitude }})
                      </span>
                      <span v-if="parking.Location_W3W">
                        &mdash;
                        <a
                          href="#"
                          class="w3w-link"
                          @click.prevent="openReusableMapWindow(parking.Location_W3W.url)"
                        >
                          {{ parking.Location_W3W.display }}
                        </a>
                      </span>
                      <span v-if="parking.Description"> - {{ parking.Description }}</span>
                    </li>
                  </ul>
                  <span v-else>-</span>
                </template>
                <template v-else-if="column.key === 'Pools'">
                  <ul
                    v-if="selectedFishingBeat.Pools.length"
                    class="fishing-beat-parking-list"
                  >
                    <li
                      v-for="(pool, poolIndex) in selectedFishingBeat.Pools"
                      :key="`pool-${poolIndex}`"
                    >
                      <strong>#{{ pool.Sequence || poolIndex + 1 }} {{ pool.Name || `Pool ${poolIndex + 1}` }}</strong>
                      <span v-if="pool.Latitude && pool.Longitude">
                        ({{ pool.Latitude }}, {{ pool.Longitude }})
                      </span>
                      <span v-if="pool.Location_W3W">
                        &mdash;
                        <a
                          href="#"
                          class="w3w-link"
                          @click.prevent="openReusableMapWindow(pool.Location_W3W.url)"
                        >
                          {{ pool.Location_W3W.display }}
                        </a>
                      </span>
                      <span v-if="pool.Description"> - {{ pool.Description }}</span>
                    </li>
                  </ul>
                  <span v-else>-</span>
                </template>
                <template v-else>
                  {{ selectedFishingBeat[column.key] || '-' }}
                </template>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="fishing-beat-map-wrap">
          <div ref="fishingBeatMap" class="fishing-beat-map"></div>
          <div class="fishing-beat-map-controls">
            <button
              v-if="fishingBeatWaypointsCount > 0"
              type="button"
              class="fishing-beat-waypoint-toggle"
              @click="toggleFishingBeatWaypoints"
            >{{ showFishingBeatWaypoints ? 'Hide Waypoints' : 'Show Waypoints' }}</button>
          </div>
          <div v-if="fishingBeatMapStatus" class="fishing-beat-map-status">
            {{ fishingBeatMapStatus }}
          </div>
        </div>
        <div v-if="fishingBeatDebugWaypoints.length > 0" class="fishing-beat-waypoints-debug">
          <h4>Waypoints (Debug)</h4>
          <table class="fishing-beat-waypoints-table">
            <thead>
              <tr>
                <th>Seq</th>
                <th>W3W</th>
                <th>Latitude</th>
                <th>Longitude</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(wp, index) in fishingBeatDebugWaypoints" :key="`waypoint-debug-${index}`">
                <td>{{ wp.Sequence }}</td>
                <td>{{ wp.W3W }}</td>
                <td>{{ wp.Latitude }}</td>
                <td>{{ wp.Longitude }}</td>
                <td>{{ wp.Description }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    <p v-else>No fishing beats are configured for this club.</p>
  </div>
</template>

<script>
import axios from 'axios';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { store, clubDetails, API_BASE_URL } from '../store.js';
import AppButton from './ui/AppButton.vue';

export default {
  name: 'FishingBeats',
  components: {
    AppButton,
  },
  data() {
    return {
      fieldOrder: {},
      sortKey: 'Beat_ID',
      sortDirection: 'asc',
      selectedFishingBeatKey: '',
      fishingBeatMapInstance: null,
      fishingBeatMapLayers: [],
      fishingBeatMapStatus: '',
      fishingBeatMapRequestId: 0,
      fishingBeatWaypointMarkers: [],
      showFishingBeatWaypoints: false,
      fishingBeatWaypointsCount: 0,
      fishingBeatDebugWaypoints: [],
    };
  },
  computed: {
    clubFullName: () => clubDetails.value.fullName,
    orderedTableColumns() {
      const columnMap = {
        Beat_ID: { key: 'Beat_ID', label: 'Beat ID' },
        Beat_Name: { key: 'Beat_Name', label: 'Beat Name' },
        River: { key: 'River', label: 'River' },
        Beat_Upstream: { key: 'Beat_Upstream', label: 'Beat Upstream' },
        Beat_Downstream: { key: 'Beat_Downstream', label: 'Beat Downstream' },
        Beat_Description: { key: 'Beat_Description', label: 'Beat Description' },
        Position: { key: 'Position', label: 'Position' },
      };
      const fallbackOrder = [
        'Beat_ID',
        'Beat_Name',
        'River',
        'Beat_Upstream',
        'Beat_Downstream',
        'Beat_Description',
        'Position',
      ];
      const configuredOrder = Array.isArray(this.fieldOrder.fishing_beats)
        ? this.fieldOrder.fishing_beats
        : fallbackOrder;
      return configuredOrder
        .filter(key => this.isColumnVisible('fishing_beats', key))
        .filter(key => columnMap[key])
        .map(key => columnMap[key]);
    },
    fishingBeatsMinWidths() {
      const configured = this.fieldOrder?.minimum_widths?.fishing_beats;
      return configured && typeof configured === 'object' ? configured : {};
    },
    orderedDetailColumns() {
      const detailColumnMap = {
        Beat_ID: { key: 'Beat_ID', label: 'Beat ID' },
        Beat_Name: { key: 'Beat_Name', label: 'Beat Name' },
        River: { key: 'River', label: 'River' },
        Beat_Upstream: { key: 'Beat_Upstream', label: 'Beat Upstream' },
        Beat_Downstream: { key: 'Beat_Downstream', label: 'Beat Downstream' },
        Beat_Description: { key: 'Beat_Description', label: 'Beat Description' },
        Position: { key: 'Position', label: 'Position' },
        Detailed_Description: { key: 'Detailed_Description', label: 'Detailed Description' },
        Beat_Upstream_Coords: { key: 'Beat_Upstream_Coords', label: 'Upstream Co-ords' },
        Beat_Downstream_Coords: { key: 'Beat_Downstream_Coords', label: 'Downstream Co-ords' },
        Parking_Locations: { key: 'Parking_Locations', label: 'Parking' },
        Pools: { key: 'Pools', label: 'Pools' },
      };
      const orderedKeys = [
        ...this.orderedTableColumns.map(column => column.key),
        'Detailed_Description',
        'Beat_Upstream_Coords',
        'Beat_Downstream_Coords',
        'Parking_Locations',
        'Pools',
      ];
      return orderedKeys.map(key => detailColumnMap[key]).filter(Boolean);
    },
    clubBeats() {
      const beats = Array.isArray(clubDetails.value.beats) ? clubDetails.value.beats : [];
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
                .filter(loc => loc && typeof loc === 'object')
                .map(loc => ({
                  Name: loc && loc.Name ? loc.Name : '',
                  Location_W3W: this.parseWhat3Words(loc && loc.Location ? loc.Location : ''),
                  Description: loc && loc.Description ? loc.Description : '',
                  Latitude: loc && loc.Latitude ? loc.Latitude : '',
                  Longitude: loc && loc.Longitude ? loc.Longitude : '',
                }))
            : [],
          Pools: this.normalizePoolsForDisplay(beat && beat.Pools),
          Waypoints: Array.isArray(beat && beat.Waypoints) ? beat.Waypoints : [],
          Beat_Description: beat && beat.Beat_Description ? beat.Beat_Description : '',
          Detailed_Description: beat && beat.Detailed_Description ? beat.Detailed_Description : '',
        };
      });
    },
    sortedClubBeats() {
      const beats = [...this.clubBeats];
      const sortKey = this.sortKey;
      const sortDirection = this.sortDirection === 'desc' ? -1 : 1;
      return beats.sort((leftBeat, rightBeat) => {
        const leftValue = this.normalizeSortValue(leftBeat?.[sortKey]);
        const rightValue = this.normalizeSortValue(rightBeat?.[sortKey]);

        if (leftValue < rightValue) return -1 * sortDirection;
        if (leftValue > rightValue) return 1 * sortDirection;

        const leftName = this.normalizeSortValue(leftBeat?.Beat_Name);
        const rightName = this.normalizeSortValue(rightBeat?.Beat_Name);
        if (leftName < rightName) return -1;
        if (leftName > rightName) return 1;
        return 0;
      });
    },
    selectedFishingBeat() {
      const beats = this.clubBeats;
      if (!beats.length) return null;
      return beats.find(b => this.beatKey(b) === this.selectedFishingBeatKey) || beats[0];
    },
  },
  watch: {
    selectedFishingBeat() {
      this.refreshFishingBeatMap();
    },
  },
  created() {
    this.loadFieldOrder();
    if (this.clubBeats.length) {
      this.selectedFishingBeatKey = this.beatKey(this.clubBeats[0]);
    }
  },
  mounted() {
    this.refreshFishingBeatMap();
  },
  beforeUnmount() {
    this.destroyFishingBeatMap();
  },
  methods: {
    goHome() {
      store.activeSection = 'home';
    },
    setSort(columnKey, direction) {
      this.sortKey = columnKey;
      this.sortDirection = direction === 'desc' ? 'desc' : 'asc';
    },
    isColumnVisible(contextKey, columnKey) {
      const configured = this.fieldOrder?.show_columns?.[contextKey]?.[columnKey];
      return configured !== false;
    },
    isSortActive(columnKey, direction) {
      return this.sortKey === columnKey && this.sortDirection === direction;
    },
    normalizeSortValue(rawValue) {
      const trimmedValue = String(rawValue ?? '').trim();
      const numericValue = Number(trimmedValue);
      if (trimmedValue !== '' && Number.isFinite(numericValue)) {
        return numericValue;
      }
      return trimmedValue.toLowerCase();
    },
    normalizeColumnMinWidth(rawWidth) {
      if (typeof rawWidth === 'number' && Number.isFinite(rawWidth) && rawWidth > 0) {
        return `${rawWidth}px`;
      }
      if (typeof rawWidth === 'string') {
        const trimmed = rawWidth.trim().toLowerCase();
        if (/^\d+px$/.test(trimmed)) {
          return trimmed;
        }
        const numericWidth = Number(trimmed);
        if (Number.isFinite(numericWidth) && numericWidth > 0) {
          return `${numericWidth}px`;
        }
      }
      return '50px';
    },
    columnMinWidthStyle(columnKey) {
      const configuredWidth = this.fishingBeatsMinWidths?.[columnKey];
      return {
        minWidth: this.normalizeColumnMinWidth(configuredWidth),
      };
    },
    loadFieldOrder() {
      axios
        .get(`${API_BASE_URL}/field-order`)
        .then(res => {
          const loadedFieldOrder = res.data?.field_order;
          this.fieldOrder = loadedFieldOrder && typeof loadedFieldOrder === 'object'
            ? loadedFieldOrder
            : {};
        })
        .catch(() => {
          this.fieldOrder = {};
        });
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
      if (typeof rawValue !== 'string') return null;
      const trimmed = rawValue.trim();
      if (!trimmed) return null;
      const withoutSlashes = trimmed.replace(/^\/+/, '');
      const words = withoutSlashes.split('.').map(w => w.trim()).filter(Boolean);
      if (words.length !== 3) return null;
      const normalizedWords = words.map(w => w.toLowerCase());
      const normalizedPath = normalizedWords.map(w => encodeURIComponent(w)).join('.');
      return {
        display: `///${normalizedWords.join('.')}`,
        url: `https://what3words.com/${normalizedPath}`,
      };
    },
    openReusableMapWindow(url) {
      if (!url) return;
      const popupWindow = window.open(
        url,
        'what3words-map-window',
        'popup=yes,width=980,height=760,resizable=yes,scrollbars=yes'
      );
      if (popupWindow) { popupWindow.focus(); return; }
      window.location.href = url;
    },
    googleMapsUrl(lat, lng) {
      return `https://www.google.com/maps?q=${encodeURIComponent(lat)},${encodeURIComponent(lng)}`;
    },
    openGoogleMapsWindow(lat, lng) {
      const url = this.googleMapsUrl(lat, lng);
      const popupWindow = window.open(
        url,
        'google-maps-window',
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
    parsePoolsInput(rawPools) {
      const parsed = Array.isArray(rawPools) ? rawPools : [];
      const normalized = parsed
        .filter(pool => pool && typeof pool === 'object')
        .map(pool => ({
          Sequence: String(pool?.Sequence || '').trim(),
          Name: String(pool?.Name || '').trim(),
          Location: String(pool?.Location || '').trim(),
          Description: String(pool?.Description || '').trim(),
          Latitude: String(pool?.Latitude || '').trim(),
          Longitude: String(pool?.Longitude || '').trim(),
        }))
        .filter(pool =>
          pool.Sequence || pool.Name || pool.Location || pool.Description || pool.Latitude || pool.Longitude
        )
        .map((pool, index) => {
          const sequenceNumber = Number.parseInt(pool.Sequence, 10);
          return {
            ...pool,
            Sequence: Number.isFinite(sequenceNumber) && sequenceNumber > 0
              ? String(sequenceNumber)
              : String(index + 1),
          };
        })
        .sort((a, b) => Number.parseInt(a.Sequence, 10) - Number.parseInt(b.Sequence, 10))
        .map((pool, index) => ({
          ...pool,
          Sequence: String(index + 1),
        }));

      return normalized;
    },
    normalizePoolsForDisplay(rawPools) {
      return this.parsePoolsInput(rawPools).map(pool => ({
        ...pool,
        Location_W3W: this.parseWhat3Words(pool.Location),
      }));
    },
    async resolveBeatPointCoordinates(wordsValue, latitudeValue, longitudeValue) {
      const lat = this.parseCoordinateValue(latitudeValue);
      const lng = this.parseCoordinateValue(longitudeValue);
      if (lat !== null && lng !== null) return { lat, lng, source: 'coordinates' };

      const parsedW3W = this.parseWhat3Words(wordsValue);
      if (!parsedW3W) return null;

      try {
        const res = await axios.get(`${API_BASE_URL}/w3w/coordinates`, {
          params: { words: parsedW3W.display },
        });
        const data = res && res.data ? res.data : {};
        const resolvedLat = this.parseCoordinateValue(data.lat);
        const resolvedLng = this.parseCoordinateValue(data.lng);
        if (resolvedLat !== null && resolvedLng !== null) {
          return { lat: resolvedLat, lng: resolvedLng, source: 'w3w' };
        }
      } catch { /* ignore */ }
      return null;
    },
    clearFishingBeatMapLayers() {
      if (!this.fishingBeatMapInstance || !Array.isArray(this.fishingBeatMapLayers)) return;
      this.fishingBeatMapLayers.forEach(layer => {
        if (layer && this.fishingBeatMapInstance.hasLayer(layer)) {
          this.fishingBeatMapInstance.removeLayer(layer);
        }
      });
      if (Array.isArray(this.fishingBeatWaypointMarkers)) {
        this.fishingBeatWaypointMarkers.forEach(marker => {
          if (marker && this.fishingBeatMapInstance.hasLayer(marker)) {
            this.fishingBeatMapInstance.removeLayer(marker);
          }
        });
      }
      this.fishingBeatMapLayers = [];
      this.fishingBeatWaypointMarkers = [];
    },
    ensureFishingBeatMap() {
      if (this.fishingBeatMapInstance) return;
      const mapElement = this.$refs.fishingBeatMap;
      if (!mapElement) return;
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

      const upstreamCoords = await this.resolveBeatPointCoordinates(
        selectedBeat.Beat_Upstream,
        selectedBeat.Beat_Upstream_Latitude,
        selectedBeat.Beat_Upstream_Longitude
      );
      const downstreamCoords = await this.resolveBeatPointCoordinates(
        selectedBeat.Beat_Downstream,
        selectedBeat.Beat_Downstream_Latitude,
        selectedBeat.Beat_Downstream_Longitude
      );

      if (requestId !== this.fishingBeatMapRequestId) return;
      this.clearFishingBeatMapLayers();

      if (!upstreamCoords || !downstreamCoords) {
        this.fishingBeatMapStatus =
          'Map requires valid W3W lookup support or fallback coordinates for both upstream and downstream limits.';
        return;
      }

      const upstreamLatLng = L.latLng(upstreamCoords.lat, upstreamCoords.lng);
      const downstreamLatLng = L.latLng(downstreamCoords.lat, downstreamCoords.lng);
      const allBoundsPoints = [upstreamLatLng, downstreamLatLng];

      const sortedPools = Array.isArray(selectedBeat.Pools)
        ? [...selectedBeat.Pools].sort((a, b) => Number.parseInt(a.Sequence, 10) - Number.parseInt(b.Sequence, 10))
        : [];

      const poolMarkers = [];
      for (let i = 0; i < sortedPools.length; i += 1) {
        const pool = sortedPools[i];
        const poolCoords = await this.resolveBeatPointCoordinates(
          pool?.Location,
          pool?.Latitude,
          pool?.Longitude
        );
        if (!poolCoords) continue;

        const poolLatLng = L.latLng(poolCoords.lat, poolCoords.lng);
        allBoundsPoints.push(poolLatLng);

        const sequenceLabel = pool?.Sequence || String(i + 1);
        const nameLabel = pool?.Name ? `#${sequenceLabel} ${pool.Name}` : `Pool #${sequenceLabel}`;
        const locationW3W = pool?.Location_W3W || this.parseWhat3Words(pool?.Location || '');
        let poolPopup = nameLabel;
        if (locationW3W) poolPopup += `<br><a href="${locationW3W.url}" target="what3words-map-window">${locationW3W.display}</a>`;
        if (pool?.Description) poolPopup += `<br>${pool.Description}`;

        const poolMarker = L.marker(poolLatLng, {
          icon: L.divIcon({
            className: 'pool-pin-marker',
            html: `<div class="pool-pin-dot">${sequenceLabel}</div>`,
            iconSize: [22, 22],
            iconAnchor: [11, 11],
          }),
        }).bindPopup(poolPopup);

        poolMarker.addTo(this.fishingBeatMapInstance);
        poolMarkers.push(poolMarker);
      }

      const upstreamMarker = L.circleMarker(upstreamLatLng, {
        radius: 7, color: '#1f77b4', fillColor: '#1f77b4', fillOpacity: 0.8,
      }).bindPopup('Upstream limit');

      const downstreamMarker = L.circleMarker(downstreamLatLng, {
        radius: 7, color: '#d62728', fillColor: '#d62728', fillOpacity: 0.8,
      }).bindPopup('Downstream limit');

      const parkingLayers = [];
      const parkingLocations = Array.isArray(selectedBeat.Parking_Locations)
        ? selectedBeat.Parking_Locations
        : [];
      parkingLocations.forEach((parking, parkingIndex) => {
        const parkingLat = this.parseCoordinateValue(parking && parking.Latitude ? parking.Latitude : '');
        const parkingLng = this.parseCoordinateValue(parking && parking.Longitude ? parking.Longitude : '');
        if (parkingLat === null || parkingLng === null) return;

        const parkingLatLng = L.latLng(parkingLat, parkingLng);
        allBoundsPoints.push(parkingLatLng);

        const label = parking && parking.Name ? parking.Name : `Parking ${parkingIndex + 1}`;
        const description = parking && parking.Description ? parking.Description : '';
        const locationW3W = parking && parking.Location_W3W ? parking.Location_W3W : null;
        let parkingPopup = label;
        if (locationW3W) parkingPopup += `<br><a href="${locationW3W.url}" target="what3words-map-window">${locationW3W.display}</a>`;
        if (description) parkingPopup += `<br>${description}`;

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

      // Render waypoints
      const sortedWaypoints = Array.isArray(selectedBeat.Waypoints)
        ? [...selectedBeat.Waypoints].sort((a, b) => Number.parseInt(a.Sequence, 10) - Number.parseInt(b.Sequence, 10))
        : [];
      const waypointMarkers = [];
      const waypointRouteLatLngs = [];
      for (let i = 0; i < sortedWaypoints.length; i += 1) {
        const wp = sortedWaypoints[i];
        const wpCoords = await this.resolveBeatPointCoordinates(wp?.W3W, wp?.Latitude, wp?.Longitude);
        if (requestId !== this.fishingBeatMapRequestId) return;
        if (!wpCoords) continue;
        const wpLatLng = L.latLng(wpCoords.lat, wpCoords.lng);
        waypointRouteLatLngs.push(wpLatLng);
        allBoundsPoints.push(wpLatLng);

        const seqLabel = wp?.Sequence || String(i + 1);
        let wpPopup = `Waypoint ${seqLabel}`;
        if (wp?.Description) wpPopup += `<br>${wp.Description}`;
        waypointMarkers.push(
          L.circleMarker(wpLatLng, {
            radius: 4, color: '#888', fillColor: '#bbb', fillOpacity: 0.9, weight: 1,
          }).bindPopup(wpPopup)
        );
      }

      let waypointRoutePolyline = null;
      if (waypointRouteLatLngs.length >= 2) {
        waypointRoutePolyline = L.polyline(waypointRouteLatLngs, { color: '#1a6ea0', weight: 3 });
      }

      upstreamMarker.addTo(this.fishingBeatMapInstance);
      downstreamMarker.addTo(this.fishingBeatMapInstance);
      if (waypointRoutePolyline) waypointRoutePolyline.addTo(this.fishingBeatMapInstance);
      if (this.showFishingBeatWaypoints) {
        waypointMarkers.forEach(marker => marker.addTo(this.fishingBeatMapInstance));
      }
      this.fishingBeatWaypointMarkers = waypointMarkers;
      this.fishingBeatWaypointsCount = waypointMarkers.length;
      this.fishingBeatDebugWaypoints = sortedWaypoints;
      this.fishingBeatMapLayers = [upstreamMarker, downstreamMarker, waypointRoutePolyline, ...poolMarkers, ...parkingLayers].filter(Boolean);

      this.fishingBeatMapInstance.invalidateSize();
      const bounds = L.latLngBounds(allBoundsPoints);
      this.fishingBeatMapInstance.fitBounds(bounds.pad(0.2), { maxZoom: 16 });
      const poolLabel = `${poolMarkers.length} pool node${poolMarkers.length === 1 ? '' : 's'}`;
      const parkingLabel = `${parkingLayers.length} parking marker${parkingLayers.length === 1 ? '' : 's'}`;
      const waypointLabel = `${waypointMarkers.length} waypoint${waypointMarkers.length === 1 ? '' : 's'}`;
      let statusMessage = 'Showing';
      if (waypointMarkers.length) statusMessage += ` route (${waypointLabel})`;
      if (poolMarkers.length) statusMessage += ` with ${poolLabel}`;
      if (parkingLayers.length) statusMessage += ` and ${parkingLabel}`;
      if (!waypointMarkers.length && !poolMarkers.length && !parkingLayers.length) {
        statusMessage += ' upstream and downstream limits';
      }
      statusMessage += '.';
      this.fishingBeatMapStatus = statusMessage;
    },
    toggleFishingBeatWaypoints() {
      this.showFishingBeatWaypoints = !this.showFishingBeatWaypoints;
      if (!this.fishingBeatMapInstance) return;
      this.fishingBeatWaypointMarkers.forEach(marker => {
        if (this.showFishingBeatWaypoints) {
          marker.addTo(this.fishingBeatMapInstance);
        } else {
          this.fishingBeatMapInstance.removeLayer(marker);
        }
      });
    },
    destroyFishingBeatMap() {
      this.clearFishingBeatMapLayers();
      if (this.fishingBeatMapInstance) {
        this.fishingBeatMapInstance.remove();
        this.fishingBeatMapInstance = null;
      }
      this.fishingBeatMapStatus = '';
    },
  },
};
</script>

<style scoped>
.fishing-beat-parking-list {
  margin: 0;
  padding-left: 18px;
}

:deep(.parking-pin-marker),
:deep(.pool-pin-marker) {
  background: transparent;
  border: none;
}

:deep(.parking-pin-dot) {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #198754;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 11px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.35);
}

:deep(.pool-pin-dot) {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #6f42c1;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 11px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.35);
}

.fishing-beat-map-controls {
  display: flex;
  gap: 8px;
  margin-top: 6px;
  margin-bottom: 2px;
}

.fishing-beat-waypoint-toggle {
  padding: 4px 10px;
  font-size: 10pt;
  background: #f0f4f8;
  border: 1px solid #aac;
  border-radius: 4px;
  cursor: pointer;
}

.fishing-beat-waypoint-toggle:hover {
  background: #dde8f5;
}

.fishing-beat-waypoints-debug {
  margin-top: 12px;
  padding: 8px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.fishing-beat-waypoints-debug h4 {
  margin: 0 0 8px 0;
  font-size: 10pt;
  color: #666;
}

.fishing-beat-waypoints-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9pt;
  background: white;
}

.fishing-beat-waypoints-table thead {
  background: #e8e8e8;
  font-weight: bold;
}

.fishing-beat-waypoints-table th,
.fishing-beat-waypoints-table td {
  border: 1px solid #ddd;
  padding: 4px 6px;
  text-align: left;
}

.fishing-beat-waypoints-table tbody tr:nth-child(even) {
  background: #f9f9f9;
}

.fishing-beat-waypoints-table tbody tr:hover {
  background: #f0e8ff;
}
</style>
