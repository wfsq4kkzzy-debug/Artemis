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

command -v git >/dev/null 2>&1 || fail "Git nenalezen"
[ -d .venv ] || fail ".venv nenalezen – spusťte first_deploy.sh"
# shellcheck disable=SC1091
source .venv/bin/activate || fail "Nelze aktivovat .venv"

# 1) Záloha DB
mkdir -p backups
DB_FILE=${DB_FILE:-library_budget.db}
if [ -f "$DB_FILE" ]; then
  TS=$(date +%Y%m%d_%H%M%S)
  BAK="backups/library_budget_${TS}.db"
  cp "$DB_FILE" "$BAK"
  ok "Záloha DB: $BAK"
else
  warn "DB soubor $DB_FILE nenalezen, záloha vynechána"
fi

# 2) Git pull
log "Aktualizuji kód (git pull)"
git pull || fail "git pull selhal"

# 3) Závislosti
log "Aktualizuji závislosti"
pip install -r requirements.txt || fail "Instalace závislostí selhala"

# 4) Migrace
for m in migrate_*.py migrate*.py; do
  [ -f "$m" ] || continue
  log "Spouštím migraci $m"
  python "$m" || warn "Migrace $m selhala"
done
ok "Migrace dokončeny"

# 5) Restart / instrukce
if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files | grep -q "library_budget.service"; then
  log "Restartuji systemd službu"
  sudo systemctl restart library_budget.service || warn "Restart selhal, zkontrolujte log"
else
  warn "Restart proveďte ručně (např. pkill -f run.py && python run.py)"
fi

ok "Deploy hotov"
