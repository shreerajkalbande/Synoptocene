import os
import json
import torch
from typing import List, Optional, Dict


def load_mplug_owl(pretrained_path: str):
    """Load the mPLUG-Owl multimodal model for video-audio-text summarization.

    Args:
        pretrained_path: Path to pretrained mPLUG-Owl checkpoint directory.

    Returns:
        Tuple of (model, processor, tokenizer).
    """
    from mplug_owl_video.modeling_mplug_owl import MplugOwlForConditionalGeneration
    from transformers import AutoTokenizer
    from mplug_owl_video.processing_mplug_owl import (
        MplugOwlImageProcessor,
        MplugOwlProcessor,
    )

    model = MplugOwlForConditionalGeneration.from_pretrained(
        pretrained_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    image_processor = MplugOwlImageProcessor.from_pretrained(pretrained_path)
    tokenizer = AutoTokenizer.from_pretrained(pretrained_path)
    processor = MplugOwlProcessor(image_processor, tokenizer)

    print("[mPLUGOwl] Model loaded successfully.")
    return model, processor, tokenizer


DEFAULT_GENERATE_KWARGS = {
    "do_sample": False,
    "top_k": 5,
    "max_length": 70,
    "temperature": 0.5,
    "top_p": 0.9,
    "num_beams": 1,
    "no_repeat_ngram_size": 2,
    "early_stopping": True,
    "length_penalty": 1,
}


def describe_video(
    prompts: List[str],
    video_list: List[str],
    model,
    processor,
    tokenizer,
    generate_kwargs: Optional[Dict] = None,
    nframes: int = 48,
) -> str:
    """Generate a description for video(s) using mPLUG-Owl.

    Args:
        prompts: Text prompt(s) for the model.
        video_list: Path(s) to video files.
        model: Loaded mPLUG-Owl model.
        processor: mPLUG-Owl processor.
        tokenizer: Model tokenizer.
        generate_kwargs: Generation parameters.
        nframes: Number of frames to sample from each video.

    Returns:
        Generated text description.
    """
    if generate_kwargs is None:
        generate_kwargs = DEFAULT_GENERATE_KWARGS

    inputs = processor(
        text=prompts, videos=video_list, num_frames=nframes, return_tensors="pt"
    )
    inputs = {
        k: v.bfloat16() if (torch.is_floating_point(v) and v.dtype == torch.float32) else v
        for k, v in inputs.items()
    }
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        res = model.generate(**inputs, **generate_kwargs)
    return tokenizer.decode(res[0], skip_special_tokens=True)


def summarize_all_snippets(
    snippet_base: str,
    snippet_count: int,
    model,
    processor,
    tokenizer,
    generate_kwargs: Optional[Dict] = None,
) -> List[Optional[str]]:
    """Summarize all generated video snippets using mPLUG-Owl.

    For each snippet, builds a prompt combining the video content with
    the audio transcript from metadata, then generates a multimodal summary.

    Args:
        snippet_base: Directory containing snippet_001/, snippet_002/, etc.
        snippet_count: Number of snippets to process.
        model: Loaded mPLUG-Owl model.
        processor: mPLUG-Owl processor.
        tokenizer: Model tokenizer.
        generate_kwargs: Generation parameters.

    Returns:
        List of summary strings (None for missing snippets).
    """
    summaries = []

    for i in range(1, snippet_count + 1):
        snippet_dir = os.path.join(snippet_base, f"snippet_{i:03d}")
        video_path = os.path.join(snippet_dir, "video.mp4")
        meta_path = os.path.join(snippet_dir, "metadata.json")

        if not os.path.exists(video_path) or not os.path.exists(meta_path):
            print(f"[WARNING] Missing files in {snippet_dir}, skipping.")
            summaries.append(None)
            continue

        with open(meta_path, "r") as f:
            meta = json.load(f)

        audio_segments = meta.get("audio_segments", [])
        transcript = (
            " ".join(seg["text"] for seg in audio_segments).strip()
            if audio_segments else "No audio segments found."
        )

        prompt = (
            "You are an expert in correlating video content with "
            "accompanying audio transcripts.\n"
            "Video: <|video|>\n"
            f"Audio Transcript: {transcript}\n"
            "Based on the visual content and the audio transcript above, "
            "provide a concise and insightful summary that connects both "
            "modalities. Ensure your summary is complete and ends with "
            "a full stop.\n"
            "Summary:"
        )

        summary = describe_video(
            [prompt], [video_path], model, processor, tokenizer,
            generate_kwargs, nframes=48,
        )
        summaries.append(summary)
        print(f"[Snippet {i}] => {summary}")

    return summaries
