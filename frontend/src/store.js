// ---------------------------------------------------------------------------
// Field Order Config (shared)
// ---------------------------------------------------------------------------
export const fieldOrderConfig = reactive({
  loaded: false,
  contexts: [],
  order: {},
});

export function loadFieldOrderConfig() {
  return axios.get(`${API_BASE_URL}/admin/field-order`)
    .then(res => {
      fieldOrderConfig.order = res.data.field_order || {};
      fieldOrderConfig.contexts = Object.keys(fieldOrderConfig.order);
      fieldOrderConfig.loaded = true;
    })
    .catch(() => {
      fieldOrderConfig.loaded = false;
    });
}
import { reactive, computed } from 'vue';
import axios from 'axios';
import { applyThemeVariables, resolveThemeVariables } from './theme.js';
import { resolveApiBaseUrl } from './mobile/api-base.js';

export const API_BASE_URL = resolveApiBaseUrl();

const MEMBER_SESSION_STORAGE_KEY = 'hlas.memberSession';

function extractPreferredClubFromUrl() {
  try {
    const params = new URLSearchParams(window.location.search || '');
    const clubFromQuery = (params.get('club') || '').trim();
    if (clubFromQuery) return clubFromQuery;

    const match = String(window.location.pathname || '').match(/^\/clubs?\/([^/]+)/i);
    if (!match || !match[1]) return '';
    return decodeURIComponent(match[1]).trim();
  } catch {
    return '';
  }
}

const URL_PREFERRED_CLUB = extractPreferredClubFromUrl();
const DEFAULT_LOGIN_CLUB = URL_PREFERRED_CLUB || 'TEST';

export const MY_CLUB_TABS = [
  { id: 'personal', label: 'Personal Info' },
  { id: 'address', label: 'Address Info' },
  { id: 'security', label: 'Login/Security Details' },
  { id: 'status', label: 'Status Flags' },
];

// ---------------------------------------------------------------------------
// Reactive shared state
// ---------------------------------------------------------------------------
export const store = reactive({
  apiBaseUrl: API_BASE_URL,
  appDateFormat: 'DD/MM/YY',
  appSettings: {},
  clubSettings: {},
  activeThemeVariables: {},
  activeThemeClub: '',

  // Auth
  loggedIn: false,
  loggedInUser: null,
  memberAuthToken: '',
  memberRefreshToken: '',
  memberRoles: [],
  memberPermissions: [],
  authInterceptorId: null,
  refreshRequestPromise: null,

  // Session identity
  loggedInUsername: '',
  loggedInClub: DEFAULT_LOGIN_CLUB,

  // Login form
  selectedClub: DEFAULT_LOGIN_CLUB,
  loginUsername: '',
  loginPassword: '',
  loginError: '',

  // Navigation
  activeSection: 'home',
  accessError: '',
  myClubActiveTab: 'personal',

  // Club list
  clubs: [],

  // Member list (shared between MembershipAdmin and MemberEdit)
  members: [],
  totalMembers: 0,
  currentPage: 1,
  pageSize: 10,
  sortKey: 'ID',
  sortOrder: 'asc',
  filterDebounceTimer: null,
  filterDebounceMs: 250,
  columnFilters: {
    ID: '',
    Number: '',
    Members_Name: '',
    Title: '',
    First_Name: '',
    Last_Name: '',
    Photo_Path: '',
    Preferred_Name: '',
    First_Names: '',
    Member_Type: '',
    Subs_Expected: '',
    Subs_paid: '',
    Join_Fee: '',
    Paid_Up_2026: '',
    Photo_Received: '',
    In_WhatsApp: '',
    In_FB: '',
    Date_of_Birth: '',
    Age: '',
    New_Member_2026: '',
    Paid_up_Card_Sent: '',
    CR2023: '',
    CR2024: '',
    CR2025: '',
    Details_Confirmed_2026: '',
    Full_Address: '',
    Address___Street_Address: '',
    Address___Address_Line_2: '',
    Address___City: '',
    County: '',
    'Address___State/Prov/Region': '',
    'Address___ZIP/Postal': '',
    Address___Country: '',
    Phone: '',
    Paused: '',
    E_Mail: '',
    Mobile: '',
    Car_Reg: '',
    EA_Licence: '',
    Licence_Exp: '',
    username: '',
    Resigned: '',
  },

  // Member lookup (shown inside MembershipAdmin)
  showMembershipDetails: false,
  lookupNumber: '',
  lookupResult: null,
  lookupError: '',

  // Member edit (shared between MembershipAdmin opener and MemberEdit form)
  editMemberData: {},
  editMemberId: null,
  editNavigationMembers: [],
  newPassword: '',
  confirmPassword: '',
  passwordError: '',
});

// ---------------------------------------------------------------------------
// Computed properties shared across components
// ---------------------------------------------------------------------------
export const clubDetails = computed(() => {
  // For admin/system users, allow no club context
  const activeClubShortName = store.loggedInClub || store.selectedClub;
  let matchedClub = store.clubs.find(c => c.shortName === activeClubShortName);
  if (!matchedClub && store.clubs.length > 0) {
    // If no match, but clubs exist, use the first club as fallback
    matchedClub = store.clubs[0];
  }
  if (!matchedClub) {
    // No clubs at all: return ADMIN dummy club for admin/system users
    return {
      fullName: 'Application Administration',
      shortName: 'ADMIN',
      websiteUrl: '',
      adminEmail: '',
      description: 'Global admin context',
      logoUrl: '',
      whatsappGroups: '',
      socialMedia: [],
      officers: [],
      beats: [],
    };
  }
  return {
    fullName: matchedClub.fullName || activeClubShortName || 'Club Information',
    shortName: matchedClub.shortName || activeClubShortName || '',
    websiteUrl: matchedClub.websiteUrl || '',
    adminEmail: matchedClub.adminEmail || '',
    description: matchedClub.description || '',
    logoUrl: matchedClub.logoUrl || '',
    whatsappGroups: matchedClub.whatsappGroups || '',
    socialMedia: Array.isArray(matchedClub.socialMedia) ? matchedClub.socialMedia : [],
    officers: Array.isArray(matchedClub.officers) ? matchedClub.officers : [],
    beats: Array.isArray(matchedClub.beats) ? matchedClub.beats : [],
  };
});

export const clubLogoSrc = computed(() => {
  if (clubDetails.value.logoUrl) {
    if (/^https?:\/\//i.test(clubDetails.value.logoUrl)) {
      return clubDetails.value.logoUrl;
    }
    const url = clubDetails.value.logoUrl;
    return `${API_BASE_URL}${url.startsWith('/') ? '' : '/'}${url}`;
  }
  // Return empty string if no logo URL - let frontend handle missing logo gracefully
  return '';
});

export const totalPages = computed(() =>
  Math.max(1, Math.ceil(store.totalMembers / store.pageSize))
);

export const visiblePages = computed(() => {
  const current = store.currentPage;
  const total = totalPages.value;
  const pageCount = 5;
  let start, end;
  if (current <= 3) {
    start = 1;
    end = Math.min(pageCount, total);
  } else {
    start = current - 2;
    end = current + 2;
    if (end > total) {
      end = total;
      start = Math.max(1, end - pageCount + 1);
    }
  }
  const pages = [];
  for (let i = start; i <= end; i++) pages.push(i);
  return pages;
});

export const canAccessMembershipAdmin = computed(() =>
  store.memberPermissions.includes('member.club.list')
);

export const canAccessNewsletters = computed(() =>
  store.memberPermissions.includes('newsletter.send')
);

export const editMemberIndex = computed(() => {
  if (!store.editNavigationMembers.length || store.editMemberId == null) return -1;
  return store.editNavigationMembers.findIndex(m => memberIdentity(m) === store.editMemberId);
});

export const hasPreviousEditMember = computed(() => editMemberIndex.value > 0);

export const hasNextEditMember = computed(() =>
  editMemberIndex.value >= 0 && editMemberIndex.value < store.editNavigationMembers.length - 1
);

export const editMemberPositionLabel = computed(() => {
  if (editMemberIndex.value < 0 || !store.editNavigationMembers.length) return '';
  return `Member ${editMemberIndex.value + 1} of ${store.editNavigationMembers.length}`;
});

export const remainingEditMemberKeys = computed(() => {
  const keys = Object.keys(store.editMemberData);
  const excludeKeys = ['username', 'password'];
  return keys.filter(k => !excludeKeys.includes(k));
});

// ---------------------------------------------------------------------------
// Utility helpers
// ---------------------------------------------------------------------------
export function memberIdentity(member) {
  return member && (member.id || member.ID || member.Number);
}

export function formatFieldName(fieldName) {
  return fieldName.replace(/__/g, '::').replace(/_/g, ' ');
}

const SHORT_MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function isLicenceExpiryField(field) {
  const normalized = String(field || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  return normalized === 'licenceexp' || normalized === 'licenceexpiry' || normalized === 'licenseexp' || normalized === 'licenseexpiry';
}

export function isDateFieldName(field) {
  const normalized = String(field || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  return normalized === 'date' || normalized === 'sessiondate' || normalized.endsWith('date');
}

export function formatDateWithPattern(dateIso, pattern = store.appDateFormat) {
  const normalized = normalizeDateInputValue(dateIso);
  if (!normalized) return String(dateIso || '');
  const [year, month, day] = normalized.split('-');
  if (!year || !month || !day) {
    return String(dateIso || '');
  }
  const monthNumber = Number(month);
  const monthLabel = SHORT_MONTH_NAMES[monthNumber - 1] || month;
  const yy = year.slice(-2);

  switch (pattern) {
    case 'DD/MM/YY':
      return `${day}/${month}/${yy}`;
    case 'DD/MM/YYYY':
      return `${day}/${month}/${year}`;
    case 'DD-MMM-YYYY':
      return `${day}-${monthLabel}-${year}`;
    case 'YYYY-MM-DD':
      return `${year}-${month}-${day}`;
    case 'MMM DD, YYYY':
      return `${monthLabel} ${day}, ${year}`;
    case 'DD MMM YYYY':
      return `${day} ${monthLabel} ${year}`;
    case 'MM/DD/YYYY':
      return `${month}/${day}/${year}`;
    default:
      return normalized;
  }
}

export function formatConfiguredDate(value, fieldName = '') {
  if (value === null || value === undefined || value === '') {
    return value;
  }

  if (!isDateOfBirthField(fieldName) && !isLicenceExpiryField(fieldName) && !isDateFieldName(fieldName)) {
    return value;
  }

  const normalized = normalizeDateInputValue(value);
  if (!normalized) {
    return value;
  }
  return formatDateWithPattern(normalized);
}

export function loadAppSettings() {
  return axios.get(`${API_BASE_URL}/app-settings`)
    .then(res => {
      const settings = res?.data?.settings || {};
      store.appSettings = settings;
      const dateFormat = String(settings.dateFormat || '').trim();
      if (dateFormat) {
        store.appDateFormat = dateFormat;
      }
      syncActiveTheme();
    })
    .catch(() => {
      store.appDateFormat = store.appDateFormat || 'DD/MM/YY';
      store.appSettings = {};
      syncActiveTheme();
    });
}

export function resolveDefaultLoginClub(clubs = null) {
  const clubsList = clubs || (Array.isArray(store.clubs) ? store.clubs : []);
  
  // Priority 1: URL-specified club
  if (URL_PREFERRED_CLUB) {
    const matchedClub = clubsList.find(
      club => String(club.shortName || '').toLowerCase() === URL_PREFERRED_CLUB.toLowerCase()
    );
    if (matchedClub) {
      return matchedClub.shortName;
    }
  }
  
  // Priority 2: Admin-configured default club
  const configuredDefault = String(store.appSettings?.defaultClub || '').trim();
  if (configuredDefault) {
    const matchedClub = clubsList.find(
      club => club.shortName === configuredDefault
    );
    if (matchedClub) {
      return matchedClub.shortName;
    }
  }
  
  // Priority 3: First alphabetical club
  if (clubsList.length > 0) {
    const sorted = [...clubsList].sort((a, b) => {
      const aName = String(a.shortName || '').toUpperCase();
      const bName = String(b.shortName || '').toUpperCase();
      return aName.localeCompare(bName);
    });
    return sorted[0].shortName;
  }
  
  // Fallback to hardcoded default
  return DEFAULT_LOGIN_CLUB;
}

export function syncActiveTheme() {
  const activeClub = String(store.loggedIn ? store.loggedInClub : store.selectedClub).trim();
  const normalizedActiveClub = activeClub.toLowerCase();

  const matchedClub = Array.isArray(store.clubs)
    ? store.clubs.find(club => String(club?.shortName || '').trim().toLowerCase() === normalizedActiveClub) || null
    : null;

  const resolvedThemeVariables = resolveThemeVariables({
    appSettings: store.appSettings,
    clubSettings: store.clubSettings,
    activeClub,
    matchedClub,
  });

  store.activeThemeClub = activeClub;
  store.activeThemeVariables = resolvedThemeVariables;
  applyThemeVariables(resolvedThemeVariables);
}

export function isDateOfBirthField(field) {
  const normalized = String(field || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  return normalized === 'dob' || normalized.includes('dateofbirth');
}

export function isAgeField(field) {
  const normalized = String(field || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  return normalized === 'age';
}

export function calculateAgeFromDOB(dob) {
  if (!dob) return '';
  const birth = new Date(dob);
  if (isNaN(birth.getTime())) return '';
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
  return age >= 0 ? String(age) : '';
}

export function normalizeDateInputValue(value) {
  const raw = String(value || '').trim();
  if (!raw) {
    return '';
  }

  const normalizeExcelSerialDate = serialText => {
    if (!/^\d{5}(?:\.0+)?$/.test(serialText)) {
      return '';
    }
    const serial = Number.parseInt(serialText, 10);
    if (!Number.isFinite(serial) || serial < 1 || serial > 80000) {
      return '';
    }
    const excelEpochUtc = Date.UTC(1899, 11, 30);
    const normalizedDate = new Date(excelEpochUtc + serial * 24 * 60 * 60 * 1000);
    if (Number.isNaN(normalizedDate.getTime())) {
      return '';
    }
    return normalizedDate.toISOString().slice(0, 10);
  };

  const normalizeTwoDigitYear = yy => {
    const yearNumber = Number(yy);
    if (!Number.isFinite(yearNumber)) return '';
    return yearNumber >= 50 ? `19${String(yy).padStart(2, '0')}` : `20${String(yy).padStart(2, '0')}`;
  };

  const excelSerialDate = normalizeExcelSerialDate(raw);
  if (excelSerialDate) {
    return excelSerialDate;
  }

  if (/^\d{4}-\d{2}-\d{2}/.test(raw)) {
    return raw.slice(0, 10);
  }
  if (/^\d{4}-\d{2}$/.test(raw)) {
    return `${raw}-01`;
  }
  if (/^\d{4}\/\d{2}$/.test(raw)) {
    const [year, month] = raw.split('/');
    return `${year}-${month}-01`;
  }
  if (/^\d{2}\/\d{4}$/.test(raw)) {
    const [month, year] = raw.split('/');
    return `${year}-${month}-01`;
  }
  if (/^\d{2}-\d{4}$/.test(raw)) {
    const [month, year] = raw.split('-');
    return `${year}-${month}-01`;
  }
  if (/^\d{2}\/\d{2}$/.test(raw)) {
    const [month, yy] = raw.split('/');
    const year = normalizeTwoDigitYear(yy);
    return year ? `${year}-${month}-01` : '';
  }
  if (/^\d{2}-\d{2}$/.test(raw)) {
    const [month, yy] = raw.split('-');
    const year = normalizeTwoDigitYear(yy);
    return year ? `${year}-${month}-01` : '';
  }
  if (/^\d{2}\/\d{2}\/\d{4}$/.test(raw)) {
    const [day, month, year] = raw.split('/');
    return `${year}-${month}-${day}`;
  }
  if (/^\d{2}\/\d{2}\/\d{2}$/.test(raw)) {
    const [day, month, yy] = raw.split('/');
    const year = normalizeTwoDigitYear(yy);
    return year ? `${year}-${month}-${day}` : '';
  }
  if (/^\d{2}-\d{2}-\d{4}$/.test(raw)) {
    const [day, month, year] = raw.split('-');
    return `${year}-${month}-${day}`;
  }
  if (/^\d{2}-\d{2}-\d{2}$/.test(raw)) {
    const [day, month, yy] = raw.split('-');
    const year = normalizeTwoDigitYear(yy);
    return year ? `${year}-${month}-${day}` : '';
  }
  const parsed = new Date(raw);
  if (!Number.isNaN(parsed.getTime())) {
    return parsed.toISOString().slice(0, 10);
  }
  return '';
}

export function getExpiryDateStyle(dateString) {
  if (!dateString) return {};
  if (dateString.toLowerCase() === 'n/a') return { color: 'green' };
  try {
    const normalized = normalizeDateInputValue(dateString) || dateString;
    const expiryDate = new Date(normalized);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    expiryDate.setHours(0, 0, 0, 0);
    return expiryDate < today ? { color: 'red' } : { color: 'black' };
  } catch {
    return {};
  }
}

export function sectionDisplayName(sectionKey) {
  const names = {
    'club-information': 'Club Information',
    'club-settings': 'Club Settings',
    'my-club': 'My Club',
    'club-store': 'Club Store',
    newsletters: 'News and Updates',
    'fishing-beats': 'Fishing Beats',
    'beat-details': 'Beat Details',
    'catch-return': 'Catch Return',
    'member-edit': 'Edit Member',
  };
  return names[sectionKey] || 'Home';
}

// ---------------------------------------------------------------------------
// Auth helpers
// ---------------------------------------------------------------------------
function normalizeStringList(values) {
  if (!Array.isArray(values)) return [];
  return values
    .filter(v => typeof v === 'string')
    .map(v => v.trim())
    .filter(Boolean);
}

export function applyMemberAuthHeader() {
  if (store.memberAuthToken) {
    axios.defaults.headers.common.Authorization = `Bearer ${store.memberAuthToken}`;
  } else {
    delete axios.defaults.headers.common.Authorization;
  }
}

export function setMemberTokens(accessToken, refreshToken) {
  store.memberAuthToken = accessToken || '';
  store.memberRefreshToken = refreshToken || '';
  applyMemberAuthHeader();
  persistMemberSession();
}

export function setMemberAuthz(roles, permissions) {
  store.memberRoles = normalizeStringList(roles);
  store.memberPermissions = normalizeStringList(permissions);
  persistMemberSession();
}

export function persistMemberSession() {
  try {
    const payload = {
      loggedIn: Boolean(store.loggedIn),
      loggedInUsername: store.loggedInUsername || '',
      loggedInClub: store.loggedInClub || store.selectedClub || 'TEST',
      loggedInUser: store.loggedInUser || null,
      memberAuthToken: store.memberAuthToken || '',
      memberRefreshToken: store.memberRefreshToken || '',
      memberRoles: store.memberRoles || [],
      memberPermissions: store.memberPermissions || [],
    };
    window.localStorage.setItem(MEMBER_SESSION_STORAGE_KEY, JSON.stringify(payload));
  } catch { /* ignore */ }
}

export function clearMemberSession() {
  try {
    window.localStorage.removeItem(MEMBER_SESSION_STORAGE_KEY);
  } catch { /* ignore */ }
}

export function restoreMemberSession() {
  try {
    const raw = window.localStorage.getItem(MEMBER_SESSION_STORAGE_KEY);
    if (!raw) return;
    const payload = JSON.parse(raw);
    if (!payload || payload.loggedIn !== true || !payload.memberAuthToken || !payload.memberRefreshToken) return;

    const restoredClub =
      typeof payload.loggedInClub === 'string' && payload.loggedInClub.trim()
        ? payload.loggedInClub.trim()
        : 'TEST';

    store.loggedIn = true;
    store.loggedInUsername = typeof payload.loggedInUsername === 'string' ? payload.loggedInUsername : '';
    store.loggedInClub = restoredClub;
    store.selectedClub = restoredClub;
    store.loggedInUser = payload.loggedInUser || null;
    store.memberAuthToken = typeof payload.memberAuthToken === 'string' ? payload.memberAuthToken : '';
    store.memberRefreshToken = typeof payload.memberRefreshToken === 'string' ? payload.memberRefreshToken : '';
    store.memberRoles = normalizeStringList(payload.memberRoles);
    store.memberPermissions = normalizeStringList(payload.memberPermissions);
    syncActiveTheme();
  } catch {
    clearMemberSession();
  }
}

export function handleAuthSessionExpired() {
  store.loggedIn = false;
  store.loggedInUser = null;
  store.memberAuthToken = '';
  store.memberRefreshToken = '';
  store.memberRoles = [];
  store.memberPermissions = [];
  store.loggedInUsername = '';
  applyMemberAuthHeader();
  clearMemberSession();
  store.loginError = 'Session expired. Please log in again.';
  store.accessError = '';
}

export async function refreshMemberAuthToken() {
  if (!store.memberRefreshToken) throw new Error('Missing refresh token');

  if (store.refreshRequestPromise) return store.refreshRequestPromise;

  store.refreshRequestPromise = axios
    .post(
      `${API_BASE_URL}/token/refresh`,
      { refreshToken: store.memberRefreshToken },
      { skipAuthRefresh: true }
    )
    .then(response => {
      const data = response && response.data ? response.data : {};
      if (!data.token || !data.refreshToken) {
        throw new Error('Invalid refresh response payload');
      }
      setMemberTokens(data.token, data.refreshToken);
    })
    .finally(() => {
      store.refreshRequestPromise = null;
    });

  return store.refreshRequestPromise;
}

export function initializeAuthInterceptor() {
  if (store.authInterceptorId !== null) return;

  store.authInterceptorId = axios.interceptors.response.use(
    response => response,
    async error => {
      const statusCode = error && error.response ? error.response.status : 0;
      const originalRequest = error && error.config ? error.config : null;

      if (!originalRequest || statusCode !== 401) return Promise.reject(error);

      const requestUrl = String(originalRequest.url || '');
      const skipRefresh =
        Boolean(originalRequest.skipAuthRefresh) ||
        requestUrl.includes('/login') ||
        requestUrl.includes('/logout') ||
        requestUrl.includes('/token/refresh');

      if (skipRefresh || originalRequest._retry || !store.memberRefreshToken || !store.loggedIn) {
        return Promise.reject(error);
      }

      originalRequest._retry = true;
      try {
        await refreshMemberAuthToken();
        originalRequest.headers = originalRequest.headers || {};
        originalRequest.headers.Authorization = `Bearer ${store.memberAuthToken}`;
        return axios(originalRequest);
      } catch (refreshError) {
        handleAuthSessionExpired();
        return Promise.reject(refreshError);
      }
    }
  );
}

export function teardownAuthInterceptor() {
  if (store.authInterceptorId !== null) {
    axios.interceptors.response.eject(store.authInterceptorId);
    store.authInterceptorId = null;
  }
}

// ---------------------------------------------------------------------------
// Club loading
// ---------------------------------------------------------------------------
export function loadClubs() {
  const normalizeAndApplyClubs = clubs => {
    const sortedClubs = [...clubs].sort((a, b) => {
      const aName = String(a.shortName || '').toUpperCase();
      const bName = String(b.shortName || '').toUpperCase();
      return aName.localeCompare(bName);
    });

    store.clubs = sortedClubs;
    store.selectedClub = resolveDefaultLoginClub(sortedClubs);
    syncActiveTheme();
  };

  const tryFallbackApiRoute = async () => {
    const normalizedBase = String(API_BASE_URL || '').trim().replace(/\/+$/, '');
    if (/\/api$/i.test(normalizedBase)) {
      return [];
    }
    const fallbackResponse = await axios.get(`${normalizedBase}/api/clubs`);
    return Array.isArray(fallbackResponse.data?.clubs) ? fallbackResponse.data.clubs : [];
  };

  return axios.get(`${API_BASE_URL}/clubs`).then(async res => {
    const primaryClubs = Array.isArray(res.data?.clubs) ? res.data.clubs : null;
    if (primaryClubs !== null) {
      normalizeAndApplyClubs(primaryClubs);
      return;
    }

    const contentType = String(res.headers?.['content-type'] || '').toLowerCase();
    if (contentType.includes('text/html')) {
      try {
        const fallbackClubs = await tryFallbackApiRoute();
        normalizeAndApplyClubs(fallbackClubs);
        return;
      } catch {
      }
    }

    normalizeAndApplyClubs([]);
  }).catch(() => {
    store.clubs = [];
    syncActiveTheme();
  });
}

function buildActiveMemberFilters() {
  return Object.fromEntries(
    Object.entries(store.columnFilters)
      .filter(([, v]) => v && v.trim() !== '')
      .map(([key, v]) => {
        const trimmed = v.trim();
        if (trimmed === '[BLANK]') return [key, '[BLANK]'];
        const hasWildcard = trimmed.includes('*') || trimmed.includes('?');
        return [key, hasWildcard ? trimmed : `*${trimmed}*`];
      })
  );
}

function buildMemberQueryParams({ limit, offset }) {
  const activeFilters = buildActiveMemberFilters();
  const params = { club: store.loggedInClub, limit, offset, ...activeFilters };
  if (store.sortKey) {
    params.sort_by = store.sortKey;
    params.sort_order = store.sortOrder;
  }
  return params;
}

function loadEditNavigationMembers() {
  const limit = Math.max(store.totalMembers || 0, store.pageSize || 0, 1);
  const params = buildMemberQueryParams({ limit, offset: 0 });

  return axios.get(`${API_BASE_URL}/members`, { params })
    .then(res => {
      const members = Array.isArray(res.data?.members) ? res.data.members : [];
      store.editNavigationMembers = members;
      return members;
    })
    .catch(() => {
      store.editNavigationMembers = [...store.members];
      return store.editNavigationMembers;
    });
}
export function login() {
  store.loginError = '';
  axios
    .post(`${API_BASE_URL}/login`, {
      username: store.loginUsername,
      password: store.loginPassword,
      club: store.selectedClub,
    })
    .then(res => {
      if (res.data.success) {
        if (!res.data.token || !res.data.refreshToken) {
          store.loginError = 'Login failed: missing session token';
          return;
        }
        store.loggedIn = true;
        store.loggedInUser = res.data.user;
        setMemberTokens(res.data.token, res.data.refreshToken);
        setMemberAuthz(res.data.roles, res.data.permissions);
        store.loggedInUsername = store.loginUsername;
        store.loggedInClub = store.selectedClub;
        store.activeSection = 'home';
        store.currentPage = 1;
        store.accessError = '';
        syncActiveTheme();
        if (store.memberPermissions.includes('member.club.list')) {
          fetchMembers();
        }
        // Persist session before redirecting
        persistMemberSession();
        // Redirect after successful login
        setTimeout(() => {
          // Always redirect to main app dashboard, not back to mini site
          window.location.href = '/index.html';
        }, 100);
      } else {
        store.loginError = res.data.error || 'Login failed';
      }
    })
    .catch(err => {
      store.loginError =
        err.response && err.response.data && err.response.data.error
          ? err.response.data.error
          : 'Login failed';
    });
}

export function logout() {
  if (store.memberAuthToken) {
    axios
      .post(
        `${API_BASE_URL}/logout`,
        { refreshToken: store.memberRefreshToken },
        { headers: { Authorization: `Bearer ${store.memberAuthToken}` }, skipAuthRefresh: true }
      )
      .catch(() => { /* ignore */ });
  }
  store.loggedIn = false;
  store.loggedInUser = null;
  store.memberAuthToken = '';
  store.memberRefreshToken = '';
  store.memberRoles = [];
  store.memberPermissions = [];
  store.loggedInUsername = '';
  applyMemberAuthHeader();
  clearMemberSession();
  store.activeSection = 'home';
  store.accessError = '';
  store.loginPassword = '';
  store.members = [];
  store.totalMembers = 0;
  syncActiveTheme();
  store.currentPage = 1;
  store.lookupNumber = '';
  store.lookupResult = null;
  store.lookupError = '';
}

// ---------------------------------------------------------------------------
// Member data actions
// ---------------------------------------------------------------------------
export function fetchMembers() {
  const offset = (store.currentPage - 1) * store.pageSize;
  const activeFilters = Object.fromEntries(
    Object.entries(store.columnFilters)
      .filter(([, v]) => v && v.trim() !== '')
      .map(([key, v]) => {
        const trimmed = v.trim();
        if (trimmed === '[BLANK]') return [key, '[BLANK]'];
        const hasWildcard = trimmed.includes('*') || trimmed.includes('?');
        return [key, hasWildcard ? trimmed : `*${trimmed}*`];
      })
  );

  const params = { club: store.loggedInClub, limit: store.pageSize, offset, ...activeFilters };
  if (store.sortKey) {
    params.sort_by = store.sortKey;
    params.sort_order = store.sortOrder;
  }

  axios.get(`${API_BASE_URL}/members`, { params }).then(res => {
    store.members = res.data.members;
    store.totalMembers = res.data.total;
  }).catch(err => {
    if (err.response?.status === 403) {
      store.members = [];
      store.totalMembers = 0;
      store.accessError = 'You do not have permission to view club members.';
      store.activeSection = 'home';
    }
  });
}

export function onFilterChange() {
  store.currentPage = 1;
  if (store.filterDebounceTimer) clearTimeout(store.filterDebounceTimer);
  store.filterDebounceTimer = setTimeout(() => fetchMembers(), store.filterDebounceMs);
}

export function setSort(key, order) {
  store.sortKey = key;
  store.sortOrder = order;
  store.currentPage = 1;
  fetchMembers();
}

export function nextPage() {
  if (store.currentPage < totalPages.value) { store.currentPage++; fetchMembers(); }
}
export function prevPage() {
  if (store.currentPage > 1) { store.currentPage--; fetchMembers(); }
}
export function firstPage() { store.currentPage = 1; fetchMembers(); }
export function lastPage() { store.currentPage = totalPages.value; fetchMembers(); }
export function goToPage(pageNum) { store.currentPage = pageNum; fetchMembers(); }
export function onPageSizeChange() { store.currentPage = 1; fetchMembers(); }

// ---------------------------------------------------------------------------
// Member lookup
// ---------------------------------------------------------------------------
export function lookupMember() {
  store.lookupResult = null;
  store.lookupError = '';
  axios
    .get(
      `${API_BASE_URL}/member_by_number/${encodeURIComponent(store.lookupNumber)}?club=${store.loggedInClub}`
    )
    .then(res => { store.lookupResult = res.data; })
    .catch(err => {
      store.lookupError =
        err.response && err.response.data && err.response.data.error
          ? err.response.data.error
          : 'Error retrieving member';
    });
}

export function lookupMemberByNumber(number) {
  store.showMembershipDetails = true;
  store.lookupNumber = number;
  lookupMember();
}

export function hideLookupDetails() {
  store.showMembershipDetails = false;
  store.lookupNumber = '';
  store.lookupResult = null;
  store.lookupError = '';
}

// ---------------------------------------------------------------------------
// Member edit actions
// ---------------------------------------------------------------------------
export function selectMemberForEdit(member) {
  store.editNavigationMembers = [...store.members];
  store.editMemberData = { ...member };
  store.editMemberId = memberIdentity(member);
  store.newPassword = '';
  store.confirmPassword = '';
  store.passwordError = '';
  store.activeSection = 'member-edit';
}

export function openMemberForEdit(member) {
  return loadEditNavigationMembers().finally(() => {
    const identity = memberIdentity(member);
    const selected = store.editNavigationMembers.find(m => memberIdentity(m) === identity) || member;
    store.editMemberData = { ...selected };
    store.editMemberId = memberIdentity(selected);
    store.newPassword = '';
    store.confirmPassword = '';
    store.passwordError = '';
    store.activeSection = 'member-edit';
  });
}

export function navigateEditMember(direction) {
  const targetIndex = editMemberIndex.value + direction;
  if (targetIndex < 0 || targetIndex >= store.editNavigationMembers.length) return;
  const targetMember = store.editNavigationMembers[targetIndex];
  store.editMemberData = { ...targetMember };
  store.editMemberId = memberIdentity(targetMember);
  store.newPassword = '';
  store.confirmPassword = '';
  store.passwordError = '';
}

export function updateMember() {
  if (store.newPassword || store.confirmPassword) {
    if (store.newPassword !== store.confirmPassword) {
      store.passwordError = 'Passwords do not match';
      return;
    }
    if (store.newPassword.length === 0) {
      store.passwordError = 'Password cannot be empty';
      return;
    }
  }
  store.passwordError = '';

  const memberData = { ...store.editMemberData, club: store.loggedInClub };
  if (store.newPassword) memberData.password = store.newPassword;

  axios.put(`${API_BASE_URL}/members/${store.editMemberId}`, memberData).then(() => {
    fetchMembers();
    store.activeSection = 'membership-admin';
    store.editMemberData = {};
    store.editMemberId = null;
    store.newPassword = '';
    store.confirmPassword = '';
    store.passwordError = '';
  }).catch(err => {
    store.passwordError =
      err.response && err.response.data && err.response.data.error
        ? err.response.data.error
        : 'Update failed';
  });
}

export function cancelEdit() {
  store.activeSection = 'membership-admin';
  store.editMemberData = {};
  store.editMemberId = null;
  store.editNavigationMembers = [];
  store.newPassword = '';
  store.confirmPassword = '';
  store.passwordError = '';
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------
export function canNavigateToSection(sectionKey) {
  if (sectionKey === 'membership-admin') return canAccessMembershipAdmin.value;
  if (sectionKey === 'club-settings') return canAccessMembershipAdmin.value;
  if (sectionKey === 'newsletters') return canAccessNewsletters.value;
  return true;
}

export function navigateToSection(sectionKey) {
  store.accessError = '';
  if (!canNavigateToSection(sectionKey)) {
    store.accessError = 'You do not have permission to access this section.';
    store.activeSection = 'home';
    return;
  }
  if (sectionKey === 'membership-admin') {
    store.activeSection = 'membership-admin';
    store.showMembershipDetails = false;
    store.lookupNumber = '';
    store.lookupResult = null;
    store.lookupError = '';
    store.currentPage = 1;
    fetchMembers();
    return;
  }
  store.activeSection = sectionKey;
}

export function setMyClubActiveTab(tabId) {
  if (!MY_CLUB_TABS.some(tab => tab.id === tabId)) return;
  store.myClubActiveTab = tabId;
}
