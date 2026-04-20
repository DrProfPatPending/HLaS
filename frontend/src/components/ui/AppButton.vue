<template>
  <button
    :type="type"
    :disabled="disabled"
    class="app-button"
    :class="[`is-${variant}`, `is-${size}`]"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
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
  },
};
</script>

<style scoped>
.app-button {
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
  border: none;
  border-radius: 0;
  background: transparent;
  color: var(--app-color-link);
  text-decoration: underline;
  text-align: left;
  padding: 0;
}

.app-button.is-danger {
  border-color: var(--app-color-state-danger);
  color: var(--app-color-state-danger);
  background: var(--app-color-bg-surface);
}

.app-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
