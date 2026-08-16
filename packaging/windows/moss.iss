; Moss Windows installer (Inno Setup)
#define MyAppName "Moss"
#ifndef MyAppVersion
  #define MyAppVersion "0.2.2"
#endif
#define MyAppPublisher "Moss"
#define MyAppURL "https://github.com/LostSaki/Moss"
#ifdef SourceExe
  #define MySourceExe SourceExe
#else
  #define MySourceExe "..\..\dist\Moss.exe"
#endif

[Setup]
AppId={{8F3A2C1B-9E47-4D6A-B105-2A7E9C4D8F01}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\..\dist
OutputBaseFilename=Moss-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\Moss.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MySourceExe}"; DestDir: "{app}"; DestName: "Moss.exe"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\Moss.exe"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\Moss.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Moss.exe"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
