import os
from typing import List, Dict, Optional

import whisper
from pydub import AudioSegment


class AudioProcessor:
    """Handles audio extraction, transcription, and snippet slicing.

    Uses OpenAI Whisper for speech-to-text with word-level timestamps,
    enabling precise temporal alignment between video snippets and
    spoken content.
    """

    def __init__(self, whisper_model: str = "medium"):
        self.whisper_model = whisper_model
        self.audio: Optional[AudioSegment] = None
        self.word_timestamps: List[Dict] = []
        self.segments: List[Dict] = []

    def extract_and_transcribe(
        self, video_path: str, tmp_audio_path: str = "/tmp/synoptocene_audio.wav"
    ) -> None:
        """Extract audio from video and transcribe with Whisper.

        Args:
            video_path: Path to the source video file.
            tmp_audio_path: Temporary path for the extracted WAV file.
        """
        os.system(
            f'ffmpeg -i "{video_path}" -vn -acodec pcm_s16le '
            f'-ar 16000 -ac 1 "{tmp_audio_path}" -y'
        )

        print(f"[AudioProcessor] Transcribing with Whisper '{self.whisper_model}'...")
        model = whisper.load_model(self.whisper_model)
        result = model.transcribe(tmp_audio_path, word_timestamps=True)

        self.audio = AudioSegment.from_wav(tmp_audio_path)
        self.word_timestamps = []
        self.segments = []

        for seg in result["segments"]:
            self.word_timestamps.extend(seg.get("words", []))
            self.segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
            })

        print(f"[AudioProcessor] Transcribed {len(self.segments)} segments, "
              f"{len(self.word_timestamps)} words.")

    def get_audio_snippet(
        self, start_frame: int, end_frame: int, fps: float
    ) -> Optional[AudioSegment]:
        """Extract an audio slice corresponding to a frame range.

        Returns None if no audio is loaded or the range is invalid.
        """
        if self.audio is None:
            return None

        start_ms = (start_frame / fps) * 1000
        end_ms = (end_frame / fps) * 1000

        if end_ms <= start_ms or start_ms >= len(self.audio):
            return None
        end_ms = min(end_ms, len(self.audio))

        return self.audio[start_ms:end_ms]

    def get_overlapping_segments(
        self, start_sec: float, end_sec: float
    ) -> List[Dict]:
        """Find transcript segments overlapping a time range."""
        return [
            seg for seg in self.segments
            if seg["end"] >= start_sec and seg["start"] <= end_sec
        ]

    def get_words_in_range(
        self, start_sec: float, end_sec: float
    ) -> List[Dict]:
        """Find word-level timestamps within a time range."""
        return [
            w for w in self.word_timestamps
            if start_sec <= w.get("start", 0.0) < end_sec
        ]
