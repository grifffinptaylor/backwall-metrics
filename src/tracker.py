import cv2
import numpy as np
import pandas as pd
from ultralytics import YOLO
from pathlib import Path


def load_model():
    """Load the YOLOv8 nano model for person detection."""
    return YOLO("yolov8n.pt")


def detect_people(model, image_path, confidence=0.3):
    """
    Detect people in one image.

    Args:
        model: Loaded YOLO model
        image_path: Path to image file (string or Path)
        confidence: Confidence threshold (0.0-1.0)

    Returns:
        List of detection dictionaries with keys:
        - x1, y1, x2, y2: Bounding box coordinates
        - conf: Confidence score
        - center_x, center_y: Center of bounding box
        - width, height: Bounding box dimensions
    """
    results = model(str(image_path), conf=confidence)

    people = []

    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])

            # COCO class 0 = person
            if cls != 0:
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            
            width = x2 - x1
            height = y2 - y1

            people.append({
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "conf": conf,
                "center_x": (x1 + x2) / 2,
                "center_y": (y1 + y2) / 2,
                "width": width,
                "height": height
            })

    return people


def draw_detections_on_frame(image_path, detections, output_path=None, thickness=2, color=(0, 255, 0), highlighted_idx=None):
    """
    Draw bounding boxes on a frame for detected people.

    Args:
        image_path: Path to input image
        detections: List of detection dictionaries from detect_people()
        output_path: Path to save annotated image (optional)
        thickness: Bounding box line thickness
        color: Bounding box color as (B, G, R) tuple
        highlighted_idx: Index of detection to highlight (for target selection)

    Returns:
        Annotated image as numpy array
    """
    frame = cv2.imread(str(image_path))
    
    if frame is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    # Draw bounding boxes
    for i, det in enumerate(detections):
        x1, y1, x2, y2 = int(det["x1"]), int(det["y1"]), int(det["x2"]), int(det["y2"])
        conf = det["conf"]
        
        # Highlight selected target in different color
        box_color = (255, 0, 0) if i == highlighted_idx else color  # Blue for target, green otherwise
        
        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, thickness + 1 if i == highlighted_idx else thickness)
        
        # Draw confidence score
        label = f"Person {i+1}: {conf:.2f}"
        if i == highlighted_idx:
            label += " [TARGET]"
        
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
        label_bg_y = max(y1 - 25, 0)
        
        cv2.rectangle(
            frame,
            (x1, label_bg_y),
            (x1 + label_size[0] + 10, label_bg_y + label_size[1] + 5),
            box_color,
            -1
        )
        cv2.putText(
            frame,
            label,
            (x1 + 5, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1
        )
        
        # Draw center point
        center_x, center_y = int(det["center_x"]), int(det["center_y"])
        cv2.circle(frame, (center_x, center_y), 4, box_color, -1)
    
    # Save if output path provided
    if output_path:
        cv2.imwrite(str(output_path), frame)
    
    return frame


def detect_people_in_frames(model, frame_paths, confidence=0.3, sample_every_n=1):
    """
    Run detection on multiple frames.

    Args:
        model: Loaded YOLO model
        frame_paths: List of paths to frames
        confidence: Confidence threshold
        sample_every_n: Process every nth frame (for speed)

    Returns:
        Dictionary mapping frame_path to list of detections
    """
    results = {}
    
    for i, frame_path in enumerate(frame_paths):
        if i % sample_every_n != 0:
            continue
        
        detections = detect_people(model, frame_path, confidence=confidence)
        results[str(frame_path)] = detections
    
    return results


def euclidean_distance(p1, p2):
    """Calculate Euclidean distance between two points."""
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def track_target_player(model, frame_paths, initial_target_point, fps=30.0, confidence=0.5, max_distance=100):
    """
    Track a target player across frames using nearest-neighbor matching.

    Args:
        model: Loaded YOLO model
        frame_paths: List of paths to video frames (in order)
        initial_target_point: Tuple (x, y) of target player's initial position
        fps: Frames per second (for time_sec calculation)
        confidence: Confidence threshold for detection
        max_distance: Maximum distance to match detections (pixels)

    Returns:
        DataFrame with columns:
        - frame_number: Frame index
        - time_sec: Time in seconds
        - video_x, video_y: Pixel coordinates
        - confidence: Detection confidence
        - matched: Boolean (True if matched, False if gap)
    """
    tracking_data = []
    last_position = initial_target_point
    frame_paths = list(frame_paths)
    
    for frame_idx, frame_path in enumerate(frame_paths):
        time_sec = frame_idx / fps
        
        # Detect people in this frame
        detections = detect_people(model, frame_path, confidence=confidence)
        
        if len(detections) == 0:
            # No detections - mark as gap
            tracking_data.append({
                "frame_number": frame_idx,
                "time_sec": time_sec,
                "video_x": None,
                "video_y": None,
                "confidence": None,
                "matched": False
            })
            continue
        
        # Find closest detection to last known position
        min_distance = float('inf')
        closest_detection = None
        
        for det in detections:
            det_pos = (det["center_x"], det["center_y"])
            dist = euclidean_distance(last_position, det_pos)
            
            if dist < min_distance:
                min_distance = dist
                closest_detection = det
        
        # Check if closest detection is within max_distance threshold
        if closest_detection and min_distance <= max_distance:
            # Found a match
            tracking_data.append({
                "frame_number": frame_idx,
                "time_sec": time_sec,
                "video_x": closest_detection["center_x"],
                "video_y": closest_detection["center_y"],
                "confidence": closest_detection["conf"],
                "matched": True
            })
            last_position = (closest_detection["center_x"], closest_detection["center_y"])
        else:
            # No match within threshold - mark as gap
            tracking_data.append({
                "frame_number": frame_idx,
                "time_sec": time_sec,
                "video_x": None,
                "video_y": None,
                "confidence": None,
                "matched": False
            })
    
    df = pd.DataFrame(tracking_data)
    return df


def draw_tracking_path(image_path, tracking_df, output_path=None, color=(255, 0, 255), thickness=2):
    """
    Draw the tracking path on a frame.

    Args:
        image_path: Path to frame image
        tracking_df: Tracking DataFrame from track_target_player()
        output_path: Path to save annotated image (optional)
        color: Path color as (B, G, R) tuple
        thickness: Line thickness

    Returns:
        Annotated image as numpy array
    """
    frame = cv2.imread(str(image_path))
    
    if frame is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    # Get valid tracked points (where matched=True)
    valid_points = tracking_df[tracking_df["matched"] == True][["video_x", "video_y"]].values
    
    if len(valid_points) < 2:
        return frame
    
    # Draw lines connecting tracked points
    points = [(int(x), int(y)) for x, y in valid_points]
    
    for i in range(len(points) - 1):
        cv2.line(frame, points[i], points[i + 1], color, thickness)
    
    # Draw circles at each point
    for i, point in enumerate(points):
        # Brighter for earlier, dimmer for later (optional visual effect)
        cv2.circle(frame, point, 4, color, -1)
        if i % 5 == 0:  # Label every 5th point to avoid clutter
            cv2.putText(frame, str(i), (point[0] + 5, point[1] - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    
    # Save if output path provided
    if output_path:
        cv2.imwrite(str(output_path), frame)
    
    return frame