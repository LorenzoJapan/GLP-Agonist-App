const { chromium } = require('playwright');
const path = require('path');

const url = 'file://' + path.resolve(__dirname, 'index.html');

async function selectOption(page, field, value) {
  await page.click(`.option-list[data-field="${field}"] .option-card[data-value="${value}"]`);
}

async function runCase(browser, { label, goal, bmiRange, diabetesStatus, delivery, comorbidities }) {
  const page = await browser.newPage();
  await page.goto(url);

  await page.click('#startBtn');
  await selectOption(page, 'goal', goal);
  await page.click('[data-screen="goal"] [data-continue]');

  await selectOption(page, 'bmiRange', bmiRange);
  await page.click('[data-screen="bmi"] [data-continue]');

  await selectOption(page, 'diabetesStatus', diabetesStatus);
  await page.click('[data-screen="diabetes"] [data-continue]');

  await selectOption(page, 'delivery', delivery);
  await page.click('[data-screen="delivery"] [data-continue]');

  for (const c of comorbidities) {
    await selectOption(page, 'comorbidities', c);
  }
  await page.click('[data-screen="comorbidities"] [data-continue]');

  await page.click('[data-screen="review"] [data-continue]');

  await page.waitForSelector('[data-screen="results"].active');

  const notIndicatedHidden = await page.getAttribute('#resultNotIndicated', 'hidden');
  const fallbackHidden = await page.getAttribute('#resultFallbackBanner', 'hidden');
  const cardCount = await page.$$eval('#resultList .result-card', els => els.length);
  const summaryText = await page.textContent('#resultsSummary');
  const notIndicatedVisible = notIndicatedHidden === null;

  console.log(`\n=== ${label} ===`);
  console.log('not-indicated card shown:', notIndicatedVisible);
  console.log('fallback banner shown:', fallbackHidden === null);
  console.log('drug cards shown:', cardCount);
  console.log('summary:', summaryText.trim());

  await page.close();
  return { notIndicatedVisible, cardCount };
}

(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });

  const results = {};

  results.trueNegative = await runCase(browser, {
    label: 'Weight-loss goal, BMI under 25, no diabetes, no comorbidities (expect: not indicated, 0 cards)',
    goal: 'weight-loss', bmiRange: 'under25', diabetesStatus: 'none', delivery: 'either', comorbidities: ['none']
  });

  results.underweightWithComorbidity = await runCase(browser, {
    label: 'Weight-loss goal, BMI under 25, ASCVD present (expect: still not indicated — BMI floor applies regardless of comorbidity)',
    goal: 'weight-loss', bmiRange: 'under25', diabetesStatus: 'none', delivery: 'either', comorbidities: ['cardiovascular']
  });

  results.overweightNoComorbidity = await runCase(browser, {
    label: 'Weight-loss goal, BMI 25-29.9, no comorbidities, no diabetes (expect: not indicated — 27 threshold not met without comorbidity)',
    goal: 'weight-loss', bmiRange: '25-29', diabetesStatus: 'none', delivery: 'either', comorbidities: ['none']
  });

  results.normalIndicated = await runCase(browser, {
    label: 'Weight-loss goal, BMI 35+, no comorbidities (expect: indicated, cards shown, e.g. Wegovy/Zepbound)',
    goal: 'weight-loss', bmiRange: '35plus', diabetesStatus: 'none', delivery: 'either', comorbidities: ['none']
  });

  results.bothGoalUnderweightType2 = await runCase(browser, {
    label: 'Goal both, BMI under 25, type 2 diabetes (expect: indicated via diabetes category, cards shown)',
    goal: 'both', bmiRange: 'under25', diabetesStatus: 'type2', delivery: 'either', comorbidities: ['none']
  });

  results.diabetesGoalNoDiagnosis = await runCase(browser, {
    label: 'Diabetes goal, no diagnosis, BMI under 25 (expect: indicated via stated goal alone, cards shown)',
    goal: 'diabetes', bmiRange: 'under25', diabetesStatus: 'none', delivery: 'either', comorbidities: ['none']
  });

  await browser.close();

  console.log('\n\nSUMMARY:', JSON.stringify(results, null, 2));

  // Assertions
  const assertTrue = (cond, msg) => { if (!cond) { console.error('FAIL:', msg); process.exitCode = 1; } else { console.log('PASS:', msg); } };

  assertTrue(results.trueNegative.notIndicatedVisible === true && results.trueNegative.cardCount === 0, 'true negative case shows not-indicated card with 0 drug cards');
  assertTrue(results.underweightWithComorbidity.notIndicatedVisible === true && results.underweightWithComorbidity.cardCount === 0, 'underweight + comorbidity still not indicated (BMI floor)');
  assertTrue(results.overweightNoComorbidity.notIndicatedVisible === true && results.overweightNoComorbidity.cardCount === 0, 'BMI 25-29.9 without comorbidity still not indicated');
  assertTrue(results.normalIndicated.notIndicatedVisible === false && results.normalIndicated.cardCount > 0, 'BMI 35+ weight-loss goal is indicated and shows cards');
  assertTrue(results.bothGoalUnderweightType2.notIndicatedVisible === false && results.bothGoalUnderweightType2.cardCount > 0, 'goal both + type2 diabetes shows cards even at low BMI');
  assertTrue(results.diabetesGoalNoDiagnosis.notIndicatedVisible === false && results.diabetesGoalNoDiagnosis.cardCount > 0, 'stated diabetes goal alone is indicated');
})();
