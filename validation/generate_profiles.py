"""
Generate 100 random synthetic patient profiles for independent validation
of the GLP-1 Match app's ranking algorithm.

This script ONLY generates random inputs. The "correct answer" ground truth
is computed separately in independent_grader.py, written from scratch against
the three source papers rather than copied from the app's own scoring code,
so the comparison is a genuine independent check rather than the algorithm
grading itself.
"""
import json
import random

SEED = 20260821  # today's date at time of test, for reproducibility
random.seed(SEED)

GOALS = ["weight-loss", "diabetes", "both"]
BMI_RANGES = ["under25", "25-29", "30-34", "35plus", "unsure"]
DIABETES_STATUS = ["none", "prediabetes", "type2"]
DELIVERY = ["injection", "oral", "either"]
COMORBIDITIES = ["cardiovascular", "bp", "cholesterol", "sleep-apnea", "fatty-liver", "ckd"]

N = 100
profiles = []

for i in range(N):
    goal = random.choice(GOALS)
    bmi = random.choice(BMI_RANGES)
    diabetes = random.choice(DIABETES_STATUS)
    delivery = random.choice(DELIVERY)

    # Comorbidities: each of the 6 real conditions included independently
    # with 22% probability (mirrors a realistic-ish rate of multimorbidity
    # in a GLP-1-eligible population without hand-tuning per test case).
    # If none are selected, the profile explicitly picks "none of these",
    # matching the one required selection the real UI enforces.
    selected = [c for c in COMORBIDITIES if random.random() < 0.22]
    if not selected:
        selected = ["none"]

    profiles.append({
        "id": i + 1,
        "goal": goal,
        "bmiRange": bmi,
        "diabetesStatus": diabetes,
        "delivery": delivery,
        "comorbidities": selected,
    })

with open("profiles.json", "w") as f:
    json.dump({"seed": SEED, "profiles": profiles}, f, indent=2)

print(f"Generated {N} profiles with seed {SEED}")
# quick distribution sanity check
from collections import Counter
print("goal:", Counter(p["goal"] for p in profiles))
print("bmi:", Counter(p["bmiRange"] for p in profiles))
print("diabetes:", Counter(p["diabetesStatus"] for p in profiles))
print("delivery:", Counter(p["delivery"] for p in profiles))
none_count = sum(1 for p in profiles if p["comorbidities"] == ["none"])
print("comorbidity-free profiles:", none_count)
