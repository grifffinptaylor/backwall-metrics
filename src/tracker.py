import cv2
import numpy as np
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


def draw_detections_on_frame(image_path, detections, output_path=None, thickness=2, color=(0, 255, 0)):
    """
    Draw bounding boxes on a frame for detected people.

    Args:
        image_path: Path to input image
        detections: List of detection dictionaries from detect_people()
        output_path: Path to save annotated image (optional)
        thickness: Bounding box line thickness
        color: Bounding box color as (B, G, R) tuple

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
        
        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
        
        # Draw confidence score
        label = f"Person {i+1}: {conf:.2f}"
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
        label_bg_y = max(y1 - 25, 0)
        
        cv2.rectangle(
            frame,
            (x1, label_bg_y),
            (x1 + label_size[0] + 10, label_bg_y + label_size[1] + 5),
            color,
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
        cv2.circle(frame, (center_x, center_y), 4, color, -1)
    
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