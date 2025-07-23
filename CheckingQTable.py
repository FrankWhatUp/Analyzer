import pickle
from collections import defaultdict
import matplotlib.pyplot as plt

# Load Q-table
with open("q_table.pkl", "rb") as f:
    q_table = pickle.load(f)

# Initialize counters
action_counts = defaultdict(int)
action_total_q = defaultdict(float)

# Loop over all entries in Q-table
for (state, action), q_value in q_table.items():
    action_counts[action] += 1
    action_total_q[action] += q_value

# Print analysis
print("=== Q-Table Analysis ===\n")
for action in ["Buy", "Sell", "Hold"]:
    count = action_counts[action]
    total_q = action_total_q[action]
    avg_q = total_q / count if count > 0 else 0.0
    print(f"Action: {action}")
    print(f"  Updates: {count}")
    print(f"  Total Q-Value: {total_q:.4f}")
    print(f"  Average Q-Value: {avg_q:.4f}\n")

# Optional: visualize Q-value distribution
actions = ["Buy", "Sell", "Hold"]
counts = [action_counts[a] for a in actions]
avgs = [action_total_q[a]/action_counts[a] if action_counts[a] > 0 else 0 for a in actions]

plt.figure(figsize=(10, 4))

plt.subplot(1, 2, 1)
plt.bar(actions, counts, color='steelblue')
plt.title("Q-Table Action Frequency")
plt.ylabel("Update Count")

plt.subplot(1, 2, 2)
plt.bar(actions, avgs, color='orange')
plt.title("Average Q-Value per Action")
plt.ylabel("Average Q-Value")

plt.tight_layout()
plt.show()
