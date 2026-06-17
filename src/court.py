"""
Court graphics, calibration, and coordinate transformation.
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional


@dataclass
class CourtConfig:
    """Configuration for court dimensions and zones."""
    
    # Court dimensions (abstract units, can be scaled)
    width: float = 100
    length: float = 100
    
    # T position (back-middle area)
    t_x: float = 50
    t_y: float = 62
    
    # T-zone radius for metrics
    t_zone_radius: float = 10
    
    # Court corners (in court coordinates)
    front_left: Tuple[float, float] = (0, 0)
    front_right: Tuple[float, float] = (100, 0)
    back_left: Tuple[float, float] = (0, 100)
    back_right: Tuple[float, float] = (100, 100)


def get_default_court_config() -> CourtConfig:
    """Get default court configuration."""
    return CourtConfig()


def get_court_zones() -> Dict[str, Dict]:
    """
    Define 9 zones on the court.
    
    Returns:
        Dict mapping zone names to zone boundaries.
        Each zone has 'min_x', 'max_x', 'min_y', 'max_y'
    """
    zones = {
        # Front row
        "front_left": {
            "min_x": 0,
            "max_x": 33.3,
            "min_y": 0,
            "max_y": 33.3,
        },
        "front_center": {
            "min_x": 33.3,
            "max_x": 66.7,
            "min_y": 0,
            "max_y": 33.3,
        },
        "front_right": {
            "min_x": 66.7,
            "max_x": 100,
            "min_y": 0,
            "max_y": 33.3,
        },
        # Middle row
        "mid_left": {
            "min_x": 0,
            "max_x": 33.3,
            "min_y": 33.3,
            "max_y": 66.7,
        },
        "mid_center": {
            "min_x": 33.3,
            "max_x": 66.7,
            "min_y": 33.3,
            "max_y": 66.7,
        },
        "mid_right": {
            "min_x": 66.7,
            "max_x": 100,
            "min_y": 33.3,
            "max_y": 66.7,
        },
        # Back row
        "back_left": {
            "min_x": 0,
            "max_x": 33.3,
            "min_y": 66.7,
            "max_y": 100,
        },
        "back_center": {
            "min_x": 33.3,
            "max_x": 66.7,
            "min_y": 66.7,
            "max_y": 100,
        },
        "back_right": {
            "min_x": 66.7,
            "max_x": 100,
            "min_y": 66.7,
            "max_y": 100,
        },
    }
    return zones


def assign_zone(court_x: float, court_y: float, zones: Dict = None) -> str:
    """
    Assign a point to a court zone.
    
    Args:
        court_x: X coordinate on court
        court_y: Y coordinate on court
        zones: Zone definitions (uses default if None)
    
    Returns:
        Zone name or "unknown"
    """
    if zones is None:
        zones = get_court_zones()
    
    for zone_name, zone_bounds in zones.items():
        if (zone_bounds["min_x"] <= court_x <= zone_bounds["max_x"] and
            zone_bounds["min_y"] <= court_y <= zone_bounds["max_y"]):
            return zone_name
    
    return "unknown"


def compute_homography(video_points: List[Tuple[float, float]], 
                       court_points: List[Tuple[float, float]]) -> np.ndarray:
    """
    Compute homography matrix from video coordinates to court coordinates.
    
    Args:
        video_points: List of (x, y) points in video frame
        court_points: Corresponding list of (x, y) points on court
    
    Returns:
        3x3 homography matrix
    
    Raises:
        ValueError: If points are invalid or insufficient
    """
    if len(video_points) != len(court_points):
        raise ValueError("video_points and court_points must have same length")
    
    if len(video_points) < 4:
        raise ValueError("Need at least 4 point pairs for homography")
    
    video_pts = np.array(video_points, dtype=np.float32)
    court_pts = np.array(court_points, dtype=np.float32)
    
    # Compute homography: video -> court
    homography, _ = cv2.findHomography(video_pts, court_pts)
    
    if homography is None:
        raise ValueError("Failed to compute homography matrix")
    
    return homography


def video_to_court_points(video_points: np.ndarray, homography: np.ndarray) -> np.ndarray:
    """
    Transform points from video coordinates to court coordinates.
    
    Args:
        video_points: Array of (x, y) points in video
        homography: 3x3 homography matrix from compute_homography()
    
    Returns:
        Array of (x, y) points in court coordinates
    """
    if isinstance(video_points, list):
        video_points = np.array(video_points, dtype=np.float32)
    
    # Add homogeneous coordinate
    ones = np.ones((video_points.shape[0], 1))
    video_points_h = np.hstack([video_points, ones])
    
    # Apply homography
    court_points_h = video_points_h @ homography.T
    
    # Normalize by homogeneous coordinate
    court_points = court_points_h[:, :2] / court_points_h[:, 2:3]
    
    return court_points


def video_to_court_point(video_point: Tuple[float, float], 
                         homography: np.ndarray) -> Tuple[float, float]:
    """
    Transform a single point from video to court coordinates.
    
    Args:
        video_point: (x, y) in video frame
        homography: 3x3 homography matrix
    
    Returns:
        (x, y) in court coordinates
    """
    points = np.array([video_point], dtype=np.float32)
    court_point = video_to_court_points(points, homography)[0]
    return tuple(court_point)


def draw_court_graphic(width: int = 800, height: int = 800, 
                      config: CourtConfig = None) -> np.ndarray:
    """
    Draw a blank top-down court graphic.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        config: CourtConfig (uses default if None)
    
    Returns:
        BGR image of court graphic
    """
    if config is None:
        config = get_default_court_config()
    
    # Create blank white image
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # Scale court coordinates to image coordinates
    def court_to_image(court_x: float, court_y: float) -> Tuple[int, int]:
        img_x = int((court_x / config.width) * width)
        img_y = int((court_y / config.length) * height)
        return (img_x, img_y)
    
    # Draw court boundary
    front_left_img = court_to_image(0, 0)
    front_right_img = court_to_image(config.width, 0)
    back_left_img = court_to_image(0, config.length)
    back_right_img = court_to_image(config.width, config.length)
    
    # Draw outer rectangle (court boundary)
    cv2.rectangle(img, front_left_img, back_right_img, (0, 0, 0), 3)
    
    # Draw center line
    mid_left = court_to_image(0, config.length / 2)
    mid_right = court_to_image(config.width, config.length / 2)
    cv2.line(img, mid_left, mid_right, (200, 200, 200), 1)
    
    # Draw T zone (circle)
    t_img = court_to_image(config.t_x, config.t_y)
    t_radius_px = int((config.t_zone_radius / config.width) * width)
    cv2.circle(img, t_img, t_radius_px, (220, 220, 220), 2)
    
    # Draw T position
    cv2.circle(img, t_img, 5, (0, 0, 255), -1)
    
    # Draw zone grid (light lines)
    for i in range(1, 3):
        # Vertical lines
        x_court = (i / 3) * config.width
        x_img = int((x_court / config.width) * width)
        cv2.line(img, (x_img, 0), (x_img, height), (230, 230, 230), 1)
        
        # Horizontal lines
        y_court = (i / 3) * config.length
        y_img = int((y_court / config.length) * height)
        cv2.line(img, (0, y_img), (width, y_img), (230, 230, 230), 1)
    
    # Add labels
    cv2.putText(img, "Front Wall", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "Back Wall", (20, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    return img


def draw_path_on_court(court_img: np.ndarray, path_points: np.ndarray, 
                       config: CourtConfig = None, color: Tuple[int, int, int] = (0, 255, 0),
                       thickness: int = 2) -> np.ndarray:
    """
    Draw a movement path on a court graphic.
    
    Args:
        court_img: Court graphic image
        path_points: Array of (x, y) points in court coordinates
        config: CourtConfig (uses default if None)
        color: Path color as (B, G, R)
        thickness: Line thickness
    
    Returns:
        Image with path drawn
    """
    if config is None:
        config = get_default_court_config()
    
    img = court_img.copy()
    height, width = img.shape[:2]
    
    def court_to_image(court_x: float, court_y: float) -> Tuple[int, int]:
        img_x = int((court_x / config.width) * width)
        img_y = int((court_y / config.length) * height)
        return (img_x, img_y)
    
    # Draw lines connecting points
    for i in range(len(path_points) - 1):
        pt1 = court_to_image(path_points[i, 0], path_points[i, 1])
        pt2 = court_to_image(path_points[i + 1, 0], path_points[i + 1, 1])
        cv2.line(img, pt1, pt2, color, thickness)
    
    # Draw circles at points
    for i, point in enumerate(path_points):
        pt = court_to_image(point[0], point[1])
        # Start point in blue, end point in red
        if i == 0:
            cv2.circle(img, pt, 6, (255, 0, 0), -1)
        elif i == len(path_points) - 1:
            cv2.circle(img, pt, 6, (0, 0, 255), -1)
        else:
            cv2.circle(img, pt, 3, color, -1)
    
    return img


def calibration_preview(frame: np.ndarray, video_calibration_points: List[Tuple[float, float]],
                        court_config: CourtConfig = None) -> np.ndarray:
    """
    Draw calibration points on a video frame for preview.
    
    Args:
        frame: Video frame image
        video_calibration_points: List of (x, y) calibration points clicked
        court_config: Court configuration
    
    Returns:
        Frame with calibration points drawn
    """
    if court_config is None:
        court_config = get_default_court_config()
    
    img = frame.copy()
    
    # Point labels
    labels = ["Front-Left", "Front-Right", "Back-Left", "Back-Right", "T-Position"]
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
    
    for i, (point, label, color) in enumerate(zip(video_calibration_points, labels, colors)):
        x, y = int(point[0]), int(point[1])
        # Draw circle
        cv2.circle(img, (x, y), 10, color, -1)
        cv2.circle(img, (x, y), 10, (255, 255, 255), 2)
        # Draw label
        cv2.putText(img, f"{i+1}. {label}", (x + 15, y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    return img
