#define MyAppName "PDF Assignment Marker"
#define MyAppVersion "11.1.2"
#define MyAppExeName "PDF_Assignment_Marker.exe"
; IMPORTANT: For seamless updates from a previously released Inno installer,
; replace MyAppId with that release's EXACT AppId before publishing.
; Keep AppId unchanged for every subsequent version.
#define MyAppId "PDF_Assignment_Marker_Mohamed_Jameel"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher=JameelEdu
VersionInfoCompany=JameelEdu
UninstallDisplayIcon={app}\PDF_Assignment_Marker.ico
SetupIconFile=..\Assets\PDF_Assignment_Marker.ico

DefaultDirName={localappdata}\Programs\PDF Assignment Marker
DefaultGroupName={#MyAppName}
UninstallDisplayName={#MyAppName}
PrivilegesRequired=lowest
OutputDir=..\Output
OutputBaseFilename=PDF_Assignment_Marker_v11_1_2_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupLogging=yes
CloseApplications=no
RestartApplications=no
UsePreviousAppDir=yes
DisableProgramGroupPage=yes

[Files]
Source: "..\dist\PDF_Assignment_Marker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\Assets\PDF_Assignment_Marker.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\PDF Assignment Marker"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\PDF Assignment Marker"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch PDF Assignment Marker"; Flags: nowait postinstall skipifsilent

[Registry]
; This user-level key provides explicit version tracking for future installs.
Root: HKCU; Subkey: "Software\PDF Assignment Marker\Installer"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey

[Code]
const
  RunningMutex = 'Local\PDF_Assignment_Marker_Running';
  VersionKey = 'Software\PDF Assignment Marker\Installer';
  // The uninstall key is only a fallback when our own Version key isn't present.
  UninstallKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppId}_is1';

function WaitForAppToClose(IsUninstall: Boolean): Boolean;
var
  Response: Integer;
  ActionText: String;
begin
  Result := True;
  if IsUninstall then
    ActionText := 'uninstall'
  else
    ActionText := 'install or update';
  while CheckForMutexes(RunningMutex) do
  begin
    Response := MsgBox(
      'PDF Assignment Marker is currently running.' + #13#10 + #13#10 +
      'Close the application, then click Retry to ' + ActionText + '.' + #13#10 +
      'Click Cancel to stop.', mbError, MB_RETRYCANCEL);
    if Response <> IDRETRY then
    begin
      Result := False;
      Exit;
    end;
  end;
end;

function ReadInstalledVersion(var PreviousVersion: String): Boolean;
begin
  PreviousVersion := '';
  Result := RegQueryStringValue(HKCU, VersionKey, 'Version', PreviousVersion);
  if not Result then
    Result := RegQueryStringValue(HKCU, UninstallKey, 'DisplayVersion', PreviousVersion);
  Result := Result and (Trim(PreviousVersion) <> '');
end;


function NextVersionPart(var Version: String): Integer;
var
  DotPosition, I: Integer;
  Part: String;
begin
  DotPosition := Pos('.', Version);

  if DotPosition > 0 then
  begin
    Part := Copy(Version, 1, DotPosition - 1);
    Delete(Version, 1, DotPosition);
  end
  else
  begin
    Part := Version;
    Version := '';
  end;

  for I := 1 to Length(Part) do
  begin
    if (Part[I] < '0') or (Part[I] > '9') then
    begin
      Part := Copy(Part, 1, I - 1);
      Break;
    end;
  end;

  Result := StrToIntDef(Part, 0);
end;

function CompareVersions(
  const InstalledVersion, NewVersion: String): Integer;
var
  A, B: String;
  I, X, Y: Integer;
begin
  A := InstalledVersion;
  B := NewVersion;
  Result := 0;

  for I := 0 to 3 do
  begin
    X := NextVersionPart(A);
    Y := NextVersionPart(B);

    if X > Y then
    begin
      Result := 1;
      Exit;
    end;

    if X < Y then
    begin
      Result := -1;
      Exit;
    end;
  end;
end;


function InitializeSetup(): Boolean;
var
  PreviousVersion: String;
  CompareResult: Integer;
begin
  Result := WaitForAppToClose(False);
  if not Result then Exit;

  if ReadInstalledVersion(PreviousVersion) then
  begin
    CompareResult := CompareVersions(PreviousVersion, '{#MyAppVersion}');
    if CompareResult > 0 then
    begin
      MsgBox('A newer PDF Assignment Marker version (' + PreviousVersion +
        ') is already installed.' + #13#10 + #13#10 +
        'Version {#MyAppVersion} cannot replace a newer version. Installation cancelled.',
        mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if CompareResult < 0 then
      Result := MsgBox('PDF Assignment Marker version ' + PreviousVersion +
        ' is installed.' + #13#10 + #13#10 +
        'Update to version {#MyAppVersion}?', mbConfirmation, MB_YESNO) = IDYES
    else
      Result := MsgBox(
    'PDF Assignment Marker version {#MyAppVersion} is already installed.' +
    Chr(13) + Chr(10) + Chr(13) + Chr(10) +
    'Reinstall the same version?',
    mbConfirmation, MB_YESNO) = IDYES;
  end;
  // No tracked previous installation: normal Setup wizard continues.
end;

function InitializeUninstall(): Boolean;
begin
  Result := WaitForAppToClose(True);
end;
