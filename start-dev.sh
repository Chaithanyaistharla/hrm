#!/bin/bash

# HRMS Development Server Script
echo "🚀 Starting HRMS Development Environment"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Navigate to backend and start Django server
echo "🔧 Starting Django backend server..."
cd backend
python manage.py migrate
echo "✅ Starting server at http://127.0.0.1:8000/"
python manage.py runserver

# Note: Add frontend server startup here when frontend is implemented
# echo "🎨 Starting frontend server..."
# cd ../frontend
# npm start