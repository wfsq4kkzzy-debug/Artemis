# 📦 Release Notes - Verze 0.71

**Datum:** 10. prosince 2025

## Co je nového

### 🤖 AI Asistent
- **Jednoduchý chat interface** - Jedna chatovací okna pro tebe
- **Setup formulář** - Snadné zadání API klíče
- **Paměť** - AI si pamatuje všechny konverzace
- **Znalostní databáze** - AI zná procedury knihovny

### 🔧 Technické detaily
- Built s Flask + SQLAlchemy
- Anthropic Claude API integration
- SQLite databáze
- Python 3.14 kompatibilní
- Bootstrap 5 frontend

## ⚡ Jak na to

1. **Setup API klíče:**
   ```
   Jdi na http://localhost:5001/ai/
   Zadej API klíč
   Klikni "Uložit a Pokračovat"
   ```

2. **Chat s AI:**
   ```
   Napiš svou otázku
   AI asistent odpoví
   Vše se ukládá
   ```

## 🐛 Známé problémy

| Problém | Status |
|---------|--------|
| Token tracking nefunguje správně | ⚠️ TODO |
| Python 3.14 kompatibilita | ✅ Works but warns |
| API timeout handling | ⚠️ Basic |

## 📊 Statistika

- **Řádky kódu:** ~1000+
- **Databázové modely:** 6
- **Šablony:** 4 (aktivní)
- **API endpoints:** 3
- **Konfigurace:** `.env` (API klíč)

## 🚀 Performance

- Chat response: ~2-5 sekund (záleží na Claude)
- Database: Instant (SQLite)
- Frontend: Responsive (Bootstrap 5)

## 🔐 Bezpečnost

- API klíč se ukládá lokálně v `.env`
- Není sdílen s nikým
- SQLAlchemy ochrana proti SQL injection
- CSRF token v formulářích

## 📚 Znalostní databáze (seed data)

1. Procedura katalogizace
2. Kontakty oddělení
3. Obecně závazná vyhláška

## 🎯 Další kroky

1. Opravit token tracking
2. Přidat error handling
3. Optimalizovat prompty
4. Přidat více znalostí
5. Export konverzací

---

**Připraveno:** GitHub Copilot  
**Testováno:** 10.12.2025  
**Stav:** Beta - funkční
