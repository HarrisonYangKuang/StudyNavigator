from datetime import datetime

# 1) Ask user for a decision
decision = input("Enter your decision: ").strip()

# 2) Save it with time
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

line = f"[{timestamp}] {decision}\n"

with open("decisions.txt", "a", encoding="utf-8") as f:
    f.write(line)

print("Saved:", line.strip())
