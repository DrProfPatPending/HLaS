<template>
  <div class="catch-return-container">
    <h2>Catch Return</h2>
    <p class="catch-return-intro">
      Record your fishing session quickly. Required fields are {{ fieldLabel('sessionDate') }}, {{ fieldLabel('beatId') }}, and catch counts.
    </p>

    <form class="catch-return-form" @submit.prevent="submitCatchReturn">
      <div class="catch-return-form-layout">
        <div class="catch-return-left-column">
          <label v-if="isFieldVisible('sessionDate')" class="catch-return-field">
            <span>{{ fieldLabel('sessionDate') }} *</span>
            <input v-model="form.sessionDate" type="date" required />
          </label>

          <label v-if="isFieldVisible('beatId')" class="catch-return-field">
            <span>{{ fieldLabel('beatId') }} *</span>
            <select v-model="form.beatId" required>
              <option value="">Select Beat</option>
              <option v-for="option in beatOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>

          <label v-for="field in visibleTextFields" :key="field.key" class="catch-return-field">
            <span>{{ field.label }}</span>
            <textarea
              v-model="form[field.key]"
              :rows="field.key === 'comments' ? 3 : 2"
              :maxlength="field.key === 'comments' ? commentsMaxLength : null"
              placeholder="Optional"
            ></textarea>
            <small v-if="field.key === 'comments'" class="catch-return-field-hint">
              {{ form.comments.length }} / {{ commentsMaxLength }}
            </small>
          </label>
        </div>

        <div v-if="filteredCountFields.length" class="catch-return-right-column">
          <label v-for="field in filteredCountFields" :key="field.key" class="catch-return-field">
            <span>{{ field.label }}</span>
            <input
              v-model.number="form[field.key]"
              type="number"
              min="0"
              step="1"
              inputmode="numeric"
            />
          </label>
        </div>
      </div>

      <div class="catch-return-actions">
        <app-button type="submit" inherit-style :disabled="submitting">
          {{ submitting ? 'Saving…' : 'Save Catch Return' }}
        </app-button>
      </div>
    </form>

    <p v-if="status" class="catch-return-status">{{ status }}</p>
    <p v-if="error" class="catch-return-error">{{ error }}</p>

    <section v-if="recentReturns.length" class="catch-return-analytics">
      <h3>My Catch Summary</h3>
      <div class="catch-return-analytics-grid">
        <div>
          <h4>By Beat</h4>
          <div class="catch-return-table-wrap">
            <table class="catch-return-table">
              <thead>
                <tr>
                  <th>Beat</th>
                  <th>Sessions</th>
                  <th v-for="column in summaryColumns" :key="column.key">{{ column.label }}</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in totalsByBeat" :key="row.beat">
                  <td>{{ row.beat }}</td>
                  <td>{{ row.sessions }}</td>
                  <td v-for="column in summaryColumns" :key="column.key">{{ row[column.key] }}</td>
                  <td class="analytics-total-cell">{{ row.total }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div>
          <h4>By Month</h4>
          <div class="catch-return-table-wrap">
            <table class="catch-return-table">
              <thead>
                <tr>
                  <th>Month</th>
                  <th>Sessions</th>
                  <th v-for="column in summaryColumns" :key="column.key">{{ column.label }}</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in totalsByMonth" :key="row.month">
                  <td>{{ formatMonth(row.month) }}</td>
                  <td>{{ row.sessions }}</td>
                  <td v-for="column in summaryColumns" :key="column.key">{{ row[column.key] }}</td>
                  <td class="analytics-total-cell">{{ row.total }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <section class="catch-return-history">
      <h3>My Recent Returns</h3>
      <p v-if="loadingReturns" class="catch-return-loading">Loading…</p>
      <p v-else-if="returnsError" class="catch-return-error">{{ returnsError }}</p>
      <template v-else>
        <p class="catch-return-debug">Debug: loaded {{ recentReturns.length }} return(s).</p>
        <p v-if="!recentReturns.length" class="catch-return-empty">No returns recorded yet.</p>
        <div v-else class="catch-return-table-wrap">
          <table class="catch-return-table">
            <thead>
              <tr>
                <th v-if="isFieldVisible('sessionDate')">{{ fieldLabel('sessionDate') }}</th>
                <th v-if="isFieldVisible('beatId')">{{ fieldLabel('beatId') }}</th>
                <th v-for="field in filteredCountFields" :key="field.key">{{ field.label }}</th>
                <th v-if="hasNotesColumn">Notes</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in recentReturns" :key="row.id">
                <td v-if="isFieldVisible('sessionDate')">{{ formatDateValue(row.session_date) }}</td>
                <td v-if="isFieldVisible('beatId')">{{ row.beat_id }}</td>
                <td v-for="field in filteredCountFields" :key="field.key">{{ row[field.column] }}</td>
                <td v-if="hasNotesColumn">{{ notesFor(row) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </section>
  </div>
</template>

<script>
import axios from 'axios';
import {
  clubDetails,
  store,
  API_BASE_URL,
  formatConfiguredDate,
  fieldOrderConfig,
  loadFieldOrderConfig,
} from '../store.js';
import AppButton from './ui/AppButton.vue';

// Labels, order and visibility come from the club's catch_return Field Order context.
const FIELD_ORDER_CONTEXT = 'catch_return';

const DEFAULT_LABELS = {
  sessionDate: 'Date',
  beatId: 'Beat ID',
  smallTrout: 'Small Trout',
  mediumTrout: 'Medium Trout',
  largeTrout: 'Large Trout',
  smallGrayling: 'Small Grayling',
  mediumGrayling: 'Medium Grayling',
  largeGrayling: 'Large Grayling',
  otherFish: 'Other Fish',
  weatherConditions: 'Weather Conditions',
  fliesUsed: 'Flies Used',
  predatorDamage: 'Predator Damage',
  comments: 'Comments',
};

const COUNT_FIELDS = [
  { key: 'smallTrout', column: 'small_trout' },
  { key: 'mediumTrout', column: 'medium_trout' },
  { key: 'largeTrout', column: 'large_trout' },
  { key: 'smallGrayling', column: 'small_grayling' },
  { key: 'mediumGrayling', column: 'medium_grayling' },
  { key: 'largeGrayling', column: 'large_grayling' },
  { key: 'otherFish', column: 'other_fish' },
];

// My Catch Summary columns: a species column is shown when any of its form fields is visible.
const SUMMARY_SPECIES = [
  { key: 'trout', label: 'Trout', fields: ['smallTrout', 'mediumTrout', 'largeTrout'] },
  { key: 'grayling', label: 'Grayling', fields: ['smallGrayling', 'mediumGrayling', 'largeGrayling'] },
  { key: 'other', label: 'Other Fish', fields: ['otherFish'] },
];

const TEXT_FIELD_KEYS = ['weatherConditions', 'fliesUsed', 'predatorDamage', 'comments'];

const DEFAULT_FIELD_ORDER = Object.keys(DEFAULT_LABELS);

const DEFAULT_FIELD_VISIBILITY = {
  sessionDate: true,
  beatId: true,
  smallTrout: true,
  mediumTrout: true,
  largeTrout: true,
  smallGrayling: true,
  mediumGrayling: true,
  largeGrayling: true,
  otherFish: true,
  fliesUsed: true,
  weatherConditions: true,
  predatorDamage: true,
  comments: true,
};

const COMMENTS_MAX_LENGTH = 500;

function defaultFieldVisibility() {
  return { ...DEFAULT_FIELD_VISIBILITY };
}

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

export default {
  name: 'CatchReturn',
  components: {
    AppButton,
  },
  data() {
    return {
      submitting: false,
      status: '',
      error: '',
      recentReturns: [],
      loadingReturns: false,
      returnsError: '',
      fieldVisibility: defaultFieldVisibility(),
      form: {
        sessionDate: todayIsoDate(),
        beatId: '',
        smallTrout: 0,
        mediumTrout: 0,
        largeTrout: 0,
        smallGrayling: 0,
        mediumGrayling: 0,
        largeGrayling: 0,
        otherFish: 0,
        fliesUsed: '',
        weatherConditions: '',
        predatorDamage: '',
        comments: '',
      },
    };
  },
  computed: {
    commentsMaxLength: () => COMMENTS_MAX_LENGTH,
    fieldOrderPositions() {
      const configured = fieldOrderConfig.order?.[FIELD_ORDER_CONTEXT];
      const order = Array.isArray(configured) && configured.length ? configured : DEFAULT_FIELD_ORDER;
      return Object.fromEntries(order.map((key, index) => [key, index]));
    },
    filteredCountFields() {
      return this.sortByFieldOrder(COUNT_FIELDS)
        .filter(field => this.isFieldVisible(field.key))
        .map(field => ({ ...field, label: this.fieldLabel(field.key) }));
    },
    visibleTextFields() {
      return this.sortByFieldOrder(TEXT_FIELD_KEYS.map(key => ({ key })))
        .filter(field => this.isFieldVisible(field.key))
        .map(field => ({ ...field, label: this.fieldLabel(field.key) }));
    },
    loggedInClub: () => store.loggedInClub,
    hasNotesColumn() {
      const notesFields = [
        this.isFieldVisible('fliesUsed') ? 'flies_used' : '',
        this.isFieldVisible('weatherConditions') ? 'weather_conditions' : '',
        this.isFieldVisible('predatorDamage') ? 'predator_damage' : '',
        this.isFieldVisible('comments') ? 'comments' : '',
      ].filter(Boolean);
      if (!notesFields.length) {
        return false;
      }
      return this.recentReturns.some(
        (row) => notesFields.some(fieldName => row[fieldName]),
      );
    },
    summaryColumns() {
      return SUMMARY_SPECIES.filter(species => species.fields.some(key => this.isFieldVisible(key)));
    },
    totalsByBeat() {
      return this.summariseReturns(row => row.beat_id || '(unknown)', 'beat')
        .sort((a, b) => b.total - a.total);
    },
    totalsByMonth() {
      return this.summariseReturns(row => String(row.session_date || '').slice(0, 7), 'month')
        .sort((a, b) => b.month.localeCompare(a.month));
    },
    beatOptions() {
      const beats = Array.isArray(clubDetails.value.beats) ? clubDetails.value.beats : [];
      return beats
        .map(beat => {
          const beatId = String(beat?.Beat_ID || '').trim();
          const beatName = String(beat?.Beat_Name || '').trim();
          const label = beatId && beatName
            ? `${beatId} - ${beatName}`
            : beatId || beatName;
          return { value: beatId, label };
        })
        .filter(option => option.value)
        .sort((leftOption, rightOption) => leftOption.label.localeCompare(rightOption.label));
    },
  },
  created() {
    if (!this.form.beatId && this.beatOptions.length) {
      this.form.beatId = this.beatOptions[0].value;
    }
    this.loadCatchReturnFieldVisibility();
    loadFieldOrderConfig(this.loggedInClub);
    this.loadRecentReturns();
  },
  methods: {
    normalizeFieldVisibility(rawVisibility) {
      const source = rawVisibility && typeof rawVisibility === 'object' ? rawVisibility : {};
      const normalized = defaultFieldVisibility();
      for (const key of Object.keys(DEFAULT_FIELD_VISIBILITY)) {
        if (Object.prototype.hasOwnProperty.call(source, key)) {
          normalized[key] = Boolean(source[key]);
        }
      }
      return normalized;
    },
    // Groups returns by groupKey; Total adds up only the species columns shown.
    summariseReturns(groupKeyOf, groupName) {
      const columnFor = Object.fromEntries(COUNT_FIELDS.map(field => [field.key, field.column]));
      const columns = this.summaryColumns;
      const map = {};
      for (const row of this.recentReturns) {
        const group = groupKeyOf(row);
        if (!group) continue;
        if (!map[group]) {
          map[group] = { [groupName]: group, sessions: 0, total: 0 };
          for (const column of columns) map[group][column.key] = 0;
        }
        map[group].sessions += 1;
        for (const column of columns) {
          const count = column.fields.reduce((sum, key) => sum + (Number(row[columnFor[key]]) || 0), 0);
          map[group][column.key] += count;
          map[group].total += count;
        }
      }
      return Object.values(map);
    },
    isFieldVisible(fieldKey) {
      const configured = fieldOrderConfig.order?.show_columns?.[FIELD_ORDER_CONTEXT];
      if (configured && typeof configured === 'object') {
        return configured[fieldKey] !== false;
      }
      // Clubs that haven't saved catch_return Field Order yet keep the older setting.
      return Boolean(this.fieldVisibility[fieldKey]);
    },
    fieldLabel(fieldKey) {
      const configured = fieldOrderConfig.order?.display_names?.[FIELD_ORDER_CONTEXT]?.[fieldKey];
      return typeof configured === 'string' && configured.trim() ? configured.trim() : DEFAULT_LABELS[fieldKey];
    },
    sortByFieldOrder(fields) {
      const positions = this.fieldOrderPositions;
      const position = key => (key in positions ? positions[key] : Number.MAX_SAFE_INTEGER);
      return [...fields].sort((a, b) => position(a.key) - position(b.key));
    },
    loadCatchReturnFieldVisibility() {
      return axios
        .get(`${API_BASE_URL}/club-settings`, {
          params: { club: this.loggedInClub },
        })
        .then((res) => {
          const visibility = res?.data?.settings?.catchReturnFieldVisibility;
          this.fieldVisibility = this.normalizeFieldVisibility(visibility);
        })
        .catch(() => {
          this.fieldVisibility = defaultFieldVisibility();
        });
    },
    normalizeCount(rawValue) {
      const parsed = Number.parseInt(rawValue, 10);
      return Number.isFinite(parsed) && parsed >= 0 ? parsed : 0;
    },
    submitCatchReturn() {
      this.status = '';
      this.error = '';

      if (!this.form.sessionDate) {
        this.error = 'Date is required.';
        return;
      }
      if (!this.form.beatId) {
        this.error = 'Beat ID is required.';
        return;
      }

      const payload = {
        club: this.loggedInClub,
        date: this.form.sessionDate,
        beat_id: this.form.beatId,
        small_trout: this.normalizeCount(this.form.smallTrout),
        medium_trout: this.normalizeCount(this.form.mediumTrout),
        large_trout: this.normalizeCount(this.form.largeTrout),
        small_grayling: this.normalizeCount(this.form.smallGrayling),
        medium_grayling: this.normalizeCount(this.form.mediumGrayling),
        large_grayling: this.normalizeCount(this.form.largeGrayling),
        other_fish: this.normalizeCount(this.form.otherFish),
        flies_used: String(this.form.fliesUsed || '').trim(),
        weather_conditions: String(this.form.weatherConditions || '').trim(),
        predator_damage: String(this.form.predatorDamage || '').trim(),
        comments: String(this.form.comments || '').trim(),
      };

      this.submitting = true;
      axios
        .post(`${API_BASE_URL}/catch-returns`, payload)
        .then(() => {
          this.status = 'Catch return saved.';
          this.form.smallTrout = 0;
          this.form.mediumTrout = 0;
          this.form.largeTrout = 0;
          this.form.smallGrayling = 0;
          this.form.mediumGrayling = 0;
          this.form.largeGrayling = 0;
          this.form.otherFish = 0;
          this.form.fliesUsed = '';
          this.form.weatherConditions = '';
          this.form.predatorDamage = '';
          this.form.comments = '';
          this.loadRecentReturns();
        })
        .catch(err => {
          this.error = err?.response?.data?.error || 'Failed to save catch return.';
        })
        .finally(() => {
          this.submitting = false;
        });
    },
    loadRecentReturns() {
      this.loadingReturns = true;
      this.returnsError = '';
      axios
        .get(`${API_BASE_URL}/catch-returns/mine`, {
          params: { club: this.loggedInClub, limit: 200 },
        })
        .then(resp => {
          if (Array.isArray(resp?.data?.returns)) {
            this.recentReturns = resp.data.returns;
            return;
          }
          this.recentReturns = Array.isArray(resp?.data) ? resp.data : [];
        })
        .catch(err => {
          this.returnsError = err?.response?.data?.error || 'Failed to load recent returns.';
        })
        .finally(() => {
          this.loadingReturns = false;
        });
    },
    notesFor(row) {
      return [
        this.isFieldVisible('fliesUsed') ? row.flies_used : '',
        this.isFieldVisible('weatherConditions') ? row.weather_conditions : '',
        this.isFieldVisible('predatorDamage') ? row.predator_damage : '',
        this.isFieldVisible('comments') ? row.comments : '',
      ]
        .filter(Boolean)
        .join(' | ');
    },
    formatDateValue(value) {
      const formatted = formatConfiguredDate(value, 'Date');
      return formatted || value || '';
    },
    formatMonth(ym) {
      if (!ym) return ym;
      const [year, month] = ym.split('-');
      return new Date(Number(year), Number(month) - 1, 1)
        .toLocaleString('default', { month: 'long', year: 'numeric' });
    },
  },
};
</script>

<style scoped>
.catch-return-container {
  width: 100%;
}

.catch-return-intro {
  margin: 0 0 12px;
  font-size: 10pt;
  color: #475569;
}

.catch-return-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.catch-return-form-layout {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.catch-return-left-column,
.catch-return-right-column {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.catch-return-field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.catch-return-field span {
  font-size: 9.5pt;
  font-weight: 600;
  color: #1f2937;
}

.catch-return-field-hint {
  align-self: flex-end;
  font-size: 7.5pt;
  color: #6b7280;
}

.catch-return-field input,
.catch-return-field select,
.catch-return-field textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 8px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
  margin-right: 0;
}

.catch-return-field textarea {
  resize: vertical;
}

.catch-return-actions {
  margin-top: 4px;
}

.catch-return-status {
  margin-top: 10px;
  color: #166534;
  font-size: 10pt;
  font-weight: 600;
}

.catch-return-error {
  margin-top: 10px;
  color: #b91c1c;
  font-size: 10pt;
  font-weight: 600;
}

.catch-return-history {
  margin-top: 28px;
}

.catch-return-history h3 {
  margin: 0 0 10px;
  font-size: 12pt;
  font-weight: 700;
  color: #17324d;
}

.catch-return-table-wrap {
  overflow-x: auto;
}

.catch-return-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 9pt;
  font-family: Helvetica, Arial, sans-serif;
}

.catch-return-table th,
.catch-return-table td {
  border: 1px solid #e2e8f0;
  padding: 6px 8px;
  text-align: left;
  white-space: nowrap;
}

.catch-return-table th {
  background: #f1f5f9;
  font-weight: 700;
  color: #334155;
}

.catch-return-table tbody tr:nth-child(even) {
  background: #f8fafc;
}

.catch-return-loading,
.catch-return-empty {
  font-size: 10pt;
  color: #64748b;
}

.catch-return-debug {
  margin: 4px 0 8px;
  font-size: 8.5pt;
  color: #64748b;
}

.catch-return-analytics {
  margin-top: 28px;
}

.catch-return-analytics h3 {
  margin: 0 0 10px;
  font-size: 12pt;
  font-weight: 700;
  color: #17324d;
}

.catch-return-analytics h4 {
  margin: 0 0 8px;
  font-size: 10.5pt;
  font-weight: 700;
  color: #334155;
}

.catch-return-analytics-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
  align-items: start;
}

.analytics-total-cell {
  font-weight: 700;
  color: #17324d;
}

@media (max-width: 720px) {
  .catch-return-analytics-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .catch-return-form-layout {
    grid-template-columns: 1fr;
  }

  .catch-return-actions {
    position: sticky;
    bottom: 8px;
    background: #fff;
    padding-top: 8px;
  }
}
</style>
