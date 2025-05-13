import os
import shutil
import subprocess
import sys

def clean_build_dirs():
    """Clean build and dist directories"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    if os.path.exists('faceID.spec'):
        os.remove('faceID.spec')

def build_executable():
    """Build the executable using PyInstaller"""
    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--name=faceID',
        '--windowed',  # No console window
        '--icon=NONE',  # Add icon path if you have one
        '--add-data=README.md;.',  # Include README
        '--hidden-import=PyQt6',
        '--hidden-import=face_recognition',
        '--hidden-import=cv2',
        '--hidden-import=numpy',
        '--hidden-import=pandas',
        '--hidden-import=sqlalchemy',
        '--hidden-import=psycopg2',
        '--hidden-import=PIL',
        '--hidden-import=openpyxl',
        '--hidden-import=docx',
        '--hidden-import=fpdf',
        '--noconfirm',  # Replace existing build
        'gui.py'  # Main script
    ]
    
    # Run PyInstaller
    subprocess.run(cmd, check=True)

def main():
    print("Starting build process...")
    
    # Clean previous builds
    print("Cleaning previous builds...")
    clean_build_dirs()
    
    # Build executable
    print("Building executable...")
    try:
        build_executable()
        print("\nBuild completed successfully!")
        print("\nExecutable location: dist/faceID/faceID.exe")
        print("\nTo run the application:")
        print("1. Navigate to the dist/faceID folder")
        print("2. Double-click faceID.exe")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 