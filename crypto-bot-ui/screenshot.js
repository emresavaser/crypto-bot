const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  await page.goto('http://localhost:3000');
  await page.waitForTimeout(3000); // Wait for chart to load
  await page.screenshot({ path: 'screenshot.png', fullPage: true });
  console.log('Screenshot saved: screenshot.png');
  await browser.close();
})();
