' SpotiSync Silent Startup Launcher
' Runs the startup check completely invisible in background and terminates immediately.
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")
strDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
strPsScript = strDir & "\SpotifyAutoManager.ps1"
strCommand = "powershell.exe -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File """ & strPsScript & """ -StartupSilent"

' Run invisible (0 = hidden window, False = don't wait if not needed)
objShell.Run strCommand, 0, True
