import { KeyboardResize } from '@capacitor/keyboard';

function normalizeProfile(raw) {
  const value = String(raw || '').trim().toLowerCase();
  if (value === 'prod' || value === 'production' || value === 'mobile-prod') return 'prod';
  if (value === 'stage' || value === 'staging' || value === 'mobile-stage') return 'stage';
  return 'dev';
}

// Get profile from Vite environment or fallback to process.env for Node.js compatibility
const profile = normalizeProfile(
  (typeof import !== 'undefined' && import.meta?.env?.VITE_CAPACITOR_PROFILE) ||
  (typeof import !== 'undefined' && import.meta?.env?.VITE_APP_ENV) ||
  process.env.VITE_CAPACITOR_PROFILE ||
  process.env.VITE_APP_ENV ||
  'prod'
);

const isProd = profile === 'prod';
const isStage = profile === 'stage';

const appId = isProd
  ? 'com.hlas.app'
  : isStage
    ? 'com.hlas.app.stage'
    : 'com.hlas.app.dev';

const appName = isProd
  ? 'HLaS'
  : isStage
    ? 'HLaS Stage'
    : 'HLaS Dev';

const config = {
  appId,
  appName,
  webDir: 'dist',
  server: {
    cleartext: !isProd,
  },
  plugins: {
    Keyboard: {
      resize: KeyboardResize.Body,
      resizeOnFullScreen: true,
    },
    StatusBar: {
      overlaysWebView: false,
    },
  },
};

console.log(`[capacitor] profile=${profile} appId=${appId} cleartext=${String(!isProd)}`);

export default config;
