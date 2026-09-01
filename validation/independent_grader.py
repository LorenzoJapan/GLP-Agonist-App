"""
Independent, evidence-based ground truth for what the "best first choice"
GLP-1 option should be for a given patient profile.

Written from scratch against the three source papers, deliberately NOT by
reading or reusing the app's scoreOption() function in index.html. The goal
is a genuinely independent second opinion, not a self-check of the algorithm
against itself.

Evidence this logic is grounded in:
  [1] Moiz et al., Ann Intern Med 2025 (GLP-1 RAs for weight loss, no diabetes)
      -> No head-to-head RCTs between agents; heterogeneity prevented
         meta-analysis. Tirzepatide (Zepbound) showed larger point estimates
         for weight loss than semaglutide (Wegovy) across separate trials,
         but the paper explicitly declines to rank them comparatively.
  [2] Yao et al., BMJ 2024 (GLP-1 RAs for type 2 diabetes, network meta-analysis)
      -> Tirzepatide (Mounjaro) ranked most effective for HbA1c and fasting
         glucose reduction, high confidence of evidence (network meta-analysis
         is designed to support this kind of ranking claim).
  [3] Rosen & Ingelfinger, NEJM 2026 (GLP-1 receptor agonists review)
      -> Wegovy: CV risk reduction in adults with obesity/overweight + established
         ASCVD (SELECT trial).
      -> Ozempic: CV risk reduction in adults with T2D + established ASCVD
         (SUSTAIN-6); CKD risk reduction in adults with T2D + CKD (FLOW trial,
         FDA approved Jan 2025).
      -> Rybelsus: CV risk reduction in adults with T2D (SOUL trial) -- newer,
         superiority result, supersedes the older PIONEER-6 noninferiority-only
         finding.
  [5] Nicholls et al., for the SURPASS-CVOT Investigators. N Engl J Med
      2025;393(24):2409-20 (SURPASS-CVOT)
      -> Mounjaro: FDA-approved (2026) to help lower cardiovascular risk in
         adults with T2D and established ASCVD, based on a trial of
         tirzepatide vs. dulaglutide (an active GLP-1 comparator with its own
         placebo-superiority CV evidence from REWIND) in T2D + established
         ASCVD -- noninferior for the composite of CV death/MI/stroke (HR
         0.92, 95% CI 0.83-1.01) but did NOT reach the prespecified
         superiority threshold (P=0.09). This is weaker evidence than
         Ozempic's SUSTAIN-6 or Rybelsus's SOUL trial, both placebo-controlled
         superiority results, so Mounjaro is graded as an acceptable
         CV-indicated alternate for T2D+ASCVD, not the primary pick, when
         Ozempic is also eligible.
      -> Zepbound: moderate-to-severe obstructive sleep apnea with obesity
         (SURMOUNT-OSA); Wegovy and Zepbound both showed improvement in
         MASLD-related liver fat/fibrosis.
      -> Rybelsus is an oral GLP-1 option, but it is a type 2 diabetes drug
         only, not a weight-management drug.
  [4] Wharton et al., for the OASIS 4 Study Group. N Engl J Med 2025;393(11):
      1077-1087 (oral semaglutide 25 mg in adults with overweight/obesity)
      -> FDA-approved Dec 2025 as "Wegovy (pill)": once-daily oral
         semaglutide 25 mg, the first oral GLP-1 approved for chronic weight
         management. Per FDA labeling and the manufacturer's approval
         announcement, it carries the same cardiovascular-risk-reduction
         indication as injectable Wegovy (adults with established
         cardiovascular disease and overweight/obesity), grounded in the same
         SELECT trial population/mechanism rather than a separate CV outcomes
         trial of the oral formulation itself.

This module returns, for each profile:
  - primary: the single most evidence-supported first choice, when the
    evidence supports picking one
  - acceptable: the full set of clinically defensible first choices,
    including "primary" -- for the genuine ties described above (e.g. no
    head-to-head weight-loss data), this set has more than one member, and
    matching ANY of them counts as evidence-consistent, not just "primary"
  - edge_case: a note when no catalog option is well-supported by the
    evidence for this exact combination
"""

DRUGS = {
    "Wegovy": {"category": "weight-loss", "form": "injection"},
    "Zepbound": {"category": "weight-loss", "form": "injection"},
    "Ozempic": {"category": "diabetes", "form": "injection"},
    "Mounjaro": {"category": "diabetes", "form": "injection"},
    "Rybelsus": {"category": "diabetes", "form": "oral"},
    "Wegovy (pill)": {"category": "weight-loss", "form": "oral"},
}


def delivery_ok(drug_form, delivery):
    if delivery == "either":
        return True
    return drug_form == delivery


def grade(profile):
    goal = profile["goal"]
    bmi = profile["bmiRange"]
    diabetes = profile["diabetesStatus"]
    delivery = profile["delivery"]
    co = set(profile["comorbidities"])

    # FDA labeling for the weight-management-indicated options requires BMI
    # >=30, or BMI >=27 plus a weight-related comorbidity (or a type 2
    # diabetes diagnosis) -- not simply a stated wish to lose weight. The
    # "25-29.9" bucket straddles the 27 cutoff, so it only counts as meeting
    # the threshold when paired with a qualifying comorbidity/diagnosis;
    # "not yet calculated" can't be ruled in or out, so it isn't gated.
    has_weight_related_comorbidity = bool(co - {"none"}) or diabetes == "type2"
    bmi_qualifies_weight_mgmt = bmi in ("30-34", "35plus", "unsure") or (
        bmi == "25-29" and has_weight_related_comorbidity
    )
    weight_mgmt_eligible = goal in ("weight-loss", "both") and bmi_qualifies_weight_mgmt
    # diabetes-category drugs are approved for type 2 diabetes; prediabetes is
    # only supportively discussed (NEJM review) as a possible future/preventive
    # use, not an approved indication, so it's treated as a soft/eligible signal
    # alongside an explicit diabetes goal, matching how a clinician would still
    # reasonably consider these drugs off-label/preventively.
    diabetes_mgmt_eligible = goal in ("diabetes", "both") or diabetes in ("type2", "prediabetes")

    def elig(name):
        d = DRUGS[name]
        if not delivery_ok(d["form"], delivery):
            return False
        if d["category"] == "weight-loss":
            return weight_mgmt_eligible
        return diabetes_mgmt_eligible

    candidates = [n for n in DRUGS if elig(n)]

    if not candidates:
        return {
            "primary": None,
            "acceptable": set(),
            "edge_case": "No approved option matches this combination of goal, BMI, "
                          "diabetes status, and delivery preference -- either no oral "
                          "option fits the stated goal (Rybelsus is diabetes-only, "
                          "Wegovy (pill) is weight-management-only), or the patient "
                          "doesn't meet the BMI/diabetes threshold for any catalog "
                          "option's approved indication at all. The latter can be a "
                          "genuinely correct 'no GLP-1 is indicated' answer, not "
                          "necessarily a gap in the catalog.",
        }

    # --- Priority 1: ASCVD -> cardiovascular-risk-reduction indication ---
    if "cardiovascular" in co:
        cv_candidates = []
        if diabetes == "type2":
            if "Ozempic" in candidates:
                cv_candidates.append("Ozempic")
            if "Mounjaro" in candidates:
                cv_candidates.append("Mounjaro")
            if "Rybelsus" in candidates:
                cv_candidates.append("Rybelsus")
        if "Wegovy" in candidates:
            cv_candidates.append("Wegovy")
        if "Wegovy (pill)" in candidates:
            cv_candidates.append("Wegovy (pill)")
        if cv_candidates:
            # When both a diabetes-specific and a weight-loss-specific CV option
            # are simultaneously eligible (goal=both, T2D, ASCVD), the literature
            # doesn't force a single winner -- treat all as acceptable, but prefer
            # the diabetes-specific injectable (Ozempic) as primary since it also
            # picks up glycemic control and, often, CKD risk in the same patient.
            # Ozempic is also preferred as primary over Mounjaro specifically
            # because SUSTAIN-6 was a placebo-controlled superiority result,
            # while Mounjaro's SURPASS-CVOT was a noninferiority-to-dulaglutide
            # result that did not reach superiority (P=0.09) -- Mounjaro is a
            # legitimate, FDA-approved, evidence-consistent alternate here, just
            # not graded as the strongest evidence when a choice must be made.
            # Between the two Wegovy forms (only both-eligible when delivery is
            # "either"), the injectable is primary since it's the original,
            # longer-established CV-outcomes formulation (SELECT); the oral pill
            # is an acceptable alternate on the same indication (OASIS 4 dosing,
            # CV benefit per labeling rather than a dedicated CV-outcomes trial).
            primary = "Ozempic" if "Ozempic" in cv_candidates else cv_candidates[0]
            return {"primary": primary, "acceptable": set(cv_candidates), "edge_case": None}

    # --- Priority 2: sleep apnea -> Zepbound (SURMOUNT-OSA is drug-specific) ---
    if "sleep-apnea" in co and "Zepbound" in candidates:
        return {"primary": "Zepbound", "acceptable": {"Zepbound"}, "edge_case": None}

    # --- Priority 3: CKD in T2D -> Ozempic (FLOW trial is drug-specific) ---
    if "ckd" in co and diabetes == "type2" and "Ozempic" in candidates:
        return {"primary": "Ozempic", "acceptable": {"Ozempic"}, "edge_case": None}

    # --- Priority 4: MASLD -> Wegovy or Zepbound (both supported, no ranking) ---
    if "fatty-liver" in co:
        masld_candidates = [n for n in ("Wegovy", "Zepbound") if n in candidates]
        if masld_candidates:
            return {"primary": masld_candidates[0], "acceptable": set(masld_candidates), "edge_case": None}

    # --- Priority 5: type 2 diabetes, no specific comorbidity match ---
    if diabetes == "type2" and goal in ("diabetes", "both"):
        diabetes_candidates = [n for n in ("Mounjaro", "Ozempic", "Rybelsus") if n in candidates]
        if diabetes_candidates:
            # Mounjaro is the network-meta-analysis-ranked top pick (BMJ 2024,
            # high confidence), so it's primary when injectable/either; but since
            # this is a comparative-efficacy claim rather than a distinct approved
            # indication, Ozempic/Rybelsus (when delivery-eligible) are graded as
            # acceptable alternates, not mismatches.
            primary = "Mounjaro" if "Mounjaro" in diabetes_candidates else diabetes_candidates[0]
            return {"primary": primary, "acceptable": set(diabetes_candidates), "edge_case": None}

    # --- Priority 6: weight-loss goal, no specific comorbidity/diabetes match ---
    if weight_mgmt_eligible:
        weight_candidates = [n for n in ("Wegovy", "Zepbound", "Wegovy (pill)") if n in candidates]
        if weight_candidates:
            # No head-to-head RCTs per Annals 2025 -- both are acceptable, tied.
            return {"primary": weight_candidates[0], "acceptable": set(weight_candidates), "edge_case": None}

    # --- Priority 7: remaining diabetes-eligible cases (e.g. prediabetes only) ---
    if candidates:
        return {"primary": candidates[0], "acceptable": set(candidates), "edge_case": None}

    return {"primary": None, "acceptable": set(), "edge_case": "No confident evidence-based match."}


if __name__ == "__main__":
    import json
    with open("profiles.json") as f:
        data = json.load(f)
    graded = []
    for p in data["profiles"]:
        g = grade(p)
        graded.append({**p, "expected_primary": g["primary"],
                        "expected_acceptable": sorted(g["acceptable"]),
                        "edge_case": g["edge_case"]})
    with open("graded_profiles.json", "w") as f:
        json.dump(graded, f, indent=2)
    edge_cases = [g for g in graded if g["edge_case"]]
    print(f"Graded {len(graded)} profiles. Edge cases with no clean evidence-based match: {len(edge_cases)}")
