#!/bin/bash

# macOS App Build Script for Smart Visiting Card Reader

echo "Building macOS application for Smart Visiting Card Reader..."

# Create a virtual environment
echo "Creating virtual environment..."
python3 -m venv macos_build_env
source macos_build_env/bin/activate

# Install required packages
echo "Installing dependencies..."
pip install -r requirements.txt
pip install py2app

# Create the app bundle
echo "Creating macOS app bundle..."
python setup_macos.py py2app

# Check if build was successful
if [ -d "dist/Smart Visiting Card Reader.app" ]; then
    echo "Build successful! App created at dist/Smart Visiting Card Reader.app"
    echo "You can now run the app by double-clicking it in Finder"
    echo "Or run it from terminal: open dist/\"Smart Visiting Card Reader.app\""
else
    echo "Build failed. Check the error messages above."
fi

echo "Cleaning up..."
# deactivate  # Don't deactivate as it might cause issues

echo "Build process completed."