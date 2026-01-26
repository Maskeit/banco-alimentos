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
Source: "*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; \
Excludes: "__pycache__\*;*.pyc;venv\*;.git\*;.vscode\*"
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

Source: "dist\*"; DestDir: "{app}\dist"; Flags: recursesubdirs createallsubdirs
Source: "run_installed.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\screenshots"
Name: "{app}\venv"

[Icons]
Name: "{group}\Banco de Alimentos"; Filename: "{app}\run.bat"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\Banco de Alimentos"; Filename: "{app}\run.bat"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon
Name: "{group}\Desinstalar"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\install.bat"; StatusMsg: "Instalando dependencias..."; Flags: runhidden waituntilterminated
Filename: "{app}\run.bat"; Description: "Iniciar Banco de Alimentos"; Flags: nowait postinstall unchecked

[UninstallDelete]
Type: dirifempty; Name: "{app}"
Type: dirifempty; Name: "{app}\screenshots"

[Code]
function InitializeSetup(): Boolean;
var
  ErrorCode: Integer;
  PythonPath: string;
  ResultCode: Integer;
begin
  // Verificar si Python está instalado
  if not FileExists('C:\Python312\python.exe') and
     not FileExists('C:\Program Files\Python312\python.exe') and
     not FileExists('C:\Program Files (x86)\Python312\python.exe') then
  begin
    if MsgBox('Python 3.12 no está instalado. ¿Descargar e instalar?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      ShellExec('open', 'https://www.python.org/downloads/', '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode);
      MsgBox('Por favor instala Python 3.12 y vuelve a ejecutar este instalador.', mbInformation, MB_OK);
      Result := False;
    end
    else
    begin
      MsgBox('Python 3.12 es requerido. La instalación será cancelada.', mbError, MB_OK);
      Result := False;
    end;
  end
  else
  begin
    Result := True;
  end;
end;
