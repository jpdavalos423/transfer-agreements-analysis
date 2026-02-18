import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.patches as mpatches
from pathlib import Path

sns.set(style="white", font_scale=0.9)

uc_schools = ["UCSD", "UCSB", "UCSC", "UCLA", "UCB", "UCI", "UCD", "UCR", "UCM"]
SCRIPT_DIR = Path(__file__).resolve().parent
QUESTION1_ROOT = SCRIPT_DIR.parents[2]
ORDER_CSV_DIR = QUESTION1_ROOT / "csvs" / "order_3_csvs"
OUTPUT_DIR = QUESTION1_ROOT / "graphs" / "heat_maps_per_order"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load and prepare data for heatmap per order
for order in range(1, 4):
    df = pd.read_csv(ORDER_CSV_DIR / f"order_{order}_averages.csv")

    # Remove average rows
    df_filtered = df[~df["Community College"].isin(["AVERAGE", "TRANSFERABLE AVERAGE"])]

    # Sort community colleges alphabetically
    df_filtered = df_filtered.sort_values("Community College")

    # Prepare matrices for heatmap and mask
    articulated_matrix = pd.DataFrame(index=df_filtered["Community College"], columns=uc_schools)
    mask_matrix = pd.DataFrame(False, index=df_filtered["Community College"], columns=uc_schools)

    for _, row in df_filtered.iterrows():
        cc = row["Community College"]
        for uc in uc_schools:
            art_col = f"{uc} Articulated"
            unart_col = f"{uc} Unarticulated"
            articulated_matrix.loc[cc, uc] = row[art_col]
            if row[unart_col] > 0:
                mask_matrix.loc[cc, uc] = True

    articulated_matrix = articulated_matrix.astype(float)

    # Plotting
    fig, ax = plt.subplots(figsize=(14, max(6, len(articulated_matrix) * 0.4)))
    sns.heatmap(
        articulated_matrix,
        mask=mask_matrix,
        annot=True,
        fmt=".1f",
        cmap="YlGnBu",
        cbar_kws={'label': 'Avg. Articulated Courses'},
        linewidths=0.5,
        linecolor='white', 
        ax=ax
    )

    # Red overlay for non-transferable (masked) cells
    for y in range(mask_matrix.shape[0]):
        for x in range(mask_matrix.shape[1]):
            if mask_matrix.iloc[y, x]:
                ax.add_patch(
                    plt.Rectangle(
                        (x, y), 1, 1,
                        fill=True,
                        facecolor='lightcoral',
                        edgecolor='white',
                        linewidth=0.5  # <- key to gridline visibility
                    )
                )


    # Add legend patch
    red_patch = mpatches.Patch(color='lightcoral', label='Untransferable')
    ax.legend(handles=[red_patch], loc='upper right', bbox_to_anchor=(1.15, 1.02))

    ax.set_title(f"Transferable Course Heatmap - Order {order}", fontsize=14, weight='bold')
    ax.set_xlabel("University of California", fontsize=11)
    ax.set_ylabel("Community College", fontsize=11)

    plt.xticks(rotation=30, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f"heatmap_order_{order}.png", dpi=300)
    plt.show()
