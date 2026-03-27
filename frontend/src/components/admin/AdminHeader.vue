<template>
  <table class="logo-table">
    <tbody>
      <tr>
        <td class="logo-cell">
          <img src="../../logos/HLaS.png" alt="HLaS logo" class="app-logo" />
        </td>
        <td class="admin-title-cell">
          <span class="admin-title">HLaS Application Administration</span>
        </td>
        <td class="logo-spacer"></td>
        <td v-if="loggedIn" class="logout-cell">
          <button type="button" class="logout-button" @click="$emit('logout')">Log Out</button>
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
.logo-table {
  width: 100%;
  border-collapse: collapse;
  background: #f8f8f8;
  border-bottom: 1px solid #ddd;
  padding: 4px 0;
}
.logo-cell {
  padding: 4px 10px;
  vertical-align: middle;
}
.app-logo {
  height: 50px;
  cursor: default;
}
.admin-title-cell {
  vertical-align: middle;
  padding-left: 12px;
}
.admin-title {
  font-size: 18pt;
  font-weight: bold;
  color: #333;
}
.logo-spacer {
  width: 100%;
}
.logout-cell {
  padding: 4px 12px;
  white-space: nowrap;
  vertical-align: middle;
}
.logout-button {
  padding: 6px 14px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 9pt;
  cursor: pointer;
}
</style>
