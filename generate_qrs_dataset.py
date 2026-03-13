"""
Generate realistic 2025 daily sales CSV for QRS Technologies,
a local electronics store in Trivandrum, Kerala, South India.
"""
import csv, random, math
from datetime import date, timedelta

random.seed(42)

CATEGORIES = {
    # category: (base_daily_units, trend_per_month, weekend_boost)
    "Mobile Phones & Accessories":  (22, 0.02, 1.40),
    "Laptops & Computers":          (10, 0.01, 1.35),
    "Televisions & Displays":       (7,  0.00, 1.50),
    "Audio & Headphones":           (15, 0.01, 1.30),
    "Home Appliances":              (12, 0.00, 1.25),
    "Kitchen Appliances":           (10, 0.00, 1.20),
    "Cameras & Surveillance":       (7,  -0.015, 1.15),   # declining
    "Smart Watches & Wearables":    (14, 0.025, 1.35),    # growing
    "Power Banks & Chargers":       (28, 0.01, 1.20),
    "Networking & Storage":         (8,  0.005, 1.15),
}

# Monthly seasonal multipliers for Trivandrum electronics
# Jan=0 … Dec=11
SEASONAL = {
    0:  1.05,  # Jan – Pongal/New Year tail
    1:  0.88,  # Feb – quiet
    2:  0.92,  # Mar – exam season, low
    3:  1.45,  # Apr – Vishu (major Kerala festival)
    4:  1.10,  # May – summer, AC/fan season ends, student purchases
    5:  0.95,  # Jun – monsoon starts, back-to-school laptops
    6:  0.82,  # Jul – heavy monsoon, low footfall
    7:  1.55,  # Aug – Onam buildup, early shopping
    8:  2.60,  # Sep – ONAM peak (Thiruvonam usually late Aug/Sep)
    9:  0.78,  # Oct – post-Onam dip
    10: 0.90,  # Nov – recovery, pre-Christmas
    11: 1.50,  # Dec – Christmas + New Year (large Christian pop in Kerala)
}

# Category-specific seasonal overrides  (month → category → extra multiplier)
CAT_SEASONAL = {
    # Laptops spike Jun (school), Aug-Sep (Onam gifts)
    5:  {"Laptops & Computers": 1.40},
    # Home Appliances spike Mar-May (summer)
    2:  {"Home Appliances": 1.35, "Kitchen Appliances": 1.10},
    3:  {"Home Appliances": 1.25},
    4:  {"Home Appliances": 1.45, "Kitchen Appliances": 1.15},
    # TVs spike during Onam & Dec
    8:  {"Televisions & Displays": 1.60, "Kitchen Appliances": 1.40},
    11: {"Televisions & Displays": 1.45, "Audio & Headphones": 1.30},
    # Cameras decline faster mid-year
    6:  {"Cameras & Surveillance": 0.70},
    7:  {"Cameras & Surveillance": 0.75},
}

# Specific date boosts (exact dates in 2025)
SPECIAL_DAYS = {
    # Vishu 2025 – Apr 14-15
    date(2025, 4, 14): 2.8,
    date(2025, 4, 15): 2.2,
    # Pre-Vishu shopping Apr 10-13
    date(2025, 4, 10): 1.6, date(2025, 4, 11): 1.7,
    date(2025, 4, 12): 1.9, date(2025, 4, 13): 2.1,
    # Onam 2025 – Thiruvonam ~Sep 5, shopping window Aug 25–Sep 5
    date(2025, 8, 25): 1.8, date(2025, 8, 26): 1.9,
    date(2025, 8, 27): 2.0, date(2025, 8, 28): 2.2,
    date(2025, 8, 29): 2.4, date(2025, 8, 30): 2.8,
    date(2025, 8, 31): 3.0,
    date(2025, 9, 1): 3.2,  date(2025, 9, 2): 3.5,
    date(2025, 9, 3): 3.8,  date(2025, 9, 4): 4.0,
    date(2025, 9, 5): 3.5,  # Thiruvonam day (shops may close early)
    date(2025, 9, 6): 2.0,  date(2025, 9, 7): 1.5,
    # Christmas / New Year
    date(2025, 12, 20): 1.6, date(2025, 12, 21): 1.8,
    date(2025, 12, 22): 2.0, date(2025, 12, 23): 2.3,
    date(2025, 12, 24): 2.5, date(2025, 12, 25): 1.8,  # Christmas day (half-day)
    date(2025, 12, 26): 1.5,
    date(2025, 12, 29): 1.6, date(2025, 12, 30): 1.8,
    date(2025, 12, 31): 2.0,
    # Republic Day sale
    date(2025, 1, 25): 1.5, date(2025, 1, 26): 1.8,
    # Independence Day sale
    date(2025, 8, 14): 1.4, date(2025, 8, 15): 1.7,
}

# Salary-day boost (1st and last 2 days of month)
def salary_boost(d):
    if d.day <= 2 or d.day >= 28:
        return 1.12
    return 1.0

def generate():
    rows = []
    start = date(2025, 1, 1)
    end = date(2025, 12, 31)
    d = start
    while d <= end:
        month = d.month - 1  # 0-indexed
        day_of_year = (d - start).days
        is_weekend = d.weekday() >= 5  # Sat=5, Sun=6

        base_seasonal = SEASONAL[month]
        special = SPECIAL_DAYS.get(d, 1.0)
        sal = salary_boost(d)

        for cat, (base_units, trend_mo, wknd_mult) in CATEGORIES.items():
            # Trend: compound monthly
            months_elapsed = month + d.day / 30.0
            trend = (1 + trend_mo) ** months_elapsed

            # Category-specific seasonal override
            cat_extra = CAT_SEASONAL.get(month, {}).get(cat, 1.0)

            # Weekend
            wknd = wknd_mult if is_weekend else 1.0

            # Combine all multipliers
            raw = base_units * trend * base_seasonal * cat_extra * wknd * special * sal

            # Add realistic noise (±20%)
            noise = random.gauss(1.0, 0.12)
            noise = max(0.6, min(1.5, noise))  # clamp
            units = max(0, round(raw * noise))

            rows.append([d.isoformat(), cat, units])

        d += timedelta(days=1)

    # Write CSV
    out_path = "Data/qrs_technologies_2025.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Category", "Sales_Units"])
        w.writerows(rows)

    print(f"Generated {len(rows)} rows → {out_path}")

    # Quick stats
    from collections import Counter
    cat_totals = Counter()
    month_totals = Counter()
    for row in rows:
        cat_totals[row[1]] += row[2]
        month_totals[row[0][:7]] += row[2]

    print("\n── Category Totals (2025) ──")
    for cat in sorted(cat_totals, key=cat_totals.get, reverse=True):
        print(f"  {cat:40s} {cat_totals[cat]:>6,} units")

    print("\n── Monthly Totals ──")
    for m in sorted(month_totals):
        print(f"  {m}  {month_totals[m]:>6,} units")

if __name__ == "__main__":
    generate()
