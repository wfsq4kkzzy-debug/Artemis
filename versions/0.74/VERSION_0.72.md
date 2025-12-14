# Verze 0.72 - Základní verze pro další vývoj

**Datum:** 10. prosince 2025

## ✅ Status: Vytvořeno

Verze byla vytvořena pro další vývoj a testování.

## 📦 Obsah verze

Tato verze obsahuje kompletní stav projektu včetně:

### Moduly
- ✅ **Rozpočet** - Kompletní správa rozpočtu 2026
- ✅ **Personální agenda** - Správa zaměstnanců a OON
- ✅ **AI Asistent** - Chat s Claude AI (verze 0.71)
- ✅ **Projekty** - Správa projektů a termínů

### Technické
- Flask 3.0
- SQLAlchemy 2.1
- Anthropic Claude API
- Bootstrap 5 frontend
- SQLite databáze

## 🚀 Spuštění této verze

```bash
cd versions/0.72
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

## 🔄 Verzování

Pro vytvoření nové verze použijte:

```bash
python create_version.py <verze> [--description "popis"]
```

Příklad:
```bash
python create_version.py 0.73 --description "Nové funkce exportu"
```

---
**Vytvořeno pomocí:** `create_version.py`
