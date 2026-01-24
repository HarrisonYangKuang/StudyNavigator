import os
import sys
from datetime import datetime
import json
import urllib.request

WEIGHTS = {
    "urgency": 0.30,
    "importance": 0.20,
    "long_term_value": 0.35,
    "effort": -0.15,
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
        contrib[k] = w * values[k] * 20
    return contrib


def build_breakdown(contrib, values):
    name_map = {
        "urgency": "Urgency",
        "importance": "Importance",
        "long_term_value": "Long-term value",
        "effort": "Effort cost",
    }

    lines = []
    items = sorted(contrib.items(), key=lambda kv: abs(kv[1]), reverse=True)

    for k, pts in items:
        sign = "+" if pts >= 0 else "-"
        lines.append(f"{sign} {name_map[k]} ({values[k]}/5): {abs(int(pts))} pts")

    top_key, top_pts = items[0]
    top_line = f"Biggest factor: {name_map[top_key]} ({abs(int(top_pts))} pts)"
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



def extract_output_text(resp_json):
    """
    Responses API returns a list of output items. We extract the first output_text.
    """
    try:
        for item in resp_json.get("output", []):
            if item.get("type") == "message":
                for c in item.get("content", []):
                    if c.get("type") == "output_text":
                        return c.get("text", "")
    except Exception:
        return ""
    return ""

def ai_score_tasks(task_a, task_b, time_left, energy):
    """
    Uses OpenAI Responses API to score both tasks. Requires OPENAI_API_KEY in env.
    Returns (values_a, values_b, reasons_a, reasons_b) or None on failure.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["taskA", "taskB"],
        "properties": {
            "taskA": {
                "type": "object",
                "additionalProperties": False,
                "required": ["urgency", "importance", "long_term_value", "effort", "reasons"],
                "properties": {
                    "urgency": {"type": "integer", "minimum": 1, "maximum": 5},
                    "importance": {"type": "integer", "minimum": 1, "maximum": 5},
                    "long_term_value": {"type": "integer", "minimum": 1, "maximum": 5},
                    "effort": {"type": "integer", "minimum": 1, "maximum": 5},
                    "reasons": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["urgency", "importance", "long_term_value", "effort"],
                        "properties": {
                            "urgency": {"type": "string"},
                            "importance": {"type": "string"},
                            "long_term_value": {"type": "string"},
                            "effort": {"type": "string"},
                        },
                    },
                },
            },
            "taskB": {
                "type": "object",
                "additionalProperties": False,
                "required": ["urgency", "importance", "long_term_value", "effort", "reasons"],
                "properties": {
                    "urgency": {"type": "integer", "minimum": 1, "maximum": 5},
                    "importance": {"type": "integer", "minimum": 1, "maximum": 5},
                    "long_term_value": {"type": "integer", "minimum": 1, "maximum": 5},
                    "effort": {"type": "integer", "minimum": 1, "maximum": 5},
                    "reasons": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["urgency", "importance", "long_term_value", "effort"],
                        "properties": {
                            "urgency": {"type": "string"},
                            "importance": {"type": "string"},
                            "long_term_value": {"type": "string"},
                            "effort": {"type": "string"},
                        },
                    },
                },
            },
        },
    }

    system_msg = (
        "You are a strict task-scoring engine for students. "
        "Score each task from 1-5 on: urgency, importance, long_term_value, effort. "
        "Use the user's time_left and energy as context. "
        "Be realistic, not optimistic. Keep each reason short (<= 12 words)."
    )

    user_msg = (
        f"Task A: {task_a}\n"
        f"Task B: {task_b}\n"
        f"time_left: {time_left}\n"
        f"energy: {energy}\n"
        "Return scores and short reasons."
    )

    payload = {
        "model": "gpt-4o-mini",
        "input": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "task_scores",
                "strict": True,
                "schema": schema,
            }
        },
        "temperature": 0.2,
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw = resp.read().decode("utf-8")
        resp_json = json.loads(raw)

        text_out = extract_output_text(resp_json).strip()
        data = json.loads(text_out)

        a = data["taskA"]
        b = data["taskB"]

        values_a = {
            "urgency": int(a["urgency"]),
            "importance": int(a["importance"]),
            "long_term_value": int(a["long_term_value"]),
            "effort": int(a["effort"]),
        }
        values_b = {
            "urgency": int(b["urgency"]),
            "importance": int(b["importance"]),
            "long_term_value": int(b["long_term_value"]),
            "effort": int(b["effort"]),
        }

        reasons_a = a.get("reasons", {})
        reasons_b = b.get("reasons", {})

        # final sanity clamp
        for k in values_a:
            values_a[k] = max(1, min(5, values_a[k]))
            values_b[k] = max(1, min(5, values_b[k]))

        return values_a, values_b, reasons_a, reasons_b
    except Exception:
        return None


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
            task_a = input("Task A: ").strip()
            task_b = input("Task B: ").strip()
            time_left = ask_choice("Time left (short/medium/long): ", {"short", "medium", "long"})
            energy = ask_choice("Energy level (low/medium/high): ", {"low", "medium", "high"})

            use_ai = ask_yesno("Use AI to auto-score tasks? (yes/no): ")
            ai_result = None
            if use_ai == "yes":
                ai_result = ai_score_tasks(task_a, task_b, time_left, energy)
                if ai_result is None:
                    print("AI scoring failed (missing key or API error). Falling back to manual ratings.")
                    use_ai = "no"

            if use_ai == "no":
                print("\nRate each task from 1 (low) to 5 (high)")
                print("Task A ratings")
                a_urgency = ask_int("Urgency (1-5, Enter=3): ", 1, 5, default=3)
                a_importance = ask_int("Importance (1-5, Enter=3): ", 1, 5, default=3)
                a_value = ask_int("Long-term value (1-5, Enter=3): ", 1, 5, default=3)
                a_effort = ask_int("Effort cost (1-5, Enter=3): ", 1, 5, default=3)

                print("\nTask B ratings")
                b_urgency = ask_int("Urgency (1-5, Enter=3): ", 1, 5, default=3)
                b_importance = ask_int("Importance (1-5, Enter=3): ", 1, 5, default=3)
                b_value = ask_int("Long-term value (1-5, Enter=3): ", 1, 5, default=3)
                b_effort = ask_int("Effort cost (1-5, Enter=3): ", 1, 5, default=3)

            reasons_a = {}
            reasons_b = {}

            if use_ai == "yes":
                values_a, values_b, reasons_a, reasons_b = ai_result
            else:
                values_a = {
                    "urgency": a_urgency,
                    "importance": a_importance,
                    "long_term_value": a_value,
                    "effort": a_effort,
                }
                values_b = {
                    "urgency": b_urgency,
                    "importance": b_importance,
                    "long_term_value": b_value,
                    "effort": b_effort,
                }

            contrib_a = compute_contrib(values_a)
            contrib_b = compute_contrib(values_b)

            score_a = clamp(sum(contrib_a.values()))
            score_b = clamp(sum(contrib_b.values()))

            if score_a > score_b:
                rec = f"Choose Task A ({task_a})."
            elif score_b > score_a:
                rec = f"Choose Task B ({task_b})."
            else:
                rec = "Both tasks are equally balanced. Try a small test of either."

            breakdown_a, top_a = build_breakdown(contrib_a, values_a)
            breakdown_b, top_b = build_breakdown(contrib_b, values_b)

            print("\n" + "=" * 30)
            print("RESULT")
            print(f"Task A score: {score_a}/100")
            for line in breakdown_a:
                print(" - " + line)
            print(top_a)

            print(f"\nTask B score: {score_b}/100")
            for line in breakdown_b:
                print(" - " + line)
            print(top_b)

            if use_ai == "yes":
                print("\nAI quick reasons (Task A):")
                for k in ["urgency", "importance", "long_term_value", "effort"]:
                    if k in reasons_a:
                        print(f" - {k}: {reasons_a[k]}")
                print("AI quick reasons (Task B):")
                for k in ["urgency", "importance", "long_term_value", "effort"]:
                    if k in reasons_b:
                        print(f" - {k}: {reasons_b[k]}")

            print("\nRecommendation:")
            print(rec)
            print("=" * 30 + "\n")

            record = (
                f"\n[{timestamp}] NEW DECISION\n"
                f"Task A: {task_a}\n"
                f"Task B: {task_b}\n"
                f"Time left: {time_left}\n"
                f"Energy: {energy}\n"
                f"Scoring mode: {'AI' if use_ai == 'yes' else 'Manual'}\n"
                f"Score A: {score_a}/100\n"
                f"Score B: {score_b}/100\n"
                f"Recommendation: {rec}\n"
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