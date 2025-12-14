#!/usr/bin/env bash
set -euo pipefail

# Přejdi do adresáře, kde je skript (kořen projektu)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

GREEN="\033[1;32m"; RED="\033[1;31m"; YELLOW="\033[1;33m"; BLUE="\033[1;34m"; NC="\033[0m"
log(){ printf "%b[BACKUP]%b %s\n" "$BLUE" "$NC" "$1"; }
ok(){ printf "%b[OK]%b %s\n" "$GREEN" "$NC" "$1"; }
warn(){ printf "%b[WARN]%b %s\n" "$YELLOW" "$NC" "$1"; }
fail(){ printf "%b[FAIL]%b %s\n" "$RED" "$NC" "$1"; exit 1; }

DB_FILE=${DB_FILE:-library_budget.db}
BACKUP_DIR=backups
mkdir -p "$BACKUP_DIR"
TS=$(date +%Y%m%d_%H%M%S)
BACKUP="$BACKUP_DIR/backup_${TS}.db"

if [ -f "$DB_FILE" ]; then
  cp "$DB_FILE" "$BACKUP"
  ok "Záloha vytvořena: $BACKUP"
else
  fail "DB soubor $DB_FILE nenalezen"
fi

# Mazání starších záloh (30 dní)
find "$BACKUP_DIR" -type f -mtime +30 -name 'backup_*.db' -print -delete || warn "Čištění starých záloh selhalo"

# Log
echo "$(date '+%F %T') : $BACKUP" >> "$BACKUP_DIR/backup.log"
ok "Hotovo"
