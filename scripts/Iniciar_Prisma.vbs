' Script de Inicialização Silenciosa do Prisma Converter
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
projectDir = fso.GetParentFolderName(scriptDir)

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = projectDir

' Encerra qualquer processo anterior travado na porta 5000 antes de iniciar
WshShell.Run "cmd /c for /f ""tokens=5"" %a in ('netstat -aon ^| findstr "":5000"" ^| findstr ""LISTENING""') do taskkill /PID %a /F", 0, True

' Verifica se o venv existe na pasta
If fso.FileExists(projectDir & "\venv\Scripts\python.exe") Then
    pythonExe = """" & projectDir & "\venv\Scripts\python.exe"""
Else
    pythonExe = "python"
End If

' Executa em segundo plano sem janela de console (0 = Oculto, False = Não espera terminar)
WshShell.Run pythonExe & " app.py", 0, False
