import { Capacitor } from '@capacitor/core';

function sanitizeBaseUrl(rawUrl) {
  return String(rawUrl || '').trim().replace(/\/+$/, '');
}

function configuredBaseUrl() {
  const fromMobileEnv = import.meta.env?.VITE_MOBILE_BACKEND_URL;
  const fromGeneralEnv = import.meta.env?.VITE_BACKEND_URL || import.meta.env?.VUE_APP_BACKEND_URL;
  return sanitizeBaseUrl(fromMobileEnv || fromGeneralEnv || '');
}

function nativeDefaultBaseUrl() {
  const platform = Capacitor.getPlatform();
  if (platform === 'android') {
    return 'http://10.0.2.2:5050';
  }
  if (platform === 'ios') {
    return 'http://localhost:5050';
  }
  return 'http://localhost:5050';
}

export function resolveApiBaseUrl() {
  const configured = configuredBaseUrl();
  if (configured) return configured;

  if (Capacitor.isNativePlatform()) {
    return nativeDefaultBaseUrl();
  }

  return `${window.location.origin}/api`;
}

export function getMobileBackendConfigHint() {
  return {
    variable: 'VITE_MOBILE_BACKEND_URL',
    example: 'https://your-host-or-proxy.example.com/api',
  };
}
