import os
import gc
import torch
from typing import List, Optional

from pipeline.video_loader import load_entire_video
from pipeline.keyframe_extractor import extract_keyframes
from pipeline.clip_scorer import load_clip, encode_prompt, score_keyframes
from pipeline.diversity_filter import filter_by_diversity
from pipeline.audio_processor import AudioProcessor
from pipeline.snippet_generator import generate_snippets


class VideoSummarizer:
    """End-to-end video summarization through a 7-stage multimodal pipeline.

    Stages:
        1. Video loading and frame extraction
        2. Dynamic keyframe extraction (pixel-level difference)
        3. CLIP-based semantic relevance scoring
        4. FAISS-style diversity pruning (cosine similarity thresholding)
        5. Optical-flow-based motion-adaptive snippet generation
        6. Whisper audio transcription with temporal alignment
        7. Snippet output (video + audio + metadata) for downstream
           multimodal summarization (mPLUG-Owl / LLM integration)

    Args:
        video_path: Path to the input video.
        prompt: Text prompt for CLIP-based relevance ranking.
        top_k: Maximum number of snippets to generate.
        resize_dim: Frame resolution (width, height).
        output_dir: Directory for snippet outputs.
        whisper_model: Whisper model size (tiny/base/small/medium/large).
        pixel_thresh: Keyframe extraction sensitivity.
        min_interval: Minimum keyframe sampling interval.
        diversity_threshold: Max cosine similarity for diversity filter.
    """

    def __init__(
        self,
        video_path: str,
        prompt: str = "Rank according to relevancy",
        top_k: int = 10,
        resize_dim: tuple = (640, 360),
        output_dir: str = "./snippets",
        whisper_model: str = "medium",
        pixel_thresh: float = 30.0,
        min_interval: int = 10,
        diversity_threshold: float = 0.98,
    ):
        self.video_path = video_path
        self.prompt = prompt
        self.top_k = top_k
        self.resize_dim = resize_dim
        self.output_dir = output_dir
        self.whisper_model = whisper_model
        self.pixel_thresh = pixel_thresh
        self.min_interval = min_interval
        self.diversity_threshold = diversity_threshold

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def run(self) -> List[str]:
        """Execute the full summarization pipeline.

        Returns:
            List of snippet directory paths containing video.mp4,
            audio.wav, and metadata.json for each extracted snippet.
        """
        # Stage 1: Load video
        frames, fps = load_entire_video(self.video_path, self.resize_dim)
        if not frames:
            print("[VideoSummarizer] No frames loaded, aborting.")
            return []

        # Stage 2: Dynamic keyframe extraction
        keyframes = extract_keyframes(
            frames, self.pixel_thresh, self.min_interval
        )
        if not keyframes:
            print("[VideoSummarizer] No keyframes extracted, aborting.")
            return []

        # Stage 3: CLIP semantic scoring
        clip_model, clip_proc = load_clip(self.device)
        prompt_emb = encode_prompt(self.prompt, clip_model, clip_proc, self.device)
        keyframes = score_keyframes(
            keyframes, prompt_emb, clip_model, clip_proc, self.device
        )

        # Stage 4: Diversity pruning
        keyframes = filter_by_diversity(keyframes, self.diversity_threshold)
        keyframes = keyframes[: self.top_k]
        print(f"[VideoSummarizer] Selected {len(keyframes)} keyframes.")

        # Free CLIP model before loading Whisper
        del clip_model, clip_proc
        if self.device == "cuda":
            torch.cuda.empty_cache()

        # Stage 5-6: Audio transcription + snippet generation
        audio_proc = AudioProcessor(self.whisper_model)
        audio_proc.extract_and_transcribe(self.video_path)

        # Sort by temporal order for coherent snippets
        keyframes.sort(key=lambda x: x["real_index"])

        snippet_dirs = generate_snippets(
            keyframes, frames, fps, audio_proc, self.output_dir, self.resize_dim
        )

        # Cleanup
        del frames
        gc.collect()
        if self.device == "cuda":
            torch.cuda.empty_cache()

        print(f"[VideoSummarizer] Generated {len(snippet_dirs)} snippets.")
        return snippet_dirs
