# The station availability logger

This folder holds the two files that collected our live data: `logger.py` and the GitHub Actions workflow `log.yml`. They are copied from our logger repository, https://github.com/AdhamKhouly/bluebikes-logger, where the workflow lives at `.github/workflows/log.yml` and the daily CSVs are committed to `data/`.

## Why we needed it

The trip history tells us where bikes start and end, so we can see which stations lose or gain bikes in each hour. It cannot tell us whether a station was actually empty: if the vans refilled it, riders still found bikes, and a rider who arrived at an empty station and walked away leaves no trip record at all. Bluebikes publishes the current state of every station in its public GBFS feed, but only the current state, with no history. So we saved that feed ourselves, every few minutes, for about a month.

## What it collects

`logger.py` reads the GBFS discovery file at https://gbfs.bluebikes.com/gbfs/gbfs.json, finds the `station_status` feed in it, and downloads that feed (if the discovery file cannot be read it falls back to the Lyft `station_status.json` URL in the script). The feed has one record per station. The script appends one row per station to a CSV named after the current UTC date, `data/station_status_YYYY-MM-DD.csv`, writing the header only when the file is new.

Each row has: `snapshot_utc` (the time the feed says it was last updated), `fetched_utc` (the time we downloaded it), `station_id`, `legacy_id`, `num_bikes_available`, `num_ebikes_available`, `num_bikes_disabled`, `num_docks_available`, `num_docks_disabled`, `is_installed`, `is_renting`, `is_returning` and `last_reported`. After each snapshot it prints how many stations were logged and how many had zero bikes or zero docks.

The log is a record of what the feed reported. It does not record van visits (the notebook estimates those from sudden jumps in bike counts), and it does not record riders who could not find a bike.

Two settings come from environment variables: `SNAPSHOTS`, how many snapshots to take in one run (default 1), and `INTERVAL_SEC`, the pause between them (default 600 seconds, ten minutes). If one download fails, the script prints the error and continues with the next snapshot.

## How often it ran

The workflow is scheduled by GitHub Actions. The schedule changed three times, which matters for reading the data:

- **September 17.** The workflow asked for a run every ten minutes (`*/10 * * * *`, later `4,14,24,34,44,54 * * * *`), one snapshot per run. GitHub treats scheduled jobs as best effort, and in practice it started the job only about six times a day. That is why the September files are thin: a handful of snapshots per day instead of 144.
- **October 4.** The schedule was changed to hourly (`0 * * * *`) with six snapshots ten minutes apart in each run. GitHub still started far fewer runs than requested.
- **October 7.** The run itself was made long instead of relying on the schedule: each run now takes `SNAPSHOTS: "33"` snapshots at `INTERVAL_SEC: "600"`, about five and a half hours of coverage, with `timeout-minutes: 355` (GitHub's limit is 360). GitHub starts about four runs a day, so the days from October 7 have 113 to 147 snapshots each, close to the ten-minute target. The commit step runs even if the job is cancelled, so partial runs are kept.

After every run the workflow commits the new rows to `data/` and pushes them (`permissions: contents: write`, with a `git pull --rebase` first in case another run pushed meanwhile). The `concurrency` block queues overlapping runs instead of cancelling them. The `.gitattributes` file in the repository sets `merge=union` for the CSVs so two runs appending to the same day's file do not conflict.

## Why the notebook uses 11 dense days

Hour-by-hour empty rates need many readings in every hour of the day. The notebook defines a day as dense when it has at least 36 snapshots, which first happens on October 7, and the saved outputs use the 31 daily files through October 17: 11 dense days (October 7 to 17, 8 weekdays and 3 weekend days). The sparse September days are still used for the station-level training period in the train/test check, where the number of readings per day matters less.

## Running it yourself

One snapshot on your own computer:

```bash
pip install requests
python logger.py
```

This writes or appends to `data/station_status_<today>.csv` next to the script. For several snapshots in one run:

```bash
SNAPSHOTS=6 INTERVAL_SEC=600 python logger.py
```

To schedule it on GitHub, put `logger.py` in the root of a repository and `log.yml` in `.github/workflows/`, and enable Actions. The workflow needs no secrets: it pushes with the token GitHub gives every workflow, which is why `permissions: contents: write` is set. You can also start a run by hand from the Actions tab (`workflow_dispatch`). Expect GitHub to start scheduled runs less often than the cron line asks for; the long-run setting from October 7 is the workaround.
