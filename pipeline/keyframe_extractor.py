import cv2
import numpy as np
from typing import List, Dict


def extract_keyframes(
    frames: List[tuple],
    pixel_thresh: float = 30.0,
    min_interval: int = 10,
) -> List[Dict]:
    """Extract keyframes using pixel-level difference analysis.

    Selects frames where the mean absolute difference from the previous
    keyframe exceeds `pixel_thresh`, or every `min_interval` frames as
    a minimum sampling guarantee.

    Args:
        frames: List of (frame_array, frame_index) tuples.
        pixel_thresh: Mean pixel difference threshold for scene change.
        min_interval: Forced keyframe interval (every N frames).

    Returns:
        List of keyframe dicts with keys: frame, real_index, diff_score.
    """
    keyframes = []
    prev_gray = None
    count = 0

    for frame, real_idx in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff_val = 0.0

        if prev_gray is not None:
            diff_img = cv2.absdiff(prev_gray, gray)
            diff_val = float(np.mean(diff_img))

        if diff_val > pixel_thresh or (count % min_interval == 0):
            keyframes.append({
                "frame": frame,
                "real_index": real_idx,
                "diff_score": diff_val,
            })
            prev_gray = gray
        elif prev_gray is None:
            prev_gray = gray

        count += 1

    print(f"[KeyframeExtractor] Extracted {len(keyframes)} keyframes.")
    return keyframes
