// Pure CommonJS — required for Capacitor CLI (npx cap sync) and Xcode Cloud compatibility.
// Do NOT use ESM import/export syntax or import.meta here.

function normalizeProfile(raw) {
  const value = String(raw || '').trim().toLowerCase();
  if (value === 'prod' || value === 'production' || value === 'mobile-prod') return 'prod';
  if (value === 'stage' || value === 'staging' || value === 'mobile-stage') return 'stage';
  return 'dev';
}

const profile = normalizeProfile(
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
      resize: 'body', // KeyboardResize.Body
      resizeOnFullScreen: true,
    },
    StatusBar: {
      overlaysWebView: false,
    },
  },
};

console.log(`[capacitor] profile=${profile} appId=${appId} cleartext=${String(!isProd)}`);

module.exports = config;
