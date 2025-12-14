# Deployment průvodce (Library Budget)

Tento návod je pro správce (ne‑vývojáře). Postup je idempotentní – skripty lze spouštět opakovaně.

## Přehled
- Aplikace: Flask (Python), databáze SQLite (`library_budget.db`), závislosti `requirements.txt`
- Spuštění: `python run.py` (nebo systémová služba)
- Konfigurace: `.env` (viz `.env.example`)
- Migrace: vlastní python skripty (`init_db.py`, `migrate_*.py`)

## Požadavky
- OS: Linux/macOS/Windows (bash skripty testované na Linux/macOS)
- Python 3.11+
- Git
- Přístup k shellu a oprávnění měnit soubory

## První nasazení (first_deploy.sh)
1. Naklonujte repo: `git clone <REPO> && cd library_budget`
2. Spusťte: `./first_deploy.sh`
   - vytvoří venv, nainstaluje závislosti
   - zkopíruje `.env.example` na `.env` a vyzve k doplnění
   - inicializuje DB (`init_db.py` + migrační skripty pokud existují)
   - vytvoří `backups/` a první zálohu
   - vypíše, jak aplikaci spustit

## Aktualizace (deploy.sh)
1. Ujistěte se, že jste v kořeni projektu a venv aktivní.
2. Spusťte: `./deploy.sh`
   - vytvoří zálohu DB s timestampem
   - stáhne změny z gitu (`git pull`)
   - nainstaluje/aktualizuje závislosti
   - spustí migrační skripty
   - restartuje aplikaci (pokud je definován systemd service, jinak připomene ruční restart)

## Zálohy a obnova
- **Záloha**: `./backup_database.sh`
- **Obnova**: `./restore_database.sh` (interaktivně; před obnovením vytvoří safety zálohu)
- Zálohy jsou v `backups/`, starší než 30 dní se mažou.

## Testovací běh (test_deployment.sh)
- Vytvoří izolované prostředí, provede první deploy, vytvoří testovací data, zkusí update a zálohu/obnovu.
- Spuštění: `./test_deployment.sh`

## Služba (systemd ukázka)
- Ukázka konfigurace: `systemd/library_budget.service`
- Nainstalujte: `sudo cp systemd/library_budget.service /etc/systemd/system/` + `sudo systemctl daemon-reload`
- Start: `sudo systemctl enable --now library_budget`

## Rychlý tahák
- **První nasazení**: `./first_deploy.sh`
- **Aktualizace**: `./deploy.sh`
- **Záloha**: `./backup_database.sh`
- **Obnova**: `./restore_database.sh`
- **Dokumentace**: tento soubor

## Troubleshooting
- Chybí Python? `sudo apt-get install python3 python3-venv` (Debian/Ubuntu)
- Chybí závislosti? Zkuste `source .venv/bin/activate && pip install -r requirements.txt`
- Migrace selhala? Obnovte DB z poslední zálohy a spusťte migraci znovu.
- Aplikace nespadá do systemd? Spusťte ručně `source .venv/bin/activate && python run.py`

