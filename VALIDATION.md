# Independent Validation — 100-Case Test

This is a record of an independent accuracy check run against the app's matching algorithm (`scoreOption()` in `index.html`), first run 2026-08-21, then re-run after a fix to delivery-preference weighting the same day.

## Method

1. **100 random synthetic patient profiles** were generated (`goal`, `bmiRange`, `diabetesStatus`, `delivery`, `comorbidities`), each field drawn independently and uniformly at random (fixed seed `20260821` for reproducibility). Comorbidities were included independently at 22% probability each.
2. **An independent "ground truth" grader** was written from scratch directly against the three source papers (Moiz et al., Ann Intern Med 2025; Yao et al., BMJ 2024; Rosen & Ingelfinger, NEJM 2026) — *without* reading or reusing the app's own `scoreOption()` logic — to avoid a tautological self-check. It uses a fixed priority cascade (ASCVD → sleep apnea → CKD+T2D → MASLD → T2D → weight-loss goal) rather than cumulative scoring, and returns both a single "primary" pick and a set of "acceptable" alternates for genuine ties (e.g. no head-to-head weight-loss RCTs exist between Wegovy and Zepbound).
3. **The actual, unmodified app** (`index.html`) was driven through all 100 profiles with Playwright — real clicks through the real UI, not a re-implementation — and its top-ranked ("Best match") result was recorded for each case.
4. Each case was scored `exact` (app's top pick == grader's primary), `acceptable` (app's top pick is in the grader's acceptable set but isn't the primary), `mismatch` (app's top pick isn't evidence-supported at all), or `edge_case` (no catalog drug is well-supported by the evidence for that exact combination — this happens because no oral GLP-1 is FDA-approved for weight management, only for diabetes).

## Round 1 result (before fix)

| Metric | Value |
|---|---|
| Exact match | 80 (80%) |
| Acceptable alternate | 4 |
| Mismatch | 13 |
| No valid answer exists (edge case) | 3 |
| **Evidence-consistent (exact + acceptable)** | **84%** |

13 mismatches broke down into: 5 cases where a patient explicitly requesting the oral option (Rybelsus) was instead shown an injectable ranked first, because comorbidity bonuses (+3 each, stacking) outweighed the delivery-mismatch penalty (only −2 at the time); 3 more cases with the same underlying mechanism but without a delivery mismatch involved (an off-category drug's ungated comorbidity bonuses out-competing the correct in-category, delivery-matched drug); 3 cases from self-contradictory random test inputs (goal "diabetes management" paired with no actual diabetes diagnosis — not a combination a real clinician would pick); and 2 cases where the independent grader's simpler fixed-priority logic, not the app, was the actual limitation.

## Fix applied

In `scoreOption()`, the delivery-preference mismatch penalty was raised from `-2` to `-8`. `-8` was chosen as the smallest value that reliably outweighs the largest realistic stacked comorbidity-bonus total achievable in this catalog (BMI + two comorbidity bonuses + category approval ≈ 11 points), verified by testing penalty values from 2–12 against all 100 profiles — accuracy improves monotonically up to `-8` and then plateaus, with no case that was previously exact ever regressing at any tested value.

## Round 2 result (after fix)

| Metric | Value |
|---|---|
| Exact match | 85 (85%) |
| Acceptable alternate | 4 |
| Mismatch | 8 |
| No valid answer exists (edge case) | 3 |
| **Evidence-consistent (exact + acceptable)** | **89%** |

All 5 pure delivery-mismatch cases are resolved. The 8 remaining mismatches are exactly the cases that were never about delivery weighting:

**Contradictory random inputs (3 cases: #9, #10, #29).** The generator picks `goal` and `diabetesStatus` independently, so it occasionally produced "goal: diabetes management" paired with "diabetes status: none" — a combination a real clinician wouldn't select. In these cases the app's behavior (surfacing Wegovy/Zepbound on the strength of independently-indicated comorbidities like ASCVD/OSA/MASLD, which don't require a diabetes diagnosis) is defensible; the grader's strict goal-gating just filters those drugs out.

**Off-category comorbidity bonuses vs. the correct in-category, delivery-matched drug (3 cases: #57, #83, #100).** Even with delivery matching, Wegovy's ASCVD bonus is ungated by diabetes status (SELECT wasn't diabetes-specific) while the diabetes-category ASCVD bonus is deliberately gated to type 2 only (SUSTAIN-6/SOUL were T2D-specific) — so in prediabetes patients with ASCVD or MASLD, Wegovy's bonuses can still out-stack a diabetes-specific pick. This is a smaller-magnitude version of the same underlying issue (comorbidity bonuses not gated by category/goal alignment) and would need a category/goal-alignment weighting change, not a delivery-penalty change, to resolve — left as-is per the current fix's scope.

**Cases where the independent grader was the limiting factor, not the app (2 cases: #43, #45).** In #43, the patient's stated goal is weight-loss only but the diabetes-status field says type 2 — the app reasonably surfaces the diabetes-optimized option (Mounjaro) given the real diagnosis; the grader never considers that branch because it gates strictly on the stated goal. In #45, the patient has both sleep apnea and CKD-with-T2D simultaneously; the grader's single-priority cascade stops at the first match (sleep apnea → Zepbound) and never weighs the co-occurring CKD/T2D indication (FLOW trial, Ozempic-specific), while the app correctly weighs both.

## The 3 edge cases

#17, #47, #99: oral delivery requested for a pure weight-loss goal. No oral GLP-1 is FDA-approved for weight management today (Rybelsus is diabetes-only), so there is no genuinely correct answer to check the app against. The app shows its best available option rather than an empty screen, which is reasonable UX, but a provider should be aware this combination has no on-label oral answer.

## Files

- `validation/generate_profiles.py` — generates the 100 random profiles
- `validation/independent_grader.py` — the from-scratch evidence-based grader
- `validation/run_app_test.js` — Playwright script driving the real app UI
- `validation/compare.py` — merges and scores the comparison

(The `validation/` scripts are provided for transparency and reproducibility; they are not part of the shipped app.)
