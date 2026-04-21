<template>
  <v-btn
    :type="type"
    :disabled="disabled"
    :variant="resolvedVariant"
    class="app-button"
    :class="[`is-${variant}`, `is-${size}`, { 'is-inherit': inheritStyle }]"
    :density="size === 'sm' ? 'compact' : 'default'"
    :ripple="!inheritStyle"
    @click="$emit('click', $event)"
  >
    <slot />
  </v-btn>
</template>

<script>
export default {
  name: 'AppButton',
  emits: ['click'],
  props: {
    type: {
      type: String,
      default: 'button',
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    variant: {
      type: String,
      default: 'subtle',
      validator: value => ['subtle', 'link', 'danger'].includes(value),
    },
    size: {
      type: String,
      default: 'md',
      validator: value => ['sm', 'md'].includes(value),
    },
    inheritStyle: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    resolvedVariant() {
      if (this.inheritStyle) return 'plain';
      if (this.variant === 'link') return 'text';
      if (this.variant === 'danger') return 'outlined';
      return 'outlined';
    },
  },
};
</script>

<style scoped>
.app-button {
  min-width: 0;
  text-transform: none;
  letter-spacing: normal;
  font-weight: 500;
  border: 1px solid var(--app-color-border-soft);
  border-radius: var(--app-radius-lg);
  background: var(--app-color-bg-subtle);
  color: var(--app-color-text-primary);
  padding: 7px 12px;
  cursor: pointer;
  font-family: var(--app-font-family-body);
}

.app-button.is-sm {
  font-size: 9pt;
  line-height: 1.15;
  padding: 4px 8px;
}

.app-button.is-link {
  border: none !important;
  border-radius: 0;
  background: transparent !important;
  color: var(--app-color-link) !important;
  text-decoration: underline;
  text-align: left;
  padding: 0;
}

.app-button.is-link :deep(.v-btn__content) {
  color: var(--app-color-link) !important;
}

.app-button.is-link :deep(.v-btn__overlay),
.app-button.is-link :deep(.v-btn__underlay) {
  background: transparent !important;
}

.app-button.is-danger {
  border-color: var(--app-color-state-danger) !important;
  color: var(--app-color-state-danger) !important;
  background: var(--app-color-bg-surface);
}

.app-button.is-danger :deep(.v-btn__content) {
  color: var(--app-color-state-danger) !important;
}

.app-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.app-button.is-inherit {
  border: inherit;
  border-radius: inherit;
  background: inherit;
  color: inherit;
  font: inherit;
  line-height: inherit;
  padding: inherit;
  min-width: inherit;
}
</style>
