# Milestone 3: Target Player Tracking

## ✓ Completed

This milestone adds player tracking capability to follow a selected player across all video frames using simple nearest-neighbor matching.

## Features Implemented

### 1. Target Player Selection UI

**Interactive Selection:**
- Display first frame with all detected people
- Show bounding boxes with confidence scores
- Click buttons to select which person to track
- Selected person highlighted in blue
- Target point stored in session state

**Visual Feedback:**
- Selected person highlighted differently from others
- Confidence scores displayed for each person
- "TARGET" label added to selected person

### 2. Nearest-Neighbor Tracking Algorithm

**Core Algorithm:**
- For each frame, detect all people
- Find the detected person closest to the target's last known position
- If closest match is within `max_distance` threshold: track as matched
- If no match within threshold: mark as gap frame (but still record None values)
- Store time in seconds based on FPS

**Tracking Functions in `src/tracker.py`:**

- `euclidean_distance(p1, p2)` - Calculate distance between two points
- `track_target_player()` - Main tracking function
- `draw_tracking_path()` - Visualize tracking path on frame

### 3. Tracking DataFrame Output

**DataFrame Structure:**
```
frame_number    | int      | Frame index (0, 1, 2, ...)
time_sec        | float    | Time in seconds from start
video_x         | float    | X pixel coordinate (None if gap)
video_y         | float    | Y pixel coordinate (None if gap)
confidence      | float    | Detection confidence (None if gap)
matched         | bool     | True if person found, False if gap
```

**Features:**
- Records all frames (including gaps)
- Gap frames marked with `matched=False`
- None values for video coordinates in gaps
- Ready for downstream analysis and court mapping

### 4. Tracking Results Visualization

**Statistics Dashboard:**
- Frames tracked (matched frames only)
- Average confidence score
- Number of gap frames
- Movement range (max X and Y spread in pixels)

**Tracking Path Visualization:**
- Magenta line connecting tracked positions
- Circles at each tracked point
- Frame numbers every 5 points (to avoid clutter)
- Overlaid on first frame for reference

**Data Export:**
- Download tracking data as CSV
- Includes all columns (frame_number, time_sec, video_x, video_y, confidence, matched)
- Ready for court calibration and metrics calculation

### 5. Enhanced Detection Visualization

**Highlighted Target Display:**
- `draw_detections_on_frame()` now supports `highlighted_idx` parameter
- Target person shown in blue, others in green
- Thicker bounding box for target
- "[TARGET]" label added

## How to Use

### Workflow

1. **Upload Video Tab** 
   - Upload squash video
   - Extract frames from desired time range
   - Select frame extraction rate

2. **Movement Analysis Tab**
   - **Run Person Detection**
     - Adjust confidence threshold (default 0.5)
     - Adjust frame sampling (default every 3rd)
     - Click "🔍 Run Person Detection"
   
   - **Select Target Player**
     - View frame with all detected people
     - Click button for person you want to track
     - See selected person highlighted in blue
   
   - **Configure Tracking**
     - Adjust max tracking distance (default 100px)
     - Set FPS for time calculation (default 30)
   
   - **Run Tracking**
     - Click "▶️ Start Tracking"
     - Wait for tracking to complete
   
   - **View Results**
     - See tracking statistics
     - View tracking path visualization
     - View first 20 rows of tracking data
     - Download full CSV

### Example Configuration

**For High-Speed Movement:**
- Max distance: 150-200px (more lenient)
- FPS: 60 (for accurate timing)

**For Slow Movement:**
- Max distance: 50-100px (stricter)
- FPS: 24-30 (typical video)

**For Difficult Lighting:**
- Lower detection confidence (0.3-0.4)
- Higher max distance (200px)
- More lenient matching

## Technical Details

### Nearest-Neighbor Matching

```python
for each frame:
    detections = detect_people(frame)
    
    if len(detections) == 0:
        mark as gap
        continue
    
    for each detected person:
        distance = euclidean_distance(detection_pos, last_position)
    
    if min_distance <= max_distance:
        track this person
        update last_position
    else:
        mark as gap
```

### Gap Frame Handling

- Frames with no detections: marked as `matched=False`
- Frames where no one is within `max_distance`: marked as `matched=False`
- Video coordinates set to `None` for gap frames
- Confidence set to `None` for gap frames
- Downstream analysis can filter gaps as needed

### Performance Considerations

- YOLO model cached in session state
- Tracking runs on all frames (no sampling)
- Distance calculations vectorized where possible
- Path visualization rendered on-demand

## Code Changes

### `src/tracker.py` - New Functions

```python
euclidean_distance(p1, p2)
    → Calculate distance between two points

track_target_player(model, frame_paths, initial_target_point, fps, confidence, max_distance)
    → Main tracking function
    → Returns DataFrame with tracking data

draw_tracking_path(image_path, tracking_df, output_path, color, thickness)
    → Draw path visualization on frame
    → Connects matched points with line
```

### `src/tracker.py` - Enhanced Functions

```python
draw_detections_on_frame(..., highlighted_idx=None)
    → Added optional highlighting for target person
    → Target shown in blue, others in green
    → Thicker box and "[TARGET]" label for selected person
```

### `app.py` - Movement Analysis Tab

**New Session State:**
- `target_point` - (x, y) of selected target
- `target_person_idx` - Index of selected person
- `tracking_df` - DataFrame from tracking

**New UI Elements:**
- Target selection buttons
- Max tracking distance slider
- FPS input
- Start Tracking button
- Tracking results dashboard
- Tracking path visualization
- Tracking data table
- CSV download button

## Data Flow

```
Video Upload
    ↓
Frame Extraction
    ↓
Person Detection (YOLO)
    ↓
Target Selection (Click)
    ↓
Tracking Algorithm (Nearest-Neighbor)
    ↓
Tracking DataFrame
    ↓
├─ Visualization (Path overlay)
├─ Statistics (Confidence, distance, etc.)
├─ CSV Export
└─ Ready for Court Calibration (M4)
```

## Next Steps (Milestone 4: Court Calibration)

Will add:
- Manual court landmark selection (front, back, sides, T position)
- Homography matrix calculation
- Mapping video coordinates to court coordinates
- Court zone assignment
- Visualization of player movement on court graphic

**Data from M3 that M4 will use:**
- Tracking DataFrame with video_x, video_y
- FPS information
- Frame count
- Matched/gap information

## Known Limitations

- **Simple matching:** No motion prediction, just nearest-neighbor
- **Lost targets:** Once target is lost (gap > max_distance), can't re-acquire
- **Occlusion:** If target hidden by another person, will likely lose track
- **Camera motion:** Assumes stationary camera (or moves predictably)
- **Multiple people:** Can't distinguish if same person reappears after gap

## Troubleshooting

### Target keeps getting lost

**Solution:**
- Decrease max_distance to be more selective
- Lower detection confidence threshold
- Check video quality and lighting

### Tracking shows too many gaps

**Solution:**
- Increase max_distance threshold
- Ensure detection confidence is low enough (0.3-0.4)
- Check camera movement isn't too erratic

### Tracking looks jerky/unrealistic

**Solution:**
- This is normal with simple nearest-neighbor
- Consider smoothing tracking data in future milestone
- May want to add motion prediction for M4+

## Files Modified

- **`src/tracker.py`** - Added tracking functions and enhanced visualization
- **`app.py`** - Expanded Movement Analysis tab with selection, tracking, and results UI
- **`src/ui.py`** - Created for future UI utilities (currently minimal)

## Session State Architecture

```python
st.session_state.video_path      # Path to uploaded video
st.session_state.frames          # List of extracted frame paths
st.session_state.model           # Cached YOLO model
st.session_state.detections      # Dict of detections by frame
st.session_state.target_point    # (x, y) of selected target
st.session_state.target_person_idx # Index of selected person
st.session_state.tracking_df     # Tracking results DataFrame
```

## Example Output

After tracking, you'll get a CSV like:

```
frame_number,time_sec,video_x,video_y,confidence,matched
0,0.0,640.5,360.2,0.95,True
1,0.033,642.1,358.9,0.94,True
2,0.067,645.2,355.1,0.93,True
3,0.1,,,False
4,0.133,652.0,350.5,0.92,True
...
```

This is ready for:
- Court coordinate mapping (M4)
- Distance calculations from T (M6)
- Heatmap generation (M5)
- Movement metrics (M6)
