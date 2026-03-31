"""
Generate all presentation diagrams for the Seasonal Demand Forecaster project.

Diagrams generated:
1) System Architecture Diagram
2) Flowchart Diagram
3) Data Flow Diagram (DFD)
4) Block Diagram

Usage:
  python generate_all_project_diagrams.py
  python generate_all_project_diagrams.py --svg
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon

from generate_system_architecture import build_architecture


OUTPUT_DIR = Path("outputs")


def _new_canvas(title: str, subtitle: str):
    fig, ax = plt.subplots(figsize=(16, 9), dpi=240)
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Soft horizontal gradient band for a presentation-like backdrop.
    ax.imshow(
        [[0.98, 0.92], [1.0, 0.95]],
        extent=(0.0, 1.0, 0.0, 1.0),
        cmap="Blues",
        alpha=0.08,
        interpolation="bicubic",
        zorder=0,
        aspect="auto",
    )

    ax.plot([0.03, 0.97], [0.905, 0.905], color="#cbd5e1", linewidth=1.2, zorder=0)

    ax.text(0.03, 0.965, title, fontsize=22, fontweight="bold", color="#0f172a", ha="left", va="top")
    ax.text(0.03, 0.928, subtitle, fontsize=11, color="#334155", ha="left", va="top")
    return fig, ax


def _box(ax, x, y, w, h, title, subtitle, face="#ffffff", edge="#334155", title_color="#0f172a", subtitle_color="#334155"):
    shadow = FancyBboxPatch(
        (x + 0.003, y - 0.004),
        w,
        h,
        boxstyle="round,pad=0.01,rounding_size=0.016",
        linewidth=0,
        facecolor="#64748b",
        alpha=0.18,
        zorder=1,
    )
    ax.add_patch(shadow)

    body = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.01,rounding_size=0.016",
        linewidth=1.5,
        edgecolor=edge,
        facecolor=face,
        zorder=2,
    )
    ax.add_patch(body)

    ax.text(x + w / 2, y + h * 0.63, title, fontsize=12, fontweight="bold", color=title_color, ha="center", va="center", zorder=3)
    ax.text(x + w / 2, y + h * 0.30, subtitle, fontsize=9.2, color=subtitle_color, ha="center", va="center", zorder=3)


def _term(ax, x, y, w, h, text, face="#dbeafe", edge="#2563eb"):
    term = Ellipse((x + w / 2, y + h / 2), width=w, height=h, facecolor=face, edgecolor=edge, linewidth=1.6, zorder=2)
    ax.add_patch(term)
    ax.text(x + w / 2, y + h / 2, text, fontsize=11, fontweight="bold", color="#0f172a", ha="center", va="center", zorder=3)


def _arrow(ax, a, b, label="", curve=0.0, color="#1e293b", label_offset=0.014):
    ar = FancyArrowPatch(
        posA=a,
        posB=b,
        arrowstyle="-|>",
        mutation_scale=13,
        linewidth=1.6,
        color=color,
        connectionstyle=f"arc3,rad={curve}",
        zorder=4,
    )
    ax.add_patch(ar)
    if label:
        lx = (a[0] + b[0]) / 2
        ly = (a[1] + b[1]) / 2 + label_offset
        ax.text(
            lx,
            ly,
            label,
            fontsize=8.5,
            color="#334155",
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.16", fc="#ffffff", ec="none", alpha=0.92),
            zorder=5,
        )


def _diamond(ax, x, y, w, h, title, subtitle, face="#ffffff", edge="#334155"):
    points = [(x + w / 2, y + h), (x + w, y + h / 2), (x + w / 2, y), (x, y + h / 2)]
    poly = Polygon(points, closed=True, facecolor=face, edgecolor=edge, linewidth=1.5, zorder=2)
    ax.add_patch(poly)
    ax.text(x + w / 2, y + h * 0.60, title, fontsize=11, fontweight="bold", color="#0f172a", ha="center", va="center", zorder=3)
    ax.text(x + w / 2, y + h * 0.40, subtitle, fontsize=8.8, color="#334155", ha="center", va="center", zorder=3)


def _orth_arrow(ax, points, label="", color="#1e293b", label_pos=None):
    for i in range(len(points) - 2):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        ax.plot([x0, x1], [y0, y1], color=color, linewidth=1.6, zorder=3)
    _arrow(ax, points[-2], points[-1], label="", color=color)
    if label:
        if label_pos is None:
            mx = (points[0][0] + points[-1][0]) / 2
            my = (points[0][1] + points[-1][1]) / 2
        else:
            mx, my = label_pos
        ax.text(
            mx,
            my,
            label,
            fontsize=8.5,
            color="#334155",
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.16", fc="#ffffff", ec="none", alpha=0.92),
            zorder=5,
        )


def _save(fig, out_png: Path, save_svg: bool):
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, bbox_inches="tight", facecolor=fig.get_facecolor())
    if save_svg:
        fig.savefig(out_png.with_suffix(".svg"), bbox_inches="tight", format="svg", facecolor=fig.get_facecolor())
    plt.close(fig)


def _lane(ax, y, h, label, tint):
    lane = FancyBboxPatch(
        (0.04, y),
        0.92,
        h,
        boxstyle="round,pad=0.01,rounding_size=0.012",
        linewidth=0,
        facecolor=tint,
        alpha=0.22,
        zorder=0,
    )
    ax.add_patch(lane)
    ax.text(0.05, y + h - 0.02, label, fontsize=9.5, color="#334155", fontweight="bold", ha="left", va="top", zorder=1)


def _badge(ax, x, y, text, color):
    bubble = Ellipse((x, y), width=0.038, height=0.038, facecolor=color, edgecolor="#0f172a", linewidth=1.0, zorder=6)
    ax.add_patch(bubble)
    ax.text(x, y, text, fontsize=9.5, color="#ffffff", fontweight="bold", ha="center", va="center", zorder=7)


def build_flowchart(out_png: Path, save_svg: bool) -> None:
    fig, ax = _new_canvas(
        "Seasonal Demand Forecaster - Flowchart Diagram",
        "End-to-end process flow from data ingestion to business dashboards",
    )

    _lane(ax, 0.69, 0.18, "PHASE 1 - DATA & MODEL PREPARATION", "#dbeafe")
    _lane(ax, 0.41, 0.20, "PHASE 2 - FORECAST GENERATION & API", "#dcfce7")
    _lane(ax, 0.12, 0.22, "PHASE 3 - BUSINESS CONSUMPTION", "#ede9fe")

    _term(ax, 0.42, 0.78, 0.16, 0.08, "START")
    _box(ax, 0.36, 0.67, 0.28, 0.12, "Load Core Inputs", "Data/train.csv + store.csv + regional/state festival calendars", face="#e0f2fe", edge="#0284c7")
    _diamond(ax, 0.45, 0.51, 0.12, 0.14, "Models", "available?", face="#dbeafe", edge="#2563eb")
    _box(ax, 0.14, 0.44, 0.24, 0.12, "Train Models", "ml_models.py -> models/*.pkl", face="#dbeafe", edge="#2563eb")
    _box(ax, 0.62, 0.44, 0.24, 0.12, "Run ml_pipeline.py", "Generate outputs/*.csv for forecast, inventory, discounts, actions", face="#dcfce7", edge="#16a34a")
    _box(ax, 0.38, 0.31, 0.24, 0.12, "Serve FastAPI APIs", "main.py + data_loader.py (alias mapping + fallback)", face="#ffedd5", edge="#f97316")

    _box(ax, 0.12, 0.15, 0.24, 0.12, "React Dashboards", "Predictive Dashboard + Shop Owner Analytics", face="#ede9fe", edge="#7c3aed")
    _box(ax, 0.40, 0.15, 0.24, 0.12, "Prediction Catalogue", "Record business decisions in predictions.db", face="#ede9fe", edge="#7c3aed")
    _term(ax, 0.72, 0.15, 0.18, 0.12, "FINAL OUTPUT")

    _arrow(ax, (0.50, 0.78), (0.50, 0.79 - 0.10), "")
    _arrow(ax, (0.50, 0.67), (0.50, 0.65), "features")
    _arrow(ax, (0.57, 0.58), (0.62, 0.50), "yes")
    _arrow(ax, (0.38, 0.50), (0.45, 0.58), "no")
    _arrow(ax, (0.26, 0.44), (0.45, 0.58), "trained", curve=0.18)
    _arrow(ax, (0.62, 0.44), (0.62, 0.43), "outputs")
    _arrow(ax, (0.62, 0.37), (0.62, 0.31), "datasets")
    _arrow(ax, (0.50, 0.31), (0.24, 0.27), "dashboard data")
    _arrow(ax, (0.50, 0.31), (0.52, 0.27), "catalog data")
    _arrow(ax, (0.36, 0.21), (0.40, 0.21), "actions")
    _arrow(ax, (0.64, 0.21), (0.72, 0.21), "insights")

    _save(fig, out_png, save_svg)


def build_dfd(out_png: Path, save_svg: bool) -> None:
    fig, ax = _new_canvas(
        "Seasonal Demand Forecaster - Data Flow Diagram (DFD)",
        "How data moves between entities, processes, and stores",
    )

    _lane(ax, 0.70, 0.16, "EXTERNAL ENTITIES", "#f1f5f9")
    _lane(ax, 0.44, 0.20, "PROCESSES", "#dcfce7")
    _lane(ax, 0.14, 0.22, "DATA STORES", "#f8fafc")

    _box(ax, 0.08, 0.73, 0.22, 0.10, "E1: Retail Data Sources", "Sales history + store metadata + festival calendars", face="#e0f2fe", edge="#0284c7")
    _box(ax, 0.72, 0.73, 0.22, 0.10, "E2: Business Users", "Planner, analyst, shop owner", face="#ede9fe", edge="#7c3aed")

    _box(ax, 0.22, 0.48, 0.26, 0.11, "P1: ML Factory", "ml_models.py + ml_pipeline.py", face="#dbeafe", edge="#2563eb")
    _box(ax, 0.52, 0.48, 0.26, 0.11, "P2: FastAPI Service", "main.py + data_loader.py", face="#ffedd5", edge="#f97316")

    _box(ax, 0.16, 0.18, 0.22, 0.11, "D1: Model Artifacts", "models/*.pkl", face="#ffffff", edge="#475569")
    _box(ax, 0.40, 0.18, 0.22, 0.11, "D2: Analytics Outputs", "outputs/*.csv", face="#ffffff", edge="#475569")
    _box(ax, 0.64, 0.18, 0.22, 0.11, "D3: Prediction Catalog", "predictions.db", face="#ffffff", edge="#475569")

    _arrow(ax, (0.30, 0.78), (0.22, 0.54), "training data")
    _arrow(ax, (0.48, 0.54), (0.52, 0.54), "forecast datasets")

    _arrow(ax, (0.30, 0.48), (0.27, 0.29), "model save")
    _arrow(ax, (0.35, 0.48), (0.51, 0.29), "CSV export")
    _arrow(ax, (0.65, 0.48), (0.75, 0.29), "catalog write")

    _arrow(ax, (0.27, 0.24), (0.52, 0.52), "load models", curve=0.14)
    _arrow(ax, (0.51, 0.24), (0.52, 0.48), "read analytics")
    _arrow(ax, (0.75, 0.24), (0.66, 0.48), "history lookup", curve=-0.08, label_offset=-0.02)

    _arrow(ax, (0.72, 0.78), (0.72, 0.59), "requests")
    _arrow(ax, (0.68, 0.59), (0.72, 0.78), "insights", curve=0.14)

    _save(fig, out_png, save_svg)


def build_block_diagram(out_png: Path, save_svg: bool) -> None:
    fig, ax = _new_canvas(
        "Seasonal Demand Forecaster - Block Diagram",
        "High-level component view for project presentation",
    )

    # Column panels inspired by academic block diagrams, with clear spacing and no text overlap.
    _box(ax, 0.06, 0.18, 0.20, 0.66, "", "", face="#e0f2fe", edge="#94a3b8")
    _box(ax, 0.28, 0.18, 0.34, 0.66, "", "", face="#d9f2ec", edge="#94a3b8")
    _box(ax, 0.64, 0.18, 0.14, 0.66, "", "", face="#e2e8f0", edge="#94a3b8")
    _box(ax, 0.80, 0.18, 0.14, 0.66, "", "", face="#dcfce7", edge="#94a3b8")

    ax.text(0.16, 0.80, "INPUT", fontsize=15, fontweight="bold", color="#0f172a", ha="center", va="center", zorder=3)
    ax.text(0.45, 0.80, "PROCESSING", fontsize=15, fontweight="bold", color="#0f172a", ha="center", va="center", zorder=3)
    ax.text(0.71, 0.80, "STORAGE", fontsize=15, fontweight="bold", color="#0f172a", ha="center", va="center", zorder=3)
    ax.text(0.87, 0.80, "OUTPUT", fontsize=15, fontweight="bold", color="#0f172a", ha="center", va="center", zorder=3)

    _term(ax, 0.08, 0.50, 0.16, 0.08, "Sales + Festival Data")
    _box(ax, 0.09, 0.33, 0.14, 0.10, "Input Stage", "train.csv, store.csv, festival calendars", face="#a5f3fc", edge="#0e7490")

    _box(ax, 0.31, 0.60, 0.26, 0.10, "Feature Engineering", "Date, promotions, holidays, regional signals", face="#0f766e", edge="#115e59", title_color="#ffffff", subtitle_color="#d1fae5")
    _box(ax, 0.31, 0.46, 0.26, 0.10, "ML Models", "Random Forest + XGBoost ensembles", face="#0f766e", edge="#115e59", title_color="#ffffff", subtitle_color="#d1fae5")
    _box(ax, 0.31, 0.32, 0.26, 0.10, "Decision Engines", "Discount, inventory, reorder, stockout logic", face="#0f766e", edge="#115e59", title_color="#ffffff", subtitle_color="#d1fae5")

    _box(ax, 0.66, 0.54, 0.10, 0.11, "Model Store", "models/*.pkl", face="#1d4b6d", edge="#0f172a", title_color="#ffffff", subtitle_color="#c7d2fe")
    _box(ax, 0.66, 0.39, 0.10, 0.11, "Analytics CSV", "outputs/*.csv", face="#1d4b6d", edge="#0f172a", title_color="#ffffff", subtitle_color="#c7d2fe")
    _box(ax, 0.66, 0.24, 0.10, 0.11, "Prediction DB", "predictions.db", face="#1d4b6d", edge="#0f172a", title_color="#ffffff", subtitle_color="#c7d2fe")

    _box(ax, 0.82, 0.54, 0.10, 0.10, "FastAPI APIs", "main.py endpoints", face="#5c9f67", edge="#166534")
    _box(ax, 0.82, 0.39, 0.10, 0.10, "React UI", "Dashboard + analytics", face="#d97706", edge="#92400e")
    _box(ax, 0.82, 0.24, 0.10, 0.10, "Final Presentation", "AI-Based Seasonal Demand Forecaster", face="#d97706", edge="#92400e")

    _arrow(ax, (0.24, 0.54), (0.31, 0.65), "input feed")
    _arrow(ax, (0.44, 0.60), (0.44, 0.56), "engineered")
    _arrow(ax, (0.44, 0.46), (0.44, 0.42), "predictions")

    _arrow(ax, (0.57, 0.65), (0.66, 0.59), "save models")
    _arrow(ax, (0.57, 0.51), (0.66, 0.44), "write analytics")
    _arrow(ax, (0.57, 0.37), (0.66, 0.29), "catalog records")

    _arrow(ax, (0.76, 0.59), (0.82, 0.59), "serve")
    _arrow(ax, (0.76, 0.44), (0.82, 0.44), "load")
    _arrow(ax, (0.87, 0.54), (0.87, 0.49), "response")
    _arrow(ax, (0.87, 0.39), (0.87, 0.34), "insights")

    tech_bar = FancyBboxPatch(
        (0.06, 0.03),
        0.88,
        0.10,
        boxstyle="round,pad=0.01,rounding_size=0.01",
        linewidth=1.0,
        edgecolor="#cbd5e1",
        facecolor="#f1f5f9",
        zorder=1,
    )
    ax.add_patch(tech_bar)
    ax.text(0.08, 0.08, "Technology Stack:", fontsize=10, fontweight="bold", color="#0f172a", ha="left", va="center", zorder=2)
    ax.text(0.24, 0.08, "Python + Pandas", fontsize=10, color="#1f2937", ha="center", va="center", zorder=2)
    ax.text(0.40, 0.08, "RF + XGBoost", fontsize=10, color="#1f2937", ha="center", va="center", zorder=2)
    ax.text(0.56, 0.08, "FastAPI", fontsize=10, color="#1f2937", ha="center", va="center", zorder=2)
    ax.text(0.72, 0.08, "SQLite", fontsize=10, color="#1f2937", ha="center", va="center", zorder=2)
    ax.text(0.86, 0.08, "React + Tailwind", fontsize=10, color="#1f2937", ha="center", va="center", zorder=2)

    _save(fig, out_png, save_svg)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate all project diagrams")
    parser.add_argument("--svg", action="store_true", help="Also export SVG files")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Diagram 1: System architecture (uses existing builder)
    build_architecture(OUTPUT_DIR / "01_system_architecture_presentation.png", args.svg)

    # Diagram 2: Flowchart
    build_flowchart(OUTPUT_DIR / "02_flowchart_diagram.png", args.svg)

    # Diagram 3: DFD
    build_dfd(OUTPUT_DIR / "03_data_flow_diagram.png", args.svg)

    # Diagram 4: Block Diagram
    build_block_diagram(OUTPUT_DIR / "04_block_diagram.png", args.svg)

    print("Generated 4 diagrams:")
    print(" - outputs/01_system_architecture_presentation.png")
    print(" - outputs/02_flowchart_diagram.png")
    print(" - outputs/03_data_flow_diagram.png")
    print(" - outputs/04_block_diagram.png")
    if args.svg:
        print("SVG variants generated for all four diagrams as well.")


if __name__ == "__main__":
    main()
