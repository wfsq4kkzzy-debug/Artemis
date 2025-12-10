# Rychlý start - Správa rozpočtu knihovny

## 🚀 30-ti sekund instalace

```bash
# 1. Přejděte do složky
cd library_budget

# 2. Vytvořte virtuální prostředí
python3 -m venv venv
source venv/bin/activate

# 3. Instalujte závislosti
pip install -r requirements.txt

# 4. Inicializujte databázi
python init_db.py

# 5. Spusťte aplikaci
python dev.py
```

**Aplikace je přístupná na: http://127.0.0.1:5000**

---

## 📖 Co máte

✅ **Kompletní rozpočet 2026**
- 22 účtových skupin
- 73 rozpočtových položek  
- Náklady: 7,697,240 Kč
- Výnosy: 7,697,240 Kč

✅ **Modul Rozpočet**
- Dashboard s přehledem
- Filtrování a vyhledávání
- Přidávání výdajů
- Sledování faktur

✅ **Modul Personální agenda**
- Správa zaměstnanců
- Evidence mezd
- OON management

✅ **Web-ready**
- Responzivní design (Bootstrap 5)
- Připraveno pro nasazení na web
- Docker support
- Bezpečnostní nastavení

---

## 🔗 Důležité odkazy

| Soubor | Popis |
|--------|-------|
| [README.md](README.md) | Kompletní dokumentace |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Návod na nasazení na web |
| [.env.example](.env.example) | Příklad konfigurace |
| [requirements.txt](requirements.txt) | Python závislosti |

---

## 📚 Struktury v databázi

### Náklady (15 kategorií)
```
501 - Spotřeba materiálu         488,660 Kč
502 - Spotřeba energie           311,000 Kč
511 - Opravy a udržování          20,000 Kč
512 - Cestovné                    10,000 Kč
513 - Reprezentace                 8,000 Kč
518 - Ostatní služby             391,500 Kč
521 - Mzdové náklady           4,320,000 Kč
524 - Sociální pojištění       1,352,000 Kč
525 - Jiné pojištění              10,000 Kč
527 - Sociální náklady           278,000 Kč
... a další
```

### Výnosy (6 kategorií)
```
601 - Prodej výrobků              50,220 Kč
602 - Prodej služeb              513,000 Kč
603 - Pronájem prostor            98,000 Kč
604 - Prodej zásob                60,000 Kč
662 - Úroky                           50 Kč
672 - Provozní dotace         6,976,970 Kč
```

---

## 💡 Co si možete vyzkoušet

1. **Přejděte na Dashboard** - Vidíte celkový přehled
2. **Klikněte na účet** - Filtruje položky
3. **Detail položky** - Vidíte výdaje
4. **Přidejte výdaj** - Např. fakturu
5. **Personální agenda** - Přidejte zaměstnance

---

## 🛠️ Příkazy pro práci

```bash
# Otevřít Flask shell (pro SQL dotazy)
flask shell

# Resetovat databázi
python init_db.py

# Spustit testy (až budou přidány)
pytest

# Generovat database migration
flask db init
```

---

## 🌐 Nasazení na web

Aplikace je připravena pro nasazení na:
- **Heroku** - nejjednodušší (1 příkaz)
- **DigitalOcean** - více kontroly
- **Docker** - kontejnerizace
- Váš vlastní server

**Viz [DEPLOYMENT.md](DEPLOYMENT.md) pro podrobnosti.**

---

## 🐛 Běžné problémy

**Port 5000 je obsazen:**
```bash
lsof -i :5000  # Najít proces
kill -9 <PID>  # Zabít ho
```

**Chyba s databází:**
```bash
rm library_budget.db
python init_db.py
```

**Chyba s Python balíčky:**
```bash
pip install -r requirements.txt --upgrade
```

---

## 📞 Podpora

- GitHub: Vidíte issues v repozitáři
- Dokumentace: Přečtěte si README.md
- Deployment: Přečtěte si DEPLOYMENT.md

---

**Vítejte v Správě rozpočtu Knihovny Polička!** 📚
