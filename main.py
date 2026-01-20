import os
import sys
from datetime import datetime

WEIGHTS = {
    "impact": 20,
    "reversible": 10,
    "cost": -15,
    "risk": -15,
}


def clear():
    # Avoid TERM errors in IDE run consoles (not a real terminal)
    if not sys.stdout.isatty():
        print("\n" * 40)
        return

    if os.name == "nt":
        os.system("cls")
    else:
        # Only clear when TERM exists
        if os.environ.get("TERM"):
            os.system("clear")
        else:
            print("\n" * 40)


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


def ask_int(prompt, lo, hi, default=None):
    while True:
        raw = input(prompt).strip()
        if raw == "" and default is not None:
            return default
        if raw.isdigit():
            n = int(raw)
            if lo <= n <= hi:
                return n
        if default is None:
            print(f"Please type a number from {lo} to {hi}.")
        else:
            print(f"Please type a number from {lo} to {hi} (or press Enter for {default}).")


def pause():
    input("\nPress Enter to continue...")


def save(text):
    with open("decisions.txt", "a", encoding="utf-8") as f:
        f.write(text)


def load_entries(path="decisions.txt"):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = f.read().strip()
    if not data:
        return []

    # Entries are written starting with a line like: [YYYY-MM-DD ...] NEW DECISION / REFLECTION
    parts = data.split("\n[")
    entries = []
    for i, p in enumerate(parts):
        if i == 0:
            chunk = p
        else:
            chunk = "[" + p
        entries.append(chunk.strip())
    return entries


def summarize_entry(entry):
    # Return a short one-line summary for list/search results
    first_line = entry.splitlines()[0].strip()

    label = "LOG"
    title = ""

    if "NEW DECISION" in entry:
        label = "DECISION"
        for line in entry.splitlines():
            if line.startswith("Decision:"):
                title = line.replace("Decision:", "").strip()
                break
    elif "REFLECTION" in entry:
        label = "REFLECTION"
        for line in entry.splitlines():
            if line.startswith("Past decision:"):
                title = line.replace("Past decision:", "").strip()
                break

    if title:
        return f"{first_line}  {label}  {title}"
    return f"{first_line}  {label}"


def browse_history():
    while True:
        clear()
        print("=== History (decisions.txt) ===")
        print("(1) List recent")
        print("(2) Search keyword")
        print("(0) Back")

        action = ask_choice("Choose: ", {"0", "1", "2"})
        if action == "0":
            return

        entries = load_entries()
        if not entries:
            print("\nNo history found yet. Make a decision first.")
            pause()
            continue

        if action == "1":
            n = ask_int("How many recent entries? (Enter=5): ", 1, 50, default=5)
            shown = entries[-n:]

            print("\nRecent entries")
            for idx, e in enumerate(reversed(shown), start=1):
                print(f"{idx}. {summarize_entry(e)}")

            choice = input("\nType a number to view, or press Enter to go back: ").strip()
            if choice.isdigit():
                k = int(choice)
                if 1 <= k <= len(shown):
                    clear()
                    selected = list(reversed(shown))[k - 1]
                    print(selected)
                    pause()

        if action == "2":
            kw = input("Keyword: ").strip()
            if not kw:
                continue
            kw_low = kw.lower()
            matches = [e for e in entries if kw_low in e.lower()]

            if not matches:
                print("\nNo matches.")
                pause()
                continue

            print("\nMatches")
            for idx, e in enumerate(matches, start=1):
                print(f"{idx}. {summarize_entry(e)}")

            choice = input("\nType a number to view, or press Enter to go back: ").strip()
            if choice.isdigit():
                k = int(choice)
                if 1 <= k <= len(matches):
                    clear()
                    print(matches[k - 1])
                    pause()


def main():
    while True:
        clear()
        print("=== StudyNavigator v0.4 (with reflection) ===")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mode = ask_choice(
            "Choose mode: (1) New  (2) Reflect  (3) Browse  (0) Exit: ",
            {"0", "1", "2", "3"},
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
            impact = ask_int("Impact on goal (1-5, Enter=3): ", 1, 5, default=3)
            cost = ask_int("Time/effort cost (1-5, Enter=3): ", 1, 5, default=3)
            risk = ask_int("Risk level (1-5, Enter=3): ", 1, 5, default=3)
            reversible = ask_int("Reversibility (1-5, Enter=3): ", 1, 5, default=3)

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
            pause()

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
            pause()

        elif mode == "3":
            browse_history()

        else:
            print("Invalid option.")
            pause()


if __name__ == "__main__":
    main()