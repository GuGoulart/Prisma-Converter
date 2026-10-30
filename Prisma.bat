@echo off
chcp 65001 >nul
title Prisma Converter - Central de Controle
color 0B
cd /d "%~dp0"

if "%1"=="--start" goto START
if "%1"=="--stop" goto STOP
if "%1"=="--shortcut" goto SHORTCUT
if "%1"=="--install" goto INSTALL

:MENU
cls
echo.
echo  =============================================================================
echo.
echo     ██████╗ ██████╗ ██╗███████╗███╗   ███╗ █████╗
echo     ██╔══██╗██╔══██╗██║██╔════╝████╗ ████║██╔══██╗
echo     ██████╔╝██████╔╝██║███████╗██╔████╔██║███████║
echo     ██╔═══╝ ██╔══██╗██║╚════██║██║╚██╔╝██║██╔══██║
echo     ██║     ██║  ██║██║███████║██║ ╚═╝ ██║██║  ██║
echo     ╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝
echo.
echo           CONVERSOR UNIVERSAL ^& FERRAMENTAS DE ARQUIVOS
echo.
echo  =============================================================================
echo.
echo    [1]  Iniciar o Prisma Converter
echo    [2]  Encerrar o Prisma Converter
echo    [3]  Criar atalho na Area de Trabalho
echo    [4]  Instalar ou atualizar dependencias
echo    [0]  Sair
echo.
echo  =============================================================================
echo.
set /p opcao=" Escolha uma opcao [0-4]: "

if "%opcao%"=="1" goto START
if "%opcao%"=="2" goto STOP
if "%opcao%"=="3" goto SHORTCUT
if "%opcao%"=="4" goto INSTALL
if "%opcao%"=="0" exit /b
goto MENU

:START
if not exist "venv\Scripts\python.exe" call :SETUP || goto FIM
if not exist "%USERPROFILE%\Desktop\Prisma Converter.lnk" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\criar_atalho.ps1" >nul 2>&1
)
wscript.exe "%~dp0scripts\Iniciar_Prisma.vbs"
exit /b

:STOP
rem O PID identifica o processo do Prisma: nada de encerrar outro programa que use a porta.
if exist "instance\prisma.pid" (
    set /p PID=<"instance\prisma.pid"
    setlocal enabledelayedexpansion
    taskkill /PID !PID! /T /F >nul 2>&1
    endlocal
    del "instance\prisma.pid" >nul 2>&1
    echo Prisma encerrado.
) else (
    echo O Prisma nao esta em execucao.
)
timeout /t 2 >nul
if "%1"=="--stop" exit /b
goto MENU

:SHORTCUT
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\criar_atalho.ps1"
echo Atalho criado na Area de Trabalho.
timeout /t 2 >nul
if "%1"=="--shortcut" exit /b
goto MENU

:INSTALL
call :SETUP
pause
if "%1"=="--install" exit /b
goto MENU

:SETUP
echo Preparando o ambiente (pode levar alguns minutos na primeira vez)...
if not exist "venv\Scripts\python.exe" (
    python -m venv venv
    if errorlevel 1 (
        echo Nao foi possivel criar o ambiente. Instale o Python 3.11 ou superior: https://www.python.org/downloads/
        exit /b 1
    )
)
"venv\Scripts\python.exe" -m pip install --upgrade pip -q
"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Falha ao instalar as dependencias.
    exit /b 1
)
exit /b 0

:FIM
pause
exit /b 1
