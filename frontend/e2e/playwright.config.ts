import { execSync } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { defineConfig } from '@playwright/test';

const PORTA = 5099;
const dados = mkdtempSync(path.join(tmpdir(), 'prisma_e2e_'));
execSync('python frontend/e2e/fixtures.py', { stdio: 'inherit' });

export default defineConfig({
  testDir: '.',
  timeout: 90_000,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: `http://127.0.0.1:${PORTA}`,
    channel: process.env.CI ? undefined : 'msedge',
    acceptDownloads: true,
    locale: 'pt-BR',
  },
  webServer: {
    command: 'python app.py',
    url: `http://127.0.0.1:${PORTA}/health`,
    cwd: path.resolve(import.meta.dirname, '../..'),
    env: { PORT: String(PORTA), NO_BROWSER: '1', NO_AUTO_SHUTDOWN: '1', PRISMA_DATA_DIR: dados },
    reuseExistingServer: false,
  },
});
