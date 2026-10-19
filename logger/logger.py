"""
Bluebikes GBFS station_status logger.

Fetches the current bikes/docks available at every Bluebikes station
and appends one row per station to a daily CSV in data/.
"""

import csv
import os
import sys
import time
from datetime import datetime, timezone

import requests

# GBFS discovery URL (official, from bluebikes.com/system-data).
# We resolve station_status from it so the logger keeps working
# even if Lyft moves the underlying feed URL.
DISCOVERY_URL = "https://gbfs.bluebikes.com/gbfs/gbfs.json"
FALLBACK_STATUS_URL = "https://gbfs.lyft.com/gbfs/1.1/bos/en/station_status.json"

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# How many snapshots to take in one run, and how far apart (seconds).
# Defaults keep the old behaviour: one snapshot, exit.
SNAPSHOTS = int(os.environ.get("SNAPSHOTS", "1"))
INTERVAL_SEC = int(os.environ.get("INTERVAL_SEC", "600"))

FIELDS = [
    "snapshot_utc",        # when the feed said it was last updated
    "fetched_utc",         # when we fetched it
    "station_id",
    "legacy_id",
    "num_bikes_available",
    "num_ebikes_available",
    "num_bikes_disabled",
    "num_docks_available",
    "num_docks_disabled",
    "is_installed",
    "is_renting",
    "is_returning",
    "last_reported",
]


def get_station_status_url() -> str:
    """Resolve the station_status feed URL from the GBFS discovery file."""
    try:
        r = requests.get(DISCOVERY_URL, timeout=30)
        r.raise_for_status()
        feeds = r.json()["data"]["en"]["feeds"]
        for feed in feeds:
            if feed["name"] == "station_status":
                return feed["url"]
    except Exception as e:
        print(f"Discovery failed ({e}); using fallback URL.", file=sys.stderr)
    return FALLBACK_STATUS_URL


def fetch_snapshot(url: str) -> tuple[str, list[dict]]:
    """Fetch station_status and return (feed_timestamp_iso, station rows)."""
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    payload = r.json()
    snapshot_utc = datetime.fromtimestamp(
        payload["last_updated"], tz=timezone.utc
    ).isoformat()
    return snapshot_utc, payload["data"]["stations"]


def append_rows(snapshot_utc: str, stations: list[dict]) -> str:
    """Append one row per station to today's CSV. Returns the file path."""
    os.makedirs(DATA_DIR, exist_ok=True)
    fetched_utc = datetime.now(timezone.utc).isoformat()
    # One file per day keeps files small and diffs manageable.
    day = fetched_utc[:10]  # YYYY-MM-DD
    path = os.path.join(DATA_DIR, f"station_status_{day}.csv")
    new_file = not os.path.exists(path)

    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if new_file:
            w.writeheader()
        for s in stations:
            w.writerow({
                "snapshot_utc": snapshot_utc,
                "fetched_utc": fetched_utc,
                "station_id": s.get("station_id", ""),
                "legacy_id": s.get("legacy_id", ""),
                "num_bikes_available": s.get("num_bikes_available", ""),
                "num_ebikes_available": s.get("num_ebikes_available", 0),
                "num_bikes_disabled": s.get("num_bikes_disabled", ""),
                "num_docks_available": s.get("num_docks_available", ""),
                "num_docks_disabled": s.get("num_docks_disabled", ""),
                "is_installed": s.get("is_installed", ""),
                "is_renting": s.get("is_renting", ""),
                "is_returning": s.get("is_returning", ""),
                "last_reported": s.get("last_reported", ""),
            })
    return path


def log_once(url: str) -> None:
    """Fetch one snapshot, append it, print a one-line summary."""
    snapshot_utc, stations = fetch_snapshot(url)
    path = append_rows(snapshot_utc, stations)
    empty = sum(1 for s in stations
                if s.get("num_bikes_available") == 0 and s.get("is_renting") == 1)
    full = sum(1 for s in stations
               if s.get("num_docks_available") == 0 and s.get("is_returning") == 1)
    print(f"Logged {len(stations)} stations to {os.path.basename(path)} "
          f"(snapshot {snapshot_utc}). Empty: {empty}, full: {full}.", flush=True)


def main() -> None:
    url = get_station_status_url()          # resolve once per run, not per snapshot
    for i in range(SNAPSHOTS):
        try:
            log_once(url)
        except Exception as e:              # one bad fetch shouldn't kill the whole run
            print(f"Snapshot {i + 1}/{SNAPSHOTS} failed: {e}", file=sys.stderr, flush=True)
        if i < SNAPSHOTS - 1:
            time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()
