# Milestone 2: Person Detection

## ✓ Completed

This milestone adds YOLO-based person detection to identify people in extracted video frames and visualize them with bounding boxes and confidence scores.

## Features Implemented

### 1. Enhanced Person Detection (`src/tracker.py`)

**New Functions:**

- `detect_people_in_frames(model, frame_paths, confidence, sample_every_n)` 
  - Batch detection across multiple frames
  - Configurable sampling to speed up processing
  - Returns detection results indexed by frame path

- `draw_detections_on_frame(image_path, detections, output_path, thickness, color)`
  - Draws bounding boxes on detected people
  - Labels each detection with confidence score
  - Marks center point of each detection
  - Optional save to disk

**Enhanced `detect_people()` function:**
  - Now returns bounding box width and height
  - More robust error handling

### 2. Detection UI in Movement Analysis Tab

**New Controls:**

- **Confidence Threshold Slider** (0.1 - 1.0)
  - Lower = more detections (including false positives)
  - Higher = fewer but more confident detections
  - Default: 0.5

- **Sample Every N Frames Slider** (1 - 10)
  - Process every Nth frame for speed
  - Lower = more thorough but slower
  - Higher = faster but less comprehensive
  - Default: 3 (every 3rd frame)

- **Run Person Detection Button**
  - Loads YOLO model (cached in session state)
  - Runs batch detection on extracted frames
  - Shows progress spinner

### 3. Detection Results Display

**Summary Statistics:**
- Frames with detections
- Total people detected
- Average people per frame

**Annotated Frame Samples:**
- Shows first 5 frames with detections
- Displays bounding boxes in green
- Shows confidence scores
- Marks center point of each person
- Person count displayed per frame

**Full Frame Gallery:**
- Always visible below detection results
- Shows all extracted frames
- Easy reference to original frames

## How to Use

### Step 1: Extract Frames
1. Go to **Upload Video** tab
2. Upload a squash video
3. Select time range
4. Click **Extract Frames**

### Step 2: Run Person Detection
1. Go to **Movement Analysis** tab
2. Adjust confidence threshold if needed (default: 0.5)
3. Adjust frame sampling if needed (default: every 3rd frame)
4. Click **🔍 Run Person Detection**
5. Wait for model to load and process frames

### Step 3: View Results
- See summary stats (frames with people, total detections, etc.)
- View annotated sample frames with bounding boxes
- View full frame gallery below

## Code Changes

### `src/tracker.py`
- Added `draw_detections_on_frame()` function
- Added `detect_people_in_frames()` function
- Enhanced `detect_people()` with width/height calculations
- Improved documentation

### `app.py`
- Added model and detections to session state
- Expanded Movement Analysis tab with detection UI
- Added confidence threshold and frame sampling controls
- Added detection results display with statistics
- Added annotated frame visualization

## Technical Details

### YOLO Model
- Uses YOLOv8 Nano (`yolov8n.pt`)
- Detects COCO class 0 (person)
- Configurable confidence threshold
- Bounding box format: (x1, y1, x2, y2) in pixel coordinates

### Detection Output Format
Each detection dictionary contains:
```python
{
    "x1": float,          # Top-left x
    "y1": float,          # Top-left y
    "x2": float,          # Bottom-right x
    "y2": float,          # Bottom-right y
    "conf": float,        # Confidence score (0.0-1.0)
    "center_x": float,    # Center x coordinate
    "center_y": float,    # Center y coordinate
    "width": float,       # Bounding box width
    "height": float       # Bounding box height
}
```

### Performance Considerations
- YOLO model is cached in session state (loaded once)
- Frame sampling reduces computation time
- Batch detection is efficient
- Annotated frames are generated on-demand only for display

## Example Workflow

1. Upload a 30-second squash video
2. Extract frames from 5-15 seconds (10 seconds, ~300 frames at 30 FPS)
3. With `sample_every_n=3`, detect on 100 frames
4. View results showing number of people per frame
5. See annotated samples with bounding boxes

## Next Steps (Milestone 3: Target Player Tracking)

- Manual player selection from detected people
- Tracking the selected player across consecutive frames
- Simple nearest-neighbor matching between frames
- Store tracking data in a DataFrame
- Calculate movement paths

## Known Limitations

- Detection runs on CPU by default (YOLO supports GPU if available)
- Confidence threshold may need tuning for your specific court/lighting
- Performance depends on frame resolution and total frame count
- No filtering for squash court boundaries yet

## Troubleshooting

**No people detected?**
- Try lowering the confidence threshold
- Check that your video is clear and well-lit
- Ensure people are clearly visible in frames

**Detection is very slow?**
- Increase `sample_every_n` value (e.g., 5 or 10)
- Reduce number of extracted frames
- Consider lower resolution video input

**False positives (false people)?**
- Increase confidence threshold (e.g., 0.7 or 0.8)
- Check for shadows or other objects being detected

## Files Modified

- `src/tracker.py` - Person detection visualization functions
- `app.py` - Movement Analysis tab with detection UI
