# Verze 0.74 - Modulární architektura

**Datum:** 10. prosince 2025

## ✅ Status: Kompletní refaktoring

Kompletní přepracování projektu do modulární architektury pro lepší přehlednost a údržbu.

## 🎯 Nová modulární struktura

### Koncept
- **Hub aplikace** (`app.py`) - pouze inicializace a registrace modulů
- **Core** (`core/`) - základní funkce (databáze, konfigurace)
- **Moduly** (`modules/`) - samostatné moduly pro každou funkcionalitu
- **Oddělené zodpovědnosti** - každý modul má svou složku s routes, models, executor

### Struktura

```
library_budget/
├── app.py                    # Hub - inicializace a základní routes
├── core/                     # Základní funkce
│   ├── __init__.py          # db instance
│   └── config.py            # Konfigurace
├── modules/
│   ├── budget/              # Modul Rozpočet
│   │   ├── __init__.py
│   │   ├── models.py        # UctovaSkupina, RozpoctovaPolozka, Vydaj
│   │   ├── routes.py        # Budget routes (blueprint)
│   │   └── executor.py      # BudgetExecutor (budoucí)
│   ├── projects/            # Modul Projekty
│   │   ├── __init__.py
│   │   ├── models.py        # Projekt, VydajProjektu, Termin, Zprava, Znalost
│   │   ├── routes.py        # Project routes (blueprint)
│   │   └── executor.py      # ProjectExecutor
│   ├── personnel/           # Modul Personální
│   │   ├── __init__.py
│   │   ├── models.py        # ZamestnanecAOON
│   │   └── routes.py        # Personnel routes (blueprint)
│   └── ai/                  # Modul AI
│       ├── __init__.py
│       ├── models.py        # Employee, AISession, Message, KnowledgeEntry, ServiceRecord, AssistantMemory
│       ├── routes.py        # AI routes (blueprint)
│       └── executor.py      # AIExecutor
├── models.py                # Centralizované modely (pro zpětnou kompatibilitu)
├── forms.py                 # Formuláře (lazy importy)
└── templates/               # Šablony (zůstávají stejné)
```

## 🔄 Co bylo změněno

### 1. **Core modul**
- ✅ Vytvořena složka `core/` s `__init__.py` a `config.py`
- ✅ Databáze instance v `core/__init__.py`
- ✅ Konfigurace přesunuta do `core/config.py`

### 2. **Budget modul**
- ✅ Modely přesunuty do `modules/budget/models.py`
- ✅ Routes přesunuty do `modules/budget/routes.py` (blueprint `budget`)
- ✅ Všechny url_for aktualizovány na `budget.*`

### 3. **Projects modul**
- ✅ Modely přesunuty do `modules/projects/models.py`
- ✅ Routes přesunuty do `modules/projects/routes.py` (blueprint `projects`)
- ✅ Executor přesunut do `modules/projects/executor.py`
- ✅ Importy aktualizovány

### 4. **Personnel modul**
- ✅ Modely přesunuty do `modules/personnel/models.py`
- ✅ Routes přesunuty do `modules/personnel/routes.py` (blueprint `personnel`)
- ✅ Všechny url_for aktualizovány na `personnel.*`

### 5. **AI modul**
- ✅ Modely přesunuty do `modules/ai/models.py`
- ✅ Routes přesunuty do `modules/ai/routes.py` (blueprint `ai_assistant`)
- ✅ Executor přesunut do `modules/ai/executor.py`
- ✅ Importy aktualizovány

### 6. **App.py jako Hub**
- ✅ `app.py` nyní pouze inicializuje aplikaci a registruje blueprinty
- ✅ Dashboard route zůstává v `app.py` (společný)
- ✅ Index route zůstává v `app.py` (hub stránka)

### 7. **Zpětná kompatibilita**
- ✅ `models.py` importuje všechny modely z modulů
- ✅ `forms.py` používá lazy importy pro cyklické závislosti
- ✅ Staré importy stále fungují

### 8. **Templates**
- ✅ Všechny `url_for` aktualizovány na nové názvy blueprintů
- ✅ `budget.seznam`, `budget.detail_polozky`, `personnel.seznam`, atd.

## 📊 Výhody nové struktury

1. **Oddělení zodpovědností** - každý modul má svou složku
2. **Snadná údržba** - změny v jednom modulu neovlivní ostatní
3. **Přehlednost** - jasně vidět, co patří kam
4. **Škálovatelnost** - snadné přidání nových modulů
5. **Testovatelnost** - každý modul lze testovat samostatně
6. **Týmová práce** - různí vývojáři mohou pracovat na různých modulech

## 🔧 Technické detaily

### Importy
- Moduly používají relativní importy: `from .models import ...`
- Core používá absolutní importy: `from core import db`
- Zpětná kompatibilita: `from models import ...` stále funguje

### Blueprinty
- `budget` - `/rozpocet/*`
- `projects` - `/projekty/*`
- `personnel` - `/personalni-agenda/*`
- `ai_assistant` - `/ai/*`

### Routes
- Všechny routes jsou v blueprintech
- Hub routes (`/`, `/dashboard`) zůstávají v `app.py`

## 📝 Migrace

### Pro vývojáře
- Staré importy stále fungují díky `models.py`
- Nové importy: `from modules.budget.models import ...`
- Templates používají nové názvy blueprintů

### Pro uživatele
- Žádné změny v UI
- Všechny funkce fungují stejně
- Pouze interní struktura se změnila

## 🚀 Použití

### Práce na konkrétním modulu
```python
# Budget modul
from modules.budget.models import RozpoctovaPolozka
from modules.budget.routes import budget_bp

# Projects modul
from modules.projects.models import Projekt
from modules.projects.executor import ProjectExecutor
```

### Přidání nového modulu
1. Vytvořit `modules/nazev_modulu/`
2. Přidat `__init__.py`, `models.py`, `routes.py`
3. Zaregistrovat blueprint v `app.py`

---
**Vytvořeno:** 10.12.2025  
**Verze:** 0.74  
**Status:** ✅ Kompletní modulární refaktoring




