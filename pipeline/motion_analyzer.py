import cv2
import numpy as np
from typing import List, Tuple


def compute_optical_flow_magnitude(
    snippet_frames: List[np.ndarray],
    resize_dim: Tuple[int, int] = (640, 360),
) -> float:
    """Compute mean optical flow magnitude across consecutive frames.

    Uses OpenCV DISOpticalFlow (FAST preset) to measure inter-frame
    motion intensity. Returns 0.0 for single-frame snippets.

    Args:
        snippet_frames: List of BGR frame arrays.
        resize_dim: Resolution for flow computation.

    Returns:
        Mean flow magnitude across all consecutive frame pairs.
    """
    if len(snippet_frames) < 2:
        return 0.0

    dis_flow = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_FAST)

    gray_frames = []
    for frm in snippet_frames:
        resized = cv2.resize(frm, resize_dim)
        gray_frames.append(cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY))

    magnitudes = []
    prev = gray_frames[0]
    for curr in gray_frames[1:]:
        flow = dis_flow.calc(prev, curr, None)
        mag = np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)
        magnitudes.append(float(np.mean(mag)))
        prev = curr

    return float(np.mean(magnitudes))


def motion_adaptive_window(local_motion: float) -> int:
    """Determine snippet half-window size based on motion intensity.

    Low motion -> wider window (more context needed).
    High motion -> narrower window (rapid changes, keep focused).

    Args:
        local_motion: Mean optical flow magnitude.

    Returns:
        Half-window size in frames.
    """
    if local_motion < 0.3:
        return 7
    elif local_motion < 0.7:
        return 5
    else:
        return 3
