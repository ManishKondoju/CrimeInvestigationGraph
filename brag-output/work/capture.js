// Frame capture. Steps render(f) explicitly rather than letting time run,
// so output is deterministic and reproducible.
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const only = process.argv[2] ? process.argv[2].split(',').map(Number) : null;
  const outDir = path.join(__dirname, 'frames');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(__dirname, 'film.html'));
  // Fonts must be in before any capture or early frames render in fallback type
  // FontFaceSet settles at 'loaded', not 'done'; fonts.ready is the
  // promise form and avoids depending on the exact status string.
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(400);

  const total = await page.evaluate(() => window.TOTAL);
  const list = only || Array.from({ length: total }, (_, i) => i);
  for (const f of list) {
    await page.evaluate((n) => window.render(n), f);
    await page.screenshot({ path: path.join(outDir, String(f).padStart(4, '0') + '.png') });
    if (!only && f % 60 === 0) process.stdout.write(`  ${f}/${total}\n`);
  }
  await browser.close();
  console.log(only ? `stills: ${list.join(',')}` : `captured ${list.length} frames`);
})();
