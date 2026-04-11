[Setup]
AppName=Stockometer
AppVersion=1.0
AppPublisher=Stockometer
DefaultDirName={pf}\Stockometer
DefaultGroupName=Stockometer
OutputDir=installer_output
OutputBaseFilename=StockometerSetup
Compression=lzma
SolidCompression=yes
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\Stockometer.exe

[Files]
Source: "dist\Stockometer.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Stockometer"; Filename: "{app}\Stockometer.exe"
Name: "{userdesktop}\Stockometer"; Filename: "{app}\Stockometer.exe"

[Run]
Filename: "{app}\Stockometer.exe"; Description: "Launch Stockometer"; Flags: nowait postinstall skipifsilent