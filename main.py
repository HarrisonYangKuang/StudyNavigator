from datetime import datetime

print("=== StudyNavigator v0.4 (with reflection) ===")
mode = input("Choose mode: (1) New decision  (2) Reflect on a past decision: ").strip()

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def save(text):
    with open("decisions.txt", "a", encoding="utf-8") as f:
        f.write(text)

if mode == "1":
    decision = input("What was the decision? ").strip()
    options = input("What options did you have? ").strip()
    goal = input("What was your goal? ").strip()
    concern = input("Main concern at the time? ").strip()

    print("\nRate from 1 (low) to 5 (high)")
    impact = int(input("Impact on goal: ") or 3)
    cost = int(input("Time/effort cost: ") or 3)
    risk = int(input("Risk level: ") or 3)
    reversible = int(input("Reversibility: ") or 3)

    score = 20 * impact + 10 * reversible - 15 * cost - 15 * risk
    score = max(0, min(100, score))

    if score >= 65:
        rec = "Lean toward doing it."
    elif score >= 45:
        rec = "Borderline. Try a small test first."
    else:
        rec = "Lean toward not doing it or delaying."

    record = (
        f"\n[{timestamp}] NEW DECISION\n"
        f"Decision: {decision}\n"
        f"Options: {options}\n"
        f"Goal: {goal}\n"
        f"Concern: {concern}\n"
        f"Ratings: impact={impact}, cost={cost}, risk={risk}, reversible={reversible}\n"
        f"Score: {score}/100\n"
        f"Recommendation: {rec}\n"
    )

    save(record)
    print("\nSaved decision and recommendation.")

elif mode == "2":
    past = input("Briefly describe the past decision: ").strip()
    outcome = input("What actually happened? ").strip()
    regret = input("Do you regret the decision? (yes/no): ").strip().lower()
    accuracy = input("Was the original recommendation helpful? (yes/no): ").strip().lower()

    reflection = (
        f"\n[{timestamp}] REFLECTION\n"
        f"Past decision: {past}\n"
        f"Outcome: {outcome}\n"
        f"Regret: {regret}\n"
        f"Recommendation helpful: {accuracy}\n"
    )

    save(reflection)
    print("\nReflection saved.")

else:
    print("Invalid option.")