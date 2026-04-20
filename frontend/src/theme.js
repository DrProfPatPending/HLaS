const APP_THEME_VAR_PREFIX = '--app-';

let activeVariableNames = [];

function isPlainObject(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function sanitizeVariableName(name) {
  const normalized = String(name || '').trim();
  return /^--app-[a-z0-9-]+$/i.test(normalized) ? normalized : '';
}

function sanitizeVariableValue(value) {
  if (value === null || value === undefined) return '';
  if (typeof value === 'number' && Number.isFinite(value)) return String(value);
  if (typeof value === 'string') return value.trim();
  return '';
}

function normalizeVariableMap(raw) {
  if (!isPlainObject(raw)) return {};

  return Object.entries(raw).reduce((acc, [name, value]) => {
    const key = sanitizeVariableName(name);
    const val = sanitizeVariableValue(value);
    if (!key || !val) return acc;
    acc[key] = val;
    return acc;
  }, {});
}

function extractVariableMapFromObject(raw) {
  if (!isPlainObject(raw)) return {};

  const explicitCandidates = [
    raw.cssVariables,
    raw.themeVariables,
    raw.variables,
    raw.theme && raw.theme.cssVariables,
    raw.theme && raw.theme.themeVariables,
    raw.branding && raw.branding.cssVariables,
    raw.branding && raw.branding.themeVariables,
  ];

  const mergedFromCandidates = explicitCandidates.reduce((acc, candidate) => {
    return {
      ...acc,
      ...normalizeVariableMap(candidate),
    };
  }, {});

  const mergedInlineVariables = Object.entries(raw).reduce((acc, [name, value]) => {
    if (!String(name || '').startsWith(APP_THEME_VAR_PREFIX)) return acc;
    const key = sanitizeVariableName(name);
    const val = sanitizeVariableValue(value);
    if (!key || !val) return acc;
    acc[key] = val;
    return acc;
  }, {});

  return {
    ...mergedFromCandidates,
    ...mergedInlineVariables,
  };
}

export function extractThemeVariables(raw) {
  return extractVariableMapFromObject(raw);
}

export function resolveThemeVariables({
  appSettings,
  clubSettings,
  activeClub,
  matchedClub,
}) {
  const globalTheme = extractVariableMapFromObject(appSettings);

  const clubThemeFromSettings = (() => {
    const byShortName =
      appSettings?.clubThemes ||
      appSettings?.theme?.clubThemes ||
      appSettings?.branding?.clubThemes;
    if (!isPlainObject(byShortName)) return {};

    const normalizedActiveClub = String(activeClub || '').trim().toLowerCase();
    if (!normalizedActiveClub) return {};

    const exactKey = Object.keys(byShortName).find(
      key => String(key || '').trim().toLowerCase() === normalizedActiveClub
    );
    if (!exactKey) return {};
    return extractVariableMapFromObject(byShortName[exactKey]);
  })();

  const clubThemeFromClubsConfig = extractVariableMapFromObject(matchedClub);
  const clubThemeFromClubSettings = extractVariableMapFromObject(clubSettings);

  return {
    ...globalTheme,
    ...clubThemeFromSettings,
    ...clubThemeFromClubsConfig,
    ...clubThemeFromClubSettings,
  };
}

export function applyThemeVariables(themeVariables) {
  if (typeof document === 'undefined') return;

  const root = document.documentElement;
  const normalizedMap = normalizeVariableMap(themeVariables);

  activeVariableNames.forEach(variableName => {
    root.style.removeProperty(variableName);
  });

  const variableNames = Object.keys(normalizedMap);
  variableNames.forEach(variableName => {
    root.style.setProperty(variableName, normalizedMap[variableName]);
  });

  activeVariableNames = variableNames;
}
