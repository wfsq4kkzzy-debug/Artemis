# Modulární struktura projektu

## Přehled

Projekt je rozdělen do modulů pro lepší přehlednost a údržbu.

## Struktura

```
library_budget/
├── app.py                    # Hub - inicializace a základní routes
├── core/                     # Základní funkce
│   ├── __init__.py          # db instance
│   └── config.py            # Konfigurace
├── modules/
│   ├── budget/              # Modul Rozpočet
│   │   ├── models.py        # UctovaSkupina, RozpoctovaPolozka, Vydaj
│   │   ├── routes.py        # Budget routes
│   │   ├── executor.py      # BudgetExecutor
│   │   └── forms.py         # Budget formuláře
│   ├── projects/            # Modul Projekty
│   │   ├── models.py        # Projekt, VydajProjektu, Termin, Zprava, Znalost
│   │   ├── routes.py        # Project routes
│   │   ├── executor.py      # ProjectExecutor
│   │   └── forms.py         # Project formuláře
│   ├── personnel/           # Modul Personální
│   │   ├── models.py        # ZamestnanecAOON
│   │   ├── routes.py        # Personnel routes
│   │   ├── executor.py      # PersonnelExecutor
│   │   └── forms.py         # Personnel formuláře
│   └── ai/                  # Modul AI
│       ├── routes.py        # AI routes
│       └── executor.py      # AIExecutor
├── templates/               # HTML šablony
│   ├── base.html
│   ├── index.html          # Hub stránka
│   ├── budget/
│   ├── projects/
│   ├── personnel/
│   └── ai/
└── static/                 # Statické soubory
```

## Moduly

### Core
Základní funkce aplikace - databáze, konfigurace.

### Budget Module
Správa rozpočtu knihovny - účtové skupiny, rozpočtové položky, výdaje.

### Projects Module
Správa projektů - projekty, jejich rozpočty, výdaje, termíny, zprávy, znalosti.

### Personnel Module
Personální agenda - zaměstnanci, brigádníci, OON.

### AI Module
AI asistent - chat, znalostní databáze, poradenství.

## Výhody

1. **Oddělení zodpovědností** - každý modul má svou složku
2. **Snadná údržba** - změny v jednom modulu neovlivní ostatní
3. **Přehlednost** - jasně vidět, co patří kam
4. **Škálovatelnost** - snadné přidání nových modulů
5. **Testovatelnost** - každý modul lze testovat samostatně




