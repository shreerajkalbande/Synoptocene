import os
import json
import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional

from pipeline.motion_analyzer import compute_optical_flow_magnitude
from pipeline.audio_processor import AudioProcessor


def extract_frames_range(
    frames: List[Tuple[np.ndarray, int]],
    start_idx: int,
    end_idx: int,
) -> List[np.ndarray]:
    """Extract frame arrays within a given index range (inclusive)."""
    return [frm for frm, idx in frames if start_idx <= idx <= end_idx]


def generate_snippets(
    keyframes: List[Dict],
    frames: List[Tuple[np.ndarray, int]],
    fps: float,
    audio_proc: AudioProcessor,
    output_dir: str,
    resize_dim: Tuple[int, int] = (640, 360),
) -> List[str]:
    """Generate video snippet files from selected keyframes.

    For each keyframe, determines an adaptive window size based on local
    motion intensity, expands it to align with audio transcript segments,
    and writes video + audio + metadata to disk.

    Args:
        keyframes: Selected keyframes sorted by real_index (temporal order).
        frames: All video frames as (array, index) pairs.
        fps: Video frame rate.
        audio_proc: AudioProcessor with completed transcription.
        output_dir: Base directory for snippet output.
        resize_dim: Frame resolution for output video.

    Returns:
        List of snippet directory paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    total_frames = len(frames)
    snippet_dirs = []
    snippet_idx = 1

    for kf in keyframes:
        real_idx = kf["real_index"]

        # Measure local motion around the keyframe
        probe_start = max(0, real_idx - 5)
        probe_end = min(total_frames - 1, real_idx + 5)
        probe_frames = extract_frames_range(frames, probe_start, probe_end)
        local_motion = compute_optical_flow_magnitude(probe_frames, resize_dim)

        # Adaptive window based on motion intensity
        from pipeline.motion_analyzer import motion_adaptive_window
        halfw = motion_adaptive_window(local_motion)
        start_f = max(0, real_idx - halfw)
        end_f = min(total_frames - 1, real_idx + halfw)

        if end_f <= start_f:
            continue

        # Expand to align with audio segments
        start_sec = start_f / fps
        end_sec = end_f / fps
        overlapping = audio_proc.get_overlapping_segments(start_sec, end_sec)

        if overlapping:
            seg_start = min(s["start"] for s in overlapping)
            seg_end = max(s["end"] for s in overlapping)
            start_f = max(0, int(seg_start * fps))
            end_f = min(total_frames - 1, int(seg_end * fps))
            if end_f <= start_f:
                continue

        snippet_frames = extract_frames_range(frames, start_f, end_f)
        final_motion = compute_optical_flow_magnitude(snippet_frames, resize_dim)

        # Write snippet to disk
        snippet_dir = os.path.join(output_dir, f"snippet_{snippet_idx:03d}")
        os.makedirs(snippet_dir, exist_ok=True)

        _write_video(snippet_dir, snippet_frames, fps, resize_dim)
        _write_audio(snippet_dir, audio_proc, start_f, end_f, fps)

        snippet_start_sec = start_f / fps
        snippet_end_sec = end_f / fps

        metadata = {
            "real_index": real_idx,
            "diff_score": kf["diff_score"],
            "clip_score": kf["clip_score"],
            "local_motion": final_motion,
            "snippet_start_frame": start_f,
            "snippet_end_frame": end_f,
            "snippet_start_s": snippet_start_sec,
            "snippet_end_s": snippet_end_sec,
            "frames_written": len(snippet_frames),
            "audio_words": audio_proc.get_words_in_range(
                snippet_start_sec, snippet_end_sec
            ),
            "audio_segments": audio_proc.get_overlapping_segments(
                snippet_start_sec, snippet_end_sec
            ),
        }
        with open(os.path.join(snippet_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

        dur = len(snippet_frames) / fps
        print(f"[Snippet {snippet_idx:03d}] idx={real_idx}, "
              f"clip={kf['clip_score']:.3f}, motion={final_motion:.2f}, "
              f"frames={len(snippet_frames)}, dur={dur:.2f}s")

        snippet_dirs.append(snippet_dir)
        snippet_idx += 1

    return snippet_dirs


def _write_video(
    snippet_dir: str,
    snippet_frames: List[np.ndarray],
    fps: float,
    resize_dim: Tuple[int, int],
) -> None:
    """Write snippet frames as an MP4 video file."""
    path = os.path.join(snippet_dir, "video.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(path, fourcc, fps, resize_dim)
    for frm in snippet_frames:
        writer.write(cv2.resize(frm, resize_dim))
    writer.release()


def _write_audio(
    snippet_dir: str,
    audio_proc: AudioProcessor,
    start_f: int,
    end_f: int,
    fps: float,
) -> None:
    """Write the corresponding audio slice as a WAV file."""
    clip = audio_proc.get_audio_snippet(start_f, end_f, fps)
    if clip:
        clip.export(os.path.join(snippet_dir, "audio.wav"), format="wav")
