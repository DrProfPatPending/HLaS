<template>
  <div class="beat-details-container">
    <div class="beat-details-header">
      <h2>{{ clubFullName }} - Beat Details</h2>
    </div>

    <div v-if="clubBeats.length" class="beat-details-selector-row">
      <label for="beat-details-select">Select Beat:</label>
      <select
        id="beat-details-select"
        v-model="selectedBeatKey"
        class="beat-details-select"
      >
        <option
          v-for="beat in clubBeats"
          :key="`option-${beatKey(beat)}`"
          :value="beatKey(beat)"
        >
          {{ formatBeatOptionLabel(beat) }}
        </option>
      </select>
    </div>

    <table v-if="selectedBeat" class="beat-details-table">
      <tbody>
        <tr v-for="column in orderedDetailColumns" :key="`detail-${column.key}`">
          <th>{{ column.label }}</th>
          <td>
            <template v-if="column.key === 'Beat_Upstream'">
              <a
                v-if="selectedBeat.Beat_Upstream_W3W"
                :href="selectedBeat.Beat_Upstream_W3W.url"
                rel="noopener noreferrer"
                @click.prevent="openReusableMapWindow(selectedBeat.Beat_Upstream_W3W.url)"
              >
                {{ selectedBeat.Beat_Upstream_W3W.display }}
              </a>
              <span v-else>{{ selectedBeat.Beat_Upstream || '-' }}</span>
            </template>

            <template v-else-if="column.key === 'Beat_Downstream'">
              <a
                v-if="selectedBeat.Beat_Downstream_W3W"
                :href="selectedBeat.Beat_Downstream_W3W.url"
                rel="noopener noreferrer"
                @click.prevent="openReusableMapWindow(selectedBeat.Beat_Downstream_W3W.url)"
              >
                {{ selectedBeat.Beat_Downstream_W3W.display }}
              </a>
              <span v-else>{{ selectedBeat.Beat_Downstream || '-' }}</span>
            </template>

            <template v-else-if="column.key === 'Detailed_Description'">
              {{ selectedBeat.Detailed_Description || '-' }}
            </template>

            <template v-else-if="column.key === 'Beat_Upstream_Coords'">
              <span
                v-if="selectedBeat.Beat_Upstream_Latitude && selectedBeat.Beat_Upstream_Longitude"
              >
                {{ selectedBeat.Beat_Upstream_Latitude }}, {{ selectedBeat.Beat_Upstream_Longitude }}
              </span>
              <span v-else>-</span>
            </template>

            <template v-else-if="column.key === 'Beat_Downstream_Coords'">
              <span
                v-if="selectedBeat.Beat_Downstream_Latitude && selectedBeat.Beat_Downstream_Longitude"
              >
                {{ selectedBeat.Beat_Downstream_Latitude }}, {{ selectedBeat.Beat_Downstream_Longitude }}
              </span>
              <span v-else>-</span>
            </template>

            <template v-else-if="column.key === 'Parking_Locations'">
              <ul v-if="selectedBeat.Parking_Locations.length" class="beat-details-parking-list">
                <li
                  v-for="(parking, parkingIndex) in selectedBeat.Parking_Locations"
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
              {{ selectedBeat[column.key] || '-' }}
            </template>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="selectedBeat" class="beat-details-map-wrap">
      <div ref="beatDetailsMap" class="beat-details-map"></div>
      <div v-if="beatDetailsMapStatus" class="beat-details-map-status">
        {{ beatDetailsMapStatus }}
      </div>
    </div>

    <p v-else-if="!clubBeats.length">No fishing beats are configured for this club.</p>
  </div>
</template>

<script>
import axios from 'axios';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { store, clubDetails, API_BASE_URL } from '../store.js';

export default {
  name: 'BeatDetails',
  data() {
    return {
      selectedBeatKey: '',
      fieldOrder: {},
      beatDetailsMapInstance: null,
      beatDetailsMapLayers: [],
      beatDetailsMapStatus: '',
      beatDetailsMapRequestId: 0,
    };
  },
  computed: {
    clubFullName: () => clubDetails.value.fullName,
    orderedDetailColumns() {
      const detailColumnMap = {
        Beat_ID: { key: 'Beat_ID', label: 'Beat ID' },
        Beat_Name: { key: 'Beat_Name', label: 'Beat Name' },
        River: { key: 'River', label: 'River' },
        Position: { key: 'Position', label: 'Position' },
        Beat_Upstream: { key: 'Beat_Upstream', label: 'Beat Upstream' },
        Beat_Downstream: { key: 'Beat_Downstream', label: 'Beat Downstream' },
        Beat_Description: { key: 'Beat_Description', label: 'Beat Description' },
        Detailed_Description: { key: 'Detailed_Description', label: 'Detailed Description' },
        Beat_Upstream_Coords: { key: 'Beat_Upstream_Coords', label: 'Upstream Co-ords' },
        Beat_Downstream_Coords: { key: 'Beat_Downstream_Coords', label: 'Downstream Co-ords' },
        Parking_Locations: { key: 'Parking_Locations', label: 'Parking' },
      };
      const fallbackOrder = [
        'Beat_ID',
        'Beat_Name',
        'River',
        'Position',
        'Beat_Upstream',
        'Beat_Downstream',
        'Beat_Description',
        'Detailed_Description',
        'Beat_Upstream_Coords',
        'Beat_Downstream_Coords',
        'Parking_Locations',
      ];
      const configuredOrder = Array.isArray(this.fieldOrder.beat_details)
        ? this.fieldOrder.beat_details
        : fallbackOrder;
      return configuredOrder
        .filter(key => this.isColumnVisible('beat_details', key))
        .map(key => detailColumnMap[key])
        .filter(Boolean);
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
    selectedBeat() {
      if (!this.clubBeats.length) return null;
      return this.clubBeats.find(b => this.beatKey(b) === this.selectedBeatKey) || this.clubBeats[0];
    },
  },
  watch: {
    selectedBeat() {
      this.refreshBeatDetailsMap();
    },
  },
  created() {
    this.loadFieldOrder();
    if (this.clubBeats.length) {
      this.selectedBeatKey = this.beatKey(this.clubBeats[0]);
    }
  },
  mounted() {
    this.refreshBeatDetailsMap();
  },
  beforeUnmount() {
    this.destroyBeatDetailsMap();
  },
  methods: {
    goHome() {
      store.activeSection = 'home';
    },
    isColumnVisible(contextKey, columnKey) {
      const configured = this.fieldOrder?.show_columns?.[contextKey]?.[columnKey];
      return configured !== false;
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
    formatBeatOptionLabel(beat) {
      const beatId = beat && beat.Beat_ID ? String(beat.Beat_ID).trim() : '';
      const beatName = beat && beat.Beat_Name ? String(beat.Beat_Name).trim() : '';
      const combinedLabel = `${beatId} ${beatName}`.trim();
      return combinedLabel || 'Unnamed Beat';
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
      if (popupWindow) {
        popupWindow.focus();
      }
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
      } catch {
        return null;
      }
      return null;
    },
    clearBeatDetailsMapLayers() {
      if (!this.beatDetailsMapInstance || !Array.isArray(this.beatDetailsMapLayers)) return;
      this.beatDetailsMapLayers.forEach(layer => {
        if (layer && this.beatDetailsMapInstance.hasLayer(layer)) {
          this.beatDetailsMapInstance.removeLayer(layer);
        }
      });
      this.beatDetailsMapLayers = [];
    },
    ensureBeatDetailsMap() {
      if (this.beatDetailsMapInstance) return;
      const mapElement = this.$refs.beatDetailsMap;
      if (!mapElement) return;
      this.beatDetailsMapInstance = L.map(mapElement, {
        zoomControl: true,
        attributionControl: true,
      }).setView([54.5, -2.5], 6);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors',
      }).addTo(this.beatDetailsMapInstance);
    },
    async refreshBeatDetailsMap() {
      const selectedBeat = this.selectedBeat;
      if (!selectedBeat) {
        this.beatDetailsMapStatus = 'No beat selected.';
        this.clearBeatDetailsMapLayers();
        return;
      }

      const requestId = ++this.beatDetailsMapRequestId;
      this.beatDetailsMapStatus = 'Loading map...';

      await this.$nextTick();
      this.ensureBeatDetailsMap();

      if (!this.beatDetailsMapInstance) {
        this.beatDetailsMapStatus = 'Map is unavailable.';
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

      if (requestId !== this.beatDetailsMapRequestId) return;
      this.clearBeatDetailsMapLayers();

      if (!upstreamCoords || !downstreamCoords) {
        this.beatDetailsMapStatus =
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
        if (locationW3W) {
          parkingPopup += `<br><a href="${locationW3W.url}" target="what3words-map-window">${locationW3W.display}</a>`;
        }
        if (description) parkingPopup += `<br>${description}`;

        const parkingMarker = L.marker(parkingLatLng, {
          icon: L.divIcon({
            className: 'parking-pin-marker',
            html: '<div class="parking-pin-dot">P</div>',
            iconSize: [20, 20],
            iconAnchor: [10, 10],
          }),
        }).bindPopup(parkingPopup);

        parkingMarker.addTo(this.beatDetailsMapInstance);
        parkingLayers.push(parkingMarker);
      });

      upstreamMarker.addTo(this.beatDetailsMapInstance);
      downstreamMarker.addTo(this.beatDetailsMapInstance);
      boundaryLine.addTo(this.beatDetailsMapInstance);
      this.beatDetailsMapLayers = [upstreamMarker, downstreamMarker, boundaryLine, ...parkingLayers];

      this.beatDetailsMapInstance.invalidateSize();
      const bounds = L.latLngBounds(allBoundsPoints);
      this.beatDetailsMapInstance.fitBounds(bounds.pad(0.2), { maxZoom: 16 });
      this.beatDetailsMapStatus = parkingLayers.length
        ? `Showing upstream/downstream limits and ${parkingLayers.length} parking marker${parkingLayers.length === 1 ? '' : 's'}.`
        : 'Showing upstream and downstream limits.';
    },
    destroyBeatDetailsMap() {
      this.clearBeatDetailsMapLayers();
      if (this.beatDetailsMapInstance) {
        this.beatDetailsMapInstance.remove();
        this.beatDetailsMapInstance = null;
      }
      this.beatDetailsMapStatus = '';
    },
  },
};
</script>

<style scoped>
.beat-details-container {
  max-width: 900px;
  margin: 40px auto;
  font-family: Helvetica, Arial, sans-serif;
}

.beat-details-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.beat-details-header h2 {
  margin: 0;
}

.beat-details-selector-row {
  margin: 14px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.beat-details-select {
  min-width: 260px;
  padding: 6px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: #fff;
}

.beat-details-table {
  width: 100%;
  border-collapse: collapse;
}

.beat-details-table th,
.beat-details-table td {
  border: 1px solid #ccc;
  padding: 8px;
  text-align: left;
  font-size: 10pt;
  vertical-align: top;
}

.beat-details-table th {
  width: 180px;
  background: #f0f0f0;
}

.beat-details-parking-list {
  margin: 0;
  padding-left: 18px;
}

.beat-details-map-wrap {
  margin-top: 16px;
}

.beat-details-map {
  width: 100%;
  height: 360px;
  border: 1px solid #ccc;
}

.beat-details-map-status {
  margin-top: 8px;
  font-size: 10pt;
  color: #333;
}

:deep(.parking-pin-marker) {
  background: transparent;
  border: none;
}

:deep(.parking-pin-dot) {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2ca02c;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 11px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.35);
}
</style>
