import assert from 'node:assert/strict';
import test from 'node:test';
import { createServer } from 'vite';

test('Beat Admin (fishing-beats) is only reachable by committee members and above', async () => {
  // store.js reads browser globals when it loads; a minimal stand-in is enough here.
  const storage = new Map();
  globalThis.window = {
    location: { origin: 'http://localhost', hostname: 'localhost', pathname: '/', protocol: 'http:', search: '' },
    localStorage: {
      getItem: key => (storage.has(key) ? storage.get(key) : null),
      setItem: (key, value) => storage.set(key, String(value)),
      removeItem: key => storage.delete(key),
    },
    addEventListener() {},
    removeEventListener() {},
  };
  globalThis.localStorage = globalThis.window.localStorage;
  const server = await createServer({ configFile: false, server: { middlewareMode: true, hmr: false } });
  try {
    const { store, canAccessBeatAdmin, canNavigateToSection, sectionDisplayName } = await server.ssrLoadModule('/src/store.js');

    store.memberPermissions = ['member.self.read', 'member.self.update'];
    assert.equal(canAccessBeatAdmin.value, false, 'ordinary members do not get Beat Admin');
    assert.equal(canNavigateToSection('fishing-beats'), false);
    assert.equal(canNavigateToSection('beat-details'), true, 'Beat Details stays open to members');

    // Committee members (member.club.list) and above.
    store.memberPermissions = ['member.self.read', 'member.club.list'];
    assert.equal(canAccessBeatAdmin.value, true);
    assert.equal(canNavigateToSection('fishing-beats'), true);
    assert.equal(sectionDisplayName('fishing-beats'), 'Beat Admin');
  } finally {
    delete globalThis.window;
    delete globalThis.localStorage;
    await server.close();
  }
});
