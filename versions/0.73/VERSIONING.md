# 📦 Systém verzování

Tento dokument popisuje, jak pracovat s verzováním projektu.

## 🎯 Koncept

Každá verze projektu se ukládá do samostatné složky v `versions/`. To umožňuje:
- ✅ Snadné porovnání verzí
- ✅ Rychlý návrat k předchozí verzi
- ✅ Bezpečné testování změn
- ✅ Archivaci stabilních verzí

## 📁 Struktura

```
library_budget/
├── versions/
│   ├── 0.71/
│   │   ├── app.py
│   │   ├── models.py
│   │   ├── templates/
│   │   ├── static/
│   │   └── README.md
│   └── 0.72/
│       ├── app.py
│       ├── models.py
│       ├── templates/
│       ├── static/
│       └── README.md
├── create_version.py    # Skript pro vytváření verzí
└── VERSIONING.md        # Tento dokument
```

## 🚀 Vytvoření nové verze

### Automaticky (doporučeno)

```bash
python create_version.py <verze> [--description "popis"]
```

**Příklady:**
```bash
# Základní verze
python create_version.py 0.73

# S popisem
python create_version.py 0.73 --description "Přidán export do Excelu"

# Verze s podverzí
python create_version.py 0.73.1 --description "Oprava bugu v exportu"
```

### Co se kopíruje

✅ **Kopíruje se:**
- Všechny Python soubory (`.py`)
- Templates (`templates/`)
- Statické soubory (`static/`)
- Konfigurační soubory (`config.py`, `requirements.txt`)
- Dokumentace (`.md` soubory)
- `.env.example` a `.gitignore`

❌ **NEkopíruje se:**
- Databáze (`.db`, `.sqlite`)
- Cache (`__pycache__/`, `*.pyc`)
- Virtuální prostředí (`venv/`, `env/`)
- `.env` soubor (obsahuje citlivé údaje)
- Složka `versions/` (aby se nevytvářely vnořené verze)
- Log soubory (`.log`)

## 📖 Spuštění konkrétní verze

```bash
# Přejdi do složky verze
cd versions/0.72

# Vytvoř virtuální prostředí (pokud neexistuje)
python3 -m venv venv
source venv/bin/activate  # nebo venv\Scripts\activate na Windows

# Instaluj závislosti
pip install -r requirements.txt

# Inicializuj databázi
python init_db.py

# Spusť aplikaci
python dev.py
```

## 🔄 Kdy vytvořit novou verzi?

Vytvořte novou verzi když:
- ✅ Dokončíte významnou funkci
- ✅ Opravíte kritický bug
- ✅ Chcete "zmrazit" stabilní stav před velkými změnami
- ✅ Před refaktoringem
- ✅ Před experimentálními změnami

## 📝 Best Practices

1. **Pojmenování verzí:**
   - Používejte semver: `0.72`, `0.73`, `1.0`
   - Pro opravy: `0.73.1`, `0.73.2`
   - Pro experimenty: `0.73-beta`, `0.73-rc1`

2. **Popis změn:**
   - Vždy přidejte `--description` s popisem změn
   - Aktualizujte `CHANGELOG.md` v hlavní složce
   - Vytvořte `VERSION_X.XX.md` pro detailní popis

3. **Před vytvořením verze:**
   - Otestujte, že aplikace funguje
   - Zkontrolujte, že nejsou chyby
   - Commitněte změny (pokud používáte git)

4. **Po vytvoření verze:**
   - Otestujte, že verze se dá spustit
   - Zkontrolujte README v `versions/X.XX/`
   - Aktualizujte dokumentaci

## 🗑️ Mazání starých verzí

Staré verze můžete smazat ručně:

```bash
rm -rf versions/0.71  # Smazat verzi 0.71
```

⚠️ **Pozor:** Smazání verze je nevratné!

## 🔍 Porovnání verzí

Pro porovnání dvou verzí můžete použít:

```bash
# Porovnat soubory
diff -r versions/0.71/app.py versions/0.72/app.py

# Nebo použít git (pokud je projekt v gitu)
git diff versions/0.71 versions/0.72
```

## 📊 Seznam verzí

Aktuální verze:
- **0.72** - Základní verze pro další vývoj (10.12.2025)
- **0.71** - AI Asistent (10.12.2025)

## 💡 Tipy

- Pravidelně vytvářejte verze (např. po každé větší změně)
- Uchovávejte alespoň poslední 3-5 verzí
- Před velkými změnami vždy vytvořte verzi
- Používejte popisné názvy verzí

---
**Poslední aktualizace:** 10.12.2025
