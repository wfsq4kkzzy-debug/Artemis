# Plán refaktoringu do modulární architektury

## Cíl
Vytvořit přehlednou modulární strukturu, kde každý modul je samostatný a lze na něm pracovat nezávisle.

## Nová struktura

```
library_budget/
├── app.py                    # Hub - pouze inicializace a základní routes
├── core/                     # Základní funkce aplikace
│   ├── __init__.py          # db instance
│   └── config.py            # Konfigurace
├── modules/
│   ├── budget/              # Modul Rozpočet
│   │   ├── __init__.py
│   │   ├── models.py        # UctovaSkupina, RozpoctovaPolozka, Vydaj
│   │   ├── routes.py        # Budget routes (blueprint)
│   │   ├── executor.py      # BudgetExecutor
│   │   └── forms.py         # Budget formuláře
│   ├── projects/            # Modul Projekty
│   │   ├── __init__.py
│   │   ├── models.py        # Projekt, VydajProjektu, Termin, Zprava, Znalost
│   │   ├── routes.py        # Project routes (blueprint)
│   │   ├── executor.py      # ProjectExecutor
│   │   └── forms.py         # Project formuláře
│   ├── personnel/           # Modul Personální
│   │   ├── __init__.py
│   │   ├── models.py        # ZamestnanecAOON
│   │   ├── routes.py        # Personnel routes (blueprint)
│   │   ├── executor.py      # PersonnelExecutor
│   │   └── forms.py         # Personnel formuláře
│   └── ai/                  # Modul AI
│       ├── __init__.py
│       ├── routes.py        # AI routes (blueprint)
│       ├── executor.py      # AIExecutor
│       └── models.py        # AI modely (pokud jsou)
├── templates/               # Šablony (zůstávají stejné)
│   ├── base.html
│   ├── index.html          # Hub stránka
│   ├── dashboard.html
│   ├── budget/
│   ├── projects/
│   ├── personnel/
│   └── ai/
└── static/                 # Statické soubory (zůstávají stejné)
```

## Postup refaktoringu

### Fáze 1: Vytvoření struktury ✅
- [x] Vytvořit složky core/ a modules/
- [x] Vytvořit __init__.py soubory

### Fáze 2: Přesun modelů
- [x] modules/budget/models.py - UctovaSkupina, RozpoctovaPolozka, Vydaj
- [x] modules/projects/models.py - Projekt, VydajProjektu, Termin, Zprava, Znalost
- [ ] modules/personnel/models.py - ZamestnanecAOON

### Fáze 3: Přesun routes
- [ ] modules/budget/routes.py - z app.py
- [ ] modules/projects/routes.py - z project_routes.py
- [ ] modules/personnel/routes.py - z app.py
- [ ] modules/ai/routes.py - z ai_assistant.py

### Fáze 4: Přesun executory
- [ ] modules/budget/executor.py - z app.py
- [ ] modules/projects/executor.py - z project_executor.py
- [ ] modules/personnel/executor.py - nový
- [ ] modules/ai/executor.py - z ai_executor.py

### Fáze 5: Přesun formulářů
- [ ] modules/budget/forms.py - z forms.py
- [ ] modules/projects/forms.py - z forms.py (pokud jsou)
- [ ] modules/personnel/forms.py - z forms.py

### Fáze 6: Úprava app.py
- [ ] app.py jako hub - pouze inicializace a registrace blueprintů
- [ ] Aktualizovat všechny importy

### Fáze 7: Testování
- [ ] Otestovat všechny moduly
- [ ] Opravit případné chyby

## Výhody nové struktury

1. **Oddělení zodpovědností** - každý modul má svou složku
2. **Snadná údržba** - změny v jednom modulu neovlivní ostatní
3. **Přehlednost** - jasně vidět, co patří kam
4. **Škálovatelnost** - snadné přidání nových modulů
5. **Testovatelnost** - každý modul lze testovat samostatně
