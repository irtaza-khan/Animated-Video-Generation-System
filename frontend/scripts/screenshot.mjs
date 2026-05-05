import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT_DIR = path.resolve(__dirname, '..', 'screenshots');
const URL = process.env.UI_URL || 'http://localhost:5173/';

const VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'tablet',  width: 820,  height: 1180 },
  { name: 'mobile',  width: 390,  height: 844 },
];

await mkdir(OUT_DIR, { recursive: true });

const browser = await chromium.launch();
const issues = [];

const THEMES = ['night', 'day'];

for (const theme of THEMES)
for (const vp of VIEWPORTS) {
  const context = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
    deviceScaleFactor: 2,
    colorScheme: theme === 'night' ? 'dark' : 'light',
    reducedMotion: 'no-preference',
  });
  await context.addInitScript((t) => {
    try { window.localStorage.setItem('ai-studio:theme', t); } catch {}
  }, theme);
  const page = await context.newPage();
  const tag = `${vp.name}-${theme}`;

  page.on('console', msg => {
    if (msg.type() === 'error') {
      issues.push(`[${tag}] CONSOLE ERROR: ${msg.text()}`);
    }
  });
  page.on('pageerror', err => {
    issues.push(`[${tag}] PAGE ERROR: ${err.message}`);
  });

  await page.goto(URL, { waitUntil: 'networkidle' });
  // Let entrance animations settle
  await page.waitForTimeout(700);

  // Default
  await page.screenshot({
    path: path.join(OUT_DIR, `${tag}-default.png`),
    fullPage: true,
  });

  // Focus prompt
  const promptInput = page.locator('#prompt-input');
  if (await promptInput.count()) {
    await promptInput.focus();
    await page.waitForTimeout(350);
    await page.screenshot({
      path: path.join(OUT_DIR, `${tag}-prompt-focus.png`),
      fullPage: false,
    });
    await promptInput.blur();
  }

  // Hover Generate button
  const genBtn = page.locator('button[aria-label="Generate video"]');
  if (await genBtn.count()) {
    await genBtn.hover();
    await page.waitForTimeout(350);
    await page.screenshot({
      path: path.join(OUT_DIR, `${tag}-generate-hover.png`),
      fullPage: false,
    });
  }

  // Focus chat composer (sidebar may be below the fold on mobile)
  const chat = page.locator('input[aria-label="Edit instruction"]');
  if (await chat.count()) {
    await chat.scrollIntoViewIfNeeded();
    await chat.focus();
    await page.waitForTimeout(300);
    await chat.fill('Update scene 1 prompt to a stormy seaside cliff at dusk');
    await page.waitForTimeout(250);
    await page.screenshot({
      path: path.join(OUT_DIR, `${tag}-chat-typing.png`),
      fullPage: false,
    });
    await chat.fill('');
  }

  // Simulate mid-pipeline loading state via route mocks (no backend required)
  await page.route('**/api/generate', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ job_id: 'mock-job', status: 'processing' }),
    });
  });
  let pollCount = 0;
  await page.route('**/api/status/**', async route => {
    pollCount++;
    const stages = [
      { status: 'generating_story', progress: 5 },
      { status: 'casting_characters', progress: 12, portraits: { Alice: 'mock-1', Bob: 'mock-2' } },
      { status: 'generating_audio', progress: 24 },
      { status: 'generating_video', progress: 48 },
      { status: 'compositing', progress: 88 },
    ];
    const idx = Math.min(pollCount - 1, stages.length - 1);
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(stages[idx]),
    });
  });
  // Mock portrait images so they render
  await page.route('**/mock-*', async route => {
    // 1x1 transparent PNG
    const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Zn0H4kAAAAASUVORK5CYII=', 'base64');
    await route.fulfill({ status: 200, contentType: 'image/png', body: png });
  });

  await page.click('button[aria-label="Generate video"]');
  // Let polling tick a few times
  await page.waitForTimeout(2200);
  await page.screenshot({
    path: path.join(OUT_DIR, `${tag}-loading.png`),
    fullPage: false,
  });
  await page.waitForTimeout(2000);
  await page.screenshot({
    path: path.join(OUT_DIR, `${tag}-loading-late.png`),
    fullPage: false,
  });

  // Stop intercepting + reload to clean state for next vp
  await page.unroute('**/api/generate');
  await page.unroute('**/api/status/**');
  await page.unroute('**/mock-*');

  // Layout sanity checks
  const layout = await page.evaluate(() => {
    const out = { overflows: [], cards: [] };
    const docW = document.documentElement.clientWidth;
    const inScrollContainer = (el) => {
      let p = el.parentElement;
      while (p) {
        const ox = getComputedStyle(p).overflowX;
        if (ox === 'auto' || ox === 'scroll' || ox === 'hidden') return true;
        p = p.parentElement;
      }
      return false;
    };
    document.querySelectorAll('*').forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.right > docW + 1 && !inScrollContainer(el)) {
        out.overflows.push({
          tag: el.tagName.toLowerCase(),
          cls: (el.className || '').toString().slice(0, 60),
          right: Math.round(r.right),
          docW,
        });
      }
    });
    document.querySelectorAll('.card, .viewport, .studio-sidebar').forEach(el => {
      const r = el.getBoundingClientRect();
      out.cards.push({
        cls: (el.className || '').toString().slice(0, 60),
        w: Math.round(r.width),
        h: Math.round(r.height),
      });
    });
    return out;
  });

  if (layout.overflows.length) {
    issues.push(`[${tag}] HORIZONTAL OVERFLOW from ${layout.overflows.length} elements: ${JSON.stringify(layout.overflows.slice(0, 5))}`);
  }

  await context.close();
}

await browser.close();

if (issues.length) {
  console.log('\n--- ISSUES ---');
  for (const i of issues) console.log(i);
  console.log(`\nTotal issues: ${issues.length}`);
} else {
  console.log('\nNo issues detected.');
}

console.log(`\nScreenshots saved to ${OUT_DIR}`);
