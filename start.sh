#!/bin/bash

# Správa rozpočtu Městské knihovny Polička
# Spustitelný skript pro spuštění aplikace

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Správa rozpočtu Městské knihovny Polička                ║"
echo "║  Inicializace...                                          ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Zkontroluj Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Chyba: Python3 není nainstalován"
    exit 1
fi

# Zkontroluj virtuální prostředí
if [ ! -d "venv" ]; then
    echo "📦 Vytváření virtuálního prostředí..."
    python3 -m venv venv
fi

# Aktivuj virtuální prostředí
echo "🔌 Aktivace virtuálního prostředí..."
source venv/bin/activate

# Instaluj dependencies
echo "📚 Instalace závislostí..."
pip install -q -r requirements.txt || pip install -q --no-binary markupsafe -r requirements.txt

# Inicializuj databázi, pokud neexistuje
if [ ! -f "library_budget.db" ]; then
    echo "🗄️  Inicializace databáze..."
    python3 init_db.py
fi

# Inicializuj AI asistenta
echo "🤖 Inicializace AI asistenta..."
python3 init_ai.py

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Správa rozpočtu Městské knihovny Polička                ║"
echo "║  http://localhost:5000                                    ║"
echo "║  Stiskni CTRL+C pro zastavení                             ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Spusť aplikaci
python3 run.py
