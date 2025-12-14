#!/usr/bin/env bash
set -euo pipefail
GREEN="\033[1;32m"; RED="\033[1;31m"; YELLOW="\033[1;33m"; BLUE="\033[1;34m"; NC="\033[0m"
log(){ printf "%b[TEST]%b %s\n" "$BLUE" "$NC" "$1"; }
ok(){ printf "%b[OK]%b %s\n" "$GREEN" "$NC" "$1"; }
fail(){ printf "%b[FAIL]%b %s\n" "$RED" "$NC" "$1"; exit 1; }

# Izolované prostředí v .test_env
TEST_DIR=.test_env
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"
cp -r . "$TEST_DIR" >/dev/null 2>&1 || true
cd "$TEST_DIR"

log "Spouštím first_deploy.sh (test)"
chmod +x first_deploy.sh deploy.sh backup_database.sh restore_database.sh
./first_deploy.sh || fail "first_deploy selhal"

log "Vytvářím testovací data (pokud init_db existuje)"
python - <<'PY'
try:
    from init_db import main
    main()
except Exception:
    pass
PY

log "Spouštím deploy.sh (test)"
./deploy.sh || fail "deploy selhal"

log "Test zálohy"
./backup_database.sh || fail "backup selhal"

ok "Testovací běh dokončen (artefakty v $TEST_DIR)"
