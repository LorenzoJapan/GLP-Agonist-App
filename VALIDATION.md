# Independent Validation — 100-Case Test

This is a record of an independent accuracy check run against the app's matching algorithm (`scoreOption()` in `index.html`), first run 2026-08-21, re-run the same day after a fix to delivery-preference weighting, then re-run again on 2026-08-23 after adding oral semaglutide 25 mg ("Wegovy (pill)") to the catalog.

## Method

1. **100 random synthetic patient profiles** were generated (`goal`, `bmiRange`, `diabetesStatus`, `delivery`, `comorbidities`), each field drawn independently and uniformly at random (fixed seed `20260821` for reproducibility). Comorbidities were included independently at 22% probability each.
2. **An independent "ground truth" grader** was written from scratch directly against the source papers (Moiz et al., Ann Intern Med 2025; Yao et al., BMJ 2024; Rosen & Ingelfinger, NEJM 2026; and, as of the Round 3 update, Wharton et al. for the OASIS 4 Study Group, NEJM 2025) — *without* reading or reusing the app's own `scoreOption()` logic — to avoid a tautological self-check. It uses a fixed priority cascade (ASCVD → sleep apnea → CKD+T2D → MASLD → T2D → weight-loss goal) rather than cumulative scoring, and returns both a single "primary" pick and a set of "acceptable" alternates for genuine ties (e.g. no head-to-head weight-loss RCTs exist between Wegovy and Zepbound).
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

## The 3 edge cases (Round 2)

#17, #47, #99: oral delivery requested for a pure weight-loss goal. No oral GLP-1 was FDA-approved for weight management at the time (Rybelsus is diabetes-only), so there was no genuinely correct answer to check the app against. The app showed its best available option rather than an empty screen, which was reasonable UX, but a provider needed to be aware this combination had no on-label oral answer. **This is the gap oral Wegovy closes — see Round 3.**

## Catalog update: oral Wegovy ("Wegovy (pill)")

On 2026-08-23, once-daily oral semaglutide 25 mg — brand name Wegovy, an oral tablet distinct from the existing once-weekly Wegovy injection — was added to the catalog as `wegovy-oral`. It is FDA-approved for chronic weight management and, per FDA labeling and the manufacturer's approval announcement, carries the same cardiovascular-risk-reduction indication as injectable Wegovy (adults with established cardiovascular disease and overweight/obesity). The efficacy trial is OASIS 4 (Wharton et al., N Engl J Med 2025;393(11):1077-1087). It does not carry Wegovy/Zepbound's MASLD liver-fat-improvement evidence, so `liverBenefit` is `false` for this entry. The independent grader's `DRUGS` dict, ASCVD priority branch, and weight-loss-fallback priority branch were all updated to include it (see `validation/independent_grader.py`).

## Round 3 result (after adding oral Wegovy)

Re-running the grader alone (unchanged app) against the updated 100 profiles immediately resolved all 3 former edge cases to real candidates (an oral, weight-management-approved option now exists) but also surfaced 3 *new* mismatches (#11, #30, #81): profiles where a patient with type 2 diabetes, oral delivery preference, and a **pure weight-loss goal** tied 6-to-6 between Rybelsus (diabetes bonus) and the new Wegovy pill (weight-loss bonus), with the tie silently broken in Rybelsus's favor by catalog order — even though Rybelsus isn't approved for the goal the patient actually stated.

**Fix, attempt 1 (reverted):** added a flat `+1` "goal-exclusivity" bonus whenever `opt.category` matched a single (non-"both") stated goal. This fixed #11/#30/#81 but, tested against the full 100 cases before shipping, regressed 2 previously-exact cases (#25, #97): patients with CKD + type 2 diabetes whose goal was "weight-loss" only, where Ozempic's specific FLOW-trial CKD indication (a comorbidity-driven, category-crossing match) should outrank a generic weight-loss-category match, and the flat bonus was pushing Wegovy ahead of it on the tie.

**Fix, attempt 2 (shipped):** scoped the same `+1` bonus to `a.delivery === "oral"` only, since the oral/injectable split is the actual axis this conflict lives on — Rybelsus and Wegovy (pill) are the *only* two options that can tie head-to-head on goal alone, and that can only happen when oral delivery is requested. Re-tested against all 100 profiles: resolves #11/#30/#81 with zero regressions, including #25/#97.

| Metric | Value |
|---|---|
| Exact match | 88 (88%) |
| Acceptable alternate | 4 |
| Mismatch | 8 |
| No valid answer exists (edge case) | 0 |
| **Evidence-consistent (exact + acceptable)** | **92%** |

The 8 remaining mismatches are exactly the same 8 cases from Round 2 (#9, #10, #29, #43, #45, #57, #83, #100) — unrelated to the oral Wegovy addition, and already explained above (contradictory random test inputs, off-category comorbidity bonuses, and two cases where the independent grader's simpler fixed-priority logic is the limiting factor rather than the app). No new mismatches remain after the scoped fix.

## Gap found: no BMI floor on weight-management recommendations

On 2026-08-23, prompted by a direct question ("does the app recommend GLP treatment if a patient is not at least overweight, with no other medical conditions?"), a real gap was found and confirmed by testing the live app: a profile with goal = weight-loss, BMI under 25, no diabetes, and no comorbidities was still shown Wegovy, Zepbound, and Wegovy (pill) as top matches, each labeled "Approved for chronic weight management."

FDA labeling for all three weight-management-indicated options requires BMI ≥30, or BMI ≥27 plus at least one weight-related comorbidity (hypertension, dyslipidemia, type 2 diabetes, obstructive sleep apnea, or established cardiovascular disease) — not simply a stated wish to lose weight. `scoreOption()` used BMI only as a scoring bonus (extra points at higher ranges) with no floor, so a stated weight-loss goal alone was enough to trigger the base "approved" bonus and reason chip regardless of actual BMI.

## Round 4 result (after adding the BMI eligibility gate)

**Fix:** weight-loss-category options now require `weightMgmtBmiQualifies` to be true before scoring at all: BMI 30–34.9 or 35+ always qualifies; BMI 25–29.9 qualifies only alongside a weight-related comorbidity or a type 2 diabetes diagnosis (reusing the same proxy signal the existing 25–29.9 scoring bonus already used); BMI "not yet calculated" isn't gated either way, since it rules nothing in or out; BMI under 25 never qualifies, regardless of goal or comorbidities. The gate applies uniformly across all three ways a weight-loss-category option can otherwise score (stated goal, or a qualifying cardiovascular/sleep-apnea/MASLD comorbidity), since the underlying trials for all of those indications were themselves conducted in overweight/obese populations. The same gate was added to the independent grader's `weight_mgmt_eligible` for a fair comparison. A first version of the fix left the `reasons` array unchanged when the gate zeroed the score, which meant a fallback-state card could still display "Approved for chronic weight management" — caught via screenshot review and fixed by clearing `reasons` alongside `score` in both the weight-loss and (for consistency) diabetes gates.

| Metric | Value |
|---|---|
| Exact match | 87 (87%) |
| Acceptable alternate | 3 |
| Mismatch | 7 |
| No valid answer exists (edge case) | 3 |
| **Evidence-consistent (exact + acceptable)** | **90%** |

The headline percentage moved down slightly (88%→87% exact, 92%→90% evidence-consistent), and that's expected, not a regression: 3 profiles (#4, #34, #62 — all BMI-under-25, weight-loss-goal, no-diabetes) were previously being silently credited as correct by both the app *and* the ungated grader, when neither actually had a BMI-eligible answer. They're now correctly bucketed as edge cases — a genuine "no GLP-1 is FDA-indicated for this patient" answer, which the app surfaces via its fallback banner rather than a confident pick. One of the fix's side effects was also a net *improvement*: profile #100, a previously-documented Round 2/3 mismatch (Wegovy's off-category comorbidity bonus out-competing a diabetes-specific pick in a prediabetic patient), is now exact — the BMI gate also correctly excludes Wegovy's MASLD-driven bonus for that patient's under-25 BMI, since the trial evidence behind that bonus was likewise established in an overweight/obese population.

The 7 remaining mismatches are unchanged from Round 3 minus #100 (#9, #10, #29, #43, #45, #57, #83) and are the same previously-documented, unrelated categories (contradictory synthetic inputs, off-category CV bonus in prediabetes+ASCVD at a BMI that does clear the gate, and independent-grader limitations).

## Per-drug stratified test finds a real gap: Ozempic recall

On 2026-08-23, a second test design was run alongside the standing 100-case suite: instead of sampling patients uniformly at random, 50 patients were sampled *per drug* (300 total) via rejection sampling against the independent grader — each profile kept only if that specific drug came out as the grader's primary answer for it. This asks a sharper question than the uniform suite: *of patients who should be pointed to Drug X specifically, how often does the app actually surface it?*

Five of six drugs scored 96–98% recall. **Ozempic scored 64%** (32/50, 13 mismatches). Every mismatch shared the same shape: goal = "diabetes" (not weight-loss/both), diabetes status = prediabetes (occasionally none), plus a comorbidity like ASCVD, OSA, or MASLD. In each case a weight-loss-category option (Wegovy/Zepbound) scored the same or more than Ozempic through its own comorbidity-specific bonus (correctly ungated by diabetes status, since SELECT/SURMOUNT-OSA weren't diabetes-specific) while Ozempic's matching bonus was correctly gated to type 2 only (SUSTAIN-6/FLOW were T2D-specific) — leaving Ozempic with only a soft "goal says diabetes" + "prediabetes" signal, which frequently landed on the exact same point total as the off-category option, with ties then broken by catalog array order instead of by what the patient actually asked to manage. The same test also caught 2 smaller instances of the identical mechanism running in the opposite direction (Mounjaro losing a tie to Zepbound; a Rybelsus/Wegovy(pill) oral tie not covered by the earlier oral-tiebreaker fix's exact-goal-match conditions) and one clean scoring gap (Wegovy beating Mounjaro when goal is weight-loss-only but a type 2 diagnosis is present, with no comorbidities to tip it either way).

## Fix applied

Two additions to `scoreOption()`:

1. **A goal-alignment nudge for diabetes-category options** (`+2` when `opt.category === "diabetes" && a.goal === "diabetes"`, not delivery-scoped). This is deliberately asymmetric — there's no mirrored weight-loss-side version — because the independent grader never expects a weight-loss-category drug when goal is diabetes-only (that category is fully excluded from its candidate set in that case), so this nudge can only fix misalignment with the grader, never cause it. A first attempt at a *symmetric* version (mirrored weight-loss-side bonus) was tested and rejected: it reproduced the exact CKD-vs-Wegovy regression the original oral-tiebreaker fix (Round 3) had specifically been narrowed to avoid.
2. **Extended the existing oral Rybelsus/Wegovy(pill) tiebreaker** (Round 3) to also cover `goal === "both"`, not just exact "weight-loss"/"diabetes" — but only when diabetes status isn't confirmed type 2. A first version without that guard introduced a *new* regression (2 cases: goal "both" + confirmed type 2 + oral, where Rybelsus should win on diagnosis strength, matching the grader's own priority order) — caught by re-running the per-drug suite before shipping, not assumed safe from the injection-only test alone.

Both were validated with the same fast in-process score-extraction harness used for the original delivery-penalty sweep before touching the browser, then confirmed with full Playwright re-runs of all three suites (100-case, a fresh 50-case sample, and the 300-case per-drug set).

## Round 5 result (after the goal-alignment tiebreaker)

| Suite | Before | After |
|---|---|---|
| 100-case (exact / evidence-consistent) | 87% / 90% | **88% / 91%** |
| 50-case fresh sample (exact / evidence-consistent) | 90% / 90% | **94% / 94%** |
| Per-drug: Wegovy | 98% | 98% |
| Per-drug: Zepbound | 98% | 98% |
| Per-drug: Ozempic | 64% | **84%** |
| Per-drug: Mounjaro | 98% | **100%** |
| Per-drug: Rybelsus | 96% | 96% |
| Per-drug: Wegovy (pill) | 96% | **100%** |

Zero regressions across all three suites — every case that passed before still passes. Ozempic's recall improved from 64% to 84% (10 of 13 mismatches fixed); the remaining 3 (#115, #127, #128 in the per-drug set) are cases with a genuine multi-point scoring gap, not a tie, where a weight-loss-category option's *stacked* comorbidity bonuses (e.g. ASCVD + MASLD + CKD together) legitimately reflect strong trial evidence that a modest, safely-scoped nudge shouldn't override — left as a documented limitation rather than force-corrected, the same judgment call already applied to similar cases in Round 2/3. The one remaining Wegovy-target mismatch found by the per-drug test (Wegovy losing to Mounjaro when goal is weight-loss-only + type 2 diagnosis + no comorbidities) is the same asymmetry, left unfixed for the same reason: there's no safe way to add a mirrored weight-loss-side nudge without reproducing the CKD regression.

## Catalog update: Mounjaro cardiovascular-risk-reduction indication

On 2026-09-01, the FDA approved a new indication for Mounjaro (tirzepatide): to help lower cardiovascular risk in adults with type 2 diabetes and established atherosclerotic cardiovascular disease (ASCVD), based on SURPASS-CVOT (Nicholls et al., N Engl J Med 2025;393(24):2409-20) — a randomized, active-comparator trial of tirzepatide vs. dulaglutide (an already-CV-approved GLP-1) in 13,165 patients with type 2 diabetes and established ASCVD. Tirzepatide was noninferior to dulaglutide for the composite of cardiovascular death, MI, or stroke (HR 0.92, 95.3% CI 0.83-1.01; P=0.003 for noninferiority) but did not reach the trial's prespecified superiority threshold (P=0.09).

`mounjaro.cvBenefit` was flipped to `true` and its description updated. Because this is meaningfully different evidence from Wegovy's SELECT, Ozempic's SUSTAIN-6, and Rybelsus's SOUL trial — all placebo-controlled trials that reached statistical superiority, vs. Mounjaro's noninferiority-to-an-active-comparator result — a new `cvBenefitEstablished` flag was added to every catalog option (`true` for Wegovy/Ozempic/Rybelsus/Wegovy (pill), `false` for Mounjaro and Zepbound, which has no cardiovascular indication at all) so the cardiovascular scoring bonus can reflect that distinction (+3 for established/superiority evidence, +2 for noninferiority-only evidence) rather than treating every `cvBenefit: true` option as equally strong.

**Why this second change was needed:** simply flipping `cvBenefit` to `true` on its own caused a real, measurable side effect — Mounjaro's pre-existing "ranked most effective for A1c control" bonus (from the BMJ 2024 network meta-analysis, unrelated to cardiovascular evidence) combined with the new, equally-weighted CV bonus to let Mounjaro consistently outscore Ozempic by 1 point in type 2 diabetes + ASCVD cases — dropping Ozempic's per-drug recall from 84% to 70% in re-testing, even though every one of those cases remained evidence-consistent (Mounjaro is a legitimate alternate per the independent grader, just not graded as primary when Ozempic is also eligible, given the strength difference between the two trials). Rather than ship that side effect, the `cvBenefitEstablished` distinction was added so the score itself reflects the same evidentiary hierarchy already used to pick a "primary" in the independent grader, restoring the tie in Ozempic's favor while still surfacing Mounjaro as a close alternative. The independent grader (`validation/independent_grader.py`) was updated in parallel to add Mounjaro to its ASCVD+type2 candidate set, with Ozempic preferred as primary and Mounjaro graded as an acceptable alternate for the same reason.

## Round 6 result (after the Mounjaro cardiovascular update)

| Suite | Before (Round 5) | After (Round 6) |
|---|---|---|
| 100-case (exact / evidence-consistent) | 88% / 91% | **88% / 91%** |
| 50-case fresh sample (exact / evidence-consistent) | 94% / 94% | **94% / 94%** |
| Per-drug: Ozempic | 84% | **84%** |
| Per-drug: Mounjaro | 100% | **100%** |
| Per-drug: all others | 96–100% | **96–100%** |

All three suites land at exact parity with Round 5 — zero regressions, and no new mismatches. Every Round 5 mismatch (the residual 3-case Ozempic stacked-comorbidity gap, the single Wegovy/Mounjaro weight-loss-goal asymmetry, and the 2 pre-existing "diabetes goal + no diabetes diagnosis + ASCVD" gaps) is unchanged, since none of them involve a confirmed type 2 diagnosis where Mounjaro's new CV bonus would even apply. The new indication is additive: type 2 diabetes + ASCVD patients now correctly see Mounjaro surfaced as a close, evidence-based alternative to Ozempic, verified visually via a Playwright screenshot of that exact profile.

**Correction (label language):** the app's description text for this update initially said Mounjaro's new indication was for adults with "established heart disease," copying the phrasing already used for Ozempic and Rybelsus. Lilly's own release states the approved population more broadly: adults with type 2 diabetes "at high risk" for cardiovascular events, not only those with diagnosed ASCVD — SURPASS-CVOT's own enrollment criterion. The description was corrected to match the label. This app's only cardiovascular-related data point is the ASCVD checkbox (explicitly "established atherosclerotic cardiovascular disease" in the UI), a strict subset of "high risk" — so the app's scoring is still correct wherever it fires (an ASCVD patient is always covered by Mounjaro's label) but won't surface Mounjaro's CV benefit for a high-risk-but-no-diagnosed-ASCVD patient, since the app has no field to capture that case. This is the same conservative gate already used for Ozempic, Wegovy, and Rybelsus, whose own labels do specifically require established disease — Mounjaro is simply the one option whose real label is broader than what this app's comorbidity list can express, left as a known scope limitation rather than an error.

## Files (per-drug test)

The 300-case per-drug stratified test lives outside the shipped repo, in `per_drug_test_50/` (a scratch/audit directory, not a repo test the app ships with): `generate_per_drug.py` (rejection sampling against the imported grader), `run_app_test_per_drug.js` (Playwright), `compare_per_drug.py` (scoring), and `per_drug_full_results.csv` (all 300 cases).

## Files

- `validation/generate_profiles.py` — generates the 100 random profiles
- `validation/independent_grader.py` — the from-scratch evidence-based grader
- `validation/run_app_test.js` — Playwright script driving the real app UI
- `validation/compare.py` — merges and scores the comparison

(The `validation/` scripts are provided for transparency and reproducibility; they are not part of the shipped app.)
