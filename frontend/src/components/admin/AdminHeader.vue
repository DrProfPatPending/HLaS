<template>
  <table class="admin-header-table">
    <tbody>
      <tr>
        <td class="admin-header-logo-cell">
          <img src="/logos/HLaS.png" alt="HLaS logo" class="admin-header-logo" />
        </td>
        <td class="admin-header-title-cell">
          <span class="admin-header-title">HLaS Application Administration</span>
        </td>
        <td class="admin-header-spacer"></td>
        <td v-if="loggedIn" class="admin-header-logout-cell">
          <button type="button" class="admin-header-logout-button" @click="$emit('logout')">Log Out</button>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script>
export default {
  name: 'AdminHeader',
  props: {
    loggedIn: { type: Boolean, default: false }
  }
};
</script>

<style scoped>
.admin-header-table {
  width: 100%;
  border-collapse: collapse;
  background: #f8f8f8;
  border-bottom: 1px solid #ddd;
  padding: 4px 0;
}

.admin-header-logo-cell {
  padding: 4px 10px;
  vertical-align: middle;
}

.admin-header-logo {
  height: 50px;
  cursor: default;
}

.admin-header-title-cell {
  vertical-align: middle;
  padding-left: 12px;
}

.admin-header-title {
  font-size: 18pt;
  font-weight: bold;
  color: #333;
}

.admin-header-spacer {
  width: 100%;
}

.admin-header-logout-cell {
  padding: 4px 12px;
  white-space: nowrap;
  vertical-align: middle;
}

.admin-header-logout-button {
  padding: 6px 14px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 9pt;
  cursor: pointer;
}
</style>
