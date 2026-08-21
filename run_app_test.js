// Drives the REAL app UI (the actual shipped index.html, unmodified) through
// all 100 synthetic profiles, exactly the way a user would tap through it,
// and records what the app's algorithm actually surfaces as the top
// ("Best match") result for each one.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function main() {
  const profiles = JSON.parse(fs.readFileSync('profiles.json', 'utf8')).profiles;

  // Build a full standalone document from the real app file (same wrapping
  // used throughout this project's own QA passes -- the app file itself
  // ships as a fragment meant to be embedded by the Artifact tool).
  const appSource = fs.readFileSync(path.resolve(__dirname, '../glp_match.html'), 'utf8');
  const wrapped = `<!doctype html><html><head><meta charset="utf-8"></head><body>${appSource}</body></html>`;
  const tmpPath = path.resolve(__dirname, '_app_under_test.html');
  fs.writeFileSync(tmpPath, wrapped);

  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const context = await browser.newContext({ viewport: { width: 428, height: 926 } });
  const page = await context.newPage();

  const results = [];

  for (const p of profiles) {
    await page.goto('file://' + tmpPath);
    await page.click('#startBtn');

    await page.click(`[data-field="goal"] .option-card[data-value="${p.goal}"]`);
    await page.click('.screen.active [data-continue]');

    await page.click(`[data-field="bmiRange"] .option-card[data-value="${p.bmiRange}"]`);
    await page.click('.screen.active [data-continue]');

    await page.click(`[data-field="diabetesStatus"] .option-card[data-value="${p.diabetesStatus}"]`);
    await page.click('.screen.active [data-continue]');

    await page.click(`[data-field="delivery"] .option-card[data-value="${p.delivery}"]`);
    await page.click('.screen.active [data-continue]');

    for (const c of p.comorbidities) {
      await page.click(`[data-field="comorbidities"] .option-card[data-value="${c}"]`);
    }
    await page.click('.screen.active [data-continue]');

    await page.waitForTimeout(60);

    const cards = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('.result-card')).map(card => ({
        name: card.querySelector('.result-name').textContent.trim(),
        hasBadge: !!card.querySelector('.result-badge'),
        reasons: Array.from(card.querySelectorAll('.reason-chip')).map(r => r.textContent.trim()),
      }));
    });

    results.push({
      id: p.id,
      appTop: cards.length ? cards[0].name : null,
      appTopReasons: cards.length ? cards[0].reasons : [],
      appRanked: cards.map(c => c.name),
    });

    if (p.id % 20 === 0) console.error(`...${p.id}/100`);
  }

  fs.writeFileSync(path.resolve(__dirname, 'app_results.json'), JSON.stringify(results, null, 2));
  fs.unlinkSync(tmpPath);
  await browser.close();
  console.error('Done.');
}

main();
