# Deployment průvodce (Library Budget)

Tento návod je pro správce (ne‑vývojáře). Postup je idempotentní – skripty lze spouštět opakovaně.

## Přehled
- Aplikace: Flask (Python), databáze SQLite (`library_budget.db`), závislosti `requirements.txt`
- Spuštění: `python run.py` (nebo systémová služba)
- Konfigurace: `.env` (viz `.env.example`)
- Migrace: vlastní python skripty (`init_db.py`, `migrate_*.py`)

## Požadavky na systém

### Minimální požadavky
- **OS**: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+), macOS 10.15+, Windows 10+
- **Python**: 3.11 nebo novější (doporučeno 3.11+)
- **Git**: 2.20+ (pro klonování repozitáře)
- **Paměť**: Minimálně 512 MB RAM (doporučeno 1 GB+)
- **Disk**: Minimálně 100 MB volného místa (pro databázi a závislosti)
- **Přístup**: Shell s oprávněními pro vytváření souborů a adresářů

### Instalace Pythonu podle OS

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3-pip git
```

#### CentOS/RHEL
```bash
sudo yum install python3.11 python3-pip git
# nebo pro novější verze:
sudo dnf install python3.11 python3-pip git
```

#### macOS
```bash
# Pomocí Homebrew
brew install python@3.11 git

# Nebo stáhněte z python.org
```

#### Windows
- Stáhněte Python 3.11+ z [python.org](https://www.python.org/downloads/)
- Během instalace zaškrtněte "Add Python to PATH"
- Git: stáhněte z [git-scm.com](https://git-scm.com/download/win)

## Použité technologie a knihovny

### Backend Framework
- **Flask 3.0.0** - Webový framework pro Python
  - Účel: HTTP server, routing, request handling, template rendering
  - Dokumentace: https://flask.palletsprojects.com/
  - Kompatibilita: Python 3.8+

### Databáze a ORM
- **SQLAlchemy >=2.0** - Python SQL toolkit a ORM
  - Účel: Databázové modely, dotazy, migrace
  - Dokumentace: https://docs.sqlalchemy.org/
  - Kompatibilita: Python 3.7+, podporuje SQLite, PostgreSQL, MySQL
- **Flask-SQLAlchemy 3.1.1** - Flask rozšíření pro SQLAlchemy
  - Účel: Integrace SQLAlchemy s Flask aplikací
  - Dokumentace: https://flask-sqlalchemy.palletsprojects.com/
  - Kompatibilita: Flask 2.0+, SQLAlchemy 2.0+

### Formuláře a validace
- **WTForms 3.1.1** - Flexibilní framework pro formuláře
  - Účel: Validace formulářů, CSRF ochrana
  - Dokumentace: https://wtforms.readthedocs.io/
  - Kompatibilita: Python 3.7+
- **Flask-WTF 1.2.1** - Flask rozšíření pro WTForms
  - Účel: Integrace WTForms s Flask, CSRF tokeny
  - Dokumentace: https://flask-wtf.readthedocs.io/
  - Kompatibilita: Flask 2.0+, WTForms 3.0+
- **email-validator 2.0.0** - Validace emailových adres
  - Účel: Validace emailových adres ve formulářích
  - Dokumentace: https://github.com/JoshData/python-email-validator
  - Kompatibilita: Python 3.7+

### Konfigurace a prostředí
- **python-dotenv 1.0.0** - Načítání proměnných prostředí z .env souboru
  - Účel: Správa konfigurace (API klíče, databázové URI, secret keys)
  - Dokumentace: https://github.com/theskumar/python-dotenv
  - Kompatibilita: Python 3.5+

### AI a externí API
- **anthropic 0.7.1** - Python SDK pro Claude API (Anthropic)
  - Účel: AI asistent v aplikaci (modul AI)
  - Dokumentace: https://github.com/anthropics/anthropic-sdk-python
  - Kompatibilita: Python 3.7+
  - Poznámka: Vyžaduje API klíč (nastaveno v .env)

### HTTP a síť
- **requests >=2.31.0** - HTTP knihovna pro Python
  - Účel: HTTP požadavky k externím API
  - Dokumentace: https://requests.readthedocs.io/
  - Kompatibilita: Python 3.7+

### Databáze
- **SQLite 3** - Vestavěná databáze (součást Pythonu)
  - Účel: Hlavní databáze aplikace (`library_budget.db`)
  - Dokumentace: https://www.sqlite.org/docs.html
  - Kompatibilita: Součást Python standardní knihovny
  - Poznámka: Pro produkci s vysokou zátěží zvažte PostgreSQL

### Frontend (statické soubory)
- **Bootstrap 5** - CSS framework (CDN)
  - Účel: Responsivní UI komponenty, grid systém
  - Dokumentace: https://getbootstrap.com/docs/5.0/
  - Kompatibilita: Moderní prohlížeče (Chrome, Firefox, Safari, Edge)
- **Font Awesome 6** - Ikony (CDN)
  - Účel: Ikony v UI
  - Dokumentace: https://fontawesome.com/docs
  - Kompatibilita: Všechny moderní prohlížeče

### Python standardní knihovny (součást Pythonu)
- `datetime` - Práce s daty a časy
- `json` - JSON serializace/deserializace
- `os`, `sys` - Systémové operace
- `collections` - Speciální datové struktury (defaultdict)
- `sqlite3` - SQLite databázový driver

## Kompatibilita verzí

| Komponenta | Minimální verze | Doporučená verze | Testováno na |
|------------|----------------|------------------|--------------|
| Python | 3.8 | 3.11+ | 3.11, 3.12 |
| Flask | 3.0.0 | 3.0.0 | 3.0.0 |
| SQLAlchemy | 2.0 | 2.0+ | 2.0.23 |
| Flask-SQLAlchemy | 3.1.1 | 3.1.1 | 3.1.1 |
| WTForms | 3.1.1 | 3.1.1 | 3.1.1 |
| Flask-WTF | 1.2.1 | 1.2.1 | 1.2.1 |

## Instalace závislostí

### Automatická instalace (doporučeno)
```bash
# Použijte deployment skripty (viz níže)
./first_deploy.sh
```

### Ruční instalace
```bash
# Vytvoření virtuálního prostředí
python3 -m venv .venv

# Aktivace venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Instalace závislostí
pip install --upgrade pip
pip install -r requirements.txt
```

### Ověření instalace
```bash
# Zkontrolujte nainstalované verze
pip list | grep -E "Flask|SQLAlchemy|WTForms"

# Očekávaný výstup:
# Flask             3.0.0
# Flask-SQLAlchemy  3.1.1
# Flask-WTF         1.2.1
# SQLAlchemy        2.0.23
# WTForms           3.1.1
```

## Řešení problémů s závislostmi

### Konflikt verzí
```bash
# Pokud máte konflikty, vytvořte nové venv
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Chybějící systémové knihovny (Linux)
```bash
# Ubuntu/Debian
sudo apt-get install python3-dev build-essential

# CentOS/RHEL
sudo yum install python3-devel gcc
```

### Problémy s pip
```bash
# Aktualizujte pip
python3 -m pip install --upgrade pip

# Použijte pip3 explicitně
pip3 install -r requirements.txt
```

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

### Python a závislosti
- **Chybí Python?**
  - Ubuntu/Debian: `sudo apt-get install python3.11 python3.11-venv python3-pip`
  - CentOS/RHEL: `sudo yum install python3.11 python3-pip`
  - macOS: `brew install python@3.11`
  - Windows: Stáhněte z [python.org](https://www.python.org/downloads/)

- **Chybí závislosti?**
  ```bash
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  ```

- **Chyba při instalaci některé knihovny?**
  - Zkontrolujte, že máte Python 3.11+
  - Aktualizujte pip: `pip install --upgrade pip`
  - Pro Linux: nainstalujte systémové závislosti (viz výše)

### Databáze
- **Migrace selhala?**
  - Obnovte DB z poslední zálohy: `./restore_database.sh`
  - Spusťte migraci znovu: `python init_db.py`

- **Databáze je zamčená?**
  - Zavřete všechny instance aplikace
  - Zkontrolujte procesy: `ps aux | grep python`
  - Pokud problém přetrvává, restartujte server

### Aplikace
- **Aplikace se nespustí?**
  - Zkontrolujte, že je venv aktivní: `which python` (mělo by ukázat .venv)
  - Zkontrolujte .env soubor: `cat .env`
  - Spusťte ručně: `source .venv/bin/activate && python run.py`

- **Aplikace nespadá do systemd?**
  - Zkontrolujte logy: `sudo journalctl -u library_budget -f`
  - Zkontrolujte konfiguraci: `cat /etc/systemd/system/library_budget.service`
  - Spusťte ručně pro test: `source .venv/bin/activate && python run.py`

- **Port 5000 je obsazený?**
  ```bash
  # Najděte proces
  lsof -i :5000  # Linux/macOS
  netstat -ano | findstr :5000  # Windows
  
  # Nebo změňte port v run.py
  ```

### AI modul
- **AI asistent nefunguje?**
  - Zkontrolujte API klíč v `.env`: `ANTHROPIC_API_KEY=...`
  - Ověřte připojení k internetu
  - Zkontrolujte logy aplikace pro chybové hlášky

### Obecné problémy
- **Permission denied při spuštění skriptů?**
  ```bash
  chmod +x first_deploy.sh deploy.sh backup_database.sh restore_database.sh
  ```

- **Git pull selhává?**
  - Zkontrolujte připojení k internetu
  - Ověřte oprávnění k repozitáři
  - Zkuste: `git fetch origin && git pull origin main`

