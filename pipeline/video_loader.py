import cv2
import numpy as np
from typing import List, Tuple


def load_entire_video(
    video_path: str, resize_dim: Tuple[int, int] = (640, 360)
) -> Tuple[List[Tuple[np.ndarray, int]], float]:
    """Load all frames of a video into memory.

    Args:
        video_path: Path to the video file.
        resize_dim: Target (width, height) for each frame.

    Returns:
        A tuple of (frames_list, fps) where frames_list contains
        (frame, frame_index) pairs.
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0

    frames = []
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, resize_dim)
        frames.append((frame, idx))
        idx += 1
    cap.release()

    print(f"[VideoLoader] Loaded {len(frames)} frames at {fps:.1f} FPS.")
    return frames, fps
