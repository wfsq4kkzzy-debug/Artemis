# 🤖 AI Asistent - Osobní Pomoc

Jednoduchý AI asistent, který ti pomáhá s prací v knihovně. Vše si zapamatuje a poskytuje personalizovanou pomoc.

## Funkce

### 💬 Chat s AI
- Přímá komunikace s Claude AI
- Paměť všech konverzací
- Znalostní databáze se procedurami
- Sledování tokenů

## Instalace

### 1. Klonuj nebo zkopíruj projekt
```bash
cd library_budget
```

### 2. Vytvoř .env soubor
```bash
cp .env.example .env
```

### 3. Přidej Anthropic API klíč
Otevři `.env` a přidej svůj API klíč:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Klíč získáš na: https://console.anthropic.com

### 4. Spusť aplikaci
```bash
./start.sh
```

Nebo ručně:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 init_db.py
python3 init_ai.py
python3 run.py
```

### 5. Otevři v prohlížeči
```
http://localhost:5001/ai/
```

## Jak se používá

1. Otevři `/ai/` v aplikaci
2. Napiš svou otázku
3. AI asistent ti odpoví
4. Vše si pamatuje

## Příklady otázek

- "Jaká je procedura pro katalogizaci nové knihy?"
- "Kdo je správce katalogu?"
- "Jaká jsou otevírací doba?"
- "Jak se vracejí knihy?"

## API Klíč

Musíš mít API klíč od Anthropic:

1. Jdi na https://console.anthropic.com
2. Vytvoř nový projekt
3. Vygeneruj API klíč
4. Vlož do `.env` souboru jako `ANTHROPIC_API_KEY`

## Architektura

### Databázové Modely

- **Employee** - Jednoho uživatele (tebe)
- **AISession** - Jednu konverzaci
- **Message** - Zprávy v konverzaci
- **KnowledgeEntry** - Znalostní záznamy
- **AssistantMemory** - Paměť o tobě

### AI Logika

AI asistent:
1. Načte všechny znalostní záznamy
2. Načte paměť o tobě
3. Vytvoří system prompt
4. Odešle zprávu Claude
5. Ulož odpověď a zprávu

## Konfigurace

### Model
Default: `claude-3-5-sonnet-20241022`

Změnit v `ai_assistant.py`:
```python
self.model = 'claude-3-5-sonnet-20241022'
```

### Token limit
Default: 2048 tokenů na odpověď

## Bezpečnost

- Paměť AI je privátní
- Všechny zprávy se ukládají lokálně
- API klíč je v `.env` (nije v gitu)

## Řešení problémů

### "API klíč není nalezen"
- Zkontroluj `.env` soubor
- Ověř, že je klíč správně nastaven

### "Port je obsazen"
- Změň port v `run.py` na jiný (např. 5002)
- Nebo ukonči proces: `lsof -i :5001 | grep python | awk '{print $2}' | xargs kill -9`

### "Chyba připojení"
- Zkontroluj internet
- Ověř API klíč na console.anthropic.com

---

**Verze:** 2.0 (zjednoduš)  
**Poslední aktualizace:** 2025-12-10
