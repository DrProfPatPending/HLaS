<template>
  <span class="app-status-badge" :class="badgeClass">
    <slot>{{ status }}</slot>
  </span>
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
  display: inline-block;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 9pt;
  font-weight: 700;
  background: #e5e7eb;
  color: #374151;
}

.app-status-badge.is-draft {
  background: #fff2cc;
  color: #7a5a00;
}

.app-status-badge.is-planned {
  background: #dceeff;
  color: #0f4c81;
}

.app-status-badge.is-queued,
.app-status-badge.is-published {
  background: #e4f7e7;
  color: #21633a;
}

.app-status-badge.is-archived {
  background: #e5e7eb;
  color: #374151;
}
</style>
