# Windows release – final packaging procedure

1. Extract the release-source ZIP to a new folder on your Windows PC.
2. Install Inno Setup 6 if not already installed. Its default installation path allows automatic detection by the build script.
3. Double-click `build_windows.bat`. Wait for the final `RELEASE OUTPUT FILES` listing and inspect errors.
4. In `release/`, expect `PDF_Assignment_Marker_v11.0.0_Windows_Portable.zip` and, if Inno Setup compiled successfully, `PDF_Assignment_Marker_v11.0.0_Windows_Setup.exe`.
5. Test the portable package after extracting: `PDF Assignment Marker/PDF Assignment Marker.exe`, retaining `_internal` next to the executable.
6. Run the installer. Verify per-user installation, app launch, proper icon, About v11.0.0, Single View / Split View settings popup placement, Save As / Close, and uninstall.
7. Verify third-party licences and included Qt libraries before publishing; see `docs/THIRD_PARTY_NOTICES.md` and `docs/RELEASE_CHECKLIST.md`.
8. Publish separately: installer EXE, portable ZIP, and complete source ZIP. Generate or review `release/SHA256SUMS.txt` for the Windows artifacts.

**Do not distribute the build or internal test files as a final release until these checks pass.** No installer EXE is contained in this source archive; creating a genuine Windows executable requires running the provided scripts on Windows.
