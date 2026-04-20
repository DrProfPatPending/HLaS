<template>
  <v-card
    :tag="tag"
    class="app-card"
    :class="{ 'is-inherit': inheritStyle }"
    :variant="inheritStyle ? 'flat' : 'outlined'"
  >
    <slot />
  </v-card>
</template>

<script>
export default {
  name: 'AppCard',
  props: {
    tag: {
      type: String,
      default: 'div',
    },
    inheritStyle: {
      type: Boolean,
      default: false,
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

.app-card.is-inherit {
  background: inherit;
  border: inherit;
  border-radius: inherit;
  box-shadow: inherit;
  padding: inherit;
}
</style>
