import { spawnSync } from 'node:child_process';

function parseArg(argv, key, fallback = '') {
  const long = `--${key}=`;
  const longMatch = argv.find(arg => arg.startsWith(long));
  if (longMatch) return longMatch.slice(long.length).trim();

  const flag = `--${key}`;
  const index = argv.findIndex(arg => arg === flag);
  if (index >= 0 && argv[index + 1]) {
    return String(argv[index + 1]).trim();
  }

  return fallback;
}

function normalizeProfile(raw) {
  const value = String(raw || '').trim().toLowerCase();
  if (value === 'prod' || value === 'production' || value === 'mobile-prod') return 'prod';
  if (value === 'stage' || value === 'staging' || value === 'mobile-stage') return 'stage';
  return 'dev';
}

const argv = process.argv.slice(2);
const profile = normalizeProfile(parseArg(argv, 'profile', 'prod'));
const platform = parseArg(argv, 'platform', '').toLowerCase();
const dryRun = argv.includes('--dry-run');

const cmdArgs = ['cap', 'sync'];
if (platform === 'android' || platform === 'ios') {
  cmdArgs.push(platform);
}

console.log(`[mobile-sync] profile=${profile}${platform ? ` platform=${platform}` : ''}`);
console.log(`[mobile-sync] command=npx ${cmdArgs.join(' ')}`);

if (dryRun) {
  process.exit(0);
}

const result = spawnSync('npx', cmdArgs, {
  stdio: 'inherit',
  shell: process.platform === 'win32',
  env: {
    ...process.env,
    CAPACITOR_PROFILE: profile,
  },
});

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}

process.exit(result.status ?? 1);
