import faiss
import numpy as np
from typing import List, Dict


def filter_by_diversity(
    keyframes: List[Dict], threshold_dot: float = 0.98
) -> List[Dict]:
    """Remove near-duplicate keyframes using FAISS cosine similarity thresholding.

    Iterates through keyframes (assumed sorted by relevance) and keeps
    a frame only if its cosine similarity with all previously selected
    frames is below `threshold_dot`.

    Args:
        keyframes: Keyframes sorted by CLIP score (descending).
        threshold_dot: Maximum cosine similarity allowed between kept frames.

    Returns:
        Filtered keyframe list preserving diversity.
    """
    if not keyframes:
        return []

    dim = len(keyframes[0]["clip_emb"])
    index = faiss.IndexFlatIP(dim)

    selected = []
    for kf in keyframes:
        emb = np.array(kf["clip_emb"], dtype=np.float32).reshape(1, -1)
        faiss.normalize_L2(emb)

        if index.ntotal == 0:
            index.add(emb)
            selected.append(kf)
            continue

        sims, _ = index.search(emb, index.ntotal)
        if float(sims[0].max()) <= threshold_dot:
            index.add(emb)
            selected.append(kf)

    print(f"[DiversityFilter] {len(keyframes)} -> {len(selected)} frames "
          f"(threshold={threshold_dot})")
    return selected
