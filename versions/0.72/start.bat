@echo off
REM Spustitelný skript pro verzi 0.72 (Windows)
REM Automaticky nastaví prostředí a spustí aplikaci

set VERSION=0.72
cd /d "%~dp0"

echo ╔════════════════════════════════════════════════════════════════╗
echo ║   📚 Správa rozpočtu - Verze %VERSION%                              ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Zkontroluj Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python není nainstalován!
    pause
    exit /b 1
)

echo 🐍 Python:
python --version
echo.

REM Vytvoř venv, pokud neexistuje
if not exist "venv" (
    echo 📦 Vytváření virtuálního prostředí...
    python -m venv venv
    echo ✅ Virtuální prostředí vytvořeno
) else (
    echo ✅ Virtuální prostředí již existuje
)

REM Aktivuj venv
echo 🔧 Aktivace virtuálního prostředí...
call venv\Scripts\activate.bat

REM Aktualizuj pip
echo ⬆️  Aktualizace pip...
python -m pip install --quiet --upgrade pip

REM Instaluj závislosti
if not exist "venv\.deps_installed" (
    echo 📥 Instalace závislostí...
    pip install --quiet -r requirements.txt
    type nul > venv\.deps_installed
    echo ✅ Závislosti nainstalovány
) else (
    echo ✅ Závislosti již nainstalovány
)

REM Zkontroluj databázi
if not exist "instance\library_budget.db" (
    echo 💾 Databáze neexistuje, vytvářím...
    python init_db.py
    echo ✅ Databáze vytvořena
) else (
    echo ✅ Databáze již existuje
)

REM Zkontroluj .env
if not exist ".env" (
    if exist ".env.example" (
        echo ⚠️  .env soubor neexistuje, kopíruji z .env.example...
        copy .env.example .env >nul
        echo ✅ .env soubor vytvořen (upravte ho podle potřeby)
    ) else (
        echo ⚠️  .env soubor neexistuje (vytvořte ho ručně pro AI asistent)
    )
)

echo.
echo 🚀 Spouštím aplikaci...
echo    🌐 http://127.0.0.1:5000
echo    ⏹️  Pro zastavení stiskněte Ctrl+C
echo.

REM Spusť aplikaci
python dev.py

pause
