# Synoptocene

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![CUDA](https://img.shields.io/badge/CUDA-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://developer.nvidia.com/cuda-toolkit)
[![FAISS](https://img.shields.io/badge/FAISS-0467DF?style=for-the-badge&logo=meta&logoColor=white)](https://github.com/facebookresearch/faiss)
[![Transformers](https://img.shields.io/badge/Transformers-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/transformers)
[![OpenAI CLIP](https://img.shields.io/badge/CLIP_ViT--B/32-412991?style=for-the-badge&logo=openai&logoColor=white)](https://github.com/openai/CLIP)
[![Whisper](https://img.shields.io/badge/Whisper-74AA9C?style=for-the-badge&logo=openai&logoColor=white)](https://github.com/openai/whisper)
[![mPLUG-Owl2](https://img.shields.io/badge/mPLUG--Owl2-FF6F00?style=for-the-badge&logo=alibaba-cloud&logoColor=white)](https://github.com/X-PLUG/mPLUG-Owl)

**Multimodal video summarization pipeline combining computer vision, NLP, and deep learning.**

Upload a video &rarr; extract semantically relevant snippets &rarr; transcribe audio &rarr; generate a coherent multimodal summary. The system fuses visual, auditory, and textual signals through a 7-stage pipeline built on CLIP, Whisper, optical flow analysis, FAISS vector search, and mPLUG-Owl.

> *Synopsis + Scene = **Synoptocene*** &mdash; understanding video by seeing and hearing it the way humans do.

---

## Architecture

```
                         Input Video
                             |
                    [1] Frame Extraction
                   (pixel-diff adaptive sampling)
                             |
                    [2] CLIP Semantic Scoring
                   (rank frames by text prompt)
                             |
                    [3] FAISS Diversity Pruning
                   (cosine similarity deduplication)
                             |
                    [4] Optical Flow Analysis
                   (DISOpticalFlow motion intensity)
                             |
                    [5] Adaptive Snippet Generation
                   (motion-aware temporal windowing)
                             |
                    [6] Whisper Transcription
                   (word-level temporal alignment)
                             |
                    [7] mPLUG-Owl Summarization
                   (multimodal video+audio+text fusion)
                             |
                      Final Summary
```

## Key Technical Decisions

### Why adaptive keyframe extraction instead of uniform sampling?

Uniform sampling treats a static lecture slide the same as a fast-paced action sequence. This pipeline uses **pixel-level frame differencing** with a configurable threshold (`pixel_thresh=30`) to detect scene changes, plus a minimum interval guarantee (`min_interval=10`) to avoid over-representation of static content. This reduces the keyframe set by 80-95% while preserving all the distinct visual content.

### Why CLIP scoring + FAISS pruning as a two-stage filter?

CLIP ranks frames by **semantic relevance** to a text prompt, but nearby frames often have near-identical embeddings. A simple top-K would select K copies of the same scene. The diversity filter uses **dot-product thresholding** (default 0.98) to ensure selected frames are semantically distinct. This approximates a maximal marginal relevance objective without requiring a full FAISS index build.

### Why motion-adaptive snippet windows?

The optimal temporal context around a keyframe depends on the pace of the scene:
- **Low motion** (< 0.3 optical flow magnitude): 7-frame window &mdash; static content needs more context
- **Medium motion** (0.3 - 0.7): 5-frame window &mdash; balanced coverage
- **High motion** (> 0.7): 3-frame window &mdash; rapid changes, stay focused

Window boundaries are then expanded to align with Whisper transcript segments, ensuring each snippet has complete sentences rather than mid-word cuts.

### Why Whisper + mPLUG-Owl for multimodal fusion?

Whisper provides **word-level timestamps**, enabling precise temporal alignment between audio transcription and video snippets. mPLUG-Owl processes both the video frames and aligned transcript simultaneously, generating summaries that correlate visual content with spoken content rather than treating them independently.

---

## Project Structure

```
Synoptocene/
├── pipeline/                    # Video summarization pipeline (GPU)
│   ├── __init__.py
│   ├── summarizer.py            # End-to-end orchestrator
│   ├── video_loader.py          # Frame extraction and memory management
│   ├── keyframe_extractor.py    # Pixel-diff adaptive keyframe selection
│   ├── clip_scorer.py           # CLIP semantic relevance scoring
│   ├── diversity_filter.py      # Cosine similarity deduplication
│   ├── motion_analyzer.py       # DISOpticalFlow + adaptive windowing
│   ├── audio_processor.py       # Whisper transcription + temporal alignment
│   ├── snippet_generator.py     # Snippet video/audio/metadata output
│   └── mplug_summarizer.py      # mPLUG-Owl multimodal summarization
│
├── web/                         # Flask web application
│   ├── __init__.py
│   ├── app.py                   # Application factory
│   ├── models.py                # SQLAlchemy data models
│   └── routes.py                # HTTP routes + Kaggle orchestration
│
├── templates/                   # Jinja2 HTML templates
├── static/                      # CSS, JS, images
├── tests/                       # pytest test suite
├── forms.py                     # WTForms definitions
├── main.py                      # Entrypoint
├── requirements.txt             # Web + orchestration dependencies
├── requirements-pipeline.txt    # GPU pipeline dependencies
└── setup_env.py                 # Interactive environment setup
```

## Pipeline Modules

| Module | Responsibility | Core Libraries |
|---|---|---|
| `video_loader` | Load all frames into memory with configurable resize | OpenCV |
| `keyframe_extractor` | Adaptive keyframe selection via pixel-level differencing | OpenCV, NumPy |
| `clip_scorer` | Encode text prompt + score keyframes by semantic relevance | CLIP (ViT-B/32), PyTorch |
| `diversity_filter` | Remove near-duplicate frames via cosine similarity thresholding | NumPy |
| `motion_analyzer` | Compute optical flow magnitude, determine adaptive window size | OpenCV DISOpticalFlow |
| `audio_processor` | Extract audio, transcribe with word-level timestamps | Whisper, FFmpeg, PyDub |
| `snippet_generator` | Generate video + audio + JSON metadata per snippet | OpenCV, JSON |
| `mplug_summarizer` | Multimodal video-audio-text summarization | mPLUG-Owl, Transformers |

## Usage

### Pipeline (requires GPU)

```python
from pipeline import VideoSummarizer

summarizer = VideoSummarizer(
    video_path="input.mp4",
    prompt="Summarize the key events",
    top_k=10,
    resize_dim=(640, 360),
)
snippet_dirs = summarizer.run()
# Each dir contains: video.mp4, audio.wav, metadata.json
```

### Web Application

```bash
# 1. Clone and install
git clone https://github.com/shreerajkalbande/Synoptocene.git
cd Synoptocene
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# For GPU pipeline (on a CUDA machine):
pip install -r requirements-pipeline.txt

# 2. Configure environment
python setup_env.py  # Interactive credential setup

# 3. Run
python main.py       # Flask dev server on http://localhost:5000
```

### Tests

```bash
pytest tests/ -v
```

## Tech Stack

| Layer | Technologies |
|---|---|
| **Vision** | OpenCV, CLIP (ViT-B/32), DISOpticalFlow |
| **Audio** | Whisper, FFmpeg, PyDub |
| **NLP/Multimodal** | mPLUG-Owl, Transformers |
| **Vector Search** | FAISS-style cosine similarity |
| **Compute** | PyTorch (CUDA), NumPy |
| **Web** | Flask, SQLAlchemy, Bootstrap 4 |
| **Orchestration** | Kaggle API, Selenium |

## Configuration

Key parameters in `VideoSummarizer`:

| Parameter | Default | Description |
|---|---|---|
| `pixel_thresh` | 30.0 | Frame difference threshold for keyframe detection |
| `min_interval` | 10 | Minimum frames between forced keyframe samples |
| `diversity_threshold` | 0.98 | Max cosine similarity between selected keyframes |
| `top_k` | 10 | Maximum number of output snippets |
| `whisper_model` | "medium" | Whisper model size (tiny/base/small/medium/large) |
| `resize_dim` | (640, 360) | Frame processing resolution |

---

**Author**: Shreeraj Kalbande | IIT Kharagpur, CSE
