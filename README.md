# Audio-visual Video Summariser

A Flask-based web application that uses the best pipeline possible for efficient video and audio processing.

Made by Shreeraj Kalbande

## Environment Setup

Before running the application, you need to set up environment variables for sensitive credentials.

### 1. Create a `.env` file in the root directory:

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

### 2. Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Run the application:

```bash
python main.py
```

## Security Notes

- Never commit your `.env` file to version control
- The `.env` file is already in `.gitignore`
- Rotate your credentials regularly
- Use strong, unique passwords for each service
