import json

with open("graded_profiles.json") as f:
    graded = {g["id"]: g for g in json.load(f)}

with open("app_results.json") as f:
    app_results = {r["id"]: r for r in json.load(f)}

BMI_LABEL = {
    "under25": "<25", "25-29": "25–29.9", "30-34": "30–34.9",
    "35plus": "35+", "unsure": "Not calc.",
}
DIAB_LABEL = {"none": "No", "prediabetes": "Prediabetes", "type2": "Type 2"}
GOAL_LABEL = {"weight-loss": "Weight loss", "diabetes": "Diabetes", "both": "Both"}
DELIVERY_LABEL = {"injection": "Injection", "oral": "Oral", "either": "Either"}
COMORBID_LABEL = {
    "cardiovascular": "ASCVD", "bp": "HTN", "cholesterol": "Hyperlipidemia",
    "sleep-apnea": "OSA", "fatty-liver": "MASLD", "ckd": "CKD", "none": "None",
}

rows = []
n_exact = 0
n_acceptable = 0
n_mismatch = 0
n_edge = 0

for i in range(1, 101):
    g = graded[i]
    a = app_results[i]
    app_top = a["appTop"]

    if g["edge_case"]:
        status = "edge_case"
        n_edge += 1
    elif app_top == g["expected_primary"]:
        status = "exact"
        n_exact += 1
    elif app_top in g["expected_acceptable"]:
        status = "acceptable"
        n_acceptable += 1
    else:
        status = "mismatch"
        n_mismatch += 1

    rows.append({
        "id": i,
        "goal": GOAL_LABEL[g["goal"]],
        "bmi": BMI_LABEL[g["bmiRange"]],
        "diabetes": DIAB_LABEL[g["diabetesStatus"]],
        "delivery": DELIVERY_LABEL[g["delivery"]],
        "comorbidities": ", ".join(COMORBID_LABEL[c] for c in g["comorbidities"]),
        "app_top": app_top,
        "expected_primary": g["expected_primary"],
        "expected_acceptable": ", ".join(g["expected_acceptable"]),
        "status": status,
        "edge_case_note": g["edge_case"],
        "app_top_reasons": a["appTopReasons"],
    })

summary = {
    "n": 100,
    "exact": n_exact,
    "acceptable": n_acceptable,
    "mismatch": n_mismatch,
    "edge_case": n_edge,
    "exact_pct": round(n_exact / 100 * 100, 1),
    "evidence_consistent_pct": round((n_exact + n_acceptable) / 100 * 100, 1),
}

with open("final_results.json", "w") as f:
    json.dump({"summary": summary, "rows": rows}, f, indent=2)

print(json.dumps(summary, indent=2))
print()
print("Mismatches:")
for r in rows:
    if r["status"] == "mismatch":
        print(f"  #{r['id']}: app picked {r['app_top']!r}, expected one of "
              f"[{r['expected_acceptable']}] "
              f"(goal={r['goal']}, bmi={r['bmi']}, diabetes={r['diabetes']}, "
              f"delivery={r['delivery']}, comorbidities=[{r['comorbidities']}])")

print()
print("Edge cases:")
for r in rows:
    if r["status"] == "edge_case":
        print(f"  #{r['id']}: app picked {r['app_top']!r} -- {r['edge_case_note']}")
