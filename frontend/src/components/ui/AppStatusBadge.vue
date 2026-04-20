<template>
  <v-chip class="app-status-badge" :class="badgeClass" density="compact" label>
    <slot>{{ status }}</slot>
  </v-chip>
</template>

<script>
export default {
  name: 'AppStatusBadge',
  props: {
    status: {
      type: String,
      default: '',
    },
  },
  computed: {
    badgeClass() {
      const normalizedStatus = String(this.status || '').trim().toLowerCase();
      if (!normalizedStatus) return 'is-default';
      return `is-${normalizedStatus.replace(/[^a-z0-9_-]/g, '-')}`;
    },
  },
};
</script>

<style scoped>
.app-status-badge {
  padding: 4px 8px !important;
  border-radius: 999px;
  font-size: 9pt;
  font-weight: 700;
  background: var(--app-badge-bg-default, #e5e7eb);
  color: var(--app-badge-text-default, #374151);
}

.app-status-badge.is-draft {
  background: var(--app-badge-bg-draft, #fff2cc);
  color: var(--app-badge-text-draft, #7a5a00);
}

.app-status-badge.is-planned {
  background: var(--app-badge-bg-planned, #dceeff);
  color: var(--app-badge-text-planned, #0f4c81);
}

.app-status-badge.is-queued,
.app-status-badge.is-published {
  background: var(--app-badge-bg-positive, #e4f7e7);
  color: var(--app-badge-text-positive, #21633a);
}

.app-status-badge.is-archived {
  background: var(--app-badge-bg-archived, var(--app-badge-bg-default, #e5e7eb));
  color: var(--app-badge-text-archived, var(--app-badge-text-default, #374151));
}
</style>
