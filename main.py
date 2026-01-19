from datetime import datetime

print("=== StudyNavigator v0.2 ===")

decision = input("What is the decision you are making? ").strip()
options = input("What options do you have? ").strip()
goal = input("What is your main goal? ").strip()
risk = input("What is your biggest risk or concern? ").strip()

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

record = (
    f"\n[{timestamp}]\n"
    f"Decision: {decision}\n"
    f"Options: {options}\n"
    f"Goal: {goal}\n"
    f"Risk: {risk}\n"
)

with open("decisions.txt", "a", encoding="utf-8") as f:
    f.write(record)

print("\nDecision recorded successfully.")