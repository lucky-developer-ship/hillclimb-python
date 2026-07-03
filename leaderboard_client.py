"""Optional client for submitting scores to the leaderboard server.

Usage:
    from leaderboard_client import submit_score
    submit_score("Player1", 450.0, "jeep", {"engine": 2, "tires": 1}, coins=120, crashed=False)
"""

import json
import os
import urllib.request

SERVER_URL = os.environ.get("LEADERBOARD_URL", "http://127.0.0.1:5000")


def submit_score(player_name, distance, vehicle_id, upgrades=None, coins=0, crashed=True, timeout=3):
    payload = json.dumps({
        "player_name": player_name,
        "distance": distance,
        "vehicle_id": vehicle_id,
        "upgrades": upgrades or {},
        "coins": coins,
        "crashed": int(crashed),
        "completed": int(not crashed),
    }).encode()
    req = urllib.request.Request(
        f"{SERVER_URL}/api/submit",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=timeout)
        return True
    except Exception:
        return False
