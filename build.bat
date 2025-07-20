@echo off
REM Build Batch Zipper/Unzipper GUI using PyInstaller
REM Author: Kelvin
REM Version: 1.0.0.0

REM Ensure you have pyinstaller installed: pip install pyinstaller
REM This script will use batch_zipper.spec and batch_zipper_icon.ico
REM and embed version info from version.txt

"C:\Users\Kelvin\AppData\Local\Programs\Python\Python310\python.exe" -m PyInstaller --clean --noconfirm batch_zipper.spec

pause
