from ultralytics import YOLO


def load_model():
    return YOLO("yolov8n.pt")


def detect_people(model, image_path, confidence=0.3):
    """
    Detect people in one image.

    Returns a list of bounding boxes:
    [
      {
        "x1": ...,
        "y1": ...,
        "x2": ...,
        "y2": ...,
        "conf": ...
      }
    ]
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

            people.append({
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "conf": conf,
                "center_x": (x1 + x2) / 2,
                "center_y": (y1 + y2) / 2
            })

    return people