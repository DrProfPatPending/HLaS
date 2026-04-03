import axios from 'axios';

export const API_BASE_URL =
  window.API_BASE_URL ||
  (window.location.origin.includes('localhost')
    ? 'http://localhost:5000/api'
    : '/api');

export function adminUrl(path) {
  return `${API_BASE_URL}${path}`;
}

export function getAdminToken() {
  return localStorage.getItem('hlasAdminToken');
}

export function setAdminToken(token) {
  localStorage.setItem('hlasAdminToken', token);
}

export function clearAdminToken() {
  localStorage.removeItem('hlasAdminToken');
}

export function authHeaders() {
  const token = getAdminToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function withAdminHeaders(config = {}) {
  return {
    ...config,
    headers: {
      ...authHeaders(),
      ...(config.headers || {}),
    },
  };
}

export function adminGet(path, config = {}) {
  return axios.get(adminUrl(path), withAdminHeaders(config));
}

export function adminPost(path, data = {}, config = {}) {
  return axios.post(adminUrl(path), data, withAdminHeaders(config));
}

export function adminPut(path, data = {}, config = {}) {
  return axios.put(adminUrl(path), data, withAdminHeaders(config));
}

export function adminDelete(path, config = {}) {
  return axios.delete(adminUrl(path), withAdminHeaders(config));
}
