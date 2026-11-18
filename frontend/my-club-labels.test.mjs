import assert from 'node:assert/strict';
import test from 'node:test';
import { createSSRApp } from 'vue';
import { renderToString } from '@vue/server-renderer';
import vue from '@vitejs/plugin-vue';
import { createServer } from 'vite';

test('Member Info uses configured my_club display names, falling back to field names', async () => {
  const server = await createServer({
    configFile: false,
    server: { middlewareMode: true, hmr: false },
    plugins: [{
      name: 'stub-my-club-store',
      enforce: 'pre',
      resolveId(source) {
        if (source === '../store.js') return '\0my-club-test-store';
        if (source === './ui/AppButton.vue') return '\0my-club-test-button';
      },
      load(id) {
        if (id === '\0my-club-test-button') {
          return `import { h } from 'vue'; export default { setup: (_p, { slots }) => () => h('button', slots.default?.()) };`;
        }
        if (id === '\0my-club-test-store') {
          return `
            export const store = { loggedInClub: 'CTC', myClubActiveTab: 'personal', memberRoles: [], apiBaseUrl: '/api' };
            export const MY_CLUB_TABS = [{ id: 'personal', label: 'Personal Info' }];
            export const formatFieldName = name => name.replace(/__/g, '::').replace(/_/g, ' ');
            export const fieldOrderConfig = globalThis.__myClubFieldOrder;
            export const loadFieldOrderConfig = () => new Promise(() => {});
            export const isDateOfBirthField = name => name === 'Date_of_Birth';
            export const isAgeField = name => name === 'Age';
            export const calculateAgeFromDOB = () => '';
            export const formatConfiguredDate = value => value;
            export const normalizeDateInputValue = value => value;
          `;
        }
      },
    }, vue()],
  });

  globalThis.__myClubFieldOrder = {
    order: {
      my_club: ['First_Name', 'Date_of_Birth', 'Age'],
      display_names: {
        my_club: { Date_of_Birth: ' Date of Birth (if under 18) ', Age: '   ' },
      },
    },
  };
  try {
    const { default: MyClub } = await server.ssrLoadModule('/src/components/MyClub.vue');
    const Fixture = {
      ...MyClub,
      data() {
        return {
          ...MyClub.data.call(this),
          loading: false,
          memberData: { First_Name: 'Alex', Date_of_Birth: '', Age: '' },
        };
      },
    };
    const app = createSSRApp(Fixture);
    const html = await renderToString(app);

    assert.match(html, /<th[^>]*>Date of Birth \(if under 18\)<\/th>/);
    assert.match(html, /<th[^>]*>First Name<\/th>/);
    assert.match(html, /<th[^>]*>Age<\/th>/, 'blank configured label falls back to the field name');
  } finally {
    delete globalThis.__myClubFieldOrder;
    await server.close();
  }
});
