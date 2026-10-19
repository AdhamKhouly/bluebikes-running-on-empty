# Data and setup

This page explains what each dataset is, where it came from, and how to set things up to run the notebook.

## Running the notebook in Google Colab (step by step)

The notebook expects a folder in your Google Drive called `BA780-bluebikes` with this layout. The folder name is written into the notebook, so keep it exactly.

```text
My Drive/
└── BA780-bluebikes/
    ├── data/
    │   ├── Bluebike Stations.csv
    │   ├── NOAA daily weather, Boston Logan.csv
    │   ├── bluebikes-trips/
    │   │   ├── 202509-bluebikes-tripdata.csv
    │   │   ├── ...
    │   │   └── 202608-bluebikes-tripdata.csv
    │   └── gbfs-logs/
    │       ├── station_status_2026-09-17.csv
    │       ├── ...
    │       └── station_status_2026-10-17.csv
    └── outputs/
```

1. In Google Drive, create the folder `BA780-bluebikes`, and inside it the folders `data` and `outputs`.
2. Copy everything from this repository's `data/` folder into `BA780-bluebikes/data/` (the station list, the weather file and the `gbfs-logs` folder).
3. Download the trip files (see below) and put the twelve CSVs in `BA780-bluebikes/data/bluebikes-trips/`.
4. Open `B10-Running-On-Empty.ipynb` in Google Colab (File, Upload notebook, or open it from Drive).
5. Run the cells from the top. The first cell asks you to allow access to Google Drive.
6. The cell in Section 2.4 that clones the logger repository can be skipped: the files are already in `gbfs-logs`, and the notebook only reads files up to October 17 anyway. One later cell downloads the station information feed from Bluebikes, so the notebook needs internet access.

The whole notebook takes a few minutes; loading the trip files is the slow part.

## Running on your own computer

Replace the first code cell (the one with `drive.mount`) with:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
DATA = "data"        # path to this folder
OUT = "outputs"      # an existing folder where the Q14 priority list is saved
```

Then skip the logger sync cell in Section 2.4 and run everything else unchanged. You need Python 3 with the libraries in `requirements.txt`. We have not tested a run from a fresh clone of this repository; the saved outputs in the notebook come from our Colab run.

## Files in this folder

### Bluebike Stations.csv (included, 50 KB)

The Bluebikes station list from https://bluebikes.com/system-data (file header says last updated 8/21/2026). One row per station: name, latitude, longitude, seasonal status, municipality, total docks, and an older station ID that only matches pre-2023 trips. The first line of the file is a "Last Updated" note, which the notebook skips. 613 stations.

License: Bluebikes Data License Agreement, https://bluebikes.com/data-license-agreement.

### NOAA daily weather, Boston Logan.csv (included, 4.9 MB)

Daily Summaries from NOAA Climate Data Online, https://www.ncei.noaa.gov/cdo-web/ (GHCN-Daily), August 31, 2025 to October 12, 2026. The download contains many Massachusetts weather stations; the notebook keeps only Boston Logan Airport (`STATION == "USW00014739"`) and the study period September 1, 2025 to August 31, 2026. Columns used: `DATE`, `TMAX`, `TMIN` (degrees F), `PRCP`, `SNOW` (inches), `AWND` (mph). `TAVG` is empty for Logan and is not used.

License: U.S. Government work, public domain.

### gbfs-logs/ (included, 31 files, 123 MB)

Our own log of the live Bluebikes station status feed, collected by the script in `../logger/`. One CSV per calendar day (UTC date in the file name), `station_status_2026-09-17.csv` to `station_status_2026-10-17.csv`. One row per station per snapshot: `snapshot_utc`, `fetched_utc`, `station_id`, `legacy_id`, `num_bikes_available`, `num_ebikes_available`, `num_bikes_disabled`, `num_docks_available`, `num_docks_disabled`, `is_installed`, `is_renting`, `is_returning`, `last_reported`.

These 31 files are exactly the data behind the notebook's saved outputs: 1,542 snapshots from September 16, 2026 at 23:35 to October 17, 2026 at 19:52 Boston time, 620 to 627 stations per snapshot. The logger kept running after October 17, so the logger repository has newer files, but the notebook only reads files up to `station_status_2026-10-17.csv`. Readings are sparse before October 7 (GitHub ran the job only a few times a day); from October 7 there are 113 to 147 snapshots a day, and the hour-level analysis uses those 11 dense days.

The log records how many bikes and docks each station reported. It does not record van visits, failed rental attempts or individual riders.

Source feed: https://gbfs.bluebikes.com/gbfs/gbfs.json (station_status). License: Bluebikes Data License Agreement. The agreement allows the data to be used as source material in non-commercial analyses and reports, which is how it is used here; it does not allow redistributing the data as a stand-alone dataset or implying any endorsement by Bluebikes or Lyft.

## Files not in this folder

### bluebikes-trips/ (not included, about 1 GB)

Twelve monthly trip files, `202509-bluebikes-tripdata.csv` to `202608-bluebikes-tripdata.csv`. They are too large for GitHub (the largest month is 134 MB; GitHub rejects files over 100 MB).

To get them: open https://s3.amazonaws.com/hubway-data/index.html, download the zip files named `202509-bluebikes-tripdata.zip` through `202608-bluebikes-tripdata.zip`, unzip them, and put the twelve CSVs in `data/bluebikes-trips/`. Each CSV has the columns `ride_id`, `rideable_type`, `started_at`, `ended_at`, `start_station_name`, `start_station_id`, `end_station_name`, `end_station_id`, `start_lat`, `start_lng`, `end_lat`, `end_lng`, `member_casual`. About 4.6 million rows in total.

License: Bluebikes Data License Agreement.

### Station information (downloaded by the notebook)

Station names, short codes and dock capacity for the GBFS station IDs come from https://gbfs.bluebikes.com/gbfs/en/station_information.json. The notebook downloads this feed when it runs, so no copy is stored here. If the feed is unavailable, that cell fails with a network error; running the cell again usually works.
