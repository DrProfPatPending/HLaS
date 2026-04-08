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
      <button type="button" @click="addNewBeat" :disabled="isSaving">Add</button>
      <button type="button" @click="startEditBeat" :disabled="isSaving || !selectedBeat || isEditing">Edit</button>
      <button type="button" @click="saveBeatEdits" :disabled="isSaving || !isEditing || hasParkingValidationErrors">{{ isSaving ? 'Saving...' : 'Save' }}</button>
      <button type="button" @click="cancelEditBeat" :disabled="isSaving || !isEditing">Cancel</button>
      <button type="button" @click="deleteSelectedBeat" :disabled="isSaving || !selectedBeat">Delete</button>
    </div>

    <p v-if="beatEditError" class="beat-details-error">{{ beatEditError }}</p>
    <p v-if="beatEditSuccess" class="beat-details-success">{{ beatEditSuccess }}</p>

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
                    class="beat-details-input"
                    placeholder="What3Words (///word.word.word)"
                  />
                  <input
                    v-model="parking.Latitude"
                    class="beat-details-input"
                    placeholder="Latitude"
                  />
                  <input
                    v-model="parking.Longitude"
                    class="beat-details-input"
                    placeholder="Longitude"
                  />
                  <input
                    v-model="parking.Description"
                    class="beat-details-input"
                    placeholder="Description"
                  />
                  <button
                    type="button"
                    class="beat-details-parking-remove"
                    @click="removeParkingLocationRow(parkingIndex)"
                  >
                    Remove
                  </button>
                </div>
                <p
                  v-if="parkingValidationErrors[parkingIndex]"
                  class="beat-details-parking-validation"
                >
                  {{ parkingValidationErrors[parkingIndex] }}
                </p>
              </div>

              <button type="button" @click="addParkingLocationRow">Add Parking Location</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <table v-else-if="selectedBeat" class="beat-details-table">
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
import { store, clubDetails, API_BASE_URL, loadClubs } from '../store.js';

export default {
  name: 'BeatDetails',
  data() {
    return {
      localBeats: [],
      selectedBeatKey: '',
      fieldOrder: {},
      beatDetailsMapInstance: null,
      beatDetailsMapLayers: [],
      beatDetailsMapStatus: '',
      beatDetailsMapRequestId: 0,
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
      },
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
      const beats = Array.isArray(this.localBeats) ? this.localBeats : [];
      const mappedBeats = beats.map(beat => {
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
      };
    },
    beginEditForBeat(beat, isAdding = false) {
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
          this.beatEditError = error?.response?.data?.error || 'Failed to update beats.';
        })
        .finally(() => {
          this.isSaving = false;
        });
    },
    saveBeatEdits() {
      if (!this.isEditing) return;

      if (this.hasParkingValidationErrors) {
        this.beatEditError = 'Fix parking validation errors before saving.';
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

.beat-details-input,
.beat-details-textarea {
  width: 100%;
  box-sizing: border-box;
}

.beat-details-parking-list {
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
