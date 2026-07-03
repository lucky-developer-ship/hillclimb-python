import datetime
import json
import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "instance" / "leaderboard.db"

app = Flask(
    __name__,
    template_folder=BASE_DIR / "templates",
    static_folder=BASE_DIR / "static",
)


def _get_db():
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _init_db():
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS scores (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT    NOT NULL,
            distance    REAL    NOT NULL,
            vehicle_id  TEXT    NOT NULL,
            upgrades    TEXT    NOT NULL DEFAULT '',
            coins       INTEGER NOT NULL DEFAULT 0,
            crashed     INTEGER NOT NULL DEFAULT 1,
            completed   INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT    NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_scores_distance ON scores(distance DESC);
        CREATE INDEX IF NOT EXISTS idx_scores_created ON scores(created_at);
    """)
    conn.commit()
    conn.close()


_init_db()


# ─── API ────────────────────────────────────────────────────────────

@app.route("/api/submit", methods=["POST"])
def submit_score():
    data = request.get_json(force=True)
    player_name = (data.get("player_name") or "Anonymous").strip()[:30]
    distance = float(data.get("distance", 0))
    vehicle_id = (data.get("vehicle_id") or "jeep").strip()[:20]
    upgrades = data.get("upgrades", {})
    coins = int(data.get("coins", 0))
    crashed = int(data.get("crashed", 1))
    completed = int(data.get("completed", 0))

    if distance <= 0:
        return jsonify({"error": "distance must be > 0"}), 400

    now = datetime.datetime.utcnow().isoformat()
    conn = _get_db()
    conn.execute(
        """INSERT INTO scores (player_name, distance, vehicle_id, upgrades, coins, crashed, completed, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (player_name, distance, vehicle_id, json.dumps(upgrades), coins, crashed, completed, now),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})


@app.route("/api/leaderboard")
def leaderboard():
    limit = min(int(request.args.get("limit", 20)), 100)
    conn = _get_db()
    rows = conn.execute(
        """SELECT player_name, distance, vehicle_id, upgrades, coins, completed, created_at
           FROM scores ORDER BY distance DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/analytics")
def analytics():
    conn = _get_db()
    avg_dist = conn.execute("SELECT COALESCE(AVG(distance), 0) AS val FROM scores").fetchone()["val"]
    total_runs = conn.execute("SELECT COUNT(*) AS val FROM scores").fetchone()["val"]
    crash_rate = conn.execute(
        "SELECT COALESCE(1.0 * SUM(crashed) / COUNT(*), 0) AS val FROM scores"
    ).fetchone()["val"]
    dau = conn.execute(
        "SELECT COUNT(DISTINCT player_name) AS val FROM scores WHERE created_at >= date('now')"
    ).fetchone()["val"]
    top_vehicle_row = conn.execute(
        "SELECT vehicle_id, COUNT(*) AS cnt FROM scores GROUP BY vehicle_id ORDER BY cnt DESC LIMIT 1"
    ).fetchone()
    top_vehicle = top_vehicle_row["vehicle_id"] if top_vehicle_row else None

    top_upgrades_raw = conn.execute(
        "SELECT upgrades FROM scores WHERE upgrades != '' ORDER BY id DESC LIMIT 100"
    ).fetchall()
    upgrade_counts = {}
    for row in top_upgrades_raw:
        try:
            u = json.loads(row["upgrades"])
            if isinstance(u, dict):
                for uid, lvl in u.items():
                    upgrade_counts[uid] = upgrade_counts.get(uid, 0) + 1
        except Exception:
            pass
    top_upgrade = max(upgrade_counts, key=upgrade_counts.get) if upgrade_counts else None

    conn.close()
    return jsonify({
        "average_crash_distance": round(avg_dist, 1),
        "total_runs": total_runs,
        "crash_rate": round(crash_rate, 3),
        "daily_active_users": dau,
        "most_used_vehicle": top_vehicle,
        "most_used_upgrade": top_upgrade,
    })


# ─── PAGES ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
