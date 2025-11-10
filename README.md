# Smart Visiting Card Reader

A Streamlit application that extracts contact information from business cards using OCR (Optical Character Recognition).

## Features

- Upload or capture images of business cards
- Extract contact information including name, email, phone, company, designation, website, and address
- Save extracted information to a database
- View and manage saved contacts
- Export data as CSV or vCard format

## Requirements

- Python 3.7+
- Tesseract OCR installed on your system

## Installation

1. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

2. Install Tesseract OCR:
   - On macOS: `brew install tesseract`
   - On Ubuntu: `sudo apt-get install tesseract-ocr`
   - On Windows: Download from [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)

## Usage

Run the application:
```
streamlit run card_reader3.py
```

## Deployment

This application is configured for deployment on Vercel with the provided `vercel.json` configuration file.