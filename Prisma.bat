@echo off
title Prisma Converter - Central de Controle
color 0B
cd /d "%~dp0"

:: Garantir que o atalho exista na Área de Trabalho do usuário ao rodar
if not exist "%USERPROFILE%\Desktop\Prisma Converter.lnk" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\criar_atalho.ps1" >nul 2>&1
)

if "%1"=="--start" goto START_SILENT
if "%1"=="--stop" goto STOP_SERVER
if "%1"=="--shortcut" goto CREATE_SHORTCUT

:MENU
cls
echo.
echo  =============================================================================
echo.
echo     ██████╗ ██████╗ ██╗███████╗███╗   ███╗███╗   ██╗ ██████╗ 
echo     ██╔══██╗██╔══██╗██║██╔════╝████╗ ████║████╗  ██║██╔═══██╗
echo     ██████╔╝██████╔╝██║███████╗██╔████╔██║██╔██╗ ██║██║   ██║
echo     ██╔═══╝ ██╔══██╗██║╚════██║██║╚██╔╝██║██║╚██╗██║██║   ██║
echo     ██║     ██║  ██║██║███████║██║ ╚═╝ ██║██║ ╚████║╚██████╔╝
echo     ╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝ 
echo.
echo           ✦ CONVERSOR UNIVERSAL ^& FERRAMENTAS DE ARQUIVOS ✦
echo.
echo  =============================================================================
echo.
echo    [1]  Iniciar Prisma Converter (Modo Silencioso 1-Clique)
echo    [2]  Encerrar Servidor Local (Liberar Porta 5000)
echo    [3]  Criar/Atualizar Atalho na Area de Trabalho
echo    [0]  Sair
echo.
echo  =============================================================================
echo.
set /p opcao=" Escolha uma opcao [0-3]: "

if "%opcao%"=="1" goto START_SILENT
if "%opcao%"=="2" goto STOP_SERVER
if "%opcao%"=="3" goto CREATE_SHORTCUT
if "%opcao%"=="0" exit /b
goto MENU

:START_SILENT
cls
echo Iniciando o Prisma Converter...
if exist "scripts\Iniciar_Prisma.vbs" (
    wscript.exe "%~dp0scripts\Iniciar_Prisma.vbs"
) else (
    if exist "venv\Scripts\python.exe" (
        start "" /b "%~dp0venv\Scripts\python.exe" app.py
    ) else (
        start "" /b python app.py
    )
)
echo Pronto! Servidor iniciado em segundo plano.
timeout /t 2 >nul
exit /b

:STOP_SERVER
cls
echo Encerrando o servidor local do Prisma Converter...
taskkill /FI "WINDOWTITLE eq Prisma Converter*" /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo.
echo  =============================================================================
echo   Servidor encerrado com sucesso!
echo  =============================================================================
echo.
timeout /t 2 >nul
if "%1"=="--stop" exit /b
goto MENU

:CREATE_SHORTCUT
cls
echo Criando atalho do Prisma Converter na Area de Trabalho...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\criar_atalho.ps1"
echo.
echo  =============================================================================
echo   Atalho criado na Area de Trabalho com sucesso!
echo  =============================================================================
echo.
timeout /t 2 >nul
if "%1"=="--shortcut" exit /b
goto MENU
