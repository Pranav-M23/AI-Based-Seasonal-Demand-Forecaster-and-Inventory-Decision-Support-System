import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")
OUT_FILE = os.path.join(DATA_DIR, "store_region.csv")

STORE_FILE = os.path.join(DATA_DIR, "store.csv")


REGION_DISTRIBUTION = {
    "Kerala": 190,
    "North-India": 210,
    "West-India": 200,
    "East-India": 175,
    "Tamil Nadu": 170,
    "Pan-India": 170
}

def main():
    if not os.path.exists(STORE_FILE):
        raise FileNotFoundError(f"Missing: {STORE_FILE}")

    store_df = pd.read_csv(STORE_FILE)
    if "Store" not in store_df.columns:
        raise ValueError("store.csv must contain a 'Store' column")

    stores = sorted(store_df["Store"].unique().tolist())
    n = len(stores)

    # Normalize requested counts to exactly match total stores
    total_requested = sum(REGION_DISTRIBUTION.values())
    if total_requested != n:
        # scale counts proportionally then fix rounding
        scaled = {}
        for k, v in REGION_DISTRIBUTION.items():
            scaled[k] = int(round(v * (n / total_requested)))
        # fix rounding drift
        diff = n - sum(scaled.values())
        # distribute diff to Pan-India first, then others
        keys = ["Pan-India"] + [k for k in scaled.keys() if k != "Pan-India"]
        idx = 0
        while diff != 0:
            k = keys[idx % len(keys)]
            if diff > 0:
                scaled[k] += 1
                diff -= 1
            else:
                if scaled[k] > 1:
                    scaled[k] -= 1
                    diff += 1
            idx += 1
        counts = scaled
    else:
        counts = REGION_DISTRIBUTION

    rows = []
    start = 0
    for region, cnt in counts.items():
        chunk = stores[start:start+cnt]
        for s in chunk:
            rows.append({"Store": s, "Region": region})
        start += cnt

    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUT_FILE, index=False)
    print(f"✅ Generated: {OUT_FILE}")
    print("\n--- Store distribution ---")
    print(out_df["Region"].value_counts().to_string())

if __name__ == "__main__":
    main()
