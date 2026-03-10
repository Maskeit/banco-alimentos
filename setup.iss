[Setup]
AppName=Banco de Alimentos
AppVersion=1.0
AppPublisher=Banco de Alimentos
AppPublisherURL=https://www.example.com
AppSupportURL=https://www.example.com
AppUpdatesURL=https://www.example.com
DefaultDirName={autopf}\BancoDeAlimentos
DefaultGroupName=Banco de Alimentos
AllowNoIcons=yes
LicenseFile=LICENSE.txt
SetupIconFile=icon.ico
OutputDir=installer
OutputBaseFilename=BancoDeAlimentos-Setup

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Ejecutables empaquetados por PyInstaller (ya contienen todas las dependencias)
Source: "dist\BancoFlask\*"; DestDir: "{app}\dist\BancoFlask"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\BancoStreamlit\*"; DestDir: "{app}\dist\BancoStreamlit"; Flags: ignoreversion recursesubdirs createallsubdirs

; Archivos de soporte
Source: "run_installed.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\screenshots"

[Icons]
Name: "{group}\Banco de Alimentos"; Filename: "{app}\run_installed.bat"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\Banco de Alimentos"; Filename: "{app}\run_installed.bat"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon
Name: "{group}\Desinstalar"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\run_installed.bat"; Description: "Iniciar Banco de Alimentos"; Flags: nowait postinstall shellexec unchecked

[UninstallDelete]
Type: dirifempty; Name: "{app}"
Type: dirifempty; Name: "{app}\screenshots"

; Python ya no es necesario: PyInstaller empaqueta el intérprete dentro de dist\

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
