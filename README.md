# BackWall Metrics

A squash video analytics and scouting web app that lets you upload squash match or practice footage, select a specific player, and generate useful movement and scouting insights.

## Features

### Movement Analysis
- Track a selected player throughout a rally, point, game, or match
- Map player movement from video coordinates onto a top-down squash court graphic
- Generate a court heatmap showing where the player spent the most time
- Calculate squash-specific metrics:
  - Recovery-to-T time
  - Time spent near the T
  - Average distance from the T
  - Movement intensity

### Shot Scouting
- Scout yourself or an opponent
- Manually tag shot events during a match
- For each shot, record:
  - Who hit it
  - Where it was hit from
  - Where it went
  - Shot type
  - Outcome
- Generate scouting reports showing:
  - Shot tendencies
  - Common patterns
  - Origin-destination heatmaps
  - Shot type and outcome frequencies

## Quick Start

### Installation

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd backwall-metrics
   ```

2. Create a Python virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## Current Development Status

**Current Milestone: Milestone 1 (App Skeleton)**

### Completed (Milestone 1)
- ✓ Streamlit app structure with 4 tabs
- ✓ Video upload and preview
- ✓ Video metadata extraction
- ✓ Time range selection for rally/point isolation
- ✓ Frame extraction with configurable sampling
- ✓ First frame preview

### In Progress / Upcoming
- Milestone 2: Person Detection (YOLO)
- Milestone 3: Target Player Tracking
- Milestone 4: Court Calibration
- Milestone 5: Movement Heatmap
- Milestone 6: T-Recovery Metrics
- Milestone 7: Manual Shot Scouting
- Milestone 8: Scouting Report Generation
- Milestone 9: Polish and Documentation

See [MILESTONE1.md](MILESTONE1.md) for detailed information about the current milestone.

## Project Structure

```
backwall-metrics/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                 # This file
│
├── src/
│   ├── video.py              # Video loading, frame extraction
│   ├── tracker.py            # YOLO person detection and tracking
│   ├── court.py              # Court graphics and calibration
│   ├── heatmap.py            # Heatmap generation
│   ├── metrics.py            # Movement metrics calculation
│   ├── scouting.py           # Shot tagging and scouting stats
│   └── report.py             # Report generation
│
├── data/
│   ├── raw/                  # Raw uploaded videos
│   ├── processed/            # Processed data
│   └── tags/                 # Shot tag CSVs
│
└── outputs/
    ├── heatmaps/             # Generated heatmap images
    └── reports/              # Generated reports
```

## Tech Stack

- **Python 3.8+**
- **Streamlit** - Web app framework
- **OpenCV** - Video processing
- **NumPy** - Numerical computation
- **Pandas** - Data analysis
- **Matplotlib/Plotly** - Visualization
- **Ultralytics YOLO** - Person detection
- **MediaPipe** (optional future) - Pose estimation

## Design Principles

This project follows a **manual-first, automation-later** approach:

### MVP (Manual-First)
- Manual rally selection
- Manual player selection
- Manual court calibration
- Manual shot tagging

### Future (Automation)
- Automatic rally detection
- Automatic court calibration
- Automatic shot event detection
- Automatic shot type classification
- ML-powered opponent scouting

## Target Users

- Squash players reviewing their own footage
- Coaches analyzing player movement
- Teammates scouting opponents

## Contributing

This is an active development project. Contributions welcome!

## License

[License info here]

## Contact

[Contact info here]
