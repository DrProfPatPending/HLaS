<template>
  <div class="catch-return-container">
    <h2>Catch Return</h2>
    <p class="catch-return-intro">
      Record your fishing session quickly. Required fields are Date, Beat ID, and catch counts.
    </p>

    <form class="catch-return-form" @submit.prevent="submitCatchReturn">
      <div class="catch-return-top-fields">
        <label class="catch-return-field">
          <span>Date *</span>
          <input v-model="form.sessionDate" type="date" required />
        </label>

        <label class="catch-return-field">
          <span>Beat ID *</span>
          <select v-model="form.beatId" required>
            <option value="">Select Beat</option>
            <option v-for="option in beatOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
      </div>

      <div class="catch-return-count-grid">
        <label v-for="field in countFields" :key="field.key" class="catch-return-field">
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

      <label class="catch-return-field">
        <span>Flies Used</span>
        <textarea v-model="form.fliesUsed" rows="2" placeholder="Optional"></textarea>
      </label>

      <label class="catch-return-field">
        <span>Weather Conditions</span>
        <textarea v-model="form.weatherConditions" rows="2" placeholder="Optional"></textarea>
      </label>

      <label class="catch-return-field">
        <span>Predator Damage</span>
        <textarea v-model="form.predatorDamage" rows="2" placeholder="Optional"></textarea>
      </label>

      <div class="catch-return-actions">
        <button type="submit" :disabled="submitting">
          {{ submitting ? 'Saving…' : 'Save Catch Return' }}
        </button>
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
                  <th>Trout</th>
                  <th>Grayling</th>
                  <th>Other</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in totalsByBeat" :key="row.beat">
                  <td>{{ row.beat }}</td>
                  <td>{{ row.sessions }}</td>
                  <td>{{ row.trout }}</td>
                  <td>{{ row.grayling }}</td>
                  <td>{{ row.other }}</td>
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
                  <th>Trout</th>
                  <th>Grayling</th>
                  <th>Other</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in totalsByMonth" :key="row.month">
                  <td>{{ formatMonth(row.month) }}</td>
                  <td>{{ row.sessions }}</td>
                  <td>{{ row.trout }}</td>
                  <td>{{ row.grayling }}</td>
                  <td>{{ row.other }}</td>
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
                <th>Date</th>
                <th>Beat</th>
                <th>S.Trout</th>
                <th>M.Trout</th>
                <th>L.Trout</th>
                <th>S.Grayling</th>
                <th>M.Grayling</th>
                <th>L.Grayling</th>
                <th>Other</th>
                <th v-if="hasNotesColumn">Notes</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in recentReturns" :key="row.id">
                <td>{{ formatDateValue(row.session_date) }}</td>
                <td>{{ row.beat_id }}</td>
                <td>{{ row.small_trout }}</td>
                <td>{{ row.medium_trout }}</td>
                <td>{{ row.large_trout }}</td>
                <td>{{ row.small_grayling }}</td>
                <td>{{ row.medium_grayling }}</td>
                <td>{{ row.large_grayling }}</td>
                <td>{{ row.other_fish }}</td>
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
import { clubDetails, store, API_BASE_URL, formatConfiguredDate } from '../store.js';

const COUNT_FIELDS = [
  { key: 'smallTrout', label: 'Small Trout' },
  { key: 'mediumTrout', label: 'Medium Trout' },
  { key: 'largeTrout', label: 'Large Trout' },
  { key: 'smallGrayling', label: 'Small Grayling' },
  { key: 'mediumGrayling', label: 'Medium Grayling' },
  { key: 'largeGrayling', label: 'Large Grayling' },
  { key: 'otherFish', label: 'Other Fish' },
];

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

export default {
  name: 'CatchReturn',
  data() {
    return {
      submitting: false,
      status: '',
      error: '',
      recentReturns: [],
      loadingReturns: false,
      returnsError: '',
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
      },
    };
  },
  computed: {
    countFields: () => COUNT_FIELDS,
    loggedInClub: () => store.loggedInClub,
    hasNotesColumn() {
      return this.recentReturns.some(
        r => r.flies_used || r.weather_conditions || r.predator_damage,
      );
    },
    totalsByBeat() {
      const map = {};
      for (const row of this.recentReturns) {
        const beat = row.beat_id || '(unknown)';
        if (!map[beat]) map[beat] = { beat, trout: 0, grayling: 0, other: 0, total: 0, sessions: 0 };
        const trout = (row.small_trout || 0) + (row.medium_trout || 0) + (row.large_trout || 0);
        const grayling = (row.small_grayling || 0) + (row.medium_grayling || 0) + (row.large_grayling || 0);
        const other = row.other_fish || 0;
        map[beat].trout += trout;
        map[beat].grayling += grayling;
        map[beat].other += other;
        map[beat].total += trout + grayling + other;
        map[beat].sessions += 1;
      }
      return Object.values(map).sort((a, b) => b.total - a.total);
    },
    totalsByMonth() {
      const map = {};
      for (const row of this.recentReturns) {
        const month = String(row.session_date || '').slice(0, 7);
        if (!month) continue;
        if (!map[month]) map[month] = { month, trout: 0, grayling: 0, other: 0, total: 0, sessions: 0 };
        const trout = (row.small_trout || 0) + (row.medium_trout || 0) + (row.large_trout || 0);
        const grayling = (row.small_grayling || 0) + (row.medium_grayling || 0) + (row.large_grayling || 0);
        const other = row.other_fish || 0;
        map[month].trout += trout;
        map[month].grayling += grayling;
        map[month].other += other;
        map[month].total += trout + grayling + other;
        map[month].sessions += 1;
      }
      return Object.values(map).sort((a, b) => b.month.localeCompare(a.month));
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
    this.loadRecentReturns();
  },
  methods: {
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
      return [row.flies_used, row.weather_conditions, row.predator_damage]
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

.catch-return-top-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.catch-return-count-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
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
  .catch-return-top-fields,
  .catch-return-count-grid {
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
