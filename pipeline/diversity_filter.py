import numpy as np
from typing import List, Dict


def filter_by_diversity(
    keyframes: List[Dict], threshold_dot: float = 0.98
) -> List[Dict]:
    """Remove near-duplicate keyframes using cosine similarity thresholding.

    Iterates through keyframes (assumed sorted by relevance) and keeps
    a frame only if its cosine similarity with all previously selected
    frames is below `threshold_dot`.

    Args:
        keyframes: Keyframes sorted by CLIP score (descending).
        threshold_dot: Maximum cosine similarity allowed between kept frames.

    Returns:
        Filtered keyframe list preserving diversity.
    """
    selected = []
    for kf in keyframes:
        emb = kf["clip_emb"]
        is_diverse = all(
            float(np.dot(emb, chosen["clip_emb"])) <= threshold_dot
            for chosen in selected
        )
        if is_diverse:
            selected.append(kf)

    print(f"[DiversityFilter] {len(keyframes)} -> {len(selected)} frames "
          f"(threshold={threshold_dot})")
    return selected
