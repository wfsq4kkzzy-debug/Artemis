#!/usr/bin/env bash
set -euo pipefail

# Přejdi do adresáře, kde je skript (kořen projektu)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

GREEN="\033[1;32m"; RED="\033[1;31m"; YELLOW="\033[1;33m"; BLUE="\033[1;34m"; NC="\033[0m"
log(){ printf "%b[RESTORE]%b %s\n" "$BLUE" "$NC" "$1"; }
ok(){ printf "%b[OK]%b %s\n" "$GREEN" "$NC" "$1"; }
warn(){ printf "%b[WARN]%b %s\n" "$YELLOW" "$NC" "$1"; }
fail(){ printf "%b[FAIL]%b %s\n" "$RED" "$NC" "$1"; exit 1; }

DB_FILE=${DB_FILE:-library_budget.db}
BACKUP_DIR=backups
[ -d "$BACKUP_DIR" ] || fail "Adresář $BACKUP_DIR neexistuje"

mapfile -t FILES < <(ls -1t $BACKUP_DIR/backup_*.db 2>/dev/null || true)
if [ ${#FILES[@]} -eq 0 ]; then
  fail "Žádné zálohy nenalezeny"
fi

echo "Dostupné zálohy:"; i=1
for f in "${FILES[@]}"; do
  echo "  [$i] $f"; i=$((i+1))
done
read -rp "Zadejte číslo zálohy k obnovení: " CH
[[ $CH =~ ^[0-9]+$ ]] || fail "Neplatný vstup"
IDX=$((CH-1))
[ $IDX -ge 0 ] && [ $IDX -lt ${#FILES[@]} ] || fail "Mimo rozsah"
TARGET=${FILES[$IDX]}

echo "⚠️  POZOR: dojde k přepsání $DB_FILE"; read -rp "Pokračovat? (yes/no) " CONF
[ "$CONF" = "yes" ] || fail "Zrušeno"

# Safety backup aktuální DB
if [ -f "$DB_FILE" ]; then
  TS=$(date +%Y%m%d_%H%M%S)
  SAFE="$BACKUP_DIR/backup_before_restore_${TS}.db"
  cp "$DB_FILE" "$SAFE"
  ok "Safety záloha: $SAFE"
fi

cp "$TARGET" "$DB_FILE"
ok "Obnoveno z $TARGET"

if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files | grep -q "library_budget.service"; then
  log "Restartuji službu"
  sudo systemctl restart library_budget.service || warn "Restart selhal, zkontrolujte log"
else
  warn "Restart proveďte ručně (pkill -f run.py && python run.py)"
fi

ok "Hotovo"
