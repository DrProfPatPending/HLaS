import fs from 'node:fs';
import path from 'node:path';

function parseArgs(argv) {
  const modeArg = argv.find(arg => arg.startsWith('--mode='));
  if (modeArg) {
    return modeArg.slice('--mode='.length).trim();
  }

  const modeFlagIndex = argv.findIndex(arg => arg === '--mode');
  if (modeFlagIndex >= 0 && argv[modeFlagIndex + 1]) {
    return String(argv[modeFlagIndex + 1]).trim();
  }

  return '';
}

function parseEnvFile(filePath) {
  if (!fs.existsSync(filePath)) return {};
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split(/\r?\n/);
  const values = {};

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;

    const eqIndex = trimmed.indexOf('=');
    if (eqIndex <= 0) continue;

    const key = trimmed.slice(0, eqIndex).trim();
    const raw = trimmed.slice(eqIndex + 1).trim();
    const unquoted =
      (raw.startsWith('"') && raw.endsWith('"')) || (raw.startsWith("'") && raw.endsWith("'"))
        ? raw.slice(1, -1)
        : raw;

    values[key] = unquoted;
  }

  return values;
}

function resolveEnv(mode) {
  const cwd = process.cwd();
  const files = [
    '.env',
    '.env.local',
    mode ? `.env.${mode}` : '',
    mode ? `.env.${mode}.local` : '',
  ].filter(Boolean);

  const resolved = {};
  const sources = {};

  for (const relativeFile of files) {
    const absoluteFile = path.join(cwd, relativeFile);
    const parsed = parseEnvFile(absoluteFile);

    for (const [key, value] of Object.entries(parsed)) {
      resolved[key] = value;
      sources[key] = relativeFile;
    }
  }

  return { resolved, sources };
}

const mode = parseArgs(process.argv.slice(2));
const { resolved, sources } = resolveEnv(mode);
const mobileUrl = String(resolved.VITE_MOBILE_BACKEND_URL || '').trim();
const fallbackUrl = String(resolved.VITE_BACKEND_URL || '').trim();
const effectiveUrl = mobileUrl || fallbackUrl || '(using runtime native/web fallback)';
const effectiveSource =
  (mobileUrl && sources.VITE_MOBILE_BACKEND_URL) ||
  (fallbackUrl && sources.VITE_BACKEND_URL) ||
  'runtime fallback';

console.log(`mode: ${mode || '(default)'}`);
console.log(`VITE_MOBILE_BACKEND_URL: ${mobileUrl || '(unset)'}`);
console.log(`VITE_BACKEND_URL: ${fallbackUrl || '(unset)'}`);
console.log(`effective mobile backend URL: ${effectiveUrl}`);
console.log(`source: ${effectiveSource}`);

if (effectiveUrl.includes('example.com')) {
  console.warn('warning: effective URL appears to be a placeholder (example.com).');
}
