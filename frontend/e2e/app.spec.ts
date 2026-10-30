import { readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { expect, test, type Page } from '@playwright/test';

const fx = (nome: string): string => path.join(import.meta.dirname, '.fixtures', nome);

const PAGINAS = ['/', '/conversor', '/ferramentas-avancadas', '/audio', '/video', '/historico'];

/** Falha o teste em qualquer erro de JS ou violação de CSP na página. */
function vigiarErros(page: Page): string[] {
  const erros: string[] = [];
  page.on('pageerror', (e) => erros.push(`pageerror: ${e.message}`));
  page.on('console', (m) => {
    // Respostas 4xx esperadas pelo teste aparecem como "Failed to load resource".
    if (m.type() === 'error' && !m.text().includes('Failed to load resource')) erros.push(`console: ${m.text()}`);
  });
  return erros;
}

async function esperarDownload(page: Page, acao: () => Promise<void>): Promise<{ nome: string; tamanho: number }> {
  const promessa = page.waitForEvent('download', { timeout: 60_000 });
  await acao();
  const download = await promessa;
  const caminho = await download.path();
  return { nome: download.suggestedFilename(), tamanho: statSync(caminho).size };
}

for (const rota of PAGINAS) {
  test(`página ${rota} sem erros de JS, CSP ou recurso externo`, async ({ page }) => {
    const erros = vigiarErros(page);
    const externos: string[] = [];
    page.on('request', (r) => {
      if (!r.url().startsWith('http://127.0.0.1') && !r.url().startsWith('data:') && !r.url().startsWith('blob:')) externos.push(r.url());
    });
    await page.goto(rota, { waitUntil: 'networkidle' });
    expect(erros).toEqual([]);
    expect(externos).toEqual([]);
  });
}

test.describe('áudio', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/audio');
  });

  for (const id of ['conv', 'cut', 'vol', 'spd', 'rev']) {
    test(`ferramenta ${id} baixa um arquivo`, async ({ page }) => {
      const erros = vigiarErros(page);
      await page.setInputFiles(`#arquivo-${id}`, fx('a.mp3'));
      await expect(page.locator(`#status-${id}`)).toContainText('a.mp3');
      const r = await esperarDownload(page, () => page.click(`#btn-${id}`));
      expect(r.tamanho).toBeGreaterThan(0);
      expect(erros).toEqual([]);
    });
  }

  test('corte usa a prévia e o tempo escolhido', async ({ page }) => {
    await page.setInputFiles('#arquivo-cut', fx('a.mp3'));
    await expect(page.locator('#cut-interactive-wrap')).toBeVisible();
    await expect(page.locator('#preview-total-cut')).toHaveText('0:03');
    await page.fill('#fim-cut', '0:01');
    const r = await esperarDownload(page, () => page.click('#btn-cut'));
    expect(r.nome).toContain('cortado');
  });

  test('chips de conversão atualizam o resumo', async ({ page }) => {
    await page.click('[data-chip="channels-conv"][data-val="1"]');
    await expect(page.locator('#hud-sample-display')).toContainText('Mono');
    await expect(page.locator('#channels-conv')).toHaveValue('1');
  });

  test('juntar acumula faixas e baixa', async ({ page }) => {
    await page.setInputFiles('#arquivos-join', fx('a.mp3'));
    await page.setInputFiles('#arquivos-join', fx('a.mp3'));
    await expect(page.locator('#files-list-join .file-item')).toHaveCount(2);
    const r = await esperarDownload(page, () => page.click('#btn-join'));
    expect(r.tamanho).toBeGreaterThan(0);
  });

  test('erro aparece sem travar o botão', async ({ page }) => {
    await page.click('#btn-rev');
    await expect(page.locator('#erro-rev')).toHaveClass(/visivel/);
    await expect(page.locator('#btn-rev')).toBeEnabled();
  });
});

test.describe('vídeo', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/video');
  });

  for (const id of ['v2a', 'v2g', 'vconv', 'vcomp', 'vmute', 'vsnap']) {
    test(`ferramenta ${id} baixa um arquivo`, async ({ page }) => {
      const erros = vigiarErros(page);
      await page.setInputFiles(`#input-${id}`, fx('v.mp4'));
      const r = await esperarDownload(page, () => page.click(`#btn-${id}`));
      expect(r.tamanho).toBeGreaterThan(0);
      await expect(page.locator(`#resultado-${id}`)).toContainText(r.nome);
      expect(erros).toEqual([]);
    });
  }

  test('cancelar interrompe a compressão', async ({ page }) => {
    await page.setInputFiles('#input-vcomp', fx('longo.mp4'));
    await page.click('#btn-vcomp');
    const cancelar = page.locator('.btn-job-cancel');
    await expect(cancelar).toBeVisible();
    await page.waitForTimeout(1500);
    await cancelar.click();
    await expect(page.locator('#toast')).toContainText(/cancelada/i, { timeout: 20_000 });
    await expect(page.locator('#btn-vcomp')).toBeEnabled();
  });

  test('link interno é recusado com mensagem', async ({ page }) => {
    await page.fill('#input-url-dl', 'http://127.0.0.1:9/x.mp4');
    await page.click('#btn-dl');
    await expect(page.locator('#toast')).toContainText('rede local', { timeout: 20_000 });
  });

  test('alternar para MP3 troca as opções de qualidade', async ({ page }) => {
    await page.click('[data-action="dl-format"][data-val="mp3"]');
    await expect(page.locator('#chips-qualidade-audio-dl')).toBeVisible();
    await expect(page.locator('#chips-qualidade-video-dl')).toBeHidden();
    await expect(page.locator('#formato-dl')).toHaveValue('mp3');
  });
});

test.describe('ferramentas avançadas', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/ferramentas-avancadas');
  });

  async function enviarFormulario(page: Page, acao: string): Promise<{ nome: string; tamanho: number }> {
    return esperarDownload(page, () => page.locator(`form[action="${acao}"] button[type="submit"]`).click());
  }

  test('mesclar acumula arquivos e baixa', async ({ page }) => {
    await page.setInputFiles('#mergeInput', fx('p.pdf'));
    await page.setInputFiles('#mergeInput', fx('p2.pdf'));
    await expect(page.locator('#mergeListContainer .merge-item')).toHaveCount(2);
    expect((await enviarFormulario(page, '/api/pdf/mesclar')).nome).toBe('Prisma_Mesclado.pdf');
  });

  for (const [acao, entrada, nome] of [
    ['/api/pdf/dividir', '#splitInput', 'Prisma_Dividido.zip'],
    ['/api/pdf/comprimir', '#compressInput', 'Prisma_Comprimido.pdf'],
    ['/api/pdf/extrair-imagens', '#extractInput', 'Prisma_Imagens_PDF.zip'],
  ] as const) {
    test(`${acao} baixa`, async ({ page }) => {
      await page.setInputFiles(entrada, fx('p.pdf'));
      expect((await enviarFormulario(page, acao)).nome).toBe(nome);
    });
  }

  test('proteger exige senha e baixa', async ({ page }) => {
    await page.setInputFiles('#protectInput', fx('p.pdf'));
    await page.locator('form[action="/api/pdf/proteger"] input[name="senha"]').fill('abc');
    expect((await enviarFormulario(page, '/api/pdf/proteger')).nome).toBe('Prisma_Protegido.pdf');
  });

  test('erro aparece no próprio cartão', async ({ page }) => {
    await page.setInputFiles('#manipulateInput', fx('p.pdf'));
    await page.locator('form[action="/api/pdf/manipular-paginas"] button[type="submit"]').click();
    await expect(page.locator('form[action="/api/pdf/manipular-paginas"] .ferramenta-erro')).toContainText('Informe as páginas');
  });

  test('QR Code malicioso entra como texto, sem executar', async ({ page }) => {
    await page.setInputFiles('#qrLerInput', fx('xss.png'));
    await page.click('#qrLerBtn');
    await expect(page.locator('#qrLerResultado .qr-dados')).toContainText('onerror');
    expect(await page.evaluate(() => (window as unknown as { __xss?: number }).__xss)).toBeUndefined();
    await expect(page.locator('#qrLerResultado img')).toHaveCount(0);
  });

  test('paleta e hash mostram o resultado', async ({ page }) => {
    await page.setInputFiles('#paletaInput', fx('i.png'));
    await page.click('#paletaBtn');
    await expect(page.locator('.paleta-swatch').first()).toBeVisible({ timeout: 20_000 });
    await page.setInputFiles('#hashInput', fx('t.csv'));
    await page.click('#hashBtn');
    await expect(page.locator('#hashResultado .hash-value')).toHaveCount(3, { timeout: 20_000 });
  });
});

test.describe('conversor e histórico', () => {
  async function enviar(page: Page, arquivo: string): Promise<void> {
    await page.goto('/conversor');
    await page.setInputFiles('#arquivo', fx(arquivo));
    await page.click('#btnEnviar');
    await expect(page.locator('#converterForm')).toBeVisible();
  }

  test('CSV: tabela escapa HTML, converte e entra no histórico', async ({ page }) => {
    const erros = vigiarErros(page);
    await enviar(page, 't.csv');
    await expect(page.locator('.tabela-preview')).toContainText('<script>');
    expect(await page.evaluate(() => (window as unknown as { __xss?: number }).__xss)).toBeUndefined();
    await page.click('.opcao-card:has(input[value="json"])');
    const r = await esperarDownload(page, () => page.click('#btnConverter'));
    expect(r.nome).toBe('t.json');
    await page.goto('/historico');
    await expect(page.locator('.historico-card').first()).toContainText('t.json');
    expect(erros).toEqual([]);
  });

  test('PDF: prévia em imagem e ZIP no download', async ({ page }) => {
    await enviar(page, 'p.pdf');
    await page.click('.opcao-card:has(input[value="png"])');
    await expect(page.locator('#previewViewer img')).toBeVisible({ timeout: 20_000 });
    const r = await esperarDownload(page, () => page.click('#btnConverter'));
    expect(r.nome.endsWith('.zip')).toBe(true);
  });

  test('download único entrega o arquivo e apaga', async ({ page, request }) => {
    await page.goto('/historico');
    const token = await page.locator('meta[name="csrf-token"]').getAttribute('content');
    await page.evaluate(async (t) => {
      await fetch('/api/historico/set-politica', { method: 'POST', headers: { 'X-CSRFToken': t ?? '', 'Content-Type': 'application/json' }, body: JSON.stringify({ politica: 'instant' }) });
    }, token);
    await enviar(page, 't.csv');
    await page.click('.opcao-card:has(input[value="json"])');
    const promessa = page.waitForEvent('download');
    await page.click('#btnConverter');
    const download = await promessa;
    const conteudo = readFileSync(await download.path(), 'utf8');
    expect(JSON.parse(conteudo)).toHaveLength(2);
    await expect.poll(async () => (await request.get(download.url())).status()).toBe(410);
    await page.evaluate(async (t) => {
      await fetch('/api/historico/set-politica', { method: 'POST', headers: { 'X-CSRFToken': t ?? '', 'Content-Type': 'application/json' }, body: JSON.stringify({ politica: '15min' }) });
    }, token);
  });

  test('histórico: contador, renovar e destruir tudo', async ({ page }) => {
    await enviar(page, 't.csv');
    await page.click('.opcao-card:has(input[value="json"])');
    await esperarDownload(page, () => page.click('#btnConverter'));
    await page.goto('/historico');
    const cartao = page.locator('.historico-card').first();
    await expect(cartao.locator('.hist-timer-val')).toHaveText(/\d\d:\d\d/);
    await cartao.locator('[data-action="renovar"]').click();
    await expect(page.locator('#toast')).toContainText(/renovado/i);
    await page.click('#destroyAllHistory');
    await page.click('#confirmDestroyHistory');
    await expect(cartao.locator('.hist-apagado-badge')).toBeVisible();
    await expect(page.locator('#downloadAllHistory')).toBeDisabled();
  });
});

test.describe('aparência', () => {
  test('tema, cor e idioma persistem entre páginas', async ({ page }) => {
    await page.goto('/conversor');
    await page.click('#themeToggle');
    await page.click('.theme-mode-square-btn[data-mode="light"]');
    await page.click('.theme-swatch-btn[title="Azul Real"]');
    await page.click('.btn-lang-opt[data-lang="en"]');
    await page.click('#doneCustomizerBtn');
    await page.goto('/audio');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
    expect(await page.evaluate(() => document.documentElement.style.getPropertyValue('--accent'))).toBe('#2563eb');
    await expect(page.locator('a[href="/conversor"]')).toContainText('File Converter');
  });
});
