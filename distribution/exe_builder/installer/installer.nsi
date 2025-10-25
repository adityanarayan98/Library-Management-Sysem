;NSIS Installer Script for Library Management System
;This script creates a professional Windows installer

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"

;General Configuration
Name "Library Management System"
OutFile "LibraryManagementSystem-Setup.exe"
Unicode True
InstallDir "$PROGRAMFILES\Library Management System"
InstallDirRegKey HKCU "Software\LibraryManagementSystem" ""
RequestExecutionLevel admin

;Modern UI Configuration
!define MUI_ABORTWARNING
!define MUI_ICON "installer.ico"
!define MUI_UNICON "uninstaller.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "header.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "wizard.bmp"

;Version Information
VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "Library Management System"
VIAddVersionKey "CompanyName" "Aditya Narayan Sahoo"
VIAddVersionKey "FileVersion" "1.0.0.0"
VIAddVersionKey "ProductVersion" "1.0.0.0"
VIAddVersionKey "FileDescription" "Professional Library Management System"

;Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "license.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

;Languages
!insertmacro MUI_LANGUAGE "English"

;Installer Sections
Section "Install" SecInstall

    SetOutPath "$INSTDIR"

    ;Stop application if running
    Call StopApplication

    ;Create installation directory
    CreateDirectory "$INSTDIR"
    CreateDirectory "$INSTDIR\data"
    CreateDirectory "$INSTDIR\backups"

    ;Copy main files
    File /r "library_management\dist\LibraryManagementSystem\*.*"

    ;Copy additional files
    File "library_management\run_standalone.py"
    File "library_management\requirements.txt"
    File "README.md"

    ;Create data directories
    CreateDirectory "$INSTDIR\data\instance"
    CreateDirectory "$INSTDIR\data\backups"

    ;Create start menu entries
    CreateDirectory "$SMPROGRAMS\Library Management System"

    ;Create shortcuts
    CreateShortCut "$DESKTOP\Library Management System.lnk" "$INSTDIR\LibraryManagementSystem.exe" "" "$INSTDIR\LibraryManagementSystem.exe" 0
    CreateShortCut "$SMPROGRAMS\Library Management System\Library Management System.lnk" "$INSTDIR\LibraryManagementSystem.exe" "" "$INSTDIR\LibraryManagementSystem.exe" 0
    CreateShortCut "$SMPROGRAMS\Library Management System\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0

    ;Store installation folder
    WriteRegStr HKCU "Software\LibraryManagementSystem" "" $INSTDIR

    ;Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ;Write registry keys for Windows
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LibraryManagementSystem" "DisplayName" "Library Management System"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LibraryManagementSystem" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LibraryManagementSystem" "DisplayVersion" "1.0.0"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LibraryManagementSystem" "Publisher" "Aditya Narayan Sahoo"
    WriteRegDWord HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LibraryManagementSystem" "NoModify" 1
    WriteRegDWord HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LibraryManagementSystem" "NoRepair" 1

    ;Start application after installation (optional)
    ;Exec '"$INSTDIR\LibraryManagementSystem.exe"'

SectionEnd

;Uninstaller Section
Section "Uninstall"

    ;Stop application if running
    Call un.StopApplication

    ;Remove shortcuts
    Delete "$DESKTOP\Library Management System.lnk"
    Delete "$SMPROGRAMS\Library Management System\Library Management System.lnk"
    Delete "$SMPROGRAMS\Library Management System\Uninstall.lnk"
    RMDir "$SMPROGRAMS\Library Management System"

    ;Remove files and directories
    RMDir /r "$INSTDIR"

    ;Remove registry keys
    DeleteRegKey HKCU "Software\LibraryManagementSystem"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LibraryManagementSystem"

SectionEnd

;Functions
Function StopApplication
    ;Check if application is running and stop it
    nsExec::Exec 'taskkill /F /IM "LibraryManagementSystem.exe" /T'
FunctionEnd

Function un.StopApplication
    ;Check if application is running and stop it
    nsExec::Exec 'taskkill /F /IM "LibraryManagementSystem.exe" /T'
FunctionEnd

;Modern UI Description
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecInstall} "Installs the Library Management System application and creates shortcuts."
!insertmacro MUI_FUNCTION_DESCRIPTION_END

;EOF
