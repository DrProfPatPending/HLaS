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
  display: flex;
  gap: 2px;
  font-family: Helvetica, Arial, sans-serif;
  align-items: center;
}

.member-top-menu-group {
  position: relative;
}

.member-top-menu-group > summary {
  list-style: none;
  cursor: pointer;
  background: #fff;
  color: #000;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 10pt;
  font-weight: 500;
  user-select: none;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 4px;
}

.member-top-menu-group > summary::-webkit-details-marker {
  display: none;
}

.member-top-menu-group > summary::after {
  content: '\25BE';
  font-size: 9pt;
  color: #444;
}

.member-top-menu-group[open] > summary::after {
  content: '\25B4';
}

.member-top-menu-group > summary:hover {
  background: #f0f0f0;
}

.member-top-menu-list {
  position: absolute;
  z-index: 100;
  top: calc(100% + 2px);
  left: 0;
  min-width: 180px;
  margin: 0;
  padding: 4px 0;
  list-style: none;
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.15);
}

.member-top-menu-list li + li {
  margin-top: 0;
}

.member-top-menu-list button {
  width: 100%;
  text-align: left;
  border: none;
  background: #fff;
  color: #000;
  padding: 8px 14px;
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10pt;
  cursor: pointer;
  display: block;
}

.member-top-menu-list button:hover {
  background: #f0f0f0;
}
</style>
