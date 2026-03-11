@echo off
setlocal enabledelayedexpansion
title Claude Workspace Setup Wizard
color 0F

echo.
echo  ============================================
echo   Claude ^& Antigravity Workspace Setup
echo  ============================================
echo.

:: -------------------------------------------------------
:: 1. Find Python
:: -------------------------------------------------------
set "PY="
where python >nul 2>&1 && set "PY=python"
if not defined PY (
    where python3 >nul 2>&1 && set "PY=python3"
)
if not defined PY (
    where py >nul 2>&1 && set "PY=py"
)
if not defined PY (
    echo  [ERROR] Python not found.
    echo.
    echo  Install Python 3.8+ from https://python.org
    echo  Make sure "Add Python to PATH" is checked during install.
    echo.
    pause
    exit /b 1
)

:: Verify Python version >= 3.8
for /f "tokens=2 delims= " %%v in ('!PY! --version 2^>^&1') do set "PYVER=%%v"
echo  Found Python !PYVER!

:: -------------------------------------------------------
:: 2. Detect available shells
:: -------------------------------------------------------
set "HAS_WSL=0"
set "HAS_GITBASH=0"
set "GITBASH_PATH="

where wsl >nul 2>&1 && (
    wsl --status >nul 2>&1 && set "HAS_WSL=1"
)

:: Check common Git Bash locations
if exist "C:\Program Files\Git\bin\bash.exe" (
    set "HAS_GITBASH=1"
    set "GITBASH_PATH=C:\Program Files\Git\bin\bash.exe"
)
if exist "C:\Program Files (x86)\Git\bin\bash.exe" (
    set "HAS_GITBASH=1"
    set "GITBASH_PATH=C:\Program Files (x86)\Git\bin\bash.exe"
)
:: Also check via PATH
if "!HAS_GITBASH!"=="0" (
    where bash >nul 2>&1 && (
        set "HAS_GITBASH=1"
        for /f "delims=" %%p in ('where bash 2^>nul') do (
            echo %%p | findstr /i "Git" >nul && set "GITBASH_PATH=%%p"
        )
    )
)

:: -------------------------------------------------------
:: 3. Present options
:: -------------------------------------------------------
echo.

:: Count options
set "OPT_COUNT=0"
set "OPT1="
set "OPT2="
set "OPT3="

if "!HAS_GITBASH!"=="1" (
    set /a OPT_COUNT+=1
    set "OPT!OPT_COUNT!=gitbash"
    echo  [!OPT_COUNT!] Git Bash  (RECOMMENDED - full features including hooks)
)
if "!HAS_WSL!"=="1" (
    set /a OPT_COUNT+=1
    set "OPT!OPT_COUNT!=wsl"
    echo  [!OPT_COUNT!] WSL       (full features including hooks)
)
set /a OPT_COUNT+=1
set "OPT!OPT_COUNT!=powershell"
echo  [!OPT_COUNT!] PowerShell (hooks will be skipped - everything else works)

echo.

:: If only PowerShell available, warn and auto-select
if "!OPT_COUNT!"=="1" (
    if "!OPT1!"=="powershell" (
        echo  No bash shell detected. Hooks require bash and will be skipped.
        echo  To get hooks too, install Git for Windows:
        echo  https://gitforwindows.org
        echo.
        echo  Continuing with PowerShell...
        echo.
        goto :run_powershell
    )
)

:: Auto-select if only one real option
if "!OPT_COUNT!"=="1" (
    set "CHOICE=1"
    goto :handle_choice
)

set /p "CHOICE=  Choose [1-!OPT_COUNT!]: "

:: Validate input
if not defined CHOICE set "CHOICE=1"
if !CHOICE! lss 1 set "CHOICE=1"
if !CHOICE! gtr !OPT_COUNT! set "CHOICE=1"

:handle_choice
set "SELECTED=!OPT%CHOICE%!"

if "!SELECTED!"=="gitbash" goto :run_gitbash
if "!SELECTED!"=="wsl" goto :run_wsl
if "!SELECTED!"=="powershell" goto :run_powershell

:: Fallback
goto :run_powershell

:: -------------------------------------------------------
:: 4. Launch in selected shell
:: -------------------------------------------------------

:run_gitbash
echo.
echo  Launching in Git Bash...
echo.
:: Convert Windows path to Unix-style for bash
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=!SCRIPT_DIR:\=/!"
:: Remove trailing slash
if "!SCRIPT_DIR:~-1!"=="/" set "SCRIPT_DIR=!SCRIPT_DIR:~0,-1!"
:: Convert drive letter (C: -> /c)
set "DRIVE=!SCRIPT_DIR:~0,1!"
call :lowercase DRIVE
set "UNIX_PATH=/!DRIVE!!SCRIPT_DIR:~2!"

"!GITBASH_PATH!" --login -c "cd '!UNIX_PATH!' && python install.py; echo; echo 'Press Enter to close...'; read"
goto :done

:run_wsl
echo.
echo  Launching in WSL...
echo.
:: Convert Windows path to WSL path
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=!SCRIPT_DIR:\=/!"
set "DRIVE=!SCRIPT_DIR:~0,1!"
call :lowercase DRIVE
set "WSL_PATH=/mnt/!DRIVE!!SCRIPT_DIR:~2!"
:: Remove trailing slash
if "!WSL_PATH:~-1!"=="/" set "WSL_PATH=!WSL_PATH:~0,-1!"

wsl bash -c "cd '!WSL_PATH!' && python3 install.py; echo; echo 'Press Enter to close...'; read"
goto :done

:run_powershell
echo.
echo  Running in PowerShell...
echo.
!PY! "%~dp0install.py"
echo.
pause
goto :done

:done
exit /b 0

:: -------------------------------------------------------
:: Helper: lowercase a variable
:: -------------------------------------------------------
:lowercase
set "_val=!%~1!"
for %%a in (a b c d e f g h i j k l m n o p q r s t u v w x y z) do (
    set "_val=!_val:%%a=%%a!"
)
set "%~1=!_val!"
goto :eof
