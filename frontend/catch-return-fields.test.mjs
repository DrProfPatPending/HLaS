import assert from 'node:assert/strict';
import test from 'node:test';
import { createSSRApp, h } from 'vue';
import { renderToString } from '@vue/server-renderer';
import vue from '@vitejs/plugin-vue';
import { createServer } from 'vite';

test('Catch Return uses catch_return Field Order labels, order and visibility', async () => {
  const server = await createServer({
    configFile: false,
    server: { middlewareMode: true, hmr: false },
    plugins: [{
      name: 'stub-catch-return-store',
      enforce: 'pre',
      resolveId(source) {
        if (source === '../store.js') return '\0catch-return-test-store';
        if (source === './ui/AppButton.vue') return '\0catch-return-test-button';
      },
      load(id) {
        if (id === '\0catch-return-test-button') {
          return `import { h } from 'vue'; export default { setup: (_p, { slots }) => () => h('button', slots.default?.()) };`;
        }
        if (id === '\0catch-return-test-store') {
          return `
            export const store = { loggedInClub: 'CTC' };
            export const clubDetails = { value: { beats: [{ Beat_ID: 'A', Beat_Name: 'Upper' }] } };
            export const API_BASE_URL = '/api';
            export const formatConfiguredDate = value => value;
            export const fieldOrderConfig = globalThis.__catchReturnFieldOrder;
            export const loadFieldOrderConfig = () => Promise.resolve();
          `;
        }
      },
    }, vue()],
  });

  const fieldOrder = { loaded: true, order: {} };
  globalThis.__catchReturnFieldOrder = fieldOrder;
  try {
    const { default: CatchReturn } = await server.ssrLoadModule('/src/components/CatchReturn.vue');
    const render = async (order, legacyVisibility = {}) => {
      fieldOrder.order = order;
      const Fixture = {
        ...CatchReturn,
        data() {
          const data = CatchReturn.data.call(this);
          return {
            ...data,
            fieldVisibility: { ...data.fieldVisibility, ...legacyVisibility },
            recentReturns: [{ id: 1, session_date: '2026-05-01', beat_id: 'A', small_trout: 2, large_trout: 1 }],
          };
        },
        methods: {
          ...CatchReturn.methods,
          loadCatchReturnFieldVisibility() {},
          loadRecentReturns() {},
        },
      };
      const html = await renderToString(createSSRApp({ render: () => h(Fixture) }));
      return html.replace(/ data-v-[a-z0-9]+(?:="")?/g, '');
    };
    const labelPosition = (html, label) => html.indexOf(`<span>${label}</span>`);

    // Defaults: today's labels and every field shown.
    const defaults = await render({});
    assert.match(defaults, /<span>Small Grayling<\/span>/);
    assert.match(defaults, /<span>Comments<\/span>/);
    assert.match(defaults, /<th>Small Trout<\/th>/);

    // Configured labels, order and visibility win over the older setting.
    const configured = await render({
      catch_return: ['sessionDate', 'beatId', 'largeTrout', 'smallTrout', 'mediumTrout', 'comments', 'weatherConditions'],
      display_names: { catch_return: { smallTrout: 'Small Trout (< 6 in)', sessionDate: 'Day fished' } },
      show_columns: { catch_return: { smallGrayling: false, mediumGrayling: false, comments: true } },
    }, { comments: false });
    assert.match(configured, /<span>Small Trout \(&lt; 6 in\)<\/span>/);
    assert.match(configured, /<span>Day fished \*<\/span>/);
    assert.match(configured, /<th>Small Trout \(&lt; 6 in\)<\/th>/);
    assert.doesNotMatch(configured, /Small Grayling|Medium Grayling/);
    assert.match(configured, /<span>Large Grayling<\/span>/);
    assert.match(configured, /<span>Comments<\/span>/, 'Field Order visibility overrides the older setting');
    assert.ok(labelPosition(configured, 'Large Trout') < labelPosition(configured, 'Small Trout (&lt; 6 in)'));
    assert.ok(labelPosition(configured, 'Comments') < labelPosition(configured, 'Weather Conditions'));
    assert.match(configured, /<td>1<\/td><td>2<\/td>/, 'table cells follow the configured column order');

    // No catch_return visibility yet: the older setting still applies.
    const legacy = await render({ display_names: { catch_return: { comments: 'Notes' } } }, { comments: false, smallGrayling: false });
    assert.doesNotMatch(legacy, /<span>Notes<\/span>|Small Grayling/);
    assert.match(legacy, /<span>Medium Grayling<\/span>/);
  } finally {
    delete globalThis.__catchReturnFieldOrder;
    await server.close();
  }
});

test('Club Settings seeds catch_return visibility from the older setting and saves both in step', async () => {
  const server = await createServer({
    configFile: false,
    server: { middlewareMode: true, hmr: false },
    plugins: [{
      name: 'stub-club-settings-store',
      enforce: 'pre',
      resolveId(source) {
        if (source === '../store.js') return '\0club-settings-test-store';
      },
      load(id) {
        if (id === '\0club-settings-test-store') {
          return `export const API_BASE_URL = '/api'; export const store = { loggedInClub: 'CTC' };`;
        }
      },
    }, vue()],
  });
  try {
    const { default: ClubSettings } = await server.ssrLoadModule('/src/components/ClubSettings.vue');
    const { seedCatchReturnVisibility, catchReturnVisibilityForSave, normalizeVisibility } = ClubSettings.methods;
    const context = (fieldOrder, visibility) => {
      const ctx = { fieldOrder, visibility };
      ctx.normalizeVisibility = normalizeVisibility.bind(ctx);
      return ctx;
    };

    // No catch_return visibility yet: seeded from the older setting.
    const unseeded = context(
      { catch_return: ['smallTrout', 'smallGrayling'], show_columns: { my_club: { Age: false } } },
      { smallGrayling: false },
    );
    seedCatchReturnVisibility.call(unseeded);
    assert.equal(unseeded.fieldOrder.show_columns.catch_return.smallGrayling, false);
    assert.equal(unseeded.fieldOrder.show_columns.catch_return.smallTrout, true);
    assert.deepEqual(unseeded.fieldOrder.show_columns.my_club, { Age: false });

    // Existing catch_return visibility is left alone, and the older setting is saved to match it.
    const seeded = context(
      { catch_return: ['smallTrout'], show_columns: { catch_return: { comments: false } } },
      { comments: true, smallGrayling: false },
    );
    seedCatchReturnVisibility.call(seeded);
    assert.deepEqual(seeded.fieldOrder.show_columns.catch_return, { comments: false });
    const saved = catchReturnVisibilityForSave.call(seeded);
    assert.equal(saved.comments, false);
    assert.equal(saved.smallGrayling, true);
    assert.equal(saved.smallTrout, true);

    // Field order failed to load: keep saving the older setting unchanged.
    const missing = context({}, { smallGrayling: false });
    seedCatchReturnVisibility.call(missing);
    assert.deepEqual(missing.fieldOrder, {});
    assert.equal(catchReturnVisibilityForSave.call(missing).smallGrayling, false);
  } finally {
    await server.close();
  }
});
