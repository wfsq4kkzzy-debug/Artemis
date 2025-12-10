# CHANGELOG

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
