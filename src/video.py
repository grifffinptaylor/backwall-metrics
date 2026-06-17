import cv2
from pathlib import Path


def get_video_metadata(video_path):
    """
    Get metadata from a video file.

    Args:
        video_path: Path to input video.

    Returns:
        Dictionary with keys:
            - duration: duration in seconds
            - fps: frames per second
            - frame_count: total number of frames
            - width: frame width in pixels
            - height: frame height in pixels
    """
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    duration = frame_count / fps if fps > 0 else 0

    cap.release()

    return {
        "duration": duration,
        "fps": fps,
        "frame_count": frame_count,
        "width": width,
        "height": height,
    }


def extract_frames(video_path, output_dir, start_time=None, end_time=None, every_n_frames=10):
    """
    Extract frames from a video.

    Args:
        video_path: Path to input video.
        output_dir: Directory where frames will be saved.
        start_time: Start time in seconds (None = from beginning).
        end_time: End time in seconds (None = to end).
        every_n_frames: Save every nth frame.

    Returns:
        List of saved frame paths.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Calculate frame range
    start_frame = 0
    end_frame = total_frames

    if start_time is not None:
        start_frame = max(0, int(start_time * fps))

    if end_time is not None:
        end_frame = min(total_frames, int(end_time * fps))

    # Seek to start frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    frame_paths = []
    frame_idx = start_frame
    saved_idx = 0

    while frame_idx < end_frame:
        ret, frame = cap.read()

        if not ret:
            break

        if (frame_idx - start_frame) % every_n_frames == 0:
            frame_path = output_dir / f"frame_{saved_idx:05d}.jpg"
            cv2.imwrite(str(frame_path), frame)
            frame_paths.append(frame_path)
            saved_idx += 1

        frame_idx += 1

    cap.release()
    return frame_paths