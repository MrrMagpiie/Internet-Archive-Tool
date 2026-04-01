[Setup]
; The AppId is the secret to over-the-top updates. NEVER change this GUID once you release v1.0!
AppId={{a9317892-bad6-4999-8720-b7c5534f57e4}}
AppName=Library Archive Tool
AppVersion=1.0.0
AppPublisher=Your Library/Name
DefaultDirName={autopf}\LibraryArchive
DefaultGroupName=Library Archive Tool
OutputDir=Output
OutputBaseFilename=LibraryArchive_Setup
Compression=lzma2
SolidCompression=yes
; Require admin rights to install into Program Files
PrivilegesRequired=admin

[Files]
; This grabs your ENTIRE PyInstaller output folder and copies it
Source: "dist\LibraryArchive\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Creates the Start Menu shortcut
Name: "{group}\Library Archive Tool"; Filename: "{app}\LibraryArchive.exe"
; Creates the Desktop shortcut
Name: "{autodesktop}\Library Archive Tool"; Filename: "{app}\LibraryArchive.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked