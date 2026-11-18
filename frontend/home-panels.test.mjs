import assert from 'node:assert/strict';
import test from 'node:test';
import { createSSRApp, defineComponent, h } from 'vue';
import { renderToString } from '@vue/server-renderer';
import vue from '@vitejs/plugin-vue';
import { createServer } from 'vite';

test('Home and Documents panels retain compact actions and permissions', async () => {
  const server = await createServer({
    configFile: false,
    server: { middlewareMode: true, hmr: false },
    plugins: [{
      name: 'stub-home-store',
      enforce: 'pre',
      resolveId(source) {
        if (source === '../store.js') return '\0home-test-store';
      },
      load(id) {
        if (id === '\0home-test-store') {
          return `
            export const store = globalThis.__homeTestStore;
            export const clubDetails = { value: { shortName: 'CTC' } };
            export const formatConfiguredDate = value => value;
            export const API_BASE_URL = '/api';
            export const canAccessNewsletters = { get value() { return store.canManageNews; } };
          `;
        }
      },
    }, vue()],
  });

  globalThis.__homeTestStore = {
    loggedInClub: 'CTC',
    memberRoles: ['club_admin'],
    memberPermissions: ['document.club.manage'],
    canManageNews: true,
  };
  try {
    const { default: Home } = await server.ssrLoadModule('/src/components/HomeView.vue');
    const render = async (props, fieldOrder = {}) => {
      const Fixture = {
        ...Home,
        data() {
          return {
            ...Home.data.call(this),
            fieldOrder,
            newsItems: [{ id: 1, date: '2026-11-15', status: 'Published', category: 'News', update: 'Update' }],
            documents: [{ id: 2, title: 'Club Rules', fileName: 'rules.pdf', fileSize: 1024 }],
          };
        },
      };
      const app = createSSRApp(Fixture, props);
      for (const [name, tag] of [['v-card', 'div'], ['v-btn', 'button'], ['v-chip', 'span']]) {
        app.component(name, defineComponent({
          setup(_props, { attrs, slots }) {
            return () => h(tag, attrs, slots.default?.());
          },
        }));
      }
      return renderToString(app);
    };

    const home = await render({ showDocuments: false });
    assert.match(home, /CTC News and Updates/);
    assert.doesNotMatch(home, /CTC Documents|home-documents-table/);
    assert.match(home, /<td[^>]*>(?:(?!<\/td>)[\s\S])*?2026-11-15(?:(?!<\/td>)[\s\S])*?news-actions-stack(?:(?!<\/td>)[\s\S])*?Edit(?:(?!<\/td>)[\s\S])*?Delete(?:(?!<\/td>)[\s\S])*?<\/td>/);
    assert.doesNotMatch(home, /<th[^>]*>Actions/);

    const documents = await render({ showNews: false });
    assert.match(documents, /CTC Documents/);
    assert.doesNotMatch(documents, /CTC News and Updates|home-news-table/);
    assert.match(documents, /<td[^>]*>(?:(?!<\/td>)[\s\S])*?Club Rules(?:(?!<\/td>)[\s\S])*?documents-actions-stack(?:(?!<\/td>)[\s\S])*?Download(?:(?!<\/td>)[\s\S])*?Delete(?:(?!<\/td>)[\s\S])*?<\/td>/);
    assert.doesNotMatch(documents, /<th[^>]*>Actions/);
    assert.match(documents, /class="home-documents-table documents-compact-table documents-both-details"/);

    const fallback = await render({}, {
      home_news: ['Category', 'Date', 'Update'],
      home_documents: ['Size', 'Title', 'Position'],
      show_columns: { home_news: { Date: false }, home_documents: { Title: false } },
    });
    assert.match(fallback, /<td[^>]*>(?:(?!<\/td>)[\s\S])*?News(?:(?!<\/td>)[\s\S])*?news-actions-stack(?:(?!<\/td>)[\s\S])*?<\/td>/);
    assert.match(fallback, /<td[^>]*>(?:(?!<\/td>)[\s\S])*?1\.0 KB(?:(?!<\/td>)[\s\S])*?documents-actions-stack(?:(?!<\/td>)[\s\S])*?Download(?:(?!<\/td>)[\s\S])*?<\/td>/);
    assert.match(fallback, /class="news-item-row news-single-meta"/);
    assert.doesNotMatch(fallback, /documents-compact-table/);

    const sizeOnly = await render({ showNews: false }, {
      show_columns: { home_documents: { Position: false } },
    });
    assert.match(sizeOnly, /class="home-documents-table documents-compact-table"/);
    assert.doesNotMatch(sizeOnly, /documents-both-details|documents-position-controls/);

    const updateOnly = await render({ showDocuments: false }, {
      home_news: ['Update', 'Category', 'Date'],
      show_columns: { home_news: { Date: false, Category: false } },
    });
    assert.match(updateOnly, /class="news-update-cell"[^>]*>[\s\S]*?Update[\s\S]*?news-actions-stack/);
    assert.doesNotMatch(updateOnly, /news-single-meta/);

    // Field Order widths typed as bare numbers are pixels (the Width box accepts "90").
    const sized = await render({ showDocuments: false }, {
      widths: { home_news: { Date: '90', Category: 'flex' } },
      minimum_widths: { home_news: { Category: 120 } },
    });
    assert.match(sized, /<th[^>]*style="[^"]*width:90px[^"]*"[^>]*>(?:(?!<\/th>)[\s\S])*?Date/);
    assert.match(sized, /<th[^>]*style="[^"]*min-width:120px[^"]*"[^>]*>(?:(?!<\/th>)[\s\S])*?Category/);

    globalThis.__homeTestStore.memberRoles = [];
    const readOnly = await render({}, {
      read_only: { home_news: { Actions: true }, home_documents: { Actions: true } },
    });
    assert.match(readOnly, /Download/);
    assert.doesNotMatch(readOnly, /news-actions-stack|documents-delete-btn|documents-position-controls/);

    globalThis.__homeTestStore.memberPermissions = [];
    globalThis.__homeTestStore.canManageNews = false;
    const member = await render({ contentScope: 'health-safety', newsTitle: 'Health and Safety Information', documentsTitle: 'Health & Safety Documents' });
    assert.match(member, /Health and Safety Information/);
    assert.match(member, /Health &amp; Safety Documents/);
    assert.match(member, /Download/);
    assert.doesNotMatch(member, /news-actions-stack|documents-delete-btn|documents-upload-form/);
  } finally {
    delete globalThis.__homeTestStore;
    await server.close();
  }
});
