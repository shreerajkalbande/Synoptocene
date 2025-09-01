#!/bin/bash

# Git History Cleanup Script
# This script helps remove sensitive credentials from Git history

echo "🚨 WARNING: This script will rewrite Git history!"
echo "Make sure you have a backup of your repository before proceeding."
echo ""

# Check if git-filter-repo is installed
if ! command -v git-filter-repo &> /dev/null; then
    echo "❌ git-filter-repo is not installed."
    echo "Install it with: pip install git-filter-repo"
    echo "Or use: brew install git-filter-repo (on macOS)"
    exit 1
fi

echo "📝 Creating passwords.txt file for git-filter-repo..."
cat > passwords.txt << EOF
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
EOF

echo "🧹 Cleaning Git history..."
git filter-repo --replace-text passwords.txt --force

echo "🗑️  Cleaning up temporary files..."
rm passwords.txt

echo "✅ Git history cleaned!"
echo ""
echo "📋 Next steps:"
echo "1. Create your .env file with actual credentials"
echo "2. Commit the cleaned code: git add . && git commit -m 'Clean code with environment variables'"
echo "3. Force push: git push origin main --force"
echo "4. Rotate your actual credentials (change passwords on Kaggle, ChatGPT, etc.)"
echo ""
echo "⚠️  Remember: Force push is required because history has been rewritten!"
