import type { CapacitorConfig } from '@capacitor/cli';
import { KeyboardResize } from '@capacitor/keyboard';

const KeyboardResize = {
  Body: 'body',
  Ionic: 'ionic',
  Native: 'native',
  None: 'none',
};

function normalizeProfile(raw: string | undefined | null) {
  const value = String(raw || '').trim().toLowerCase();
  if (value === 'prod' || value === 'production' || value === 'mobile-prod') return 'prod';
  if (value === 'stage' || value === 'staging' || value === 'mobile-stage') return 'stage';
  return 'dev';
}

// Use import.meta.env for Vite compatibility
const profile = normalizeProfile(
  import.meta.env.VITE_CAPACITOR_PROFILE ||
  import.meta.env.VITE_APP_ENV ||
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

// bundledWebRuntime is not a valid CapacitorConfig property and has been removed
const config: CapacitorConfig = {
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
