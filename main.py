from datetime import datetime

print("=== StudyNavigator v0.3 (rule-based) ===")

# ---- input ----
decision = input("What is the decision you are making? ").strip()
options_raw = input("What options do you have? (separate by comma) ").strip()
goal = input("What is your main goal? ").strip()
risk = input("What is your biggest risk or concern? ").strip()

options = [o.strip() for o in options_raw.split(",") if o.strip()]
if len(options) == 0:
    options = ["Option A", "Option B"]

# ---- quick self-rating ----
print("\nRate these from 1 (low) to 5 (high).")
impact = input("How much does this help your goal? ").strip()
cost = input("How much time/effort does it cost? ").strip()
risk_level = input("How risky is it? ").strip()
reversible = input("How reversible is it? (5 = easy to undo) ").strip()

def to_int(x, default):
    try:
        v = int(x)
        if v < 1: return 1
        if v > 5: return 5
        return v
    except:
        return default

impact = to_int(impact, 3)
cost = to_int(cost, 3)
risk_level = to_int(risk_level, 3)
reversible = to_int(reversible, 3)

# ---- scoring rule ----
score = 20 * impact + 10 * reversible - 15 * cost - 15 * risk_level
if score < 0: score = 0
if score > 100: score = 100

# ---- recommendation ----
if score >= 65:
    rec = f"Recommendation: Lean toward '{options[0]}'"
elif score >= 45:
    rec = "Recommendation: It’s close. Consider a small test first."
else:
    rec = f"Recommendation: Lean toward '{options[-1]}' or delay the decision."

reasons = [
    f"Impact on your goal is rated {impact}/5.",
    f"Time/effort cost is rated {cost}/5.",
    f"Risk level is rated {risk_level}/5, reversibility is {reversible}/5."
]

risk_note = "Risk note: Make a backup plan before committing."

# ---- save ----
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

record = (
    f"\n[{timestamp}]\n"
    f"Decision: {decision}\n"
    f"Options: {', '.join(options)}\n"
    f"Goal: {goal}\n"
    f"Concern: {risk}\n"
    f"Ratings: impact={impact}, cost={cost}, risk={risk_level}, reversible={reversible}\n"
    f"Score: {score}/100\n"
    f"{rec}\n"
    f"Reasons:\n"
    f"- {reasons[0]}\n"
    f"- {reasons[1]}\n"
    f"- {reasons[2]}\n"
    f"{risk_note}\n"
)

with open("decisions.txt", "a", encoding="utf-8") as f:
    f.write(record)

# ---- output ----
print("\n--- Result ---")
print(f"Score: {score}/100")
print(rec)
print("Reasons:")
for r in reasons:
    print("-", r)
print(risk_note)
print("\nSaved to decisions.txt")