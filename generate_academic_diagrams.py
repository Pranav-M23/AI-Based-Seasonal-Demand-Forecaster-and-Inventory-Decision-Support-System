import os
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon


OUTPUT_DIR = Path("outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _canvas() -> tuple:
    fig, ax = plt.subplots(figsize=(16, 9), dpi=220)
    fig.patch.set_facecolor("#eef2f7")
    ax.set_facecolor("#eef2f7")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def _header(ax, title: str) -> None:
    shadow = FancyBboxPatch((0.155, 0.902), 0.69, 0.06, boxstyle="round,pad=0.006,rounding_size=0.01", linewidth=0, facecolor="#0f172a", alpha=0.25, zorder=1)
    ax.add_patch(shadow)
    bar = FancyBboxPatch((0.15, 0.91), 0.69, 0.06, boxstyle="round,pad=0.006,rounding_size=0.01", linewidth=1.2, edgecolor="#0b3b5a", facecolor="#154b6f", zorder=2)
    ax.add_patch(bar)
    ax.text(0.495, 0.94, title.upper(), color="#f8fafc", fontsize=16, fontweight="bold", ha="center", va="center", zorder=3)


def _rounded(ax, x, y, w, h, text, fc, ec="#0f172a", tc="#ffffff", fs=11, rs=0.012):
    shadow = FancyBboxPatch((x + 0.003, y - 0.004), w, h, boxstyle=f"round,pad=0.008,rounding_size={rs}", linewidth=0, facecolor="#0f172a", alpha=0.18, zorder=2)
    ax.add_patch(shadow)
    box = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.008,rounding_size={rs}", linewidth=1.1, edgecolor=ec, facecolor=fc, zorder=3)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text, color=tc, fontsize=fs, fontweight="bold", ha="center", va="center", zorder=4)


def _pill(ax, x, y, w, h, text, fc="#17496c"):
    _rounded(ax, x, y, w, h, text, fc=fc, rs=h / 1.9, fs=10)


def _diamond(ax, x, y, w, h, text, fc="#0f3b5a", ec="#08283d"):
    vertices = [(x, y + h / 2), (x + w / 2, y + h), (x + w, y + h / 2), (x + w / 2, y)]
    poly = Polygon(vertices, closed=True, facecolor=fc, edgecolor=ec, linewidth=1.2, zorder=3)
    ax.add_patch(poly)
    ax.text(x + w / 2, y + h / 2, text, color="#ffffff", fontsize=10, fontweight="bold", ha="center", va="center", zorder=4)


def _parallelogram(ax, x, y, w, h, text, fc="#d97706", ec="#92400e", tc="#ffffff"):
    slant = 0.02
    vertices = [(x + slant, y + h), (x + w, y + h), (x + w - slant, y), (x, y)]
    poly = Polygon(vertices, closed=True, facecolor=fc, edgecolor=ec, linewidth=1.2, zorder=3)
    ax.add_patch(poly)
    ax.text(x + w / 2, y + h / 2, text, color=tc, fontsize=10, fontweight="bold", ha="center", va="center", zorder=4)


def _circle(ax, cx, cy, r, text, fc="#efad44", ec="#d18a1f", tc="#ffffff"):
    c = Ellipse((cx, cy), 2 * r, 2 * r, facecolor=fc, edgecolor=ec, linewidth=1.2, zorder=3)
    ax.add_patch(c)
    ax.text(cx, cy, text, color=tc, fontsize=10.5, fontweight="bold", ha="center", va="center", zorder=4)


def _arrow(ax, a, b, label="", ms=16, lw=1.6, curve=0.0):
    ar = FancyArrowPatch(posA=a, posB=b, arrowstyle="-|>", mutation_scale=ms, linewidth=lw, color="#111827", connectionstyle=f"arc3,rad={curve}", zorder=5)
    ax.add_patch(ar)
    if label:
        lx = (a[0] + b[0]) / 2
        ly = (a[1] + b[1]) / 2 + 0.014
        ax.text(lx, ly, label, fontsize=9.5, color="#111827", fontweight="bold", ha="center", va="center", zorder=6)


def _orth(ax, points, label=""):
    for i in range(len(points) - 1):
        p0 = points[i]
        p1 = points[i + 1]
        if i < len(points) - 2:
            plt.plot([p0[0], p1[0]], [p0[1], p1[1]], color="#111827", linewidth=1.6, zorder=4)
        else:
            _arrow(plt.gca(), p0, p1)
    if label:
        mid = points[len(points) // 2]
        plt.text(mid[0] + 0.008, mid[1] + 0.012, label, fontsize=9.5, color="#111827", fontweight="bold", zorder=6)


def build_flowchart() -> None:
    fig, ax = _canvas()
    _header(ax, "Sample Flowchart: Seasonal Demand Forecasting")

    blue = "#2f7fb5"
    green = "#4f9d62"
    orange = "#d57a16"
    navy = "#0d3b59"

    _pill(ax, 0.08, 0.76, 0.13, 0.065, "START\n(SYSTEM ACTIVATE)")
    _rounded(ax, 0.08, 0.59, 0.13, 0.11, "ACTIVATE DATA\nINGESTION &\nCAPTURE", fc=blue)
    _diamond(ax, 0.08, 0.44, 0.13, 0.13, "DATA\nVALID?")
    _rounded(ax, 0.25, 0.45, 0.14, 0.10, "EXTRACT DEMAND\nFEATURES", fc=green)
    _rounded(ax, 0.42, 0.45, 0.14, 0.10, "SEARCH MODELS\nFOR MATCH", fc=blue)
    _diamond(ax, 0.59, 0.44, 0.13, 0.13, "MATCH\nFOUND?")
    _rounded(ax, 0.75, 0.45, 0.14, 0.10, "MARK FORECAST\nFOR STORE ID", fc=green)
    _parallelogram(ax, 0.91, 0.45, 0.12, 0.10, "UPDATE\nFORECAST DB")
    _parallelogram(ax, 0.58, 0.26, 0.14, 0.09, "DISPLAY\n\"UNRECOGNIZED\"", fc=orange)
    _parallelogram(ax, 0.91, 0.31, 0.12, 0.09, "DISPLAY\n\"FORECASTED\"", fc=green, ec="#166534")
    _pill(ax, 0.91, 0.14, 0.12, 0.07, "STOP\n(END SESSION)", fc=navy)

    _arrow(ax, (0.145, 0.76), (0.145, 0.70))
    _arrow(ax, (0.145, 0.59), (0.145, 0.57))
    _arrow(ax, (0.21, 0.505), (0.25, 0.505), "YES")
    _arrow(ax, (0.39, 0.505), (0.42, 0.505))
    _arrow(ax, (0.56, 0.505), (0.59, 0.505))
    _arrow(ax, (0.72, 0.505), (0.75, 0.505), "YES")
    _arrow(ax, (0.89, 0.505), (0.91, 0.505))
    _arrow(ax, (0.97, 0.45), (0.97, 0.40))
    _arrow(ax, (0.97, 0.31), (0.97, 0.21))
    _arrow(ax, (0.655, 0.44), (0.655, 0.35), "NO")

    _orth(ax, [(0.08, 0.505), (0.04, 0.505), (0.04, 0.645), (0.08, 0.645)], "NO")
    _orth(ax, [(0.655, 0.57), (0.655, 0.66), (0.145, 0.66), (0.145, 0.70)], "NO")
    _orth(ax, [(0.655, 0.26), (0.145, 0.26), (0.145, 0.44)], "")

    fig.savefig(OUTPUT_DIR / "02_flowchart_diagram.png", bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(OUTPUT_DIR / "02_flowchart_diagram.svg", bbox_inches="tight", facecolor=fig.get_facecolor(), format="svg")
    plt.close(fig)


def build_block_diagram() -> None:
    fig, ax = _canvas()
    _header(ax, "Sample Block Diagram: Seasonal Demand Forecaster")

    def col(x, w, title, bg):
        p = FancyBboxPatch((x, 0.20), w, 0.64, boxstyle="round,pad=0.006,rounding_size=0.01", linewidth=0, facecolor=bg, alpha=0.72, zorder=1)
        ax.add_patch(p)
        ax.text(x + w / 2, 0.81, title, fontsize=16, fontweight="bold", color="#0b0f1a", ha="center", va="center", zorder=2)

    col(0.16, 0.10, "INPUT", "#d8edf2")
    col(0.27, 0.31, "PROCESSING", "#cfe7ea")
    col(0.60, 0.12, "STORAGE", "#dee7ef")
    col(0.73, 0.20, "OUTPUT", "#dcedd7")

    _pill(ax, 0.02, 0.19, 0.09, 0.07, "START\n(POWER ON)")
    _rounded(ax, 0.02, 0.52, 0.10, 0.065, "USER\n(PLANNER)", fc="#5fa1ad")
    _rounded(ax, 0.02, 0.39, 0.10, 0.065, "SALES &\nCALENDAR FEED", fc="#5fa1ad")
    _rounded(ax, 0.17, 0.45, 0.07, 0.10, "INPUT\nSTAGE", fc="#7eb6be")

    _rounded(ax, 0.29, 0.26, 0.16, 0.54, "", fc="#0f5d67", ec="#083b41")
    _rounded(ax, 0.30, 0.68, 0.14, 0.08, "FEATURE ENCODER", fc="#1b4950")
    _rounded(ax, 0.30, 0.57, 0.14, 0.08, "IMAGE PREPROCESSING", fc="#1b4950")
    _rounded(ax, 0.30, 0.46, 0.14, 0.08, "DEMAND FEATURE\nEXTRACTION", fc="#1b4950")
    _rounded(ax, 0.30, 0.35, 0.14, 0.08, "MATCHING +\nFORECAST ENGINE", fc="#1b4950")

    _rounded(ax, 0.47, 0.28, 0.09, 0.50, "DATA\nMANAGEMENT\nUNIT", fc="#156e77")

    _rounded(ax, 0.62, 0.40, 0.09, 0.40, "DATABASE\n(STUDENT\nRECORDS)", fc="#1d4b6d")
    _rounded(ax, 0.62, 0.27, 0.09, 0.09, "SYSTEM\nLOGS", fc="#1d4b6d")

    _rounded(ax, 0.74, 0.53, 0.10, 0.11, "MARKING\nSYSTEM", fc="#5c9f67")
    _rounded(ax, 0.85, 0.62, 0.08, 0.09, "FORECAST\nDATABASE", fc="#5c9f67")
    _rounded(ax, 0.85, 0.49, 0.08, 0.09, "ADMIN\nDASHBOARD", fc="#5c9f67")

    out_panel = FancyBboxPatch((0.73, 0.22), 0.20, 0.22, boxstyle="round,pad=0.008,rounding_size=0.01", linewidth=0, facecolor="#f3e1cf", zorder=2)
    ax.add_patch(out_panel)
    _rounded(ax, 0.82, 0.33, 0.10, 0.10, "USER\nINTERFACE\n(DISPLAY)", fc="#d3841b")
    _rounded(ax, 0.82, 0.22, 0.10, 0.08, "NOTIFICATION\nSERVICE", fc="#d3841b")
    _pill(ax, 0.82, 0.09, 0.10, 0.08, "STOP\n(POWER OFF)")

    _arrow(ax, (0.12, 0.55), (0.17, 0.50), "Video Feed", ms=14)
    _arrow(ax, (0.12, 0.42), (0.17, 0.49), "Video Feed", ms=14)
    _arrow(ax, (0.24, 0.50), (0.29, 0.50))
    _arrow(ax, (0.45, 0.50), (0.47, 0.50), "Processed Data", ms=14)
    _arrow(ax, (0.56, 0.50), (0.62, 0.50), "Query/Response", ms=14)
    _arrow(ax, (0.71, 0.60), (0.74, 0.585))
    _arrow(ax, (0.84, 0.585), (0.85, 0.665))
    _arrow(ax, (0.84, 0.585), (0.85, 0.535))
    _arrow(ax, (0.79, 0.53), (0.82, 0.38), "Update", ms=14)
    _arrow(ax, (0.87, 0.33), (0.87, 0.30), "Display", ms=14)
    _arrow(ax, (0.87, 0.22), (0.87, 0.17), ms=14)
    _arrow(ax, (0.665, 0.40), (0.665, 0.36), ms=14)
    _arrow(ax, (0.665, 0.36), (0.665, 0.40), ms=14)

    footer = FancyBboxPatch((0.02, 0.02), 0.74, 0.10, boxstyle="round,pad=0.007,rounding_size=0.01", linewidth=1.0, edgecolor="#c5ced8", facecolor="#e8eef5", zorder=1)
    ax.add_patch(footer)
    ax.text(0.035, 0.067, "System Components\nand Technology Stack", fontsize=10.5, fontweight="bold", color="#0b0f1a", ha="left", va="center", zorder=2)
    ax.text(0.26, 0.067, "Python &\nPandas", fontsize=10, fontweight="bold", ha="center", va="center", color="#111827")
    ax.text(0.39, 0.067, "XGBoost /\nRandom Forest", fontsize=10, fontweight="bold", ha="center", va="center", color="#111827")
    ax.text(0.52, 0.067, "FastAPI\nService", fontsize=10, fontweight="bold", ha="center", va="center", color="#111827")
    ax.text(0.65, 0.067, "SQLite\nReact UI", fontsize=10, fontweight="bold", ha="center", va="center", color="#111827")

    fig.savefig(OUTPUT_DIR / "04_block_diagram.png", bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(OUTPUT_DIR / "04_block_diagram.svg", bbox_inches="tight", facecolor=fig.get_facecolor(), format="svg")
    plt.close(fig)


def build_dfd() -> None:
    fig, ax = _canvas()
    fig.patch.set_facecolor("#f5f5f5")
    ax.set_facecolor("#f5f5f5")
    ax.text(0.50, 0.95, "Data Flow Diagram", fontsize=23, fontweight="bold", color="#111827", ha="center", va="center")
    ax.text(0.50, 0.91, "How does data move so order and demand pipelines are completed?", fontsize=12, color="#4b5563", ha="center", va="center")

    _rounded(ax, 0.08, 0.74, 0.16, 0.08, "Customer", fc="#4b83d1")
    _circle(ax, 0.50, 0.76, 0.065, "Add\nProduct\nto Cart")
    _rounded(ax, 0.70, 0.74, 0.16, 0.08, "Shopping Cart", fc="#edad45")

    _circle(ax, 0.50, 0.60, 0.065, "Checkout")
    _circle(ax, 0.50, 0.44, 0.065, "Collect\nPayment")
    _circle(ax, 0.50, 0.28, 0.065, "Order\nIssue")

    _rounded(ax, 0.70, 0.39, 0.16, 0.10, "Credit Card\nCompany", fc="#4b83d1")
    _rounded(ax, 0.70, 0.22, 0.16, 0.10, "Inventory", fc="#edad45")
    _rounded(ax, 0.08, 0.22, 0.16, 0.10, "Accounting", fc="#edad45")

    _arrow(ax, (0.24, 0.78), (0.44, 0.76), "Select Item")
    _arrow(ax, (0.565, 0.76), (0.70, 0.76), "Cart item")
    _arrow(ax, (0.50, 0.695), (0.50, 0.665))
    _arrow(ax, (0.50, 0.535), (0.50, 0.505))
    _arrow(ax, (0.50, 0.375), (0.50, 0.345))

    _arrow(ax, (0.565, 0.45), (0.70, 0.45), "Post payment")
    _arrow(ax, (0.70, 0.42), (0.565, 0.42), "Receive money")
    _arrow(ax, (0.565, 0.28), (0.70, 0.29), "Shipping request")
    _arrow(ax, (0.435, 0.295), (0.24, 0.27), "Order info")

    _orth(ax, [(0.70, 0.76), (0.61, 0.76), (0.61, 0.60), (0.56, 0.60)], "Item details")
    _orth(ax, [(0.435, 0.44), (0.35, 0.44), (0.35, 0.74), (0.24, 0.74)], "Send receipt")
    _orth(ax, [(0.76, 0.22), (0.76, 0.15), (0.12, 0.15), (0.12, 0.74)], "Ship product")

    fig.savefig(OUTPUT_DIR / "03_data_flow_diagram.png", bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(OUTPUT_DIR / "03_data_flow_diagram.svg", bbox_inches="tight", facecolor=fig.get_facecolor(), format="svg")
    plt.close(fig)


if __name__ == "__main__":
    build_flowchart()
    build_dfd()
    build_block_diagram()
    print("Generated professional reference-matched diagrams in outputs/")
