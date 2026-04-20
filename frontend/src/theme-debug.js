function readThemeVariables(prefix = '--app-') {
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return [];
  }

  const styles = window.getComputedStyle(document.documentElement);
  const values = [];

  for (let index = 0; index < styles.length; index += 1) {
    const name = styles[index];
    if (!String(name || '').startsWith(prefix)) continue;

    const value = String(styles.getPropertyValue(name) || '').trim();
    if (!value) continue;
    values.push({ name, value });
  }

  values.sort((a, b) => a.name.localeCompare(b.name));
  return values;
}

function dumpThemeVariables(prefix = '--app-') {
  const values = readThemeVariables(prefix);
  const title = typeof document !== 'undefined' ? document.title : '';

  console.group(`HLaS Theme Debug (${prefix})`);
  if (title) {
    console.log('Document title:', title);
  }
  console.table(values);
  console.groupEnd();

  return values;
}

export function registerThemeDebugHelpers() {
  if (typeof window === 'undefined') return;

  window.hlasThemeDebug = {
    readThemeVariables,
    dumpThemeVariables,
  };
}
