<template>
  <nav class="member-top-menu" aria-label="Member navigation">
    <details class="member-top-menu-group">
      <summary>{{ clubShortName }}</summary>
      <ul class="member-top-menu-list">
        <li>
          <button type="button" @click="navigate('club-information')">Club Information</button>
        </li>
        <li>
          <button type="button" @click="navigate('fishing-beats')">Fishing Beats</button>
        </li>
        <li>
          <button type="button" @click="navigate('club-store')">Club Store</button>
        </li>
      </ul>
    </details>

    <details class="member-top-menu-group">
      <summary>My HLaS</summary>
      <ul class="member-top-menu-list">
        <li>
          <button type="button" @click="navigate('my-club')">My Club</button>
        </li>
      </ul>
    </details>
  </nav>
</template>

<script>
import { clubDetails, navigateToSection } from '../store.js';

export default {
  name: 'MemberTopMenu',
  computed: {
    clubShortName() {
      return clubDetails.value.shortName || 'Club';
    },
  },
  methods: {
    navigate(sectionKey) {
      navigateToSection(sectionKey);
      this.closeMenus();
    },
    closeMenus() {
      const openMenus = this.$el.querySelectorAll('details[open]');
      openMenus.forEach(menu => menu.removeAttribute('open'));
    },
  },
};
</script>

<style scoped>
.member-top-menu {
  max-width: 900px;
  margin: 16px auto 0;
  display: flex;
  gap: 10px;
  font-family: Helvetica, Arial, sans-serif;
}

.member-top-menu-group {
  position: relative;
}

.member-top-menu-group > summary {
  list-style: none;
  cursor: pointer;
  border: 1px solid #ccc;
  background: #f7f7f7;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 10pt;
  user-select: none;
}

.member-top-menu-group > summary::-webkit-details-marker {
  display: none;
}

.member-top-menu-list {
  position: absolute;
  z-index: 20;
  top: calc(100% + 4px);
  left: 0;
  min-width: 180px;
  margin: 0;
  padding: 6px;
  list-style: none;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}

.member-top-menu-list li + li {
  margin-top: 4px;
}

.member-top-menu-list button {
  width: 100%;
  text-align: left;
  border: 1px solid transparent;
  background: #fff;
  padding: 7px 8px;
  border-radius: 3px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
  cursor: pointer;
}

.member-top-menu-list button:hover {
  background: #f3f7ff;
  border-color: #d0dcf5;
}
</style>
