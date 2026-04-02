[Setup]
AppId={{a9317892-bad6-4999-8720-b7c5534f57e4}}
AppName=Library Archive Tool
AppVersion=0.1.1
ArchitecturesInstallIn64BitMode=x64
; {autopf} magically resolves to "Program Files" for All Users, and "LocalAppData\Programs" for Current User
DefaultDirName={autopf}\ArchivePipeline
DefaultGroupName= Internet Archive Tool
OutputDir=Output
OutputBaseFilename=ArchivePipeline_Setup
Compression=lzma2
SolidCompression=yes

; THIS is the magic line that triggers the "All Users vs Current User" prompt
PrivilegesRequiredOverridesAllowed=dialog

[Dirs]
; We ONLY want to apply these global folder permissions IF they selected "All Users"
; The 'Check: IsAdminInstallMode' flag ensures this only runs when appropriate
Name: "{commonappdata}\ArchivePipeline"; Permissions: authusers-modify; Check: IsAdminInstallMode

[Files]
Source: "dist\ArchivePipeline\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[INI]
; This creates a tiny file called 'install_mode.ini' next to your .exe so Python knows what happened
Filename: "{app}\install_mode.ini"; Section: "Settings"; Key: "Mode"; String: "AllUsers"; Check: IsAdminInstallMode
Filename: "{app}\install_mode.ini"; Section: "Settings"; Key: "Mode"; String: "CurrentUser"; Check: not IsAdminInstallMode

[Icons]
Name: "{group}\Library Archive Tool"; Filename: "{app}\ArchivePipeline.exe"
; {autodesktop} dynamically resolves to the Public desktop or the User's personal desktop
Name: "{autodesktop}\Library Archive Tool"; Filename: "{app}\ArchivePipeline.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Code]
// Helper function to safely check both Admin and User registry hives
function IsImageMagickInstalled: Boolean;
begin
  // Check 64-bit and 32-bit paths, and check for both 'Current' and version-specific keys
  Result := RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\ImageMagick\Current') or
            RegKeyExists(HKEY_CURRENT_USER, 'SOFTWARE\ImageMagick\Current') or
            RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\ImageMagick') or
            RegValueExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\magick.exe', '');
end;

// InitializeSetup runs BEFORE the wizard even appears on screen
function InitializeSetup: Boolean;
var
  Response: Integer;
  ErrorCode: Integer;
begin
  Result := True; // Assume we will proceed by default

  // Loop indefinitely until ImageMagick is found or the user gives up
  while not IsImageMagickInstalled do
  begin
    // 1. The Warning
    Response := MsgBox(
      'ImageMagick is required to run the Archive Pipeline, but it was not found on your system.' + #13#10#13#10 +
      'Would you like to open the download page now?' + #13#10#13#10 +
      'CRITICAL: During the ImageMagick setup, you MUST check the box for "Install legacy utilities (e.g. convert)".',
      mbCriticalError, MB_YESNOCANCEL);

    if Response = idYes then
    begin
      // 2. Open their default web browser directly to the Windows downloads section
      ShellExec('open', 'https://imagemagick.org/script/download.php#windows', '', '', SW_SHOW, ewNoWait, ErrorCode);
      
      // 3. Pause our installer and wait for them to finish
      if MsgBox('Please complete the ImageMagick installation in the background.' + #13#10#13#10 + 
                'Click "Retry" once it has finished installing, or "Cancel" to abort.', 
                mbInformation, MB_RETRYCANCEL) = idCancel then
      begin
        Result := False; // Kills the installer
        Exit;
      end;
    end
    else if Response = idNo then
    begin
      // 4. They said NO to opening the browser. Just give them a chance to retry.
      if MsgBox('Click "Retry" once you have installed ImageMagick manually, or "Cancel" to abort setup.', 
                mbInformation, MB_RETRYCANCEL) = idCancel then
      begin
        Result := False;
        Exit;
      end;
    end
    else
    begin
      // 5. They clicked Cancel on the first prompt
      Result := False;
      Exit;
    end;
  end;
end;
