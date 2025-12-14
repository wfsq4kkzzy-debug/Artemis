#!/usr/bin/env bash
set -euo pipefail

# Přejdi do adresáře, kde je skript (kořen projektu)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

GREEN="\033[1;32m"; RED="\033[1;31m"; YELLOW="\033[1;33m"; BLUE="\033[1;34m"; NC="\033[0m"
log(){ printf "%b[DEPLOY]%b %s\n" "$BLUE" "$NC" "$1"; }
ok(){ printf "%b[OK]%b %s\n" "$GREEN" "$NC" "$1"; }
warn(){ printf "%b[WARN]%b %s\n" "$YELLOW" "$NC" "$1"; }
fail(){ printf "%b[FAIL]%b %s\n" "$RED" "$NC" "$1"; exit 1; }

# 1) Kontroly
command -v python3 >/dev/null 2>&1 || fail "Python3 nenalezen"
command -v git >/dev/null 2>&1 || fail "Git nenalezen"
PYV=$(python3 -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")')
log "Python: ${PYV}"

# 2) Venv
if [ ! -d .venv ]; then
  log "Vytvářím .venv"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate || fail "Nelze aktivovat .venv"
ok "Venv aktivní"

# 3) Závislosti
pip install --upgrade pip >/dev/null
pip install -r requirements.txt || fail "Instalace závislostí selhala"
ok "Závislosti nainstalovány"

# 4) .env
if [ ! -f .env ]; then
  cp .env.example .env
  warn "Vytvořen .env – DOPLŇTE hodnoty před spuštěním aplikace"
else
  ok ".env existuje"
fi

# 5) Záloha a adresář
mkdir -p backups
if [ -f library_budget.db ]; then
  TS=$(date +%Y%m%d_%H%M%S)
  cp library_budget.db "backups/library_budget_${TS}.db"
  ok "Záloha DB: backups/library_budget_${TS}.db"
fi

# 6) Inicializace DB (pouze pokud databáze neexistuje nebo je prázdná)
if [ -f init_db.py ]; then
  if [ ! -f library_budget.db ]; then
    log "Databáze neexistuje, spouštím init_db.py"
    python init_db.py || warn "init_db.py selhal"
  else
    log "Databáze již existuje, init_db.py přeskočen (ochrana dat)"
  fi
fi
for m in migrate_*.py migrate*.py; do
  [ -f "$m" ] || continue
  log "Spouštím migraci $m"
  python "$m" || warn "Migrace $m selhala (zkontrolujte log)"
done
ok "Migrace dokončeny"

# 7) Výstup
cat <<MSG
------------------------------------------------------------
První nasazení hotovo.
1) Ověřte a doplňte .env (SECRET_KEY, SQLALCHEMY_DATABASE_URI,...)
2) Spusťte aplikaci: source .venv/bin/activate && python run.py
3) Volitelně nastavte systemd službu (viz systemd/library_budget.service)
------------------------------------------------------------
MSG
ok "Hotovo"
