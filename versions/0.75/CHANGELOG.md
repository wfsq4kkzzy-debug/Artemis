# CHANGELOG

## [0.74] - 2025-12-10

### 🏗️ Modulární architektura
- ✅ **Kompletní refaktoring** - projekt rozdělen do modulů
- ✅ **Core modul** - základní funkce (db, config)
- ✅ **Budget modul** - modely, routes, executor
- ✅ **Projects modul** - modely, routes, executor
- ✅ **Personnel modul** - modely, routes
- ✅ **AI modul** - modely, routes, executor
- ✅ **Hub aplikace** - `app.py` pouze inicializuje a registruje moduly

### 📁 Nová struktura
```
library_budget/
├── app.py                    # Hub
├── core/                     # Základní funkce
├── modules/
│   ├── budget/              # Modul Rozpočet
│   ├── projects/            # Modul Projekty
│   ├── personnel/           # Modul Personální
│   └── ai/                  # Modul AI
└── models.py                # Zpětná kompatibilita
```

### 🔧 Technické změny
- Všechny modely rozděleny do modulů
- Všechny routes přesunuty do blueprintů
- Všechny executory přesunuty do modulů
- Importy aktualizovány (relativní pro moduly)
- Templates aktualizovány (nové názvy blueprintů)
- Zpětná kompatibilita zachována

### 📦 Aktualizované soubory
- `app.py` - hub aplikace
- `core/` - nová složka
- `modules/` - nová struktura modulů
- `models.py` - centralizované importy
- `forms.py` - lazy importy
- Všechny templates - aktualizované url_for

---

## [0.73.1] - 2025-12-10

### 🔄 Přepracování rozpočtu projektu
- ✅ **Nová logika** - Projekt má jeden celkový rozpočet (jedno číslo)
- ✅ **Zjednodušené výdaje** - Bez kategorií, jen výdaje k projektu
- ✅ **Editovatelnost** - Rozpočet i výdaje lze upravit a smazat
- ✅ **Vizuální prvky** - Progress bary, barevné kódování, přehledy
- ✅ **AI podpora** - Všechny operace zvládá AI agent

### 🏗️ Backend změny
- Přidáno pole `rozpocet` do modelu `Projekt`
- Nové metody v `ProjectExecutor`: `set_project_budget`, `update_expense`, `delete_expense`
- Odstraněna závislost na kategoriích ve výdajích
- Výdaje se počítají pouze do aktuálního data

### 🎨 Frontend změny
- Nová šablona `rozpocet.html` - nastavení rozpočtu
- Nová šablona `vydaje.html` - správa výdajů s editací
- Nová šablona `upravit_vydaj.html` - úprava výdaje
- Vylepšený detail projektu s vizualizací rozpočtu

### 🤖 AI Agent
- Nové příkazy: `set_project_budget`, `update_project_expense`, `delete_project_expense`
- Automatická detekce příkazů pro nastavení rozpočtu
- Podpora editace a mazání výdajů přes AI

### 📦 Aktualizované soubory
- `models.py` - Přidáno pole `rozpocet` do `Projekt`
- `project_executor.py` - Nové metody pro správu rozpočtu a výdajů
- `project_routes.py` - Nové routes pro editaci
- `templates/projekty/*.html` - Nové a upravené šablony
- `ai_executor.py` - Nové příkazy pro AI
- `ai_assistant.py` - Detekce nových příkazů

---

## [0.73] - 2025-12-10

### 📦 Záloha
- ✅ **Verze 0.73 vytvořena** - Záloha aktuálního stavu před dalšími změnami
- ✅ Kompletní záloha všech zdrojových souborů
- ✅ Dokumentace a konfigurační soubory

---

## [0.72] - 2025-12-10

### 🔧 Systém verzování
- ✅ **Nový systém verzování** - Každá verze se ukládá do složky `versions/`
- ✅ **Skript pro vytváření verzí** - `create_version.py` pro snadné vytváření nových verzí
- ✅ **Dokumentace verzí** - Každá verze má vlastní README a VERSION soubor

### 📦 Struktura
- Složka `versions/0.72/` obsahuje kompletní stav projektu
- Automatické vyloučení nepotřebných souborů (databáze, cache, venv)
- README pro každou verzi s instrukcemi

### 🚀 Použití
```bash
# Vytvořit novou verzi
python create_version.py 0.73 --description "Popis změn"

# Spustit konkrétní verzi
cd versions/0.72
python dev.py
```

---

## [0.71] - 2025-12-10

### ✨ Nové funkce
- 🤖 **AI Asistent** - Chat s Claude AI pro pomoc
- 📝 **Setup formulář** - Snadné zadání Anthropic API klíče
- 💾 **Paměť konverzací** - Všechny zprávy se ukládají
- 📚 **Znalostní databáze** - AI zná procedury knihovny
- 🎯 **Personální pomoc** - Jeden chat pro tebe

### 🏗️ Backend změny
- Nový modul `ai_assistant.py` s Claude API
- 6 nových databázových modelů
- `AIAssistantService` třída pro komunikaci
- 3 nové API endpoints
- Setup endpoint pro uložení API klíče

### 🎨 Frontend změny
- Nová chat stránka s single-window interface
- Setup formulář s instrukcemi
- Integration do hlavního menu
- Real-time chat s loading indicatorem

### 🔧 Technické
- Anthropic SDK `0.28.0`
- SQLAlchemy >= 2.0
- Python 3.14 kompatibilita (s varováními)

### ⚠️ Známé problémy
- Token tracking nefunguje správně
- Python 3.14 varování o semaphores

### 📦 Aktualizované soubory
- `ai_assistant.py` - Nový
- `app.py` - Integrován AI blueprint
- `requirements.txt` - Přidán anthropic
- `templates/base.html` - Přidán odkaz na AI
- `templates/ai/` - Nové šablony
- `run.py` - Port změněn z 5000 na 5001

### 🚀 Spuštění
```bash
./start.sh
# nebo
source venv/bin/activate
python3 run.py
# Navštiv: http://localhost:5001/ai/
```

---

## [0.7] - 2025-12-09

### ✨ Nové funkce
- Kompletní rozpočet 2026
- Personální agenda
- Dashboard

---

Všechny verze: [Verze 0.71](VERSION_0.71.md) | [Release 0.71](RELEASE_0.71.md)
