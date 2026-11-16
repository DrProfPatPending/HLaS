import assert from 'node:assert/strict';
import test from 'node:test';
import { createSSRApp } from 'vue';
import { renderToString } from '@vue/server-renderer';
import vue from '@vitejs/plugin-vue';
import { createServer } from 'vite';

test('Home hero renders the welcome prefix once without a colon', async () => {
  const server = await createServer({
    configFile: false,
    server: { middlewareMode: true },
    plugins: [
      {
        name: 'stub-browser-dependencies',
        enforce: 'pre',
        resolveId(source) {
          if (source === './sanitizeMiniSiteContent.js') return '\0test-sanitizer';
          if (source === '../../store.js') return '\0test-store';
        },
        load(id) {
          if (id === '\0test-sanitizer') return 'export const sanitizeMiniSiteContent = () => ""';
          if (id === '\0test-store') return 'export const API_BASE_URL = "/api"';
        },
      },
      vue(),
    ],
  });

  try {
    const { default: Home } = await server.ssrLoadModule('/src/components/MiniSite/MiniSiteHome.vue');
    for (const [headline, expected] of [
      ['', 'Welcome to Example Club'],
      ['Custom Club Name', 'Welcome to Custom Club Name'],
    ]) {
      const html = await renderToString(createSSRApp(Home, {
        clubCode: 'TEST',
        clubName: 'Example Club',
        headline,
      }));
      const heading = html.match(/<h1 class="hero-title"[^>]*>(.*?)<\/h1>/);
      assert.equal(heading?.[1], expected);
    }
  } finally {
    await server.close();
  }
});
