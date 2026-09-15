Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

strScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
strProjectDir = FSO.GetParentFolderName(strScriptDir)

WshShell.CurrentDirectory = strProjectDir

strPython = "python"
If FSO.FileExists(strProjectDir & "\venv\Scripts\python.exe") Then
    strPython = """" & strProjectDir & "\venv\Scripts\python.exe"""
End If

' Executa em segundo plano sem janela de prompt (0 = oculto)
WshShell.Run strPython & " app.py", 0, False
