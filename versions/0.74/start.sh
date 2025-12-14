#!/bin/bash
# Spustitelný skript pro verzi 0.74
# Automaticky nastaví prostředí a spustí aplikaci

set -e  # Zastavit při chybě

VERSION="0.74"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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
