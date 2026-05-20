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
            <th>Display As</th>
            <th>Show Column</th>
            <th>Read Only</th>
            <th>Min Width (px)</th>
            <th>Width</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(fieldName, index) in selectedFields" :key="`${selectedContext}-${fieldName}-${index}`">
            <td class="field-order-position">{{ index + 1 }}</td>
            <td>{{ fieldName }}</td>
            <td class="field-order-display-cell">
              <input
                type="text"
                class="admin-input"
                :value="getDisplayName(fieldName)"
                :placeholder="fieldName"
                @input="setDisplayName(fieldName, $event.target.value)"
              />
            </td>
            <td class="field-order-show-cell">
              <label class="field-order-show-toggle">
                <input
                  type="checkbox"
                  :checked="isFieldVisible(fieldName)"
                  @change="setFieldVisible(fieldName, $event.target.checked)"
                />
                Show
              </label>
            </td>
            <td class="field-order-readonly-cell">
              <label class="field-order-show-toggle">
                <input
                  type="checkbox"
                  :checked="isFieldReadOnly(fieldName)"
                  @change="setFieldReadOnly(fieldName, $event.target.checked)"
                />
                Read Only
              </label>
            </td>
            <td class="field-order-width-cell">
              <input
                type="number"
                class="admin-input"
                :value="getMinWidth(fieldName)"
                placeholder="auto"
                min="0"
                @input="setMinWidth(fieldName, $event.target.value)"
              />
            </td>
            <td class="field-order-preferred-width-cell">
              <input
                type="text"
                class="admin-input"
                :value="getColumnWidth(fieldName)"
                placeholder="flex"
                @input="setColumnWidth(fieldName, $event.target.value)"
              />
            </td>
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
    selectedShowColumns() {
      const showColumns = this.fieldOrder?.show_columns?.[this.selectedContext];
      return showColumns && typeof showColumns === 'object' ? showColumns : {};
    },
    selectedDisplayNames() {
      const displayNames = this.fieldOrder?.display_names?.[this.selectedContext];
      return displayNames && typeof displayNames === 'object' ? displayNames : {};
    },
    selectedReadOnlyColumns() {
      const readOnlyColumns = this.fieldOrder?.read_only?.[this.selectedContext];
      return readOnlyColumns && typeof readOnlyColumns === 'object' ? readOnlyColumns : {};
    },
    selectedMinimumWidths() {
      const widths = this.fieldOrder?.minimum_widths?.[this.selectedContext];
      return widths && typeof widths === 'object' ? widths : {};
    },
    selectedColumnWidths() {
      const widths = this.fieldOrder?.widths?.[this.selectedContext];
      return widths && typeof widths === 'object' ? widths : {};
    },
  },
  mounted() {
    this.fetchFieldOrder();
  },
  methods: {
    resolveFieldOrderSaveErrorMessage(err, fallbackMessage) {
      const statusCode = err?.response?.status;
      if (statusCode === 401) {
        return 'Session expired. Please log in again, then retry.';
      }
      if (statusCode === 403) {
        return 'You do not have permission to update field-order configuration.';
      }
      return err?.response?.data?.error || fallbackMessage;
    },
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
    isFieldVisible(fieldName) {
      const configured = this.selectedShowColumns?.[fieldName];
      return configured !== false;
    },
    isFieldReadOnly(fieldName) {
      const configured = this.selectedReadOnlyColumns?.[fieldName];
      return configured === true;
    },
    setFieldVisible(fieldName, isVisible) {
      if (!this.selectedContext || !fieldName) return;
      const nextShowColumns = {
        ...(this.fieldOrder?.show_columns || {}),
        [this.selectedContext]: {
          ...(this.fieldOrder?.show_columns?.[this.selectedContext] || {}),
          [fieldName]: !!isVisible,
        },
      };
      this.fieldOrder = {
        ...this.fieldOrder,
        show_columns: nextShowColumns,
      };
    },
    setFieldReadOnly(fieldName, isReadOnly) {
      if (!this.selectedContext || !fieldName) return;
      const nextReadOnlyForContext = {
        ...(this.fieldOrder?.read_only?.[this.selectedContext] || {}),
      };

      if (isReadOnly) {
        nextReadOnlyForContext[fieldName] = true;
      } else {
        delete nextReadOnlyForContext[fieldName];
      }

      this.fieldOrder = {
        ...this.fieldOrder,
        read_only: {
          ...(this.fieldOrder?.read_only || {}),
          [this.selectedContext]: nextReadOnlyForContext,
        },
      };
    },
    getDisplayName(fieldName) {
      const configured = this.selectedDisplayNames?.[fieldName];
      return typeof configured === 'string' ? configured : '';
    },
    getMinWidth(fieldName) {
      const configured = this.selectedMinimumWidths?.[fieldName];
      return Number.isFinite(configured) ? configured : '';
    },
    getColumnWidth(fieldName) {
      const configured = this.selectedColumnWidths?.[fieldName];
      return typeof configured === 'string' ? configured : '';
    },
    setDisplayName(fieldName, displayName) {
      if (!this.selectedContext || !fieldName) return;
      const nextDisplayNamesForContext = {
        ...(this.fieldOrder?.display_names?.[this.selectedContext] || {}),
      };

      const trimmed = String(displayName || '');
      if (trimmed.trim() === '') {
        delete nextDisplayNamesForContext[fieldName];
      } else {
        nextDisplayNamesForContext[fieldName] = trimmed;
      }

      this.fieldOrder = {
        ...this.fieldOrder,
        display_names: {
          ...(this.fieldOrder?.display_names || {}),
          [this.selectedContext]: nextDisplayNamesForContext,
        },
      };
    },
    setMinWidth(fieldName, widthValue) {
      if (!this.selectedContext || !fieldName) return;
      const nextMinWidthsForContext = {
        ...(this.fieldOrder?.minimum_widths?.[this.selectedContext] || {}),
      };

      const value = String(widthValue || '').trim();
      const numValue = Number(value);
      
      if (value === '' || !Number.isFinite(numValue) || numValue <= 0) {
        delete nextMinWidthsForContext[fieldName];
      } else {
        nextMinWidthsForContext[fieldName] = numValue;
      }

      this.fieldOrder = {
        ...this.fieldOrder,
        minimum_widths: {
          ...(this.fieldOrder?.minimum_widths || {}),
          [this.selectedContext]: nextMinWidthsForContext,
        },
      };
    },
    setColumnWidth(fieldName, widthValue) {
      if (!this.selectedContext || !fieldName) return;
      const nextColumnWidthsForContext = {
        ...(this.fieldOrder?.widths?.[this.selectedContext] || {}),
      };

      const value = String(widthValue || '').trim();
      
      // Accept: 'flex', 'auto', or pixel values like '120px', '120', '50%'
      if (value === '') {
        delete nextColumnWidthsForContext[fieldName];
      } else if (value.toLowerCase() === 'flex' || value.toLowerCase() === 'auto') {
        nextColumnWidthsForContext[fieldName] = value.toLowerCase();
      } else if (/^\d+%?$/.test(value)) {
        // Pure number or percentage
        nextColumnWidthsForContext[fieldName] = /^\d+$/.test(value) ? `${value}px` : value;
      } else if (/^\d+(px|rem|em|%)$/.test(value)) {
        // Already has unit
        nextColumnWidthsForContext[fieldName] = value;
      } else {
        // Invalid, remove it
        delete nextColumnWidthsForContext[fieldName];
        return;
      }

      this.fieldOrder = {
        ...this.fieldOrder,
        widths: {
          ...(this.fieldOrder?.widths || {}),
          [this.selectedContext]: nextColumnWidthsForContext,
        },
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
          this.showStatus(this.resolveFieldOrderSaveErrorMessage(err, 'Failed to save field-order configuration.'), true);
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
  max-width: 1400px;
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

.field-order-show-cell {
  white-space: nowrap;
}

.field-order-readonly-cell {
  white-space: nowrap;
}

.field-order-display-cell {
  min-width: 220px;
}

.field-order-show-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.field-order-width-cell {
  width: 120px;
}

.field-order-preferred-width-cell {
  width: 130px;
}
</style>
