const fs = require('fs');
const path = require('path');

const configPath = path.resolve(__dirname, 'server.config.json');
const defaultConfig = {
  server: {
    host: '127.0.0.1',
    port: 8080,
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
};

const devServerHost = process.env.VUE_APP_HOST || mergedConfig.server.host;
const devServerPort = Number(process.env.VUE_APP_PORT || mergedConfig.server.port);
const backendUrl = process.env.VUE_APP_BACKEND_URL || mergedConfig.api.backendUrl;

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
    historyApiFallback: {
      rewrites: [
        { from: /^\/admin/, to: '/admin.html' },
      ],
    },
  },
};
