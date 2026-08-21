# GLP-1 Match

A clinician-facing iOS-style tool that matches a patient's profile — treatment goal, BMI range, diabetes status, delivery preference, and comorbidities — against real GLP-1 receptor agonist indications and current trial evidence. Built as a single self-contained HTML file with no build step and no dependencies.

![GLP-1 Match results screen](docs/screenshot.png)

## What it does

The app walks through a five-step intake (goal, BMI range, diabetes status, delivery preference, comorbidities), then scores five FDA-approved GLP-1 options — Wegovy, Zepbound, Ozempic, Mounjaro, and Rybelsus — against the inputs. Each result surfaces the specific approved indications and trial findings behind the match (for example, semaglutide's cardiovascular-risk-reduction indication in ASCVD, or semaglutide's chronic-kidney-disease indication in type 2 diabetes), not just a bare recommendation.

It is decision support only. It does not replace clinical judgment, contraindication and drug-interaction screening, or shared decision-making with the patient — the app says so on its own results screen, along with numbered references to the trial and meta-analysis literature it draws on.

## Running it

There's nothing to install or build. Open `index.html` directly in a browser, or serve the folder with any static file server:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

On a phone-width viewport (iPhone 13 Pro Max class or narrower), the app fills the screen edge-to-edge using the device's own status bar and home indicator. On a wider viewport, it renders inside a decorative iPhone mockup for preview purposes.

## Live demo

If GitHub Pages is enabled for this repository (Settings → Pages → Source: GitHub Actions), the included workflow publishes `index.html` automatically on every push to `main`, at:

```
https://<your-username>.github.io/<repo-name>/
```

## Project structure

```
.
├── index.html              # the entire app — markup, styles, and logic in one file
├── VALIDATION.md            # independent 100-case accuracy check, method + results
├── validation/               # scripts that produced VALIDATION.md (not part of the shipped app)
├── docs/
│   └── screenshot.png       # image used in this README
└── .github/workflows/
    └── deploy-pages.yml     # GitHub Pages auto-deploy on push to main
```

## Evidence sources

The matching logic and indication text are grounded in three sources:

1. Moiz A, Filion KB, Toutounchi H, Tsoukas MA, Yu OHY, Peters TM, et al. Efficacy and safety of glucagon-like peptide-1 receptor agonists for weight loss among adults without diabetes: a systematic review of randomized controlled trials. Ann Intern Med. 2025;178(2):199–217. doi:10.7326/ANNALS-24-01590
2. Yao H, Zhang A, Li D, Wu Y, Wang CZ, Wan JY, et al. Comparative effectiveness of GLP-1 receptor agonists on glycaemic control, body weight, and lipid profile for type 2 diabetes: systematic review and network meta-analysis. BMJ. 2024;384:e076410. doi:10.1136/bmj-2023-076410
3. Rosen CJ, Ingelfinger JR. GLP-1 receptor agonists. N Engl J Med. 2026;394(13):1313–24. doi:10.1056/NEJMra2500106

These same three references appear on the app's own results screen.

## Validation

The matching algorithm was independently checked against 100 randomly generated patient profiles, graded by logic written fresh from the source papers (not from the app's own code): 85% exact match, 89% evidence-consistent overall, after a fix to delivery-preference weighting. See [VALIDATION.md](VALIDATION.md) for the full method, both rounds of results, and an honest breakdown of every remaining mismatch. The scripts that produced it are in `validation/`.

## Accessibility

Colors are checked against WCAG AA (4.5:1 minimum for body and small text); interactive targets meet the 44×44pt minimum; keyboard focus is visible throughout; `prefers-reduced-motion` is respected; and the page adapts to system light/dark mode.

## Disclaimer

This is a prototype for design and educational purposes. It is not a medical device, is not FDA-cleared, and must not be used as the sole basis for a prescribing decision. Medication indications and trial findings summarized here can change as new evidence emerges — always confirm current labeling and guidelines before applying them to patient care.

## License

See [LICENSE](LICENSE).
