<template>
  <component :is="tag" class="app-card">
    <slot />
  </component>
</template>

<script>
export default {
  name: 'AppCard',
  props: {
    tag: {
      type: String,
      default: 'div',
    },
  },
};
</script>

<style scoped>
.app-card {
  background: var(--app-color-bg-surface);
  border: 1px solid var(--app-color-border-soft);
  border-radius: var(--app-radius-xl);
  box-shadow: var(--app-shadow-soft);
  padding: 18px;
}
</style>
