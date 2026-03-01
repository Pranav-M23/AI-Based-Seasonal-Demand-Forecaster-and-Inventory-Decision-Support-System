import pandas as pd
import matplotlib.pyplot as plt
import os

OUT_DIR = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(f"{OUT_DIR}/diwali_discount_signals.csv")

# top 12 categories by FSI for PPT readability
df = df.sort_values("FSI", ascending=False).head(12)

fig, ax = plt.subplots(figsize=(10, 3))
ax.axis("off")

table = ax.table(
    cellText=df[["Product_Category", "FSI", "Discount_Signal"]].values,
    colLabels=["Product_Category", "FSI", "Discount_Signal"],
    loc="center"
)

table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.4)

plt.title("Discount Decision Table (Top Categories by FSI)", pad=10)
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/discount_table.png", dpi=200)
plt.show()

print(f"Saved: {OUT_DIR}/discount_table.png")
