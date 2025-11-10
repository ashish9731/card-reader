from setuptools import setup

APP = ['card_reader3.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['streamlit', 'PIL', 'pytesseract', 'pandas', 'numpy'],
    'includes': ['streamlit', 'PIL', 'pytesseract', 'pandas', 'numpy', 'io', 'base64', 'os', 're', 'tempfile'],
    'excludes': ['tkinter'],
    'iconfile': 'app_icon.icns',  # You'll need to create this icon file
    'plist': {
        'CFBundleName': 'Smart Visiting Card Reader',
        'CFBundleDisplayName': 'Smart Visiting Card Reader',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2023 Your Name'
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)