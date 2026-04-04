<template>
  <div class="fishing-beats-container">
    <div class="fishing-beats-header">
      <button type="button" class="fishing-beats-back-button" @click="goHome">Back to Home</button>
      <h2>{{ clubFullName }} - Fishing Beats</h2>
    </div>
    <div v-if="clubBeats.length" class="fishing-beats-layout">
      <table class="fishing-beats-table">
        <thead>
          <tr>
            <th v-for="column in orderedTableColumns" :key="`header-${column.key}`">
              <div class="fishing-beats-sort-header">
                <span>{{ column.label }}</span>
                <span class="fishing-beats-sort-controls">
                  <button
                    type="button"
                    class="fishing-beats-sort-button"
                    :class="{ 'is-active': isSortActive(column.key, 'asc') }"
                    @click="setSort(column.key, 'asc')"
                  >
                    Asc. ↑
                  </button>
                  <button
                    type="button"
                    class="fishing-beats-sort-button"
                    :class="{ 'is-active': isSortActive(column.key, 'desc') }"
                    @click="setSort(column.key, 'desc')"
                  >
                    Desc. ↓
                  </button>
                </span>
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="beat in sortedClubBeats" :key="`${beat.Beat_ID}-${beat.Beat_Name}`">
            <td v-for="column in orderedTableColumns" :key="`${beatKey(beat)}-${column.key}`">
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
                  <span
                    v-if="selectedFishingBeat.Beat_Upstream_Latitude && selectedFishingBeat.Beat_Upstream_Longitude"
                  >
                    {{ selectedFishingBeat.Beat_Upstream_Latitude }}, {{ selectedFishingBeat.Beat_Upstream_Longitude }}
                  </span>
                  <span v-else>-</span>
                </template>
                <template v-else-if="column.key === 'Beat_Downstream_Coords'">
                  <span
                    v-if="selectedFishingBeat.Beat_Downstream_Latitude && selectedFishingBeat.Beat_Downstream_Longitude"
                  >
                    {{ selectedFishingBeat.Beat_Downstream_Latitude }}, {{ selectedFishingBeat.Beat_Downstream_Longitude }}
                  </span>
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
                <template v-else>
                  {{ selectedFishingBeat[column.key] || '-' }}
                </template>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="fishing-beat-map-wrap">
          <div ref="fishingBeatMap" class="fishing-beat-map"></div>
          <div v-if="fishingBeatMapStatus" class="fishing-beat-map-status">
            {{ fishingBeatMapStatus }}
          </div>
        </div>
      </div>
    </div>
    <p v-else>No fishing beats are configured for this club.</p>
    <button type="button" class="fishing-beats-back-button" @click="goHome">Back to Home</button>
  </div>
</template>

<script>
import axios from 'axios';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { store, clubDetails, API_BASE_URL } from '../store.js';

export default {
  name: 'FishingBeats',
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
        .filter(key => columnMap[key])
        .map(key => columnMap[key]);
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
      };
      const orderedKeys = [
        ...this.orderedTableColumns.map(column => column.key),
        'Detailed_Description',
        'Beat_Upstream_Coords',
        'Beat_Downstream_Coords',
        'Parking_Locations',
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
    parseCoordinateValue(rawValue) {
      const numericValue = Number.parseFloat(String(rawValue || '').trim());
      return Number.isFinite(numericValue) ? numericValue : null;
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
      this.fishingBeatMapLayers = [];
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

      const upstreamMarker = L.circleMarker(upstreamLatLng, {
        radius: 7, color: '#1f77b4', fillColor: '#1f77b4', fillOpacity: 0.8,
      }).bindPopup('Upstream limit');

      const downstreamMarker = L.circleMarker(downstreamLatLng, {
        radius: 7, color: '#d62728', fillColor: '#d62728', fillOpacity: 0.8,
      }).bindPopup('Downstream limit');

      const boundaryLine = L.polyline([upstreamLatLng, downstreamLatLng], {
        color: '#2f2f2f', weight: 3,
      });

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
  },
};
</script>
