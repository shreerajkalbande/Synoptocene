#!/usr/bin/env python3
"""
Environment Setup Script
This script helps you create a .env file with your credentials
"""

import os
import getpass

def create_env_file():
    """Create a .env file with user input"""
    
    print("🔐 Environment Variables Setup")
    print("=" * 40)
    print("This script will help you create a .env file with your credentials.")
    print("Your credentials will NOT be stored in version control.\n")
    
    # Check if .env already exists
    if os.path.exists('.env'):
        overwrite = input("⚠️  .env file already exists. Overwrite? (y/N): ").lower()
        if overwrite != 'y':
            print("❌ Setup cancelled.")
            return
    
    # Collect credentials
    print("\n📧 Kaggle Credentials:")
    kaggle_email = input("Kaggle Email: ").strip()
    kaggle_password = getpass.getpass("Kaggle Password: ")
    
    print("\n🤖 ChatGPT Credentials (optional):")
    chatgpt_email = input("ChatGPT Email (press Enter to skip): ").strip()
    chatgpt_password = ""
    if chatgpt_email:
        chatgpt_password = getpass.getpass("ChatGPT Password: ")
    
    print("\n🔑 Flask Secret Key:")
    flask_key = getpass.getpass("Flask Secret Key (press Enter to generate random): ").strip()
    if not flask_key:
        import secrets
        flask_key = secrets.token_hex(32)
        print(f"Generated secret key: {flask_key}")
    
    # Create .env content
    env_content = f"""# Kaggle credentials
KAGGLE_EMAIL={kaggle_email}
KAGGLE_PASSWORD={kaggle_password}

# ChatGPT credentials (if needed)
CHATGPT_EMAIL={chatgpt_email}
CHATGPT_PASSWORD={chatgpt_password}

# Flask secret key
FLASK_KEY={flask_key}
FLASK_SECRET_KEY={flask_key}

# Database URI (if needed)
DB_URI=sqlite:///posts.db
"""
    
    # Write to .env file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print(f"\n✅ .env file created successfully!")
        print(f"📁 Location: {os.path.abspath('.env')}")
        print("\n🔒 Security reminders:")
        print("- .env is already in .gitignore")
        print("- Never commit this file to version control")
        print("- Keep your credentials secure")
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

if __name__ == "__main__":
    create_env_file()
