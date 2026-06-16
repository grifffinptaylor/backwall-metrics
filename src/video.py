import cv2
from pathlib import Path


def extract_frames(video_path, output_dir, every_n_frames=10):
    """
    Extract frames from a video.

    Args:
        video_path: Path to input video.
        output_dir: Directory where frames will be saved.
        every_n_frames: Save every nth frame.

    Returns:
        List of saved frame paths.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    frame_paths = []
    frame_idx = 0
    saved_idx = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        if frame_idx % every_n_frames == 0:
            frame_path = output_dir / f"frame_{saved_idx:05d}.jpg"
            cv2.imwrite(str(frame_path), frame)
            frame_paths.append(frame_path)
            saved_idx += 1

        frame_idx += 1

    cap.release()
    return frame_paths