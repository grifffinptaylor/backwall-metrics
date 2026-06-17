# Milestone 4: Court Calibration

## ✓ Completed

This milestone adds manual court calibration to transform video pixel coordinates to top-down court coordinates using homography transformation.

## Features Implemented

### 1. Court Module (`src/court.py`)

**CourtConfig Class:**
- Dimensions (width=100, length=100 abstract units)
- T position (50, 62)
- T-zone radius (10 units)
- Court corners coordinates

**Court Graphics Functions:**

- `get_default_court_config()` - Default court configuration
- `get_court_zones()` - 9-zone court layout definition
- `draw_court_graphic()` - Generate blank court image (800x800)
- `draw_path_on_court()` - Draw tracked path on court
- `assign_zone()` - Assign point to court zone (front/mid/back × left/center/right)

**Homography Transformation:**

- `compute_homography()` - Calculate perspective transform matrix
- `video_to_court_points()` - Transform array of points
- `video_to_court_point()` - Transform single point

**Calibration Utilities:**

- `calibration_preview()` - Show calibration points on frame

### 2. 9-Zone Court System

Court divided into 3×3 grid:

```
Back Wall
├─ back_left  │  back_center  │  back_right
├─────────────┼──────────────┼─────────────
├─ mid_left   │  mid_center   │  mid_right
├─────────────┼──────────────┼─────────────
├─ front_left │ front_center  │ front_right
Front Wall
```

Each zone has min_x, max_x, min_y, max_y boundaries.

### 3. Court Calibration UI

**5-Point Calibration Process:**

1. **Front-Left Corner** - (0, 0) on court
2. **Front-Right Corner** - (100, 0) on court
3. **Back-Left Corner** - (0, 100) on court
4. **Back-Right Corner** - (100, 100) on court
5. **T Position** - (50, 62) on court

**User Interaction:**
- Display first frame from tracking
- Click buttons 1-5 in order
- Each records pixel location from frame
- Preview shows all 5 points with labels
- Can reset and restart

**Status Tracking:**
- Shows number of points selected
- Shows required points (5)
- Shows completion status

### 4. Homography Transformation

**What It Does:**
- Maps video pixel space → court coordinate space
- Uses 5-point calibration (4 points for homography, 1 for validation)
- OpenCV `findHomography()` for robust calculation

**Math:**
```
Video Point (x, y) in pixels
       ↓
Homography Matrix (3×3)
       ↓
Court Point (x, y) in abstract units
```

**Implementation:**
- Handles both single points and arrays
- Homogeneous coordinate transformation
- Normalized output

### 5. Tracking Data Calibration

**Process:**
1. Take existing tracking_df (video_x, video_y)
2. Apply homography to matched frames only
3. Add new columns: court_x, court_y, zone
4. Gap frames get NaN for court coordinates
5. Zone assigned based on court_x, court_y

**Output DataFrame:**
```
frame_number | time_sec | video_x | video_y | confidence | matched | court_x | court_y | zone
0            | 0.0      | 640.5   | 360.2   | 0.95       | True    | 45.2    | 50.1    | mid_center
1            | 0.033    | 642.1   | 358.9   | 0.94       | True    | 46.1    | 51.2    | mid_center
3            | 0.1      | None    | None    | None       | False   | NaN     | NaN     | unknown
```

### 6. Court Visualization

**Empty Court Graphic:**
- 800×800 pixel image
- Black boundary rectangle
- Center line (light gray)
- T-zone circle with center point (red)
- 3×3 zone grid (very light gray)
- Labels ("Front Wall", "Back Wall")

**Path Overlay:**
- Green lines connecting tracked points
- Blue dot at start
- Red dot at end
- Point markers every 3 points
- Scaled to court coordinate space

### 7. Session State Calibration Storage

```python
st.session_state.calibration_points_video  # List of (x, y) from frame
st.session_state.calibration_points_court  # List of (x, y) on court
st.session_state.homography                # 3×3 matrix
st.session_state.calibrated_tracking_df    # DF with court_x, court_y, zone
st.session_state.court_config              # CourtConfig object
```

## How to Use

### Workflow

1. **Movement Analysis Tab**
   - Extract frames
   - Detect people
   - Select target
   - Run tracking
   - Download tracking data (optional)

2. **Court Calibration Tab**
   - See frame with tracked player
   - **Select 5 calibration points:**
     - Click "1️⃣ Front-Left" - appears as blue point
     - Click "2️⃣ Front-Right"
     - Click "3️⃣ Back-Left"
     - Click "4️⃣ Back-Right"
     - Click "5️⃣ T Position" - appears as magenta point
   - Preview shows all points with labels
   - Click "📐 Compute Calibration"
   - System calculates homography and transforms all tracking data

3. **Results**
   - Statistics (frames calibrated, unique zones, court range)
   - Calibrated tracking table
   - Court visualization with path overlay
   - Download calibrated data as CSV

### Example Session

```
① Start with tracking_df from M3 (video_x, video_y)
   ↓
② User clicks 5 points on court calibration tab
   ↓
③ System computes homography matrix
   ↓
④ Transforms all 285 tracked frames to court coords
   ↓
⑤ Assigns each frame to a zone
   ↓
⑥ Shows court graphic with player's path
   ↓
⑦ Ready for metrics calculation (M6)
```

## Technical Details

### Homography Matrix

3×3 transformation matrix from `cv2.findHomography()`:

```
[h00  h01  h02]
[h10  h11  h12]
[h20  h21  h22]
```

Applied as:
```
[x']   [h00  h01  h02] [x]
[y'] = [h10  h11  h12] [y]
[w']   [h20  h21  h22] [1]

x_court = x' / w'
y_court = y' / w'
```

### Zone Assignment Algorithm

```python
for each (court_x, court_y):
    for each zone in zones:
        if zone.min_x <= court_x <= zone.max_x AND
           zone.min_y <= court_y <= zone.max_y:
            return zone.name
    return "unknown"
```

### Court-to-Image Scaling

```python
image_x = (court_x / court_width) * image_width
image_y = (court_y / court_length) * image_height
```

## Code Changes

### `src/court.py` (New File)

**Classes:**
- `CourtConfig` - Court configuration dataclass

**Functions:**
- `get_default_court_config()`
- `get_court_zones()`
- `assign_zone(court_x, court_y, zones)`
- `compute_homography(video_points, court_points)`
- `video_to_court_points(video_points, homography)`
- `video_to_court_point(video_point, homography)` - Single point
- `draw_court_graphic(width, height, config)`
- `draw_path_on_court(court_img, path_points, config, color, thickness)`
- `calibration_preview(frame, video_calibration_points, court_config)`

### `app.py` - New Court Calibration Tab

**New Session State:**
```python
st.session_state.calibration_points_video    # Clicked points
st.session_state.calibration_points_court    # Court coordinates
st.session_state.homography                  # Transform matrix
st.session_state.calibrated_tracking_df      # Result with court_x, court_y, zone
st.session_state.court_config                # CourtConfig object
```

**New UI Elements:**
- Calibration point selection buttons (5)
- Status metrics (points selected, required, status)
- Calibration preview image
- Compute calibration button
- Reset calibration button
- Results dashboard
- Calibrated tracking table
- Court visualization with path
- CSV download button

## Data Flow

```
Video Frame
    ↓
[User clicks 5 points]
    ↓
Video Points: [(x1, y1), (x2, y2), (x3, y3), (x4, y4), (x5, y5)]
Court Points: [(0,0), (100,0), (0,100), (100,100), (50,62)]
    ↓
[Compute Homography]
    ↓
Homography Matrix (3×3)
    ↓
[Apply to Tracking DF]
    ↓
├─ Transform video_x, video_y → court_x, court_y
├─ Assign zones
└─ Keep matched/gap status
    ↓
Calibrated Tracking DF (8 columns)
    ↓
[Visualize on Court]
    ↓
Court Graphic with Path Overlay
```

## Example Output

**Calibrated DataFrame Sample:**
```
frame  time   video_x  video_y  conf  matched court_x court_y zone
0      0.000  640.5    360.2    0.95  True    45.2    50.1    mid_center
1      0.033  642.1    358.9    0.94  True    46.1    51.2    mid_center
2      0.067  645.2    355.1    0.93  True    48.5    52.8    mid_center
3      0.100  NaN      NaN      NaN   False   NaN     NaN     unknown
4      0.133  652.0    350.5    0.92  True    52.1    54.2    mid_right
5      0.167  658.3    345.8    0.91  True    55.8    56.5    back_center
```

**Statistics:**
- Frames calibrated: 285
- Gap frames: 15
- Unique zones: 7 (out of 9)
- Court range: 45.2 pixels

## Validation & Error Handling

**Checks:**
- ✓ Points must be selected in order
- ✓ Homography matrix must be valid (not None)
- ✓ Transformed points must be within court bounds or tracked
- ✓ Zone assignment handles unknown/out-of-bounds
- ✓ NaN values preserved for gap frames

**User Feedback:**
- Warnings if skipping steps
- Error messages on homography failure
- Success messages on completion
- Visual preview of calibration

## Next Steps (Milestone 5: Movement Heatmap)

The calibrated tracking data is ready for:

1. **Heatmap Generation**
   - Kernel density estimation on court_x, court_y
   - Visualize on court graphic
   - Show "hot zones" (red) and "cold zones" (blue)

2. **Movement Metrics (M6)**
   - Distance from T position
   - Time spent near T
   - Recovery times
   - Movement intensity
   - All calculated in court space

3. **Zone-Based Analysis**
   - Time spent in each zone
   - Zone transition patterns
   - Preferred zones

## Known Limitations

- **5-point calibration:** More points would improve accuracy (future)
- **Manual selection:** Future: auto-detect corners or interactive clicker
- **Static court:** Assumes stationary camera
- **Abstract coordinates:** Not real squash court dimensions (can scale later)
- **No perspective validation:** Doesn't check if homography is reasonable

## Troubleshooting

**Calibration produces weird results?**
- Verify all 5 points are selected
- Check court corners are aligned with actual court
- Try adjusting T position slightly

**Points appear in wrong locations?**
- Ensure clicking on correct court landmarks
- Check frame is showing good view of court

**Zone assignments incorrect?**
- Verify homography was computed (status should show "Complete")
- Check calibration points are accurate

## Files Modified

- **`src/court.py`** - NEW, full court module
- **`app.py`** - Added Court Calibration tab (Tab 3)

## Performance Notes

- Homography computed once, cached in session state
- Transformation applied to all tracked points efficiently
- Court graphic rendered on-demand (800×800 = ~2MB)
- Zone assignment vectorized where possible
