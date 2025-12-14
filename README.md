# Správa rozpočtu Městské knihovny Polička

Webová aplikace pro správu rozpočtu knihovny s modulem na personální agendu a **AI asistentem pro pomoc**. Vytvořená v Pythonu s použitím Flasku.

## 🎯 Hlavní funkce

### 📊 Modul Rozpočet
- ✅ Kompletní rozpočet na rok 2026 s 22 účtovými skupinami a 73 položkami
- ✅ Přidávání, úpravy a mazání rozpočtových položek
- ✅ Evidování jednotlivých výdajů s detaily (datum, faktury, dodavatel)
- ✅ Sledování čerpání rozpočtu v reálném čase
- ✅ Dashboard s přehledem nákladů a výnosů
- ✅ Barevné rozlišení nákladů (červená) a výnosů (zelená)
- ✅ Filtrování podle účtů a typů

### 👥 Modul Personální agenda
- ✅ Správa zaměstnanců, brigádníků a osob na OON
- ✅ Evidence mezd, hodinových sazeb a pozic
- ✅ Propojení s rozpočtem (OON) pro sledování nákladů
- ✅ Kategorizace a filtrování osob

### 🤖 Modul AI Asistent **(Nový v 0.71!)**
- ✅ Chat s AI (Claude) pro pomoc a poradenství
- ✅ Setup formulář pro API klíč
- ✅ Paměť konverzací
- ✅ Znalostní databáze procedur
- ✅ Personalizované odpovědi

## 🛠️ Technologický stack

| Komponenta | Technologie |
|-----------|------------|
| Backend | Flask 3.0 |
| ORM | SQLAlchemy 2.1 |
| Formuláře | WTForms 3.1 |
| Frontend | Bootstrap 5 |
| Databáze | SQLite 3 |
| CSS | Bootstrap + Custom CSS |

## 💾 Databázové modely

### 1. UctovaSkupina (Účtová skupina)
```python
- id: int (primární klíč)
- ucet: str (např. "501", "521")
- nazev: str (název skupiny)
- typ: str ("naklad" nebo "vynos")
- polozky: relationship (vazba na RozpoctovaPolozka)
```

### 2. RozpoctovaPolozka (Rozpočtová položka)
```python
- id: int (primární klíč)
- rok: int (default 2026)
- uctova_skupina_id: int (foreign key)
- analyticky_ucet: str (např. "30", "31")
- nazev: str (název položky)
- rozpocet: Decimal (rozpočtovaná částka)
- poznamka: str (volné poznámky)
- vydaje: relationship (vazba na Vydaj)
```

### 3. Vydaj (Výdaj)
```python
- id: int (primární klíč)
- rozpoctova_polozka_id: int (foreign key)
- castka: Decimal (výše výdaje)
- datum: DateTime (datum výdaje)
- popis: str (popis výdaje)
- cis_faktury: str (číslo faktury)
- dodavatel: str (dodavatel)
```

### 4. ZamestnanecAOON (Zaměstnanec/OON)
```python
- id: int (primární klíč)
- jmeno, prijmeni: str (jméno a příjmení)
- typ: str ("zamestnanec", "brigadnik", "oon")
- ic_dph: str (IČ/DIČ)
- pozice: str (pracovní pozice)
- hodinova_sazba: Decimal (sazba za hodinu)
- mesicni_plat: Decimal (měsíční plat)
- datum_zapojeni: DateTime (od kdy je osoba zapojená)
- aktivni: bool (zda je osoba aktivní)
```

## 📦 Instalace a spuštění

### Předpoklady
- Python 3.8 nebo novější
- pip
- macOS / Linux / Windows

### Krok 1: Klonování projektu
```bash
git clone <repository-url>
cd library_budget
```

### Krok 2: Vytvoření virtuálního prostředí
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Krok 3: Instalace závislostí
```bash
pip install -r requirements.txt
```

### Krok 4: Inicializace databáze
```bash
python init_db.py
```

**Výstup:**
```
Stará databáze smazána...
Nové tabulky vytvořeny...
✓ Databáze inicializována!
✓ Účtových skupin: 22
✓ Rozpočtových položek: 73

📊 Souhrn rozpočtu 2026:
  Celkové náklady: 7,697,240 Kč
  Celkové výnosy:  7,697,240 Kč
  Bilance:         0 Kč
```

### Krok 5: Spuštění aplikace
```bash
# Možnost 1 - Pomocí dev.py
python dev.py

# Možnost 2 - Pomocí run.py
python run.py

# Možnost 3 - Přímé spuštění
python -c "from app import app; app.run(debug=True, port=5000)"
```

**Aplikace je dostupná na:**
```
http://127.0.0.1:5000
```

## 📁 Struktura projektu

```
library_budget/
│
├── 📄 Hlavní soubory
│   ├── app.py                 # Flask aplikace a route handlery
│   ├── models.py              # SQLAlchemy databázové modely
│   ├── forms.py               # WTForms formuláře
│   ├── config.py              # Konfigurace aplikace
│   ├── init_db.py             # Inicializace databáze s daty
│   ├── dev.py                 # Vývojový skript
│   ├── run.py                 # Produkční spuštění
│   ├── requirements.txt       # Python závislosti
│   ├── README.md              # Tato dokumentace
│   └── .gitignore             # Git ignore soubor
│
├── 📂 templates/              # HTML šablony
│   ├── base.html              # Základní šablona (navbar, footer)
│   ├── dashboard.html         # Přehled rozpočtu
│   ├── rozpocet/              # Modul rozpočet
│   │   ├── seznam.html        # Seznam všech položek
│   │   ├── nova_polozka.html  # Formulář na novou položku
│   │   ├── upravit_polozku.html # Formulář na úpravu
│   │   ├── detail_polozky.html   # Detail s výdaji
│   │   └── pridat_vydaj.html     # Formulář na výdaj
│   ├── personalni/            # Modul personální agenda
│   │   ├── seznam.html        # Seznam osob
│   │   └── pridat.html        # Přidání nové osoby
│   └── errors/                # Chybové stránky
│       ├── 404.html           # Stránka nenalezena
│       └── 500.html           # Chyba serveru
│
├── 📂 static/                 # Statické soubory
│   └── css/
│       └── style.css          # Vlastní CSS styly
│
├── 📂 __pycache__/            # Python cache (git ignore)
└── 📂 instance/               # Instance folder (databáze)
    └── library_budget.db      # SQLite databáze
```

## 🚀 Použití aplikace

### Přehled rozpočtu (Dashboard)
- Zobrazuje shrnutí nákladů a výnosů
- Bilance rozpočtu
- Přehled všech účtových skupin
- Kliknutí na skupinu vede na filtrovaný seznam

### Seznam rozpočtu
- Kompletní seznam všech rozpočtových položek
- Filtrování podle typu (náklady/výnosy) a účtu
- Zobrazení rozpočtu, výdajů a zbytku pro každou položku
- Progress bar pro vizualizaci čerpání

### Detail položky
- Zobrazení všech informací o položce
- Seznam všech výdajů pro tuto položku
- Možnost přidávat nové výdaje
- Sledování čerpání rozpočtu

### Personální agenda
- Přehled všech zaměstnanců a osob na OON
- Filtrování podle typu (zaměstnanec, brigádník, OON)
- Zobrazení mezd a hodinových sazeb

## 🔍 Příklady dotazů v Flask shell

```bash
# Otevřít Flask shell
flask shell
```

```python
# Zobrazit všechny účtové skupiny
from models import UctovaSkupina
UctovaSkupina.query.all()

# Zobrazit položky pro konkrétní účet
polozky = RozpoctovaPolozka.query.join(UctovaSkupina).filter(
    UctovaSkupina.ucet == '521'
).all()

# Souhrn nákladů
from sqlalchemy import func
naklady = db.session.query(
    func.sum(RozpoctovaPolozka.rozpocet)
).join(UctovaSkupina).filter(
    UctovaSkupina.typ == 'naklad'
).scalar()

# Výdaje pro konkrétní položku
vydaje = Vydaj.query.filter_by(rozpoctova_polozka_id=1).all()

# Všichni aktivní zaměstnanci
lide = ZamestnanecAOON.query.filter_by(aktivni=True).all()
```

## 🔧 Konfigurační soubor (config.py)

```python
# Vývojová konfigurace (default)
DEBUG = True
TESTING = False

# Testovací konfigurace
# SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Produkční konfigurace
# DEBUG = False
# SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-key')
```

## 📋 Rozpočet 2026 - Struktury

### Náklady (účty 501-558)
- **501** - Spotřeba materiálu: 488,660 Kč
- **502** - Spotřeba energie: 311,000 Kč
- **504** - Prodané zboží: 10,000 Kč
- **508** - Změna stavu zásob: 10,000 Kč
- **511** - Opravy a udržování: 20,000 Kč
- **512** - Cestovné: 10,000 Kč
- **513** - Náklady na reprezentaci: 8,000 Kč
- **518** - Ostatní služby: 391,500 Kč
- **521** - Mzdové náklady: 4,320,000 Kč
- **524** - Sociální pojištění: 1,352,000 Kč
- **525** - Jiné sociální pojištění: 10,000 Kč
- **527** - Sociální náklady: 278,000 Kč
- **549** - Ostatní náklady: 30,000 Kč
- **551** - Odpisy: 308,080 Kč
- **558** - Tvorba fondů: 50,000 Kč

### Výnosy (účty 601-672)
- **601** - Prodej výrobků: 50,220 Kč
- **602** - Prodej služeb: 513,000 Kč
- **603** - Pronájem prostor: 98,000 Kč
- **604** - Prodej zásob: 60,000 Kč
- **648** - Čerpání fondů: 0 Kč
- **662** - Úroky: 50 Kč
- **672** - Provozní dotace: 6,976,970 Kč

## 🐛 Řešení problémů

### Chyba: "ModuleNotFoundError: No module named 'flask'"
```bash
# Zkontrolujte, zda je virtuální prostředí aktivované
# Znovu instalujte závislosti
pip install -r requirements.txt
```

### Chyba: "Database is locked"
```bash
# Zavřete všechny ostatní spuštěné instance aplikace
# Pokud problémy přetrvávají, odstraňte databázi:
rm library_budget.db
python init_db.py
```

### Port 5000 je již v použití
```bash
# Najděte proces na portu 5000
lsof -i :5000

# Nebo spusťte na jiném portu
# Upravte soubor dev.py a změňte port=5000 na port=5001
```

### SQLAlchemy chyba
```bash
# Aktualizujte SQLAlchemy
pip install -U SQLAlchemy
```

## 🚀 Budoucí rozšíření

### 1. Náhrávání faktur
- [ ] Upload PDF/obrázků fakttur
- [ ] Připojení faktury k výdaji
- [ ] Archiv faktuur

### 2. Reporty a analýzy
- [ ] Měsíční/čtvrtletní přehledy
- [ ] Grafy výdajů
- [ ] Export do Excelu/PDF

### 3. Integrací se mzdovým systémem
- [ ] Automatické výpočty odvodů
- [ ] Propojení s OON
- [ ] Reporting mezd

### 4. REST API
- [ ] Veřejné API pro třetí strany
- [ ] Mobilní aplikace
- [ ] WebSockets pro live updates

### 5. Autentizace a bezpečnost
- [ ] Login systém
- [ ] Role a oprávnění (admin, účetní, ředitel)
- [ ] Audit log
- [ ] HTTPS

### 6. Web deployment
- [ ] Nasazení na Heroku
- [ ] Nasazení na DigitalOcean
- [ ] Domain a SSL certifikát
- [ ] Email notifikace

## 📞 Kontakt a podpora

Pro otázky či problémy kontaktujte administrátora knihovny.

## 📄 Licence

MIT License - Všechny práva vyhrazena © 2024 Městská knihovna Polička

## 👨‍💻 Autor

Vytvořeno jako interní nástroj pro Městskou knihovnu Polička


## 🚀 Rychlý start (deployment)
- První nasazení: `./first_deploy.sh`
- Aktualizace: `./deploy.sh`
- Záloha DB: `./backup_database.sh`
- Obnova DB: `./restore_database.sh`
- Podrobný návod: `DEPLOYMENT.md`
