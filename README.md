# Smart HKU Transport Advisor
**COMP1110 Group D21 · Semester 2, 2025–2026**

A web-based route planning tool for navigating between HKU facilities using public transport and HKU Shuttle Buses. Built with Python and Streamlit, it generates and ranks candidate journeys across MTR, Citybus, Green Minibus, HKU Shuttle Bus, and Walking segments based on your chosen preference.

---

## Table of Contents

1. [Requirements](#requirements)
2. [How to Run](#how-to-run)
   - [Standard Method](#standard-method)
   - [Alternative Method (if standard fails)](#alternative-method-if-standard-fails)
3. [Features](#features)
4. [How to Use the App](#how-to-use-the-app)
5. [File Structure](#file-structure)
6. [Data File Formats](#data-file-formats)
7. [How the System Works](#how-the-system-works)
8. [Testing](#testing)
9. [Network Overview](#network-overview)
10. [Data Assumptions](#data-assumptions)

---

## Requirements

- **Python 3.9 or higher**
- **pip** (Python package manager)
- An internet connection for the first install (to download dependencies)

---

## How to Run

### Standard Method

**Step 1 — Clone the repository**

```bash
git clone https://github.com/kooki1000/COMP1110-Group-D21-Project.git
cd COMP1110-Group-D21-Project
```

**Step 2 — Install dependencies**

```bash
pip install -r requirements.txt
```

**Step 3 — Launch the app**

```bash
streamlit run app.py
```

The app will open automatically in your default browser at:

```
http://localhost:8501
```

If it does not open automatically, copy and paste that URL into your browser manually.

---

### Alternative Method (if standard fails)

On some Windows machines, the `streamlit` command may not be recognised in the terminal even after installation. This can happen if Python's `Scripts` folder is not on your system PATH. In that case, run the app by calling Streamlit as a Python module instead.

**Use this command (replace the Python path with yours if different):**

```bash
"C:\Users\YourUsername\AppData\Local\Programs\Python\Python311\python.exe" -m streamlit run app.py
```

> **Why this happens:** Windows Store versions of Python are sometimes installed in a non-standard location that is not automatically added to PATH. Running via `python.exe -m streamlit` bypasses this by using the Python executable directly to launch Streamlit as a module, which always works regardless of PATH settings.

**How to find your own Python path (if the path above does not match your machine):**

```bash
where python
```

or

```bash
py -3 -c "import sys; print(sys.executable)"
```

Then replace the path in the command above with whatever is printed.

---

## Features

- **Interactive map** showing all 21 HKU stops with real GPS coordinates, with each segment colour-coded by transport mode (MTR, HKU Shuttle Bus, Citybus, Green Minibus, Walking)
- **Three preference modes**: Fastest, Cheapest, Fewest Segments
- **Top 5 routes** ranked and displayed with full segment breakdown (stop sequence, mode, duration, cost, number of segments)
- **Transport modes**: MTR, Citybus, Green Minibus, HKU Shuttle Bus, Walking
- **Route visualisation**: selected route drawn on the map as a coloured polyline connecting stops in order
- **Network summary**: total stops, total segments, and segment count per transport mode
- **Input validation**: clear error messages for invalid stop names, same origin/destination, or no route found

---

## How to Use the App

1. **Launch** the app using one of the run methods above.
2. **View the map** — all 21 HKU stops will appear as markers.
3. **Select Origin** — choose your starting stop from the dropdown menu.
4. **Select Destination** — choose your target stop.
5. **Choose Preference** — select Fastest, Cheapest, or Fewest Segments.
6. **Click "Find Routes"** — the app will generate and rank candidate journeys.
7. **View results** — the top 5 routes are shown in a ranked table with full breakdowns.
8. **Select a route on the map** — click a result to highlight that route on the map.

---

## File Structure

```
├── app.py                        # Main Streamlit web application and UI logic
├── network_loader.py             # Reads stops/segments CSVs and builds the adjacency graph
├── journey_finder.py             # Depth-limited DFS path-finding algorithm
├── scorer.py                     # Scores candidate journeys and ranks by preference mode
├── validator.py                  # Input validation (stop names, preference mode, same stop)
├── requirements.txt              # All Python dependencies
├── data/
│   ├── stops.csv                 # 21 HKU stops with GPS coordinates and campus location
│   └── segments.csv              # 66 directed transport segments with mode, duration, cost
├── test_cases/
│   ├── tester.py                 # Test runner — run with: python test_cases/tester.py
│   ├── route_test_cases.csv      # 5 valid journey queries with expected ranked results
│   ├── invalid_query_test_cases.csv  # 6 invalid queries with expected error messages
│   └── sample_test_output.txt   # Expected console output for a successful test run
└── README.md                     # This file
```

### What each file does

**`app.py`** — The entry point. Renders the Streamlit interface, handles the map display using Folium or Pydeck, calls the other modules when the user submits a query, and displays ranked results.

**`network_loader.py`** — Reads `stops.csv` and `segments.csv` from the `data/` folder, validates the data, and builds an in-memory adjacency dictionary (graph) where each stop maps to a list of outgoing segments. This graph is what the path-finder operates on.

**`journey_finder.py`** — Implements a depth-limited depth-first search (DFS). Starting from the origin, it recursively explores adjacent stops, avoids revisiting stops already in the current path, and collects complete paths once the destination is reached. The default depth limit is **8 segments**.

**`scorer.py`** — Takes a list of candidate paths from the journey finder, computes total duration, total cost, and number of segments for each, then sorts them by the user's chosen preference mode. Returns the top 5 results.

**`validator.py`** — Checks that the origin and destination stops exist in the loaded network, that they are not the same stop, and that the preference mode is one of the three valid options. Returns clear error messages if any check fails.

---

## Data File Formats

Both data files live in the `data/` folder and are loaded automatically when the app starts.

### `data/stops.csv`

Each row is one named stop in the network.

| Column | Type | Description |
|--------|------|-------------|
| `stop_id` | String | Unique identifier, e.g. `S001` |
| `stop_name` | String | Display name, e.g. `HKU Main Campus` |
| `campus_location` | String | Campus area, e.g. `Main/Centennial Campus` |
| `remark` | String | Available transport modes at that stop |
| `lat` | Float | GPS latitude (optional — stops without coordinates load but show no map marker) |
| `lng` | Float | GPS longitude (optional) |

Example rows:
```
stop_id,stop_name,campus_location,remark,lat,lng
S001,HKU Main Campus,Main/Centennial Campus,HKU Shuttle Bus; Citybus; Green Minibus; MTR (short walk),22.283314,114.138142
S002,HKU Medical Campus,Sassoon Road Campus,HKU Shuttle Bus; Citybus; Green Minibus,22.267418,114.128559
```

### `data/segments.csv`

Each row is one directed travel segment between two stops.

| Column | Type | Description |
|--------|------|-------------|
| `segment_id` | String | Unique identifier, e.g. `SEG001` |
| `from_stop_id` | String | Origin stop ID |
| `from_stop_name` | String | Origin stop display name |
| `to_stop_id` | String | Destination stop ID |
| `to_stop_name` | String | Destination stop display name |
| `mode` | String | Transport mode: `MTR`, `Citybus`, `Green Minibus`, `HKU Shuttle Bus`, or `Walking` |
| `duration` | Integer | Travel time in minutes |
| `cost` | Integer | Fare in HKD (0 for walking) |
| `route_name` | String | Descriptive name of the route or service |

Example rows:
```
segment_id,from_stop_id,from_stop_name,to_stop_id,to_stop_name,mode,duration,cost,route_name
SEG001,S005,HKU MTR Station,S001,HKU Main Campus,Walking,3,0,Short walk to campus
SEG003,S001,HKU Main Campus,S002,HKU Medical Campus,HKU Shuttle Bus,15,2,HKU Shuttle Route A
```

> **Note:** Segments are **directed**. A segment from A to B does not automatically mean a return segment from B to A exists — both directions must appear separately in the file if applicable.

---

## How the System Works

The system follows this pipeline for every journey query:

```
1. Load network (stops.csv + segments.csv)
        ↓
2. Build adjacency graph
   { stop_name: [ {to, mode, duration, cost, route_name}, ... ] }
        ↓
3. Validate user inputs (origin, destination, preference)
        ↓
4. Run depth-limited DFS from origin
   - Explore adjacent stops recursively
   - Track visited stops to avoid loops
   - Stop if path length exceeds 8 segments
   - Save path when destination is reached
        ↓
5. Score each candidate path
   - total_duration = sum of segment durations
   - total_cost     = sum of segment costs
   - num_segments   = length of segment list
        ↓
6. Rank by preference mode
   - Fastest:           sort by (duration, cost, segments)
   - Cheapest:          sort by (cost, duration, segments)
   - Fewest Segments:   sort by (segments, duration, cost)
        ↓
7. Display top 5 results + draw on map
```

---

## Testing

The project includes a standard-library test runner. No extra testing framework is required.

Run from the project root:

```bash
python test_cases/tester.py
```
The tests cover:

- network size and data consistency
- reachability between stop pairs within the depth limit
- report-based route scenarios
- expected top-ranked route outputs
- invalid query handling

Expected successful ending:

```text
All test cases passed.
```

The full expected output is also saved in `test_cases/sample_test_output.txt`.

### Test files

**`tester.py`** — Runs three groups of checks in sequence: data integrity, route tests, and invalid query tests. Uses only the Python standard library.

**`route_test_cases.csv`** — 5 valid journey queries against the real network, each specifying an origin, destination, preference, and the exact expected top-ranked result (duration, cost, segment count, and stop sequence).

| Test | Scenario | Origin | Destination | Preference |
|------|----------|--------|-------------|------------|
| TC1 | Budget route | JC Student Village III | HKU Main Campus | cheapest |
| TC2 | Fastest route | HKU Medical Campus | HKU Main Campus | fastest |
| TC3 | Fewest segments | JC Student Village IV | HKU Main Campus | fewest_segments |
| TC4 | Fastest comparison | JC Student Village IV | HKU Main Campus | fastest |
| TC5 | Hub transfer | Morrison Hall | Lady Ho Tung Hall | fastest |

**`invalid_query_test_cases.csv`** — 6 invalid queries that must each be rejected by `validate_query`, each specifying the substring expected to appear in the error message.

| Test | Scenario | Expected error contains |
|------|----------|------------------------|
| V1 | Missing origin | `origin` |
| V2 | Missing destination | `destination` |
| V3 | Unknown origin ID | `not found` |
| V4 | Unknown destination ID | `not found` |
| V5 | Same origin and destination | `same` |
| V6 | Invalid preference string | `valid preference` |

---

## Network Overview

| Stat | Value |
|------|-------|
| Total stops | 21 |
| Total segments | 66 |
| Transport modes | MTR, Citybus, Green Minibus, HKU Shuttle Bus, Walking |
| Coverage | HKU Main Campus, Medical Campus, student halls, MTR stations, public bus interchanges |

Data sourced from published HKU Shuttle Bus timetables, MTR fare tables, and Citybus/Green Minibus route information at the time of collection.

---

## Data Assumptions

- All fares and durations are **static** based on published schedules at the time of data collection. Real-time arrival information is not included.
- HKU Shuttle Bus fares reflect the **subsidised HK$2 student fare**.
- **Walking segments have zero cost.**
- Routes are generated using depth-limited DFS with a maximum of **8 segments**. Mathematically optimal routes are not guaranteed — the system produces reasonable candidate journeys.
- Segments are **directional**: not all routes operate in both directions.
- No service hours or holiday schedules are modelled — all segments are treated as always available.
- No capacity limits or crowding are modelled.
- Cross-boundary transport (e.g., to Shenzhen) is not included.
