#define AppName "PDF Assignment Marker"
#define AppVersion "11.0.0"
#define AppPublisher "Mohamed Jameel"
[Setup]
AppId={{B8C21934-103D-4516-AD34-5BE77C5B52CC}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
OutputDir=..\release
OutputBaseFilename=PDF_Assignment_Marker_v11.0.0_Windows_Setup
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\PDF Assignment Marker.exe
LicenseFile=..\COPYING
[Files]
Source: "..\dist\PDF Assignment Marker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\COPYING"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"
[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\PDF Assignment Marker.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\PDF Assignment Marker.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\PDF Assignment Marker.exe"; Description: "Launch PDF Assignment Marker"; Flags: nowait postinstall skipifsilent
