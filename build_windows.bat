
@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ========================================================
echo PDF Assignment Marker v11.1.2 - Windows Release Builder
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

.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --onedir --name "PDF_Assignment_Marker" --icon "assets\PDF_Assignment_Marker.ico" --add-data "assets\PDF_Assignment_Marker.ico;." --add-data "COPYING;." --collect-data spellchecker --collect-all pymupdf "source\pdf_assignment_marker.py"

if errorlevel 1 (echo ERROR: PyInstaller build failed & pause & exit /b 1)

if not exist "dist\PDF_Assignment_Marker\PDF_Assignment_Marker.exe" (echo ERROR: exe missing & pause & exit /b 1)

.venv\Scripts\python.exe "scripts\verify_build.py"
if errorlevel 1 (echo ERROR: Resource verification failed. Do not distribute. & pause & exit /b 1)

if not exist "Output" mkdir "Output"

copy /y "COPYING" "dist\PDF_Assignment_Marker\COPYING" >nul
copy /y "LICENSE" "dist\PDF_Assignment_Marker\LICENSE" >nul
copy /y "docs\THIRD_PARTY_NOTICES.md" "dist\PDF_Assignment_Marker\THIRD_PARTY_NOTICES.md" >nul
copy /y "assets\PDF_Assignment_Marker.ico" "dist\PDF_Assignment_Marker\PDF_Assignment_Marker.ico" >nul

powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Force -Path 'dist\PDF_Assignment_Marker' -DestinationPath 'Output\PDF_Assignment_Marker_v11.1.2_Windows_Portable.zip'"

if errorlevel 1 (echo ERROR: Portable ZIP failed & pause & exit /b 1)

echo.
echo Portable ZIP created in Output folder.

set "ISCC="

if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if defined ISCC (
  "%ISCC%" "installer\PDF_Assignment_Marker.iss"
  if errorlevel 1 (echo ERROR: Inno Setup compile failed & pause & exit /b 1)
  echo Windows installer created in Output folder.
) else (
  echo Inno Setup 6 not found: installer NOT built.
  echo Install Inno Setup 6, then compile installer\PDF_Assignment_Marker.iss
)

echo.
echo Generating SHA256 checksums...

powershell -NoProfile -Command "Get-ChildItem Output -File | Where-Object { $_.Extension -in '.exe', '.zip' } | ForEach-Object { '{0}  {1}' -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash,$_.Name } | Set-Content Output\SHA256SUMS.txt -Encoding ASCII"

if errorlevel 1 (echo ERROR: Checksum generation failed & pause & exit /b 1)

echo.
echo RELEASE OUTPUT FILES:
dir /b Output

echo.
echo IMPORTANT: Test installer and portable version before distribution.
pause
endlocal
