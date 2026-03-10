const fs = require('fs');
const path = require('path');

const configPath = path.resolve(__dirname, 'server.config.json');
const defaultConfig = {
  server: {
    host: '127.0.0.1',
    port: 8080,
  },
  tls: {
    enabled: false,
    certFile: '',
    keyFile: '',
  },
  api: {
    backendUrl: 'http://127.0.0.1:5050',
  },
};

let fileConfig = {};
if (fs.existsSync(configPath)) {
  try {
    fileConfig = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  } catch (error) {
    console.warn('Unable to parse frontend/server.config.json, using defaults.', error.message);
  }
}

const mergedConfig = {
  ...defaultConfig,
  ...fileConfig,
  server: {
    ...defaultConfig.server,
    ...(fileConfig.server || {}),
  },
  api: {
    ...defaultConfig.api,
    ...(fileConfig.api || {}),
  },
  tls: {
    ...defaultConfig.tls,
    ...(fileConfig.tls || {}),
  },
};

const devServerHost = process.env.VUE_APP_HOST || mergedConfig.server.host;
const devServerPort = Number(process.env.VUE_APP_PORT || mergedConfig.server.port);
const backendUrl = process.env.VUE_APP_BACKEND_URL || mergedConfig.api.backendUrl;

const envTlsEnabledRaw = String(process.env.VUE_APP_TLS_ENABLED || '').trim().toLowerCase();
const envTlsEnabled = envTlsEnabledRaw
  ? ['1', 'true', 'yes', 'on'].includes(envTlsEnabledRaw)
  : null;
const envTlsCertFile = String(process.env.VUE_APP_TLS_CERT_FILE || '').trim();
const envTlsKeyFile = String(process.env.VUE_APP_TLS_KEY_FILE || '').trim();

const effectiveTls = {
  ...mergedConfig.tls,
  ...(envTlsEnabled === null ? {} : { enabled: envTlsEnabled }),
  ...(envTlsCertFile ? { certFile: envTlsCertFile } : {}),
  ...(envTlsKeyFile ? { keyFile: envTlsKeyFile } : {}),
};

let devServerHttps = false;
if (effectiveTls && effectiveTls.enabled) {
  const certFile = String(effectiveTls.certFile || '').trim();
  const keyFile = String(effectiveTls.keyFile || '').trim();
  if (certFile && keyFile) {
    const certPath = path.isAbsolute(certFile) ? certFile : path.resolve(__dirname, certFile);
    const keyPath = path.isAbsolute(keyFile) ? keyFile : path.resolve(__dirname, keyFile);
    if (fs.existsSync(certPath) && fs.existsSync(keyPath)) {
      devServerHttps = {
        cert: fs.readFileSync(certPath),
        key: fs.readFileSync(keyPath),
      };
    } else {
      console.warn('Frontend TLS enabled but cert/key file not found; falling back to HTTPS with generated cert.');
      devServerHttps = true;
    }
  } else {
    devServerHttps = true;
  }
}

process.env.VUE_APP_BACKEND_URL = backendUrl;

module.exports = {
  pages: {
    index: {
      entry: 'src/main.js',
      template: 'index.html',
      filename: 'index.html',
      title: 'HookLineandSinker',
    },
    admin: {
      entry: 'src/admin.js',
      template: 'index.html',
      filename: 'admin.html',
      title: 'HLaS Admin',
    },
  },
  devServer: {
    host: devServerHost,
    port: devServerPort,
    https: devServerHttps,
    historyApiFallback: {
      rewrites: [
        { from: /^\/admin/, to: '/admin.html' },
      ],
    },
  },
};
