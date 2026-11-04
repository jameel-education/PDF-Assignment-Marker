@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ========================================================
echo PDF Assignment Marker v11.0.1 - Windows Release Builder
echo ========================================================
if not exist "source\pdf_assignment_marker.py" (echo ERROR: source missing & pause & exit /b 1)
if not exist "assets\PDF_Assignment_Marker.ico" (echo ERROR: icon missing & pause & exit /b 1)
if not exist "COPYING" (echo ERROR: licence missing & pause & exit /b 1)
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 (echo ERROR: Python 3 not found or venv failed & pause & exit /b 1)
)
.venv\Scripts\python.exe -m pip install -r requirements-build.txt
if errorlevel 1 (echo ERROR: dependency installation failed & pause & exit /b 1)
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --onedir --name "PDF Assignment Marker" --icon "assets\PDF_Assignment_Marker.ico" --add-data "assets\PDF_Assignment_Marker.ico;." --add-data "COPYING;." --collect-data spellchecker --collect-all pymupdf "source\pdf_assignment_marker.py"
if errorlevel 1 (echo ERROR: PyInstaller build failed & pause & exit /b 1)
if not exist "dist\PDF Assignment Marker\PDF Assignment Marker.exe" (echo ERROR: exe missing & pause & exit /b 1)
.venv\Scripts\python.exe "scripts\verify_build.py"
if errorlevel 1 (echo ERROR: Resource verification failed. Do not distribute. & pause & exit /b 1)
if not exist "release" mkdir "release"
copy /y "COPYING" "dist\PDF Assignment Marker\COPYING" >nul
copy /y "LICENSE" "dist\PDF Assignment Marker\LICENSE" >nul
copy /y "docs\THIRD_PARTY_NOTICES.md" "dist\PDF Assignment Marker\THIRD_PARTY_NOTICES.md" >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Force -Path 'dist\PDF Assignment Marker' -DestinationPath 'release\PDF_Assignment_Marker_v11.0.1_Windows_Portable.zip'"
if errorlevel 1 (echo ERROR: Portable ZIP failed & pause & exit /b 1)
echo.
echo Portable ZIP created in release folder.
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if defined ISCC (
  "%ISCC%" "installer\PDF_Assignment_Marker.iss"
  if errorlevel 1 (echo ERROR: Inno Setup compile failed & pause & exit /b 1)
  echo Windows installer created in release folder.
) else (
  echo Inno Setup 6 not found: installer NOT built.
  echo Install Inno Setup 6, then compile installer\PDF_Assignment_Marker.iss
)
echo.
echo RELEASE OUTPUT FILES:
dir /b release
powershell -NoProfile -Command "Get-ChildItem release -File | Get-FileHash -Algorithm SHA256 | ForEach-Object { '{0}  {1}' -f $_.Hash,$_.Path } | Set-Content release\SHA256SUMS.txt"
echo.
echo IMPORTANT: Test installer and portable version before distribution.
pause
endlocal
