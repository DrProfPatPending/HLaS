<template>
  <div class="beat-details-container">
    <div class="beat-details-header">
      <button type="button" class="beat-details-back-button" @click="goHome">Back to Home</button>
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
          {{ beat.Beat_Name || beat.Beat_ID || 'Unnamed Beat' }}
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

    <p v-else-if="!clubBeats.length">No fishing beats are configured for this club.</p>
  </div>
</template>

<script>
import { store, clubDetails } from '../store.js';

export default {
  name: 'BeatDetails',
  data() {
    return {
      selectedBeatKey: '',
    };
  },
  computed: {
    clubFullName: () => clubDetails.value.fullName,
    orderedDetailColumns() {
      return [
        { key: 'Beat_ID', label: 'Beat ID' },
        { key: 'Beat_Name', label: 'Beat Name' },
        { key: 'River', label: 'River' },
        { key: 'Position', label: 'Position' },
        { key: 'Beat_Upstream', label: 'Beat Upstream' },
        { key: 'Beat_Downstream', label: 'Beat Downstream' },
        { key: 'Beat_Description', label: 'Beat Description' },
        { key: 'Detailed_Description', label: 'Detailed Description' },
        { key: 'Beat_Upstream_Coords', label: 'Upstream Co-ords' },
        { key: 'Beat_Downstream_Coords', label: 'Downstream Co-ords' },
        { key: 'Parking_Locations', label: 'Parking' },
      ];
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
  created() {
    if (this.clubBeats.length) {
      this.selectedBeatKey = this.beatKey(this.clubBeats[0]);
    }
  },
  methods: {
    goHome() {
      store.activeSection = 'home';
    },
    beatKey(beat) {
      const beatId = beat && beat.Beat_ID ? beat.Beat_ID : '';
      const beatName = beat && beat.Beat_Name ? beat.Beat_Name : '';
      return `${beatId}-${beatName}`;
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
</style>
