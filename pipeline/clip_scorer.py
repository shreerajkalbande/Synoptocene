import numpy as np
import torch
import torch.nn.functional as F
from tqdm.auto import tqdm
from transformers import CLIPProcessor, CLIPModel
from typing import List, Dict, Tuple


def load_clip(device: str = "cuda") -> Tuple[CLIPModel, CLIPProcessor]:
    """Load the CLIP model and processor."""
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return model, processor


def encode_prompt(
    prompt: str, model: CLIPModel, processor: CLIPProcessor, device: str
) -> np.ndarray:
    """Encode a text prompt into a normalised CLIP embedding."""
    text_inp = processor(text=prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        txt_feat = model.get_text_features(**text_inp)
    txt_feat = F.normalize(txt_feat, p=2, dim=1)
    return txt_feat.cpu().numpy()


def score_keyframes(
    keyframes: List[Dict],
    prompt_emb: np.ndarray,
    model: CLIPModel,
    processor: CLIPProcessor,
    device: str,
) -> List[Dict]:
    """Score each keyframe against a text prompt using CLIP.

    Each keyframe dict is augmented with `clip_score` (cosine similarity)
    and `clip_emb` (image embedding). Results are sorted descending by score.
    """
    for kf in tqdm(keyframes, desc="CLIP scoring"):
        inp = processor(images=kf["frame"], return_tensors="pt").to(device)
        with torch.no_grad():
            img_feat = model.get_image_features(**inp)
        img_feat = F.normalize(img_feat, p=2, dim=1).cpu().numpy()
        kf["clip_score"] = float(np.dot(img_feat, prompt_emb.T).squeeze())
        kf["clip_emb"] = img_feat[0]

    keyframes.sort(key=lambda x: x["clip_score"], reverse=True)
    print(f"[CLIPScorer] Scored {len(keyframes)} keyframes. "
          f"Top score: {keyframes[0]['clip_score']:.4f}")
    return keyframes
