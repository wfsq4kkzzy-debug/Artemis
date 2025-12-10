#!/usr/bin/env python3
"""
Skript pro vytvoření nové verze projektu

Použití:
    python create_version.py 0.72
    python create_version.py 0.72 --description "Nové funkce X, Y, Z"
"""

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Soubory a složky, které se NESMAJÍ kopírovat
EXCLUDE_PATTERNS = [
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '*.db',
    '*.sqlite',
    '*.sqlite3',
    '.env',
    '.DS_Store',
    'venv',
    'env',
    'versions',  # Nekopírujeme složku versions
    '.git',
    '.vscode',
    '.idea',
    '*.log',
    'instance',
    '.webassets-cache',
]

def should_exclude(path: Path, base_path: Path) -> bool:
    """Zkontroluje, zda by měl být soubor/složka vyloučen"""
    rel_path = path.relative_to(base_path)
    
    # Vyloučit složku versions
    if 'versions' in rel_path.parts:
        return True
    
    # Kontrola podle názvu
    name = path.name
    if name.startswith('.'):
        if name not in ['.env.example', '.gitignore']:
            return True
    
    # Kontrola přípon
    if path.is_file():
        ext = path.suffix
        if ext in ['.pyc', '.pyo', '.db', '.sqlite', '.sqlite3', '.log']:
            return True
    
    # Kontrola složek
    if path.is_dir():
        if name in ['__pycache__', 'venv', 'env', 'instance', '.webassets-cache', 'versions']:
            return True
    
    return False

def copy_version(version: str, description: str = None):
    """Zkopíruje aktuální stav projektu do složky versions/"""
    base_path = Path(__file__).parent
    version_path = base_path / 'versions' / version
    
    if version_path.exists():
        # V non-interactive režimu automaticky přepíšeme
        if not sys.stdin.isatty():
            print(f"⚠️  Verze {version} již existuje. Přepisuji...")
            shutil.rmtree(version_path)
        else:
            response = input(f"Verze {version} již existuje. Přepsat? (y/N): ")
            if response.lower() != 'y':
                print("Zrušeno.")
                return
            shutil.rmtree(version_path)
    
    version_path.mkdir(parents=True, exist_ok=True)
    
    print(f"📦 Vytváření verze {version}...")
    print(f"   Cíl: {version_path}")
    
    copied_files = 0
    copied_dirs = 0
    
    # Projdi všechny soubory a složky
    for item in base_path.iterdir():
        if should_exclude(item, base_path):
            continue
        
        dest = version_path / item.name
        
        try:
            if item.is_dir():
                shutil.copytree(item, dest, ignore=shutil.ignore_patterns(*EXCLUDE_PATTERNS))
                copied_dirs += 1
            else:
                shutil.copy2(item, dest)
                copied_files += 1
        except Exception as e:
            print(f"⚠️  Chyba při kopírování {item.name}: {e}")
    
    # Vytvoř README pro verzi
    readme_content = f"""# Verze {version}

**Datum vytvoření:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
    if description:
        readme_content += f"**Popis:** {description}\n\n"
    
    readme_content += f"""## 📦 Obsah

Tato složka obsahuje kompletní stav projektu v době vytvoření verze {version}.

## 🚀 Spuštění

### Jednoduché spuštění (doporučeno)

**macOS/Linux:**
```bash
cd versions/{version}
./start.sh
```

**Windows:**
```cmd
cd versions\\{version}
start.bat
```

Skript automaticky:
- ✅ Vytvoří virtuální prostředí (pokud neexistuje)
- ✅ Nainstaluje závislosti
- ✅ Vytvoří databázi (pokud neexistuje)
- ✅ Spustí aplikaci

### Ruční spuštění

```bash
cd versions/{version}
python3 -m venv venv
source venv/bin/activate  # nebo venv\\Scripts\\activate na Windows
pip install -r requirements.txt
python init_db.py
python dev.py
```

## 📝 Poznámky

- Databáze není součástí této verze (musí být vytvořena pomocí `init_db.py`)
- `.env` soubor není součástí (musí být vytvořen ručně)
- Virtuální prostředí není součástí (musí být vytvořeno)

---
**Vytvořeno pomocí:** `create_version.py`
"""
    
    readme_path = version_path / 'README.md'
    readme_path.write_text(readme_content, encoding='utf-8')
    
    # Vytvoř spustitelný start.sh (macOS/Linux)
    start_sh_content = f"""#!/bin/bash
# Spustitelný skript pro verzi {version}
# Automaticky nastaví prostředí a spustí aplikaci

set -e  # Zastavit při chybě

VERSION="{version}"
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   📚 Správa rozpočtu - Verze $VERSION                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Zkontroluj Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 není nainstalován!"
    exit 1
fi

echo "🐍 Python: $(python3 --version)"
echo ""

# Vytvoř venv, pokud neexistuje
if [ ! -d "venv" ]; then
    echo "📦 Vytváření virtuálního prostředí..."
    python3 -m venv venv
    echo "✅ Virtuální prostředí vytvořeno"
else
    echo "✅ Virtuální prostředí již existuje"
fi

# Aktivuj venv
echo "🔧 Aktivace virtuálního prostředí..."
source venv/bin/activate

# Aktualizuj pip
echo "⬆️  Aktualizace pip..."
pip install --quiet --upgrade pip

# Instaluj závislosti
if [ ! -f "venv/.deps_installed" ]; then
    echo "📥 Instalace závislostí..."
    pip install --quiet -r requirements.txt
    touch venv/.deps_installed
    echo "✅ Závislosti nainstalovány"
else
    echo "✅ Závislosti již nainstalovány"
fi

# Zkontroluj databázi
DB_FILE="instance/library_budget.db"
if [ ! -f "$DB_FILE" ]; then
    echo "💾 Databáze neexistuje, vytvářím..."
    python init_db.py
    echo "✅ Databáze vytvořena"
else
    echo "✅ Databáze již existuje"
fi

# Zkontroluj .env
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "⚠️  .env soubor neexistuje, kopíruji z .env.example..."
        cp .env.example .env
        echo "✅ .env soubor vytvořen (upravte ho podle potřeby)"
    else
        echo "⚠️  .env soubor neexistuje (vytvořte ho ručně pro AI asistent)"
    fi
fi

echo ""
echo "🚀 Spouštím aplikaci..."
echo "   🌐 http://127.0.0.1:5000"
echo "   ⏹️  Pro zastavení stiskněte Ctrl+C"
echo ""

# Spusť aplikaci
python dev.py
"""
    start_sh_path = version_path / 'start.sh'
    start_sh_path.write_text(start_sh_content, encoding='utf-8')
    os.chmod(start_sh_path, 0o755)  # Nastav jako spustitelný
    
    # Vytvoř spustitelný start.bat (Windows)
    start_bat_content = f"""@echo off
REM Spustitelný skript pro verzi {version} (Windows)
REM Automaticky nastaví prostředí a spustí aplikaci

set VERSION={version}
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
call venv\\Scripts\\activate.bat

REM Aktualizuj pip
echo ⬆️  Aktualizace pip...
python -m pip install --quiet --upgrade pip

REM Instaluj závislosti
if not exist "venv\\.deps_installed" (
    echo 📥 Instalace závislosti...
    pip install --quiet -r requirements.txt
    type nul > venv\\.deps_installed
    echo ✅ Závislosti nainstalovány
) else (
    echo ✅ Závislosti již nainstalovány
)

REM Zkontroluj databázi
if not exist "instance\\library_budget.db" (
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
"""
    start_bat_path = version_path / 'start.bat'
    start_bat_path.write_text(start_bat_content, encoding='utf-8')
    
    # Vytvoř VERSION soubor
    version_file = version_path / f'VERSION_{version}.md'
    if not version_file.exists():
        version_file.write_text(f"""# Verze {version}

## ✅ Status: Vytvořeno

Verze byla vytvořena {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}.

{description or "Žádný popis."}

## 📦 Soubory

- Všechny zdrojové soubory projektu
- Templates a statické soubory
- Konfigurační soubory

## 🚀 Další kroky

1. Otestovat funkčnost
2. Aktualizovat CHANGELOG.md
3. Vytvořit release notes
""", encoding='utf-8')
    
    print(f"\n✅ Verze {version} vytvořena!")
    print(f"   📁 Složka: {version_path}")
    print(f"   📄 Souborů: {copied_files}")
    print(f"   📂 Složek: {copied_dirs}")
    print(f"   🚀 Spustitelné soubory: start.sh, start.bat")
    print(f"\n💡 Pro spuštění této verze:")
    print(f"   cd versions/{version}")
    print(f"   ./start.sh          # macOS/Linux")
    print(f"   start.bat            # Windows")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Použití: python create_version.py <verze> [--description \"popis\"]")
        print("Příklad: python create_version.py 0.72 --description \"Nové funkce\"")
        sys.exit(1)
    
    version = sys.argv[1]
    description = None
    
    # Zpracuj argumenty
    if '--description' in sys.argv:
        idx = sys.argv.index('--description')
        if idx + 1 < len(sys.argv):
            description = sys.argv[idx + 1]
    
    copy_version(version, description)
