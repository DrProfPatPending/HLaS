<template>
  <div class="admin-panel field-order-panel">
    <h1 class="admin-panel-title">Field Order</h1>
    <div class="admin-info-text">
      Configure the display order of fields for each table context.
    </div>

    <div class="admin-inline-controls">
      <label class="admin-form-label" for="field-order-context">Context:</label>
      <select
        id="field-order-context"
        v-model="selectedContext"
        class="admin-select"
        :disabled="loading || !contextNames.length"
      >
        <option v-for="contextName in contextNames" :key="contextName" :value="contextName">
          {{ contextName }}
        </option>
      </select>
      <button type="button" :disabled="loading" @click="fetchFieldOrder">
        {{ loading ? 'Loading…' : 'Reload' }}
      </button>
    </div>

    <div v-if="loading" class="admin-loading-text">Loading field-order configuration...</div>

    <div v-else-if="!contextNames.length" class="admin-empty-state">
      No field-order contexts found.
    </div>

    <div v-else>
      <div v-if="!selectedFields.length" class="admin-empty-state">
        No fields configured for this context.
      </div>

      <table v-else class="admin-table field-order-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Field</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(fieldName, index) in selectedFields" :key="`${selectedContext}-${fieldName}-${index}`">
            <td class="field-order-position">{{ index + 1 }}</td>
            <td>{{ fieldName }}</td>
            <td class="admin-actions-cell">
              <button type="button" :disabled="index === 0" @click="moveToTop(index)">Top</button>
              <button type="button" :disabled="index === 0" @click="moveUp(index)">↑</button>
              <button type="button" :disabled="index === selectedFields.length - 1" @click="moveDown(index)">↓</button>
              <button type="button" :disabled="index === selectedFields.length - 1" @click="moveToBottom(index)">Bottom</button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="admin-inline-controls field-order-actions">
        <button type="button" class="save-btn" :disabled="saving" @click="saveFieldOrder">
          {{ saving ? 'Saving…' : 'Save Field Order' }}
        </button>
        <button type="button" :disabled="saving" @click="fetchFieldOrder">Discard Changes</button>
      </div>
    </div>

    <div v-if="statusMsg" :class="statusError ? 'error-msg' : 'success-msg'">
      {{ statusMsg }}
    </div>
  </div>
</template>

<script>
import { adminGet, adminPut } from '../../services/adminApi.js';

export default {
  name: 'FieldOrder',
  data() {
    return {
      loading: false,
      saving: false,
      selectedContext: '',
      fieldOrder: {},
      statusMsg: '',
      statusError: false,
    };
  },
  computed: {
    contextNames() {
      return Object.entries(this.fieldOrder || {})
        .filter(([, contextValue]) => Array.isArray(contextValue))
        .map(([contextName]) => contextName);
    },
    selectedFields() {
      const fields = this.fieldOrder?.[this.selectedContext];
      return Array.isArray(fields) ? fields : [];
    },
  },
  mounted() {
    this.fetchFieldOrder();
  },
  methods: {
    showStatus(msg, isError = false) {
      this.statusMsg = msg;
      this.statusError = isError;
    },
    fetchFieldOrder() {
      this.loading = true;
      this.statusMsg = '';
      return adminGet('/admin/field-order')
        .then(res => {
          const incoming = res.data?.field_order;
          this.fieldOrder = incoming && typeof incoming === 'object' ? incoming : {};
          if (!this.fieldOrder[this.selectedContext]) {
            this.selectedContext = this.contextNames[0] || '';
          }
        })
        .catch(err => {
          this.showStatus(err.response?.data?.error || 'Failed to load field-order configuration.', true);
        })
        .finally(() => {
          this.loading = false;
        });
    },
    replaceSelectedFields(nextFields) {
      if (!this.selectedContext) return;
      this.fieldOrder = {
        ...this.fieldOrder,
        [this.selectedContext]: nextFields,
      };
    },
    moveUp(index) {
      if (index <= 0) return;
      const next = [...this.selectedFields];
      [next[index - 1], next[index]] = [next[index], next[index - 1]];
      this.replaceSelectedFields(next);
    },
    moveDown(index) {
      if (index >= this.selectedFields.length - 1) return;
      const next = [...this.selectedFields];
      [next[index], next[index + 1]] = [next[index + 1], next[index]];
      this.replaceSelectedFields(next);
    },
    moveToTop(index) {
      if (index <= 0) return;
      const next = [...this.selectedFields];
      const [item] = next.splice(index, 1);
      next.unshift(item);
      this.replaceSelectedFields(next);
    },
    moveToBottom(index) {
      if (index >= this.selectedFields.length - 1) return;
      const next = [...this.selectedFields];
      const [item] = next.splice(index, 1);
      next.push(item);
      this.replaceSelectedFields(next);
    },
    saveFieldOrder() {
      this.saving = true;
      this.statusMsg = '';
      adminPut('/admin/field-order', this.fieldOrder)
        .then(() => {
          this.showStatus('Field-order configuration saved successfully.');
        })
        .catch(err => {
          this.showStatus(err.response?.data?.error || 'Failed to save field-order configuration.', true);
        })
        .finally(() => {
          this.saving = false;
        });
    },
  },
};
</script>

<style scoped>
.field-order-panel {
  max-width: 900px;
}

.field-order-table {
  margin-top: 6px;
}

.field-order-position {
  width: 58px;
  text-align: center;
}

.field-order-actions {
  margin-top: 10px;
}
</style>
