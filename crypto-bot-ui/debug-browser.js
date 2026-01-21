const { chromium } = require('playwright');

async function connect() {
  const browser = await chromium.launch({
    headless: false,
    devtools: true,
    args: ['--start-maximized']
  });

  const context = await browser.newContext({
    viewport: null // Tam ekran
  });

  const page = await context.newPage();

  page.on('console', msg => {
    const type = msg.type().toUpperCase();
    if (type === 'ERROR' || type === 'WARNING') {
      console.log(`[${type}] ${msg.text()}`);
    }
  });

  page.on('pageerror', err => {
    console.log(`[PAGE ERROR] ${err.message}`);
  });

  page.on('response', response => {
    const url = response.url();
    if (url.includes('/api/') && response.status() >= 400) {
      console.log(`[API ERROR] ${response.status()} ${url}`);
    }
  });

  await page.goto('http://localhost:3000');
  console.log('✅ Debug browser: Tam ekran + DevTools');

  await new Promise(() => {});
}

connect().catch(console.error);
