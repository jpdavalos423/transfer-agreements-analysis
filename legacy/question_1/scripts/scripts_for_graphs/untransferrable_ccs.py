import matplotlib.pyplot as plt
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
QUESTION1_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_TXT = QUESTION1_ROOT / "txts" / "data_5_greedy_txts" / "greedy_excluded_cc_uc_pairs.txt"
file_path = Path(os.environ.get("UNTRANSFERABLE_TXT_PATH", str(DEFAULT_TXT)))
OUTPUT_DIR = QUESTION1_ROOT / "graphs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Initialize count for each UC
uc_list = ["UCSD", "UCSB", "UCSC", "UCLA", "UCB", "UCI", "UCD", "UCR", "UCM"]
untransferrable_counts = {uc: 0 for uc in uc_list}

# Read the file and count untransferrable UCs
with open(file_path, 'r', encoding='utf-8') as f:
    for line in f:
        if ':' not in line:
            continue
        _, uc_str = line.strip().split(':')
        uc_str = uc_str.strip()
        if not uc_str:
            continue
        ucs = [uc.strip() for uc in uc_str.split(',') if uc.strip()]
        for uc in ucs:
            if uc in untransferrable_counts:
                untransferrable_counts[uc] += 1

# Plotting
plt.figure(figsize=(10, 6))
bars = plt.bar(untransferrable_counts.keys(), untransferrable_counts.values(), color='indianred')

# Add value labels
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 0.2, str(height), ha='center', va='bottom')

plt.title("Number of Districts Untransferrable to Each UC")
plt.xlabel("UC")
plt.ylabel("Untransferrable District Count")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "untransferrable_districts_from_txt.png")
plt.show()
