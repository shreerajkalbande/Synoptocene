# 🎬 Synoptocene: Advanced Video Intelligence Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-gray?style=for-the-badge&logo=flask&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green?style=for-the-badge&logo=opencv&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-Machine%20Learning-red?style=for-the-badge&logo=pytorch&logoColor=white)
![MIT License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

</div>

## 🚀 Overview

**Synoptocene** is an advanced video summarization platform that combines cutting-edge AI technologies to create intelligent video summaries. It implements a sophisticated 7-stage pipeline that processes video content through dynamic keyframe extraction, motion-aware analysis, and multimodal AI fusion.

### Key Innovations

- 🧠 **Dynamic Keyframe Extraction**: Intelligent frame selection based on content changes
- 🌊 **Motion-Aware Processing**: Optical flow analysis for scene understanding
- 🔍 **AI-Powered Scoring**: CLIP-based semantic content ranking
- 🎵 **Multimodal Integration**: Video, audio, and text processing
- ⚡ **Real-Time Adaptation**: Dynamic processing based on content complexity

---

## ✨ Features

### 🎬 Core Capabilities
- **Dynamic Keyframe Extraction**: Intelligent frame selection based on content changes
- **Motion-Aware Processing**: Optical flow analysis for scene understanding
- **AI-Powered Scoring**: CLIP-based semantic content ranking
- **Multimodal Integration**: Video, audio, and text processing

### 🤖 AI Technologies
- **CLIP Semantic Scoring**: Context-aware content relevance ranking
- **Whisper Audio Processing**: High-quality speech recognition and transcription
- **mPLUG-2 Owl**: Multimodal video-audio-text understanding
- **ChatGPT Integration**: Final summary refinement and coherence

### 🔧 Technical Features
- **GPU Acceleration**: CUDA support for real-time processing
- **Vector Similarity Search**: FAISS-based efficient redundancy removal
- **Temporal Synchronization**: Perfect video-audio alignment
- **Automated Pipeline**: Kaggle integration with Selenium automation

### 🌐 Web Platform
- **Modern Interface**: Responsive design with Bootstrap4
- **User Authentication**: Secure login/register system
- **Environment Security**: Credential management with environment variables
- **Comprehensive Logging**: Detailed metadata and processing insights

---

## 🛠️ Technology Stack

| Component | Technologies |
|-----------|--------------|
| **Backend** | Python, Flask, SQLAlchemy |
| **AI/ML** | CLIP, Whisper, mPLUG-2 Owl, ChatGPT |
| **Computer Vision** | OpenCV, DISOpticalFlow |
| **Vector Processing** | FAISS, PyTorch, NumPy |
| **Audio Processing** | FFmpeg, PyDub |
| **Frontend** | HTML, CSS, JavaScript, Bootstrap4 |
| **Database** | SQLite |
| **Security** | Environment Variables, Password Hashing |

---

## 🛠️ How It Works

Synoptocene implements a sophisticated 7-stage video processing pipeline that combines computer vision, audio processing, and AI to create intelligent video summaries:

#### **Stage 1: Dynamic Keyframe Extraction** 🔍
- **Intelligent Frame Selection**: Uses pixel-level difference analysis with configurable thresholds
- **Adaptive Sampling**: Automatically adjusts frame extraction based on visual content changes
- **Memory-Optimized Processing**: Loads entire video into memory for efficient batch processing
- **Configurable Parameters**: `pixel_thresh=30`, `min_interval=10` for optimal keyframe selection

#### **Stage 2: CLIP-Based Content Scoring** 🎯
- **Semantic Understanding**: Leverages OpenAI's CLIP model for content relevance scoring
- **Prompt-Driven Analysis**: Ranks frames based on user-defined relevance criteria
- **Feature Embedding**: Generates high-dimensional feature vectors for each keyframe
- **GPU Acceleration**: Utilizes CUDA for fast parallel processing when available

#### **Stage 3: FAISS-Based Redundancy Pruning** ✂️
- **Diversity Filtering**: Implements cosine similarity-based redundancy removal
- **Configurable Thresholds**: `threshold_dot=0.98` for optimal diversity vs. coverage balance
- **Efficient Vector Search**: Uses FAISS for fast similarity computations
- **Quality Preservation**: Maintains high-scoring frames while eliminating duplicates

#### **Stage 4: Motion-Aware Snippet Generation** 🎞️
- **Optical Flow Analysis**: Uses OpenCV's DISOpticalFlow for motion intensity measurement
- **Adaptive Window Sizing**: Dynamically adjusts snippet length based on motion:
  - **Fast Motion** (< 0.3): 7-frame windows for detailed analysis
  - **Medium Motion** (0.3-0.7): 5-frame windows for balanced coverage
  - **Slow Motion** (> 0.7): 3-frame windows for concise summaries
- **Temporal Alignment**: Ensures snippets align with audio segments for multimodal coherence

#### **Stage 5: Multimodal Content Analysis** 🎵
- **Audio Transcription**: Uses OpenAI Whisper for high-quality speech recognition
- **Word-Level Timestamps**: Precise temporal alignment of audio with video content
- **Segment Synchronization**: Aligns video snippets with corresponding audio segments
- **Metadata Generation**: Comprehensive logging of all processing parameters and results

#### **Stage 6: mPLUG-2 Owl Summarization** 🦉
- **Multimodal Understanding**: Processes both video frames and audio transcripts simultaneously
- **Context-Aware Generation**: Creates summaries that correlate visual and auditory content
- **Advanced Language Model**: Leverages state-of-the-art multimodal LLM capabilities
- **Optimized Generation**: Configurable parameters for length, creativity, and coherence

#### **Stage 7: ChatGPT Final Integration** 🤖
- **Snippet Aggregation**: Combines individual snippet summaries into cohesive narratives
- **Context Refinement**: Enhances summaries with additional context and coherence
- **Quality Assurance**: Ensures final output meets user requirements and standards
- **Selenium Automation**: Seamless integration with web-based ChatGPT interface

### 🔄 **Pipeline Flow Architecture**

```
Video Input → Dynamic Extraction → CLIP Scoring → FAISS Pruning → Motion Analysis → 
Snippet Generation → mPLUG-2 Owl → ChatGPT → Final Summary
```

### ⚙️ **Technical Specifications**

- **Video Processing**: OpenCV with configurable resolution (default: 640x360)
- **AI Models**: CLIP, Whisper, mPLUG-2 Owl, ChatGPT
- **Vector Database**: FAISS for efficient similarity search
- **Audio Processing**: FFmpeg integration with 16kHz mono conversion
- **Memory Management**: Optimized for large video files with GPU acceleration
- **Output Format**: MP4 video snippets + WAV audio + JSON metadata

---


## 🧪 Setup & Run

### 1. **Clone the repository**
```bash
git clone https://github.com/shreerajkalbande/Synoptocene.git
cd Synoptocene
```

### 2. **Create a virtual environment (Recommended)**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. **Install dependencies**
```bash
pip install -r requirements.txt
```

### 4. **Set up environment variables**
Create a `.env` file in the root directory:

```bash
# Kaggle credentials
KAGGLE_EMAIL=your_actual_kaggle_email
KAGGLE_PASSWORD=your_actual_kaggle_password

# ChatGPT credentials (if needed)
CHATGPT_EMAIL=your_actual_chatgpt_email
CHATGPT_PASSWORD=your_actual_chatgpt_password

# Flask secret key
FLASK_KEY=your_actual_flask_secret_key
FLASK_SECRET_KEY=your_actual_flask_secret_key

# Database URI (if needed)
DB_URI=sqlite:///posts.db
```

**Quick Setup**: Run the interactive setup script:
```bash
python setup_env.py
```

### 5. **Run the application**
```bash
python main.py
```

The Flask app will run on http://localhost:5000

---

## 🔒 Security Features

- **Environment Variables**: All credentials stored securely in `.env` files
- **Password Hashing**: Secure password storage using PBKDF2 with SHA256
- **User Authentication**: Flask-Login integration with session management
- **Input Validation**: Secure form handling and data validation
- **Git History Clean**: Automated cleanup of sensitive data from version control

---

## 📁 Project Structure

```
Synoptocene/
├── main.py                 # Main Flask application
├── forms.py               # Form definitions and validation
├── static/                # Static assets (CSS, JS, images)
├── templates/             # HTML templates
├── instance/              # Database and instance files
├── tests/                 # Test suite
├── setup_env.py          # Environment setup helper
├── cleanup_git_history.sh # Git history cleanup script
└── SECURITY_CHECKLIST.md  # Security guidelines
```

---

## 🧪 Testing

Run the test suite to ensure everything works correctly:

```bash
python -m pytest tests/
```

---

## 🔬 Advanced Algorithms

### **Dynamic Keyframe Extraction**
- Pixel-level difference analysis using OpenCV
- Adaptive thresholding for different video types
- Memory-optimized batch processing

### **CLIP-Based Semantic Scoring**
- Multimodal understanding with OpenAI's CLIP
- High-dimensional feature embeddings
- GPU-accelerated processing

### **FAISS Vector Similarity Search**
- Efficient cosine similarity-based redundancy removal
- Scalable processing for large keyframe sets
- Quality preservation through diversity maintenance

### **Motion-Aware Snippet Generation**
- Optical flow analysis using DISOpticalFlow
- Adaptive window sizing based on motion intensity
- Temporal synchronization of video and audio

### **Multimodal AI Integration**
- Whisper for high-quality audio transcription
- mPLUG-2 Owl for multimodal understanding
- ChatGPT for final summary refinement

---

## 🚀 Deployment

The application includes a `Procfile` for easy deployment on platforms like Heroku. Ensure your environment variables are properly configured in your deployment environment.

---

## 📄 License
This project is licensed under the MIT License.

---

## 🤝 Contributions
Feel free to fork, raise issues, or submit PRs to improve this project!

---

## 📝 Author

**Shreeraj Kalbande** | IIT Kharagpur CSE

Email: [shreerajkalbande25@gmail.com](mailto:shreerajkalbande25@gmail.com)

---

## ⚠️ Security Notes

- Never commit your `.env` file to version control
- The `.env` file is already in `.gitignore`
- Rotate your credentials regularly
- Use strong, unique passwords for each service
- Consider using 2FA where available
