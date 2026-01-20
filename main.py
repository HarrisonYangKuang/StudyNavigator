import os
from datetime import datetime

WEIGHTS = {
    "impact": 20,
    "reversible": 10,
    "cost": -15,
    "risk": -15,
}


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def clamp(n, lo=0, hi=100):
    return max(lo, min(hi, n))


def compute_contrib(values):
    contrib = {}
    for k, w in WEIGHTS.items():
        contrib[k] = w * values[k]
    return contrib


def build_breakdown(contrib, values):
    name_map = {
        "impact": "Impact on goal",
        "reversible": "Reversibility",
        "cost": "Time or effort cost",
        "risk": "Risk level",
    }

    lines = []
    items = sorted(contrib.items(), key=lambda kv: abs(kv[1]), reverse=True)

    for k, pts in items:
        sign = "+" if pts >= 0 else "-"
        lines.append(f"{sign} {name_map[k]} ({values[k]}/5) : {abs(pts)} pts")

    top_key, top_pts = items[0]
    top_line = f"Biggest factor: {name_map[top_key]} ({abs(top_pts)} pts)"
    return lines, top_line


def ask_yesno(prompt):
    while True:
        x = input(prompt).strip().lower()
        if x in {"yes", "y"}:
            return "yes"
        if x in {"no", "n"}:
            return "no"
        print("Please type yes or no.")


def ask_choice(prompt, choices):
    while True:
        x = input(prompt).strip()
        if x in choices:
            return x
        print(f"Please type one of {', '.join(sorted(choices))}.")


def save(text):
    with open("decisions.txt", "a", encoding="utf-8") as f:
        f.write(text)


def main():
    while True:
        print("=== StudyNavigator v0.4 (with reflection) ===")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mode = ask_choice(
            "Choose mode: (1) New  (2) Reflect  (0) Exit: ",
            {"0", "1", "2"},
        )

        if mode == "0":
            print("Bye.")
            break

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

            values = {
                "impact": impact,
                "cost": cost,
                "risk": risk,
                "reversible": reversible,
            }

            contrib = compute_contrib(values)
            raw_score = sum(contrib.values())
            score = clamp(raw_score)

            if score >= 65:
                rec = "Lean toward doing it."
            elif score >= 45:
                rec = "Borderline. Try a small test first."
            else:
                rec = "Lean toward not doing it or delaying."

            breakdown_lines, top_line = build_breakdown(contrib, values)

            print("\n" + "=" * 30)
            print("RESULT")
            print(f"Score: {score}/100")
            print(f"Recommendation: {rec}")
            print("Why (score breakdown)")
            for line in breakdown_lines:
                print(" - " + line)
            print(top_line)
            print("=" * 30 + "\n")

            record = (
                f"\n[{timestamp}] NEW DECISION\n"
                f"Decision: {decision}\n"
                f"Options: {options}\n"
                f"Goal: {goal}\n"
                f"Concern: {concern}\n"
                f"Ratings: impact={impact}, cost={cost}, risk={risk}, reversible={reversible}\n"
                f"Score: {score}/100\n"
                f"Recommendation: {rec}\n"
                "Breakdown:\n"
                + "\n".join(["- " + x for x in breakdown_lines])
                + "\n"
                + top_line
                + "\n"
            )

            save(record)
            print("Saved decision and recommendation.")

        elif mode == "2":
            past = input("Briefly describe the past decision: ").strip()
            outcome = input("What actually happened? ").strip()
            regret = ask_yesno("Do you regret the decision? (yes/no): ")
            accuracy = ask_yesno("Was the original recommendation helpful? (yes/no): ")

            reflection = (
                f"\n[{timestamp}] REFLECTION\n"
                f"Past decision: {past}\n"
                f"Outcome: {outcome}\n"
                f"Regret: {regret}\n"
                f"Recommendation helpful: {accuracy}\n"
            )

            print("\n" + "=" * 30)
            print("REFLECTION SAVED")
            print("Thank you for reviewing a past decision.")
            print("=" * 30 + "\n")

            save(reflection)
            print("Reflection saved.")

        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()