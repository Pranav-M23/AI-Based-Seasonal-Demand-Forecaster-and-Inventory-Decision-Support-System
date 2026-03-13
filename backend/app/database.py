"""
SQLite database for Predictions Catalog.
Uses built-in sqlite3 — no extra dependencies needed.
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "predictions.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create the predictions table if it doesn't exist."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_name      TEXT NOT NULL,
            business_name   TEXT NOT NULL,
            category        TEXT NOT NULL DEFAULT '',
            region          TEXT NOT NULL DEFAULT '',
            state           TEXT NOT NULL DEFAULT '',
            month           INTEGER NOT NULL,
            year            INTEGER NOT NULL,
            predicted_sales INTEGER NOT NULL DEFAULT 0,
            predicted_range_min INTEGER NOT NULL DEFAULT 0,
            predicted_range_max INTEGER NOT NULL DEFAULT 0,
            baseline_sales  INTEGER NOT NULL DEFAULT 0,
            growth_percent  REAL NOT NULL DEFAULT 0,
            discount_recommendation TEXT NOT NULL DEFAULT '',
            stock_range_min INTEGER NOT NULL DEFAULT 0,
            stock_range_max INTEGER NOT NULL DEFAULT 0,
            demand_level    TEXT NOT NULL DEFAULT '',
            festival_name   TEXT DEFAULT NULL,
            status          TEXT NOT NULL DEFAULT 'Draft',
            notes           TEXT NOT NULL DEFAULT '',
            prediction_name TEXT NOT NULL DEFAULT '',
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL,
            history         TEXT NOT NULL DEFAULT '[]'
        )
    """)
    conn.commit()
    conn.close()


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    # Parse history JSON
    try:
        d["history"] = json.loads(d.get("history", "[]"))
    except (json.JSONDecodeError, TypeError):
        d["history"] = []
    return d


def create_prediction(data: dict) -> dict:
    conn = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history_entry = json.dumps([{"time": now, "action": "Created", "by": data.get("owner_name", "")}])

    cur = conn.execute("""
        INSERT INTO predictions (
            owner_name, business_name, category, region, state,
            month, year, predicted_sales, predicted_range_min, predicted_range_max,
            baseline_sales, growth_percent, discount_recommendation,
            stock_range_min, stock_range_max, demand_level, festival_name,
            status, notes, prediction_name, created_at, updated_at, history
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("owner_name", ""),
        data.get("business_name", ""),
        data.get("category", ""),
        data.get("region", ""),
        data.get("state", ""),
        data.get("month", 1),
        data.get("year", 2026),
        data.get("predicted_sales", 0),
        data.get("predicted_range_min", 0),
        data.get("predicted_range_max", 0),
        data.get("baseline_sales", 0),
        data.get("growth_percent", 0),
        data.get("discount_recommendation", ""),
        data.get("stock_range_min", 0),
        data.get("stock_range_max", 0),
        data.get("demand_level", ""),
        data.get("festival_name"),
        data.get("status", "Draft"),
        data.get("notes", ""),
        data.get("prediction_name", ""),
        now, now, history_entry
    ))
    conn.commit()
    row = conn.execute("SELECT * FROM predictions WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def get_all_predictions(
    status: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    category: Optional[str] = None,
    region: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> list:
    conn = get_connection()
    query = "SELECT * FROM predictions WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if month:
        query += " AND month = ?"
        params.append(month)
    if year:
        query += " AND year = ?"
        params.append(year)
    if category:
        query += " AND category = ?"
        params.append(category)
    if region:
        query += " AND region = ?"
        params.append(region)
    if search:
        query += " AND (owner_name LIKE ? OR business_name LIKE ? OR prediction_name LIKE ? OR notes LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like, like])

    # Whitelist sort columns
    allowed_sort = {"created_at", "updated_at", "month", "year", "predicted_sales", "status", "owner_name"}
    col = sort_by if sort_by in allowed_sort else "created_at"
    direction = "ASC" if sort_order.lower() == "asc" else "DESC"
    query += f" ORDER BY {col} {direction}"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_prediction(prediction_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM predictions WHERE id = ?", (prediction_id,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def update_prediction(prediction_id: int, data: dict) -> Optional[dict]:
    conn = get_connection()
    existing = conn.execute("SELECT * FROM predictions WHERE id = ?", (prediction_id,)).fetchone()
    if not existing:
        conn.close()
        return None

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build history
    try:
        history = json.loads(existing["history"])
    except (json.JSONDecodeError, TypeError):
        history = []

    changes = []
    if "status" in data and data["status"] != existing["status"]:
        changes.append(f'Status changed to "{data["status"]}"')
    if "notes" in data and data["notes"] != existing["notes"]:
        changes.append("Notes updated")
    if "prediction_name" in data and data["prediction_name"] != existing["prediction_name"]:
        changes.append("Name updated")
    if not changes:
        changes.append("Updated")

    history.append({"time": now, "action": "; ".join(changes), "by": data.get("owner_name", existing["owner_name"])})

    # Updatable fields
    updatable = [
        "status", "notes", "prediction_name", "owner_name", "business_name",
        "category", "region", "state", "month", "year",
        "predicted_sales", "predicted_range_min", "predicted_range_max",
        "baseline_sales", "growth_percent", "discount_recommendation",
        "stock_range_min", "stock_range_max", "demand_level", "festival_name"
    ]

    set_parts = ["updated_at = ?", "history = ?"]
    params = [now, json.dumps(history)]

    for field in updatable:
        if field in data:
            set_parts.append(f"{field} = ?")
            params.append(data[field])

    params.append(prediction_id)

    conn.execute(f"UPDATE predictions SET {', '.join(set_parts)} WHERE id = ?", params)
    conn.commit()
    row = conn.execute("SELECT * FROM predictions WHERE id = ?", (prediction_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def delete_prediction(prediction_id: int) -> bool:
    conn = get_connection()
    cur = conn.execute("DELETE FROM predictions WHERE id = ?", (prediction_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def bulk_delete_predictions(ids: list) -> int:
    if not ids:
        return 0
    conn = get_connection()
    placeholders = ",".join("?" for _ in ids)
    cur = conn.execute(f"DELETE FROM predictions WHERE id IN ({placeholders})", ids)
    conn.commit()
    conn.close()
    return cur.rowcount


def get_catalog_stats() -> dict:
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) as c FROM predictions").fetchone()["c"]
    this_month = conn.execute(
        "SELECT COUNT(*) as c FROM predictions WHERE month = ? AND year = ?",
        (datetime.now().month, datetime.now().year)
    ).fetchone()["c"]

    status_rows = conn.execute(
        "SELECT status, COUNT(*) as c FROM predictions GROUP BY status"
    ).fetchall()
    status_breakdown = {r["status"]: r["c"] for r in status_rows}

    category_rows = conn.execute(
        "SELECT category, COUNT(*) as c FROM predictions GROUP BY category ORDER BY c DESC LIMIT 5"
    ).fetchall()
    top_categories = [{"category": r["category"], "count": r["c"]} for r in category_rows]

    region_rows = conn.execute(
        "SELECT region, COUNT(*) as c FROM predictions GROUP BY region ORDER BY c DESC"
    ).fetchall()
    region_breakdown = {r["region"]: r["c"] for r in region_rows}

    conn.close()
    return {
        "total": total,
        "this_month": this_month,
        "status_breakdown": status_breakdown,
        "top_categories": top_categories,
        "region_breakdown": region_breakdown,
    }
