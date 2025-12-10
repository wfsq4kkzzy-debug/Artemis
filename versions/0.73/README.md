# Verze 0.73

**Datum vytvoření:** 2025-12-10 20:01:44

**Popis:** Záloha před dalšími změnami

## 📦 Obsah

Tato složka obsahuje kompletní stav projektu v době vytvoření verze 0.73.

## 🚀 Spuštění

### Jednoduché spuštění (doporučeno)

**macOS/Linux:**
```bash
cd versions/0.73
./start.sh
```

**Windows:**
```cmd
cd versions\0.73
start.bat
```

Skript automaticky:
- ✅ Vytvoří virtuální prostředí (pokud neexistuje)
- ✅ Nainstaluje závislosti
- ✅ Vytvoří databázi (pokud neexistuje)
- ✅ Spustí aplikaci

### Ruční spuštění

```bash
cd versions/0.73
python3 -m venv venv
source venv/bin/activate  # nebo venv\Scripts\activate na Windows
pip install -r requirements.txt
python init_db.py
python dev.py
```

## 📝 Poznámky

- Databáze není součástí této verze (musí být vytvořena pomocí `init_db.py`)
- `.env` soubor není součástí (musí být vytvořen ručně)
- Virtuální prostředí není součástí (musí být vytvořeno)

---
**Vytvořeno pomocí:** `create_version.py`
