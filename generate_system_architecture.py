"""
Generate a presentation-ready system architecture diagram for the
Seasonal Demand Forecaster project.

Usage:
  python generate_system_architecture.py
  python generate_system_architecture.py --output outputs/system_architecture_presentation.png --svg
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


@dataclass
class Card:
    title: str
    subtitle: str
    x: float
    y: float
    w: float
    h: float
    face: str
    edge: str


def draw_gradient_background(ax) -> None:
    gradient = np.linspace(0, 1, 600)
    gradient = np.vstack((gradient, gradient))
    ax.imshow(
        gradient,
        extent=(0, 1, 0, 1),
        transform=ax.transAxes,
        cmap="Blues",
        alpha=0.09,
        aspect="auto",
        zorder=0,
    )


def draw_lane(ax, x: float, y: float, w: float, h: float, title: str, color: str) -> None:
    lane = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        linewidth=1.3,
        edgecolor=color,
        facecolor="#ffffff",
        alpha=0.88,
        zorder=1,
    )
    ax.add_patch(lane)
    ax.text(
        x + 0.012,
        y + h - 0.02,
        title,
        fontsize=10,
        fontweight="bold",
        color=color,
        ha="left",
        va="top",
        zorder=4,
    )


def draw_card(ax, card: Card) -> None:
    shadow = FancyBboxPatch(
        (card.x + 0.003, card.y - 0.004),
        card.w,
        card.h,
        boxstyle="round,pad=0.01,rounding_size=0.018",
        linewidth=0,
        facecolor="#475569",
        alpha=0.18,
        zorder=2,
    )
    ax.add_patch(shadow)

    body = FancyBboxPatch(
        (card.x, card.y),
        card.w,
        card.h,
        boxstyle="round,pad=0.01,rounding_size=0.018",
        linewidth=1.2,
        edgecolor=card.edge,
        facecolor=card.face,
        zorder=3,
    )
    ax.add_patch(body)

    ax.text(
        card.x + card.w / 2,
        card.y + card.h * 0.63,
        card.title,
        fontsize=10,
        fontweight="bold",
        color="#0f172a",
        ha="center",
        va="center",
        zorder=5,
    )
    ax.text(
        card.x + card.w / 2,
        card.y + card.h * 0.31,
        card.subtitle,
        fontsize=8.1,
        color="#334155",
        ha="center",
        va="center",
        zorder=5,
    )


def draw_flow(
    ax,
    start: tuple[float, float],
    end: tuple[float, float],
    label: str,
    color: str = "#1e293b",
    curve: float = 0.0,
    dy: float = 0.014,
) -> None:
    flow = FancyArrowPatch(
        posA=start,
        posB=end,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=1.5,
        color=color,
        connectionstyle=f"arc3,rad={curve}",
        zorder=6,
    )
    ax.add_patch(flow)

    lx = (start[0] + end[0]) / 2
    ly = (start[1] + end[1]) / 2 + dy
    ax.text(
        lx,
        ly,
        label,
        fontsize=7.4,
        color="#334155",
        ha="center",
        va="center",
        bbox=dict(boxstyle="round,pad=0.14", fc="#ffffff", ec="none", alpha=0.93),
        zorder=7,
    )


def build_architecture(output_file: Path, save_svg: bool) -> None:
    fig, ax = plt.subplots(figsize=(16, 9), dpi=240)
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    draw_gradient_background(ax)

    ax.text(
        0.03,
        0.965,
        "Seasonal Demand Forecaster - Presentation Architecture",
        fontsize=22,
        fontweight="bold",
        color="#0f172a",
        ha="left",
        va="top",
    )
    ax.text(
        0.03,
        0.927,
        "Offline ML Factory + High-Speed API + Business Dashboards",
        fontsize=11,
        color="#334155",
        ha="left",
        va="top",
    )

    draw_lane(ax, 0.03, 0.14, 0.21, 0.73, "1) Data + Training", "#0284c7")
    draw_lane(ax, 0.27, 0.14, 0.23, 0.73, "2) ML Pipeline", "#16a34a")
    draw_lane(ax, 0.53, 0.14, 0.22, 0.73, "3) Backend Service", "#ea580c")
    draw_lane(ax, 0.78, 0.14, 0.19, 0.73, "4) Frontend + Users", "#7c3aed")

    cards = {
        "raw": Card(
            "Raw Data Sources",
            "Data/train.csv, Data/store.csv\nFestival calendars (regional/state)",
            0.055,
            0.64,
            0.16,
            0.11,
            "#e0f2fe",
            "#0284c7",
        ),
        "train": Card(
            "Model Training",
            "ml_models.py\nRF + XGBoost (5 models)",
            0.055,
            0.46,
            0.16,
            0.11,
            "#dbeafe",
            "#2563eb",
        ),
        "models": Card(
            "Model Artifacts",
            "models/*.pkl\nencoders + estimators",
            0.055,
            0.28,
            0.16,
            0.11,
            "#dbeafe",
            "#2563eb",
        ),
        "pipeline": Card(
            "Forecast Pipeline",
            "ml_pipeline.py\nstore x category x day",
            0.305,
            0.54,
            0.16,
            0.11,
            "#dcfce7",
            "#16a34a",
        ),
        "outputs": Card(
            "Output Analytics",
            "outputs/*.csv\nforecast, discounts, inventory, actions",
            0.305,
            0.32,
            0.16,
            0.11,
            "#dcfce7",
            "#16a34a",
        ),
        "loader": Card(
            "Data Loader Layer",
            "backend/app/data_loader.py\ncolumn alias + fallback mapping",
            0.56,
            0.57,
            0.16,
            0.11,
            "#ffedd5",
            "#f97316",
        ),
        "api": Card(
            "FastAPI Application",
            "backend/app/main.py\nforecast, inventory, discount, KPI APIs",
            0.56,
            0.37,
            0.16,
            0.11,
            "#ffedd5",
            "#f97316",
        ),
        "db": Card(
            "Predictions Catalog DB",
            "SQLite (predictions.db)\ncreate, update, workflow tracking",
            0.56,
            0.20,
            0.16,
            0.11,
            "#ede9fe",
            "#8b5cf6",
        ),
        "ui": Card(
            "React Dashboards",
            "Predictive Dashboard\nShop Owner Analytics\nPrediction Catalog",
            0.80,
            0.50,
            0.15,
            0.13,
            "#ede9fe",
            "#7c3aed",
        ),
        "users": Card(
            "AI-BASED SEASONAL\nDEMAND FORECASTER",
            "Final Unified Dashboard\n1) Predictive Dashboard\n2) Shop Owner Analytics\n3) Prediction Catalogue",
            0.795,
            0.21,
            0.16,
            0.17,
            "#fef3c7",
            "#f59e0b",
        ),
    }

    for card in cards.values():
        draw_card(ax, card)

    # Vertical flows in each lane
    draw_flow(ax, (0.135, 0.64), (0.135, 0.57), "prepare training data")
    draw_flow(ax, (0.135, 0.46), (0.135, 0.39), "save trained models")
    draw_flow(ax, (0.385, 0.54), (0.385, 0.43), "generate daily forecasts")
    draw_flow(ax, (0.64, 0.57), (0.64, 0.48), "load analytics datasets")
    draw_flow(ax, (0.64, 0.37), (0.64, 0.31), "save prediction history")
    draw_flow(ax, (0.875, 0.50), (0.875, 0.38), "deliver final insights")

    # Cross-lane flows (left to right, no line intersections)
    draw_flow(ax, (0.215, 0.515), (0.305, 0.595), "train ML models", dy=0.02)
    draw_flow(ax, (0.215, 0.335), (0.305, 0.595), "load trained ML models", dy=-0.018, curve=0.10)
    draw_flow(ax, (0.465, 0.375), (0.56, 0.625), "export analytics datasets", dy=0.018, curve=0.02)
    draw_flow(ax, (0.72, 0.435), (0.80, 0.58), "API responses (JSON)", dy=0.028, curve=0.12)
    draw_flow(ax, (0.80, 0.515), (0.72, 0.405), "dashboard filters + data requests", dy=-0.034, curve=-0.14)
    draw_flow(ax, (0.72, 0.24), (0.80, 0.315), "catalog records", dy=0.012)

    # Bottom highlights for presentation talking points
    ax.text(
        0.875,
        0.402,
        "MAIN OUTPUT",
        fontsize=9,
        fontweight="bold",
        color="#7c2d12",
        ha="center",
        va="center",
        bbox=dict(boxstyle="round,pad=0.24", fc="#fde68a", ec="#f59e0b", lw=1.2),
        zorder=8,
    )

    highlights = FancyBboxPatch(
        (0.03, 0.05),
        0.94,
        0.06,
        boxstyle="round,pad=0.01,rounding_size=0.016",
        linewidth=0,
        facecolor="#0f172a",
        alpha=0.92,
        zorder=3,
    )
    ax.add_patch(highlights)
    ax.text(
        0.045,
        0.081,
        "Presentation Message: Offline ML computation -> precomputed CSV analytics -> low latency FastAPI -> business ready dashboards",
        fontsize=9,
        color="#f8fafc",
        ha="left",
        va="center",
        zorder=5,
    )
    ax.text(
        0.045,
        0.058,
        "Models: Demand Ensemble | Festival Uplift | Discount Optimization | Inventory Classification | Stockout Risk",
        fontsize=8.2,
        color="#cbd5e1",
        ha="left",
        va="center",
        zorder=5,
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, bbox_inches="tight", facecolor=fig.get_facecolor())
    if save_svg:
        fig.savefig(output_file.with_suffix(".svg"), bbox_inches="tight", format="svg", facecolor=fig.get_facecolor())
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate presentation architecture diagram")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs") / "system_architecture_presentation.png",
        help="Output PNG path",
    )
    parser.add_argument("--svg", action="store_true", help="Also export SVG")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_architecture(args.output, args.svg)
    print(f"Architecture diagram generated: {args.output}")
    if args.svg:
        print(f"Architecture diagram generated: {args.output.with_suffix('.svg')}")


if __name__ == "__main__":
    main()
