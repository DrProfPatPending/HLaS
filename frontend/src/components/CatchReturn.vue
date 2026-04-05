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
  </div>
</template>

<script>
import axios from 'axios';
import { clubDetails, store, API_BASE_URL } from '../store.js';

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
        })
        .catch(err => {
          this.error = err?.response?.data?.error || 'Failed to save catch return.';
        })
        .finally(() => {
          this.submitting = false;
        });
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
