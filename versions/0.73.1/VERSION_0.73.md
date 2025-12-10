# Verze 0.73 - Záloha před dalšími změnami

**Datum:** 10. prosince 2025

## ✅ Status: Záloha vytvořena

Verze byla vytvořena jako záloha aktuálního stavu projektu před dalšími změnami.

## 📦 Obsah verze

Tato verze obsahuje kompletní stav projektu včetně:

### Moduly
- ✅ **Rozpočet** - Kompletní správa rozpočtu 2026
- ✅ **Personální agenda** - Správa zaměstnanců a OON
- ✅ **AI Asistent** - Chat s Claude AI
- ✅ **Projekty** - Správa projektů a termínů
- ✅ **Systém verzování** - Skript `create_version.py` pro vytváření verzí

### Technické
- Flask 3.0
- SQLAlchemy 2.1
- Anthropic Claude API
- Bootstrap 5 frontend
- SQLite databáze

## 🚀 Spuštění této verze

```bash
cd versions/0.73
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python init_db.py
python dev.py
```

Aplikace bude dostupná na: `http://127.0.0.1:5000`

## 📝 Poznámky

- Databáze není součástí této verze (musí být vytvořena pomocí `init_db.py`)
- `.env` soubor není součástí (musí být vytvořen ručně s API klíčem)
- Virtuální prostředí není součástí (musí být vytvořeno)

## 🔄 Rozdíly oproti 0.72

- Přidán systém verzování (`create_version.py`)
- Přidána dokumentace verzování (`VERSIONING.md`)
- Aktualizován `CHANGELOG.md`

---
**Vytvořeno pomocí:** `create_version.py`
