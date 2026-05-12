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

    <div v-if="canManageBeats" class="beat-details-actions-row">
      <app-button type="button" inherit-style @click="addNewBeat" :disabled="isSaving">Add</app-button>
      <app-button type="button" inherit-style @click="startEditBeat" :disabled="isSaving || !selectedBeat || isEditing">Edit</app-button>
      <app-button type="button" inherit-style @click="saveBeatEdits" :disabled="isSaving || !isEditing || hasLocationValidationErrors">{{ isSaving ? 'Saving...' : 'Save' }}</app-button>
      <app-button type="button" inherit-style @click="cancelEditBeat" :disabled="isSaving || !isEditing">Cancel</app-button>
      <app-button type="button" inherit-style @click="deleteSelectedBeat" :disabled="isSaving || !selectedBeat">Delete</app-button>
    </div>

    <p v-if="beatEditError" class="beat-details-error">{{ beatEditError }}</p>
    <p v-if="beatEditSuccess" class="beat-details-success">{{ beatEditSuccess }}</p>

    <table v-if="selectedBeat && !isEditing" class="beat-details-quick-info-table">
      <tbody>
        <tr>
          <th>{{ detailLabelMap.River }}</th>
          <td>{{ selectedBeat.River || '-' }}</td>
          <th>{{ detailLabelMap.Beat_Name }}</th>
          <td>{{ selectedBeat.Beat_Name || '-' }}</td>
        </tr>
      </tbody>
    </table>

    <div v-if="selectedBeat && !isEditing" class="beat-details-map-wrap">
      <div ref="beatDetailsMap" class="beat-details-map"></div>
      <div class="beat-details-map-controls">
        <div class="rotation-controls">
          <button
            type="button"
            class="rotation-btn"
            title="Rotate Left"
            @click="changeBeatDetailsRotation(-15)"
          >↺</button>
          <button
            v-if="currentBeatDetailsBearing !== 0"
            type="button"
            class="rotation-btn compass-reset"
            title="North"
            @click="resetBeatDetailsNorth"
          >⬆</button>
          <button
            type="button"
            class="rotation-btn"
            title="Rotate Right"
            @click="changeBeatDetailsRotation(15)"
          >↻</button>
        </div>
        <button
          v-if="beatDetailsWaypointsCount > 0"
          type="button"
          class="beat-details-waypoint-toggle"
          @click="toggleWaypointMarkers"
        >{{ showWaypointMarkers ? 'Hide Waypoints' : 'Show Waypoints' }}</button>
      </div>
      <div v-if="beatDetailsMapStatus" class="beat-details-map-status">
        {{ beatDetailsMapStatus }}
      </div>
    </div>

    <table v-if="selectedBeat && isEditing" class="beat-details-table">
      <tbody>
        <tr>
          <th>Beat ID</th>
          <td><input v-model="editForm.Beat_ID" class="beat-details-input" /></td>
        </tr>
        <tr>
          <th>Beat Name</th>
          <td><input v-model="editForm.Beat_Name" class="beat-details-input" /></td>
        </tr>
        <tr>
          <th>River</th>
          <td><input v-model="editForm.River" class="beat-details-input" /></td>
        </tr>
        <tr>
          <th>Position</th>
          <td><input v-model="editForm.Position" class="beat-details-input" /></td>
        </tr>
        <tr>
          <th>Beat Upstream</th>
          <td><input v-model="editForm.Beat_Upstream" class="beat-details-input" /></td>
        </tr>
        <tr>
          <th>Beat Downstream</th>
          <td><input v-model="editForm.Beat_Downstream" class="beat-details-input" /></td>
        </tr>
        <tr>
          <th>Upstream Latitude</th>
          <td><input v-model="editForm.Beat_Upstream_Latitude" class="beat-details-input" /></td>
        </tr>
        <tr>
          <th>Upstream Longitude</th>
          <td><input v-model="editForm.Beat_Upstream_Longitude" class="beat-details-input" /></td>
        </tr>
        <tr>
          <th>Downstream Latitude</th>
          <td><input v-model="editForm.Beat_Downstream_Latitude" class="beat-details-input" /></td>
        </tr>
        <tr>
          <th>Downstream Longitude</th>
          <td><input v-model="editForm.Beat_Downstream_Longitude" class="beat-details-input" /></td>
        </tr>
        <tr>
          <th>Beat Description</th>
          <td><textarea v-model="editForm.Beat_Description" class="beat-details-textarea" rows="3"></textarea></td>
        </tr>
        <tr>
          <th>Detailed Description</th>
          <td><textarea v-model="editForm.Detailed_Description" class="beat-details-textarea" rows="4"></textarea></td>
        </tr>
        <tr>
          <th>Parking Locations</th>
          <td>
            <div class="beat-details-parking-editor">
              <div
                v-for="(parking, parkingIndex) in editForm.Parking_Locations"
                :key="`parking-edit-${parkingIndex}`"
                class="beat-details-parking-editor-row-wrap"
              >
                <div class="beat-details-parking-editor-row">
                  <input
                    v-model="parking.Name"
                    class="beat-details-input"
                    placeholder="Name"
                  />
                  <input
                    v-model="parking.Location"
                    :class="['beat-details-input', { 'beat-details-input-invalid': isParkingFieldInvalid(parkingIndex, 'Location') }]"
                    placeholder="What3Words (///word.word.word)"
                  />
                  <input
                    v-model="parking.Latitude"
                    :class="['beat-details-input', { 'beat-details-input-invalid': isParkingFieldInvalid(parkingIndex, 'Latitude') }]"
                    placeholder="Latitude"
                  />
                  <input
                    v-model="parking.Longitude"
                    :class="['beat-details-input', { 'beat-details-input-invalid': isParkingFieldInvalid(parkingIndex, 'Longitude') }]"
                    placeholder="Longitude"
                  />
                  <input
                    v-model="parking.Description"
                    class="beat-details-input"
                    placeholder="Description"
                  />
                  <app-button
                    type="button"
                    class="beat-details-parking-remove"
                    inherit-style
                    @click="removeParkingLocationRow(parkingIndex)"
                  >
                    Remove
                  </app-button>
                </div>
                <p
                  v-if="parkingValidationErrors[parkingIndex]"
                  class="beat-details-parking-validation"
                >
                  {{ parkingValidationErrors[parkingIndex] }}
                </p>
              </div>

              <app-button type="button" inherit-style @click="addParkingLocationRow">Add Parking Location</app-button>
            </div>
          </td>
        </tr>
        <tr>
          <th>Pools</th>
          <td>
            <div class="beat-details-pools-editor">
              <div
                v-for="(pool, poolIndex) in editForm.Pools"
                :key="`pool-edit-${poolIndex}`"
                class="beat-details-pools-editor-row-wrap"
              >
                <div class="beat-details-pools-editor-row">
                  <input
                    v-model="pool.Sequence"
                    :class="['beat-details-input', { 'beat-details-input-invalid': isPoolFieldInvalid(poolIndex, 'Sequence') }]"
                    placeholder="Seq"
                  />
                  <input
                    v-model="pool.Name"
                    class="beat-details-input"
                    placeholder="Name"
                  />
                  <input
                    v-model="pool.Location"
                    :class="['beat-details-input', { 'beat-details-input-invalid': isPoolFieldInvalid(poolIndex, 'Location') }]"
                    placeholder="What3Words (///word.word.word)"
                  />
                  <input
                    v-model="pool.Latitude"
                    :class="['beat-details-input', { 'beat-details-input-invalid': isPoolFieldInvalid(poolIndex, 'Latitude') }]"
                    placeholder="Latitude"
                  />
                  <input
                    v-model="pool.Longitude"
                    :class="['beat-details-input', { 'beat-details-input-invalid': isPoolFieldInvalid(poolIndex, 'Longitude') }]"
                    placeholder="Longitude"
                  />
                  <input
                    v-model="pool.Description"
                    class="beat-details-input"
                    placeholder="Description"
                  />
                  <app-button
                    type="button"
                    class="beat-details-pool-remove"
                    inherit-style
                    @click="removePoolRow(poolIndex)"
                  >
                    Remove
                  </app-button>
                </div>
                <p
                  v-if="poolValidationErrors[poolIndex]"
                  class="beat-details-pool-validation"
                >
                  {{ poolValidationErrors[poolIndex] }}
                </p>
              </div>

              <app-button type="button" inherit-style @click="addPoolRow">Add Pool</app-button>
            </div>
          </td>
        </tr>
        <tr>
          <th>Waypoints</th>
          <td>
            <div class="beat-details-waypoints-editor">
              <div
                v-for="(waypoint, waypointIndex) in editForm.Waypoints"
                :key="`waypoint-edit-${waypointIndex}`"
                class="beat-details-waypoints-editor-row-wrap"
              >
                <div class="beat-details-waypoints-editor-row">
                  <input
                    v-model="waypoint.Sequence"
                    class="beat-details-input beat-details-input-narrow"
                    placeholder="Seq"
                    readonly
                  />
                  <input
                    v-model="waypoint.W3W"
                    class="beat-details-input"
                    placeholder="What3Words (optional)"
                  />
                  <input
                    v-model="waypoint.Latitude"
                    class="beat-details-input"
                    placeholder="Latitude"
                  />
                  <input
                    v-model="waypoint.Longitude"
                    class="beat-details-input"
                    placeholder="Longitude"
                  />
                  <input
                    v-model="waypoint.Description"
                    class="beat-details-input"
                    placeholder="Description (optional)"
                  />
                  <app-button
                    type="button"
                    class="beat-details-waypoint-remove"
                    inherit-style
                    @click="removeWaypointRow(waypointIndex)"
                  >
                    Remove
                  </app-button>
                </div>
              </div>

              <div class="beat-details-waypoints-actions">
                <app-button type="button" inherit-style @click="addWaypointRow">Add Waypoint</app-button>
                <label class="beat-details-gpx-label">
                  Import GPX
                  <input
                    type="file"
                    accept=".gpx,application/gpx+xml"
                    class="beat-details-gpx-input"
                    @change="importGpxFile"
                  />
                </label>
              </div>
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <table v-else-if="selectedBeat" class="beat-details-table beat-details-table-readonly">
      <tbody>
        <tr v-for="(row, rowIndex) in detailCompactRows" :key="`detail-row-${rowIndex}`">
          <th>{{ row.left.label }}</th>
          <td>
            <template v-if="row.left.key === 'Beat_Upstream'">
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
            <template v-else-if="row.left.key === 'Beat_Downstream'">
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
            <template v-else-if="row.left.key === 'Beat_Upstream_Coords' || row.left.key === 'Beat_Downstream_Coords'">
              <a
                v-if="getCoordsPair(row.left.key)"
                :href="googleMapsUrl(getCoordsPair(row.left.key).lat, getCoordsPair(row.left.key).lng)"
                rel="noopener noreferrer"
                @click.prevent="openGoogleMapsWindow(getCoordsPair(row.left.key).lat, getCoordsPair(row.left.key).lng)"
              >
                {{ getCoordsDisplayValue(row.left.key) }}
              </a>
              <span v-else>-</span>
            </template>
            <template v-else>
              {{ selectedBeat[row.left.key] || '-' }}
            </template>
          </td>

          <template v-if="row.right">
            <th>{{ row.right.label }}</th>
            <td>
              <template v-if="row.right.key === 'Beat_Upstream'">
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
              <template v-else-if="row.right.key === 'Beat_Downstream'">
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
              <template v-else-if="row.right.key === 'Beat_Upstream_Coords' || row.right.key === 'Beat_Downstream_Coords'">
                <a
                  v-if="getCoordsPair(row.right.key)"
                  :href="googleMapsUrl(getCoordsPair(row.right.key).lat, getCoordsPair(row.right.key).lng)"
                  rel="noopener noreferrer"
                  @click.prevent="openGoogleMapsWindow(getCoordsPair(row.right.key).lat, getCoordsPair(row.right.key).lng)"
                >
                  {{ getCoordsDisplayValue(row.right.key) }}
                </a>
                <span v-else>-</span>
              </template>
              <template v-else>
                {{ selectedBeat[row.right.key] || '-' }}
              </template>
            </td>
          </template>
          <template v-else>
            <th class="beat-details-empty-cell"></th>
            <td class="beat-details-empty-cell"></td>
          </template>
        </tr>

        <tr v-for="column in detailWideColumns" :key="`detail-wide-${column.key}`">
          <th>{{ column.label }}</th>
          <td colspan="3">
            <template v-if="column.key === 'Parking_Locations'">
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
            <template v-else-if="column.key === 'Pools'">
              <ul v-if="selectedBeat.Pools.length" class="beat-details-pools-list">
                <li
                  v-for="(pool, poolIndex) in selectedBeat.Pools"
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
import axios from 'axios';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-rotate/dist/leaflet-rotate.js';
import { store, clubDetails, API_BASE_URL, loadClubs } from '../store.js';
import AppButton from './ui/AppButton.vue';

export default {
  name: 'BeatDetails',
  components: {
    AppButton,
  },
  data() {
    return {
      localBeats: [],
      selectedBeatKey: '',
      fieldOrder: {},
      beatDetailsMapInstance: null,
      beatDetailsMapLayers: [],
      beatDetailsMapStatus: '',
      beatDetailsMapRequestId: 0,
      currentBeatDetailsBearing: 0,
      isEditing: false,
      isAddingNewBeat: false,
      isSaving: false,
      beatEditError: '',
      beatEditSuccess: '',
      editOriginalBeatKey: '',
      editForm: {
        Beat_ID: '',
        Beat_Name: '',
        River: '',
        Position: '',
        Beat_Upstream: '',
        Beat_Downstream: '',
        Beat_Upstream_Latitude: '',
        Beat_Upstream_Longitude: '',
        Beat_Downstream_Latitude: '',
        Beat_Downstream_Longitude: '',
        Beat_Description: '',
        Detailed_Description: '',
        Parking_Locations: [],
        Pools: [],
        Waypoints: [],
      },
      beatDetailsWaypointMarkers: [],
      beatDetailsWaypointsCount: 0,
      showWaypointMarkers: false,
    };
  },
  computed: {
    clubFullName: () => clubDetails.value.fullName,
    canManageBeats: () => store.memberRoles.includes('club_admin'),
    parkingValidationErrors() {
      if (!this.isEditing || !Array.isArray(this.editForm.Parking_Locations)) {
        return [];
      }
      return this.editForm.Parking_Locations.map(location => this.getParkingValidationError(location));
    },
    hasParkingValidationErrors() {
      return this.parkingValidationErrors.some(Boolean);
    },
    poolValidationErrors() {
      if (!this.isEditing || !Array.isArray(this.editForm.Pools)) {
        return [];
      }
      return this.editForm.Pools.map(pool => this.getPoolValidationError(pool));
    },
    hasPoolValidationErrors() {
      return this.poolValidationErrors.some(Boolean);
    },
    hasLocationValidationErrors() {
      return this.hasParkingValidationErrors || this.hasPoolValidationErrors;
    },
    detailLabelMap() {
      const defaultLabels = {
        Beat_ID: 'Beat ID',
        Beat_Name: 'Beat Name',
        River: 'River',
        Position: 'Position',
        Beat_Upstream: 'Beat Upstream',
        Beat_Downstream: 'Beat Downstream',
        Beat_Upstream_Coords: 'Upstream Co-ords',
        Beat_Downstream_Coords: 'Downstream Co-ords',
        Beat_Description: 'Beat Description',
        Detailed_Description: 'Detailed Description',
        Parking_Locations: 'Parking',
        Pools: 'Pools',
      };

      const configured = this.fieldOrder?.display_names?.beat_details;
      if (!configured || typeof configured !== 'object') return defaultLabels;

      const merged = { ...defaultLabels };
      Object.keys(defaultLabels).forEach(key => {
        const custom = configured[key];
        if (typeof custom === 'string' && custom.trim()) {
          merged[key] = custom.trim();
        }
      });
      return merged;
    },
    detailCompactRows() {
      const compactKeys = [
        'Beat_ID',
        'Beat_Name',
        'River',
        'Position',
        'Beat_Upstream',
        'Beat_Downstream',
        'Beat_Upstream_Coords',
        'Beat_Downstream_Coords',
      ];

      const visible = compactKeys
        .filter(key => this.isColumnVisible('beat_details', key))
        .map(key => ({ key, label: this.detailLabelMap[key] || key }));

      const rows = [];
      for (let i = 0; i < visible.length; i += 2) {
        rows.push({
          left: visible[i],
          right: visible[i + 1] || null,
        });
      }
      return rows;
    },
    detailWideColumns() {
      const wideKeys = ['Beat_Description', 'Detailed_Description', 'Parking_Locations', 'Pools'];
      return wideKeys
        .filter(key => this.isColumnVisible('beat_details', key))
        .map(key => ({ key, label: this.detailLabelMap[key] || key }));
    },
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
        Pools: { key: 'Pools', label: 'Pools' },
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
        'Pools',
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
      const beats = Array.isArray(this.localBeats) ? this.localBeats : [];
      const mappedBeats = beats.map(beat => {
        const beatUpstream = beat && beat.Beat_Upstream ? beat.Beat_Upstream : '';
        const beatDownstream = beat && beat.Beat_Downstream ? beat.Beat_Downstream : '';
        return {
          id: beat && beat.id ? beat.id : null,
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
          Waypoints: this.parseWaypointsInput(beat && beat.Waypoints),
          Beat_Description: beat && beat.Beat_Description ? beat.Beat_Description : '',
          Detailed_Description: beat && beat.Detailed_Description ? beat.Detailed_Description : '',
        };
      });
      return mappedBeats.sort((leftBeat, rightBeat) => {
        const leftLabel = this.formatBeatOptionLabel(leftBeat).toLowerCase();
        const rightLabel = this.formatBeatOptionLabel(rightBeat).toLowerCase();
        if (leftLabel < rightLabel) return -1;
        if (leftLabel > rightLabel) return 1;
        return 0;
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
    clubDetails: {
      deep: true,
      handler() {
        if (!this.isEditing) {
          this.syncLocalBeats();
        }
      },
    },
  },
  created() {
    this.syncLocalBeats();
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
    syncLocalBeats() {
      const beats = Array.isArray(clubDetails.value.beats) ? clubDetails.value.beats : [];
      this.localBeats = beats.map(beat => this.normalizeBeatRecord(beat));
      if (!this.localBeats.length) {
        this.selectedBeatKey = '';
        return;
      }
      const selectedExists = this.localBeats.some(beat => this.beatKey(beat) === this.selectedBeatKey);
      if (!selectedExists) {
        this.selectedBeatKey = this.beatKey(this.localBeats[0]);
      }
    },
    normalizeBeatRecord(beat) {
      return {
        Beat_Name: String(beat?.Beat_Name || '').trim(),
        Beat_ID: String(beat?.Beat_ID || '').trim(),
        River: String(beat?.River || '').trim(),
        Position: String(beat?.Position || '').trim(),
        Beat_Upstream: String(beat?.Beat_Upstream || '').trim(),
        Beat_Downstream: String(beat?.Beat_Downstream || '').trim(),
        Beat_Upstream_Latitude: String(beat?.Beat_Upstream_Latitude || '').trim(),
        Beat_Upstream_Longitude: String(beat?.Beat_Upstream_Longitude || '').trim(),
        Beat_Downstream_Latitude: String(beat?.Beat_Downstream_Latitude || '').trim(),
        Beat_Downstream_Longitude: String(beat?.Beat_Downstream_Longitude || '').trim(),
        Beat_Description: String(beat?.Beat_Description || '').trim(),
        Detailed_Description: String(beat?.Detailed_Description || '').trim(),
        Parking_Locations: Array.isArray(beat?.Parking_Locations)
          ? beat.Parking_Locations
              .filter(loc => loc && typeof loc === 'object')
              .map(loc => ({
                Name: String(loc?.Name || '').trim(),
                Location: String(loc?.Location || '').trim(),
                Description: String(loc?.Description || '').trim(),
                Latitude: String(loc?.Latitude || '').trim(),
                Longitude: String(loc?.Longitude || '').trim(),
              }))
          : [],
        Pools: this.parsePoolsInput(beat?.Pools),
        Waypoints: this.parseWaypointsInput(beat?.Waypoints),
      };
    },
    beginEditForBeat(beat, isAdding = false) {
      this.destroyBeatDetailsMap();
      const source = this.normalizeBeatRecord(beat);
      this.isAddingNewBeat = isAdding;
      this.editOriginalBeatKey = this.beatKey(source);
      this.editForm = {
        Beat_ID: source.Beat_ID,
        Beat_Name: source.Beat_Name,
        River: source.River,
        Position: source.Position,
        Beat_Upstream: source.Beat_Upstream,
        Beat_Downstream: source.Beat_Downstream,
        Beat_Upstream_Latitude: source.Beat_Upstream_Latitude,
        Beat_Upstream_Longitude: source.Beat_Upstream_Longitude,
        Beat_Downstream_Latitude: source.Beat_Downstream_Latitude,
        Beat_Downstream_Longitude: source.Beat_Downstream_Longitude,
        Beat_Description: source.Beat_Description,
        Detailed_Description: source.Detailed_Description,
        Parking_Locations: this.cloneParkingLocations(source.Parking_Locations),
        Pools: this.clonePools(source.Pools),
        Waypoints: this.cloneWaypoints(source.Waypoints),
      };
      this.isEditing = true;
    },
    cloneParkingLocations(parkingLocations) {
      if (!Array.isArray(parkingLocations)) return [];
      return parkingLocations
        .filter(loc => loc && typeof loc === 'object')
        .map(loc => ({
          Name: String(loc?.Name || '').trim(),
          Location: String(loc?.Location || '').trim(),
          Description: String(loc?.Description || '').trim(),
          Latitude: String(loc?.Latitude || '').trim(),
          Longitude: String(loc?.Longitude || '').trim(),
        }));
    },
    addParkingLocationRow() {
      if (!this.isEditing) return;
      this.editForm.Parking_Locations = [
        ...this.editForm.Parking_Locations,
        {
          Name: '',
          Location: '',
          Description: '',
          Latitude: '',
          Longitude: '',
        },
      ];
    },
    removeParkingLocationRow(index) {
      if (!this.isEditing) return;
      this.editForm.Parking_Locations = this.editForm.Parking_Locations.filter((_, i) => i !== index);
    },
    clonePools(pools) {
      if (!Array.isArray(pools)) return [];
      return pools
        .filter(pool => pool && typeof pool === 'object')
        .map(pool => ({
          Sequence: String(pool?.Sequence || '').trim(),
          Name: String(pool?.Name || '').trim(),
          Location: String(pool?.Location || '').trim(),
          Description: String(pool?.Description || '').trim(),
          Latitude: String(pool?.Latitude || '').trim(),
          Longitude: String(pool?.Longitude || '').trim(),
        }));
    },
    addPoolRow() {
      if (!this.isEditing) return;
      const nextSequence = this.editForm.Pools.length + 1;
      this.editForm.Pools = [
        ...this.editForm.Pools,
        {
          Sequence: String(nextSequence),
          Name: '',
          Location: '',
          Description: '',
          Latitude: '',
          Longitude: '',
        },
      ];
    },
    removePoolRow(index) {
      if (!this.isEditing) return;
      this.editForm.Pools = this.editForm.Pools.filter((_, i) => i !== index);
    },
    cloneWaypoints(waypoints) {
      if (!Array.isArray(waypoints)) return [];
      return waypoints
        .filter(wp => wp && typeof wp === 'object')
        .map(wp => ({
          Sequence: String(wp?.Sequence || '').trim(),
          W3W: String(wp?.W3W || '').trim(),
          Latitude: String(wp?.Latitude || '').trim(),
          Longitude: String(wp?.Longitude || '').trim(),
          Description: String(wp?.Description || '').trim(),
        }));
    },
    addWaypointRow() {
      if (!this.isEditing) return;
      const nextSequence = this.editForm.Waypoints.length + 1;
      this.editForm.Waypoints = [
        ...this.editForm.Waypoints,
        { Sequence: String(nextSequence), W3W: '', Latitude: '', Longitude: '', Description: '' },
      ];
    },
    removeWaypointRow(index) {
      if (!this.isEditing) return;
      this.editForm.Waypoints = this.editForm.Waypoints
        .filter((_, i) => i !== index)
        .map((wp, i) => ({ ...wp, Sequence: String(i + 1) }));
    },
    parseWaypointsInput(rawWaypoints) {
      const parsed = Array.isArray(rawWaypoints) ? rawWaypoints : [];
      return parsed
        .filter(wp => wp && typeof wp === 'object')
        .filter(wp => {
          const lat = String(wp?.Latitude || '').trim();
          const lng = String(wp?.Longitude || '').trim();
          const w3w = String(wp?.W3W || '').trim();
          return (lat && lng) || w3w;
        })
        .map((wp, index) => {
          const sequenceNumber = Number.parseInt(String(wp?.Sequence || ''), 10);
          return {
            Sequence: Number.isFinite(sequenceNumber) && sequenceNumber > 0
              ? String(sequenceNumber)
              : String(index + 1),
            W3W: String(wp?.W3W || '').trim(),
            Latitude: String(wp?.Latitude || '').trim(),
            Longitude: String(wp?.Longitude || '').trim(),
            Description: String(wp?.Description || '').trim(),
          };
        })
        .sort((a, b) => Number.parseInt(a.Sequence, 10) - Number.parseInt(b.Sequence, 10))
        .map((wp, index) => ({ ...wp, Sequence: String(index + 1) }));
    },
    importGpxFile(event) {
      const file = event.target.files && event.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (loadEvent) => {
        try {
          const parser = new DOMParser();
          const gpxDoc = parser.parseFromString(loadEvent.target.result, 'application/xml');
          if (gpxDoc.querySelector('parsererror')) {
            this.beatEditError = 'GPX file could not be parsed. Please check the file format.';
            event.target.value = '';
            return;
          }
          // Prefer track points; fall back to route points
          const trkPoints = Array.from(gpxDoc.querySelectorAll('trkpt'));
          const rtePoints = Array.from(gpxDoc.querySelectorAll('rtept'));
          const gpxPoints = trkPoints.length > 0 ? trkPoints : rtePoints;
          if (!gpxPoints.length) {
            this.beatEditError = 'No track or route points found in the GPX file.';
            event.target.value = '';
            return;
          }
          const imported = gpxPoints
            .map((pt, index) => {
              const lat = pt.getAttribute('lat');
              const lon = pt.getAttribute('lon');
              if (!lat || !lon) return null;
              const descEl = pt.querySelector('desc');
              const nameEl = pt.querySelector('name');
              const description = (descEl && descEl.textContent.trim()) ||
                                  (nameEl && nameEl.textContent.trim()) || '';
              return { Sequence: String(index + 1), W3W: '', Latitude: lat, Longitude: lon, Description: description };
            })
            .filter(Boolean);
          if (!imported.length) {
            this.beatEditError = 'No valid lat/lon points found in the GPX file.';
            event.target.value = '';
            return;
          }
          this.editForm.Waypoints = imported;
          this.beatEditError = '';
        } catch {
          this.beatEditError = 'Failed to read GPX file.';
        }
        event.target.value = '';
      };
      reader.readAsText(file);
    },
    getParkingValidationError(location) {
      const w3wValue = String(location?.Location || '').trim();
      const latitudeValue = String(location?.Latitude || '').trim();
      const longitudeValue = String(location?.Longitude || '').trim();

      const errors = [];

      if (w3wValue && !this.isValidWhat3WordsValue(w3wValue)) {
        errors.push('What3Words must be in format ///word.word.word');
      }

      if (latitudeValue && !this.isValidLatitudeValue(latitudeValue)) {
        errors.push('Latitude must be a number between -90 and 90');
      }

      if (longitudeValue && !this.isValidLongitudeValue(longitudeValue)) {
        errors.push('Longitude must be a number between -180 and 180');
      }

      if ((latitudeValue && !longitudeValue) || (!latitudeValue && longitudeValue)) {
        errors.push('Latitude and Longitude must both be provided together');
      }

      return errors.join(' · ');
    },
    getPoolValidationError(pool) {
      const sequenceValue = String(pool?.Sequence || '').trim();
      const sequenceNumber = Number.parseInt(sequenceValue, 10);
      const errors = [];

      if (!sequenceValue || !Number.isFinite(sequenceNumber) || sequenceNumber < 1) {
        errors.push('Sequence must be a whole number starting at 1');
      }

      const locationError = this.getParkingValidationError({
        Location: pool?.Location,
        Latitude: pool?.Latitude,
        Longitude: pool?.Longitude,
      });
      if (locationError) errors.push(locationError);

      return errors.join(' · ');
    },
    isParkingFieldInvalid(parkingIndex, fieldName) {
      const location = this.editForm?.Parking_Locations?.[parkingIndex] || {};
      const w3wValue = String(location?.Location || '').trim();
      const latitudeValue = String(location?.Latitude || '').trim();
      const longitudeValue = String(location?.Longitude || '').trim();

      if (fieldName === 'Location') {
        return Boolean(w3wValue) && !this.isValidWhat3WordsValue(w3wValue);
      }

      const hasCoordinatePairMismatch =
        (Boolean(latitudeValue) && !Boolean(longitudeValue)) ||
        (!Boolean(latitudeValue) && Boolean(longitudeValue));

      if (fieldName === 'Latitude') {
        return (Boolean(latitudeValue) && !this.isValidLatitudeValue(latitudeValue)) || hasCoordinatePairMismatch;
      }

      if (fieldName === 'Longitude') {
        return (Boolean(longitudeValue) && !this.isValidLongitudeValue(longitudeValue)) || hasCoordinatePairMismatch;
      }

      return false;
    },
    isPoolFieldInvalid(poolIndex, fieldName) {
      const pool = this.editForm?.Pools?.[poolIndex] || {};
      const sequenceValue = String(pool?.Sequence || '').trim();
      const sequenceNumber = Number.parseInt(sequenceValue, 10);

      if (fieldName === 'Sequence') {
        return !sequenceValue || !Number.isFinite(sequenceNumber) || sequenceNumber < 1;
      }

      return this.isParkingFieldInvalidLike(pool, fieldName);
    },
    isParkingFieldInvalidLike(location, fieldName) {
      const w3wValue = String(location?.Location || '').trim();
      const latitudeValue = String(location?.Latitude || '').trim();
      const longitudeValue = String(location?.Longitude || '').trim();

      if (fieldName === 'Location') {
        return Boolean(w3wValue) && !this.isValidWhat3WordsValue(w3wValue);
      }

      const hasCoordinatePairMismatch =
        (Boolean(latitudeValue) && !Boolean(longitudeValue)) ||
        (!Boolean(latitudeValue) && Boolean(longitudeValue));

      if (fieldName === 'Latitude') {
        return (Boolean(latitudeValue) && !this.isValidLatitudeValue(latitudeValue)) || hasCoordinatePairMismatch;
      }

      if (fieldName === 'Longitude') {
        return (Boolean(longitudeValue) && !this.isValidLongitudeValue(longitudeValue)) || hasCoordinatePairMismatch;
      }

      return false;
    },
    isValidWhat3WordsValue(rawValue) {
      const trimmed = String(rawValue || '').trim();
      if (!trimmed) return true;
      const withoutSlashes = trimmed.replace(/^\/+/, '');
      const words = withoutSlashes
        .split('.')
        .map(word => word.trim())
        .filter(Boolean);
      return words.length === 3 && words.every(word => /^[A-Za-z]+$/.test(word));
    },
    isValidLatitudeValue(rawValue) {
      const value = Number.parseFloat(String(rawValue || '').trim());
      return Number.isFinite(value) && value >= -90 && value <= 90;
    },
    isValidLongitudeValue(rawValue) {
      const value = Number.parseFloat(String(rawValue || '').trim());
      return Number.isFinite(value) && value >= -180 && value <= 180;
    },
    startEditBeat() {
      this.beatEditError = '';
      this.beatEditSuccess = '';
      if (!this.selectedBeat) return;
      this.beginEditForBeat(this.selectedBeat, false);
    },
    addNewBeat() {
      this.beatEditError = '';
      this.beatEditSuccess = '';
      if (this.isEditing) {
        this.beatEditError = 'Save or cancel current edit first.';
        return;
      }
      const newBeat = this.normalizeBeatRecord({
        Beat_ID: `NEW-${Date.now()}`,
        Beat_Name: 'New Beat',
        River: '',
        Position: '',
        Beat_Upstream: '',
        Beat_Downstream: '',
        Beat_Upstream_Latitude: '',
        Beat_Upstream_Longitude: '',
        Beat_Downstream_Latitude: '',
        Beat_Downstream_Longitude: '',
        Beat_Description: '',
        Detailed_Description: '',
        Parking_Locations: [],
        Pools: [],
        Waypoints: [],
      });
      this.localBeats = [...this.localBeats, newBeat];
      this.selectedBeatKey = this.beatKey(newBeat);
      this.beginEditForBeat(newBeat, true);
    },
    cancelEditBeat() {
      if (this.isAddingNewBeat) {
        this.localBeats = this.localBeats.filter(beat => this.beatKey(beat) !== this.editOriginalBeatKey);
        this.selectedBeatKey = this.localBeats.length ? this.beatKey(this.localBeats[0]) : '';
      }
      this.isEditing = false;
      this.isAddingNewBeat = false;
      this.editOriginalBeatKey = '';
      this.beatEditError = '';
    },
    parseParkingLocationsInput(rawParkingLocations) {
      const parsed = Array.isArray(rawParkingLocations)
        ? rawParkingLocations
        : [];

      return parsed
        .filter(loc => loc && typeof loc === 'object')
        .map(loc => ({
          Name: String(loc?.Name || '').trim(),
          Location: String(loc?.Location || '').trim(),
          Description: String(loc?.Description || '').trim(),
          Latitude: String(loc?.Latitude || '').trim(),
          Longitude: String(loc?.Longitude || '').trim(),
        }));
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
    buildBeatFromEditForm() {
      return this.normalizeBeatRecord({
        Beat_ID: this.editForm.Beat_ID,
        Beat_Name: this.editForm.Beat_Name,
        River: this.editForm.River,
        Position: this.editForm.Position,
        Beat_Upstream: this.editForm.Beat_Upstream,
        Beat_Downstream: this.editForm.Beat_Downstream,
        Beat_Upstream_Latitude: this.editForm.Beat_Upstream_Latitude,
        Beat_Upstream_Longitude: this.editForm.Beat_Upstream_Longitude,
        Beat_Downstream_Latitude: this.editForm.Beat_Downstream_Latitude,
        Beat_Downstream_Longitude: this.editForm.Beat_Downstream_Longitude,
        Beat_Description: this.editForm.Beat_Description,
        Detailed_Description: this.editForm.Detailed_Description,
        Parking_Locations: this.parseParkingLocationsInput(this.editForm.Parking_Locations),
        Pools: this.parsePoolsInput(this.editForm.Pools),
        Waypoints: this.parseWaypointsInput(this.editForm.Waypoints),
      });
    },
    persistBeats(updatedBeats, successMessage, selectedKeyAfterSave = '') {
      this.isSaving = true;
      this.beatEditError = '';
      this.beatEditSuccess = '';

      const payload = {
        fullName: clubDetails.value.fullName || '',
        description: clubDetails.value.description || '',
        websiteUrl: clubDetails.value.websiteUrl || '',
        adminEmail: clubDetails.value.adminEmail || '',
        logoUrl: clubDetails.value.logoUrl || '',
        beats: updatedBeats,
      };

      return axios
        .put(`${API_BASE_URL}/admin/clubs/${encodeURIComponent(clubDetails.value.shortName)}`, payload)
        .then(() => loadClubs())
        .then(() => {
          this.syncLocalBeats();
          if (selectedKeyAfterSave && this.localBeats.some(beat => this.beatKey(beat) === selectedKeyAfterSave)) {
            this.selectedBeatKey = selectedKeyAfterSave;
          } else if (!this.selectedBeatKey && this.localBeats.length) {
            this.selectedBeatKey = this.beatKey(this.localBeats[0]);
          }
          this.isEditing = false;
          this.isAddingNewBeat = false;
          this.editOriginalBeatKey = '';
          this.beatEditSuccess = successMessage;
        })
        .catch(error => {
          this.beatEditError = this.resolveBeatSaveErrorMessage(error);
        })
        .finally(() => {
          this.isSaving = false;
        });
    },
    resolveBeatSaveErrorMessage(error) {
      const statusCode = error?.response?.status;
      if (statusCode === 401) {
        return 'Session expired. Please log in again, then retry saving beat changes.';
      }
      if (statusCode === 403) {
        return 'You do not have permission to update beats for this club.';
      }

      const apiError = String(error?.response?.data?.error || '').trim();
      if (apiError) return apiError;

      if (store?.loginError && String(store.loginError).trim()) {
        return String(store.loginError).trim();
      }

      return 'Failed to update beats.';
    },
    saveBeatEdits() {
      if (!this.isEditing) return;

      if (this.hasLocationValidationErrors) {
        this.beatEditError = 'Fix parking/pool validation errors before saving.';
        return;
      }

      let updatedBeat;
      try {
        updatedBeat = this.buildBeatFromEditForm();
      } catch (error) {
        this.beatEditError = error?.message || 'Invalid beat data.';
        return;
      }

      const updatedBeats = [...this.localBeats];
      const targetIndex = updatedBeats.findIndex(beat => this.beatKey(beat) === this.editOriginalBeatKey);
      if (targetIndex < 0) {
        this.beatEditError = 'Could not find the selected beat to save.';
        return;
      }
      updatedBeats[targetIndex] = updatedBeat;
      const nextKey = this.beatKey(updatedBeat);

      this.persistBeats(updatedBeats, 'Beat details updated.', nextKey);
    },
    deleteSelectedBeat() {
      this.beatEditError = '';
      this.beatEditSuccess = '';
      if (!this.selectedBeat) return;
      if (!window.confirm(`Delete beat "${this.formatBeatOptionLabel(this.selectedBeat)}"?`)) {
        return;
      }

      const currentKey = this.beatKey(this.selectedBeat);
      const updatedBeats = this.localBeats.filter(beat => this.beatKey(beat) !== currentKey);
      const nextKey = updatedBeats.length ? this.beatKey(updatedBeats[0]) : '';
      this.persistBeats(updatedBeats, 'Beat deleted.', nextKey);
    },
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
      if (beatId && beatName) return `${beatId} - ${beatName}`;
      return beatId || beatName || 'Unnamed Beat';
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
    getCoordsPair(columnKey) {
      if (columnKey === 'Beat_Upstream_Coords') {
        const lat = this.selectedBeat?.Beat_Upstream_Latitude;
        const lng = this.selectedBeat?.Beat_Upstream_Longitude;
        if (lat && lng) return { lat, lng };
      }
      if (columnKey === 'Beat_Downstream_Coords') {
        const lat = this.selectedBeat?.Beat_Downstream_Latitude;
        const lng = this.selectedBeat?.Beat_Downstream_Longitude;
        if (lat && lng) return { lat, lng };
      }
      return null;
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
      }
    },
    getCoordsDisplayValue(columnKey) {
      if (columnKey === 'Beat_Upstream_Coords') {
        if (this.selectedBeat?.Beat_Upstream_Latitude && this.selectedBeat?.Beat_Upstream_Longitude) {
          return `${this.selectedBeat.Beat_Upstream_Latitude}, ${this.selectedBeat.Beat_Upstream_Longitude}`;
        }
        return '-';
      }

      if (columnKey === 'Beat_Downstream_Coords') {
        if (this.selectedBeat?.Beat_Downstream_Latitude && this.selectedBeat?.Beat_Downstream_Longitude) {
          return `${this.selectedBeat.Beat_Downstream_Latitude}, ${this.selectedBeat.Beat_Downstream_Longitude}`;
        }
        return '-';
      }

      return '-';
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
      if (!this.beatDetailsMapInstance) return;
      if (Array.isArray(this.beatDetailsMapLayers)) {
        this.beatDetailsMapLayers.forEach(layer => {
          if (layer && this.beatDetailsMapInstance.hasLayer(layer)) {
            this.beatDetailsMapInstance.removeLayer(layer);
          }
        });
        this.beatDetailsMapLayers = [];
      }
      if (Array.isArray(this.beatDetailsWaypointMarkers)) {
        this.beatDetailsWaypointMarkers.forEach(marker => {
          if (marker && this.beatDetailsMapInstance.hasLayer(marker)) {
            this.beatDetailsMapInstance.removeLayer(marker);
          }
        });
        this.beatDetailsWaypointMarkers = [];
      }
      this.beatDetailsWaypointsCount = 0;
    },
    ensureBeatDetailsMap() {
      if (this.beatDetailsMapInstance) return;
      const mapElement = this.$refs.beatDetailsMap;
      if (!mapElement) return;
      this.beatDetailsMapInstance = L.map(mapElement, {
        zoomControl: true,
        attributionControl: true,
        rotate: true,
        bearing: 0,
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
        if (locationW3W) {
          poolPopup += `<br><a href="${locationW3W.url}" target="what3words-map-window">${locationW3W.display}</a>`;
        }
        if (pool?.Description) poolPopup += `<br>${pool.Description}`;

        const poolMarker = L.marker(poolLatLng, {
          icon: L.divIcon({
            className: 'pool-pin-marker',
            html: `<div class="pool-pin-dot">${sequenceLabel}</div>`,
            iconSize: [22, 22],
            iconAnchor: [11, 11],
          }),
        }).bindPopup(poolPopup);

        poolMarker.addTo(this.beatDetailsMapInstance);
        poolMarkers.push(poolMarker);
      }

      // Build route polyline from ordered waypoints
      const sortedWaypoints = Array.isArray(selectedBeat.Waypoints)
        ? [...selectedBeat.Waypoints].sort((a, b) => Number.parseInt(a.Sequence, 10) - Number.parseInt(b.Sequence, 10))
        : [];
      const waypointMarkers = [];
      const routeLatLngs = [];
      for (let i = 0; i < sortedWaypoints.length; i += 1) {
        const wp = sortedWaypoints[i];
        const wpCoords = await this.resolveBeatPointCoordinates(wp?.W3W, wp?.Latitude, wp?.Longitude);
        if (requestId !== this.beatDetailsMapRequestId) return;
        if (!wpCoords) continue;
        const wpLatLng = L.latLng(wpCoords.lat, wpCoords.lng);
        routeLatLngs.push(wpLatLng);
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

      let routePolyline = null;
      if (routeLatLngs.length >= 2) {
        routePolyline = L.polyline(routeLatLngs, { color: '#1a6ea0', weight: 3 });
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
      if (routePolyline) routePolyline.addTo(this.beatDetailsMapInstance);
      if (this.showWaypointMarkers) {
        waypointMarkers.forEach(marker => marker.addTo(this.beatDetailsMapInstance));
      }
      this.beatDetailsWaypointMarkers = waypointMarkers;
      this.beatDetailsWaypointsCount = waypointMarkers.length;
      const routeLayers = routePolyline ? [routePolyline] : [];
      this.beatDetailsMapLayers = [upstreamMarker, downstreamMarker, ...routeLayers, ...poolMarkers, ...parkingLayers];

      this.beatDetailsMapInstance.invalidateSize();
      const bounds = L.latLngBounds(allBoundsPoints);
      this.beatDetailsMapInstance.fitBounds(bounds.pad(0.2), { maxZoom: 16 });
      
      // Load and apply saved map rotation for this beat
      if (selectedBeat && selectedBeat.id) {
        await this.loadAndApplyBeatRotation(selectedBeat.id);
      }

      const routeDesc = waypointMarkers.length > 0
        ? `route (${waypointMarkers.length} waypoint${waypointMarkers.length === 1 ? '' : 's'})`
        : null;
      const poolDesc = poolMarkers.length > 0
        ? `${poolMarkers.length} pool${poolMarkers.length === 1 ? '' : 's'}`
        : null;
      const parkingDesc = parkingLayers.length > 0
        ? `${parkingLayers.length} parking`
        : null;
      const parts = [routeDesc, poolDesc, parkingDesc].filter(Boolean);
      this.beatDetailsMapStatus = parts.length
        ? `Showing ${parts.join(', ')}.`
        : 'Showing upstream and downstream limits.';
    },
    toggleWaypointMarkers() {
      this.showWaypointMarkers = !this.showWaypointMarkers;
      if (!this.beatDetailsMapInstance) return;
      this.beatDetailsWaypointMarkers.forEach(marker => {
        if (this.showWaypointMarkers) {
          marker.addTo(this.beatDetailsMapInstance);
        } else {
          this.beatDetailsMapInstance.removeLayer(marker);
        }
      });
    },
    changeBeatDetailsRotation(angle) {
      if (!this.beatDetailsMapInstance) return;
      const newBearing = this.currentBeatDetailsBearing + angle;
      this.currentBeatDetailsBearing = newBearing % 360;
      this.beatDetailsMapInstance.setBearing(this.currentBeatDetailsBearing);
    },
    resetBeatDetailsNorth() {
      if (!this.beatDetailsMapInstance) return;
      this.currentBeatDetailsBearing = 0;
      this.beatDetailsMapInstance.setBearing(0);
    },
    async loadAndApplyBeatRotation(beatId) {
      if (!beatId || !this.beatDetailsMapInstance) return;
      try {
        const response = await axios.get(`${API_BASE_URL}/beat/${beatId}/map-rotation`);
        if (response.data && typeof response.data.rotation_bearing === 'number') {
          this.beatDetailsMapInstance.setBearing(response.data.rotation_bearing);
        }
      } catch (error) {
        if (this.beatDetailsMapInstance && this.beatDetailsMapInstance.setBearing) {
          this.beatDetailsMapInstance.setBearing(0);
        }
      }
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

.beat-details-actions-row {
  display: flex;
  gap: 8px;
  margin: 10px 0 12px;
}

.beat-details-error {
  color: #b42318;
  margin: 0 0 8px;
  font-weight: 600;
}

.beat-details-success {
  color: #21633a;
  margin: 0 0 8px;
  font-weight: 600;
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

.beat-details-quick-info-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 16px;
  background: #fff;
}

.beat-details-quick-info-table th,
.beat-details-quick-info-table td {
  border: 1px solid #ccc;
  padding: 8px;
  text-align: left;
  font-size: 10pt;
}

.beat-details-quick-info-table th {
  width: 20%;
  background: #f0f0f0;
  font-weight: 600;
}

.beat-details-quick-info-table td {
  width: 30%;
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

.beat-details-empty-cell {
  background: #fafafa;
}

.beat-details-input,
.beat-details-textarea {
  width: 100%;
  box-sizing: border-box;
}

.beat-details-input-invalid {
  border-color: #b42318;
}

.beat-details-parking-list {
  margin: 0;
  padding-left: 18px;
}

.beat-details-pools-list {
  margin: 0;
  padding-left: 18px;
}

.beat-details-parking-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.beat-details-parking-editor-row-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.beat-details-parking-editor-row {
  display: grid;
  grid-template-columns: 1fr 1fr 120px 120px 1fr auto;
  gap: 6px;
  align-items: center;
}

.beat-details-parking-remove {
  white-space: nowrap;
}

.beat-details-parking-validation {
  margin: 0;
  font-size: 9pt;
}

.beat-details-pools-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.beat-details-pools-editor-row-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.beat-details-pools-editor-row {
  display: grid;
  grid-template-columns: 70px 1fr 1fr 120px 120px 1fr auto;
  gap: 6px;
  align-items: center;
}

.beat-details-pool-remove {
  white-space: nowrap;
}

.beat-details-pool-validation {
  margin: 0;
  font-size: 9pt;
}

.beat-details-waypoints-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.beat-details-waypoints-editor-row-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.beat-details-waypoints-editor-row {
  display: grid;
  grid-template-columns: 46px 1fr 120px 120px 1fr auto;
  gap: 6px;
  align-items: center;
}

.beat-details-waypoint-remove {
  white-space: nowrap;
}

.beat-details-waypoints-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.beat-details-gpx-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 10px;
  border: 1px solid #aaa;
  border-radius: 4px;
  font-size: 10pt;
  background: #f5f5f5;
}

.beat-details-gpx-label:hover {
  background: #e8e8e8;
}

.beat-details-gpx-input {
  display: none;
}

.beat-details-input-narrow {
  max-width: 46px;
}

.beat-details-map-wrap {
  margin-top: 16px;
  position: relative;
}

.beat-details-map-controls {
  display: flex;
  gap: 8px;
  margin-top: 6px;
  margin-bottom: 2px;
}

.beat-details-waypoint-toggle {
  padding: 4px 10px;
  font-size: 10pt;
  background: #f0f4f8;
  border: 1px solid #aac;
  border-radius: 4px;
  cursor: pointer;
}

.beat-details-waypoint-toggle:hover {
  background: #dde8f5;
}

.rotation-controls {
  display: flex;
  gap: 4px;
}

.rotation-btn {
  padding: 4px 8px;
  font-size: 12pt;
  background: #f0f4f8;
  border: 1px solid #aac;
  border-radius: 4px;
  cursor: pointer;
  min-width: 32px;
  text-align: center;
}

.rotation-btn:hover {
  background: #dde8f5;
}

.rotation-btn.compass-reset {
  background: #ffffcc;
}

.rotation-btn.compass-reset:hover {
  background: #ffff99;
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

@media (max-width: 1000px) {
  .beat-details-table-readonly {
    width: 100%;
    table-layout: fixed;
  }

  .beat-details-table-readonly tbody tr {
    display: grid;
    grid-template-columns: minmax(120px, 36%) minmax(0, 1fr);
    width: 100%;
  }

  .beat-details-table-readonly th,
  .beat-details-table-readonly td {
    width: auto;
    min-width: 0;
    overflow-wrap: anywhere;
    word-break: break-word;
  }

  .beat-details-table-readonly .beat-details-empty-cell {
    display: none;
  }

  .beat-details-table-readonly td[colspan="3"] {
    grid-column: 2;
  }
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

:deep(.pool-pin-marker) {
  background: transparent;
  border: none;
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
</style>
