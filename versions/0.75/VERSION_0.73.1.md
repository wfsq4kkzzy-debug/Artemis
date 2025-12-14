# Verze 0.73.1 - Přepracování rozpočtu projektu

**Datum:** 10. prosince 2025

## ✅ Status: Kompletní přepracování

Kompletně přepracovaná logika rozpočtu projektu - jednoduchý a intuitivní systém.

## 🎯 Nová logika rozpočtu

### Koncept
- **Projekt má jeden celkový rozpočet** (jedno číslo)
- **K projektu se přidávají výdaje** (bez kategorií)
- **Výdaje se pouze hlídají** proti celkovému rozpočtu
- **Všechny operace zvládá AI agent**

### Co bylo změněno

#### 1. **Model Projekt**
- ✅ Přidáno pole `rozpocet` (Numeric) - celkový rozpočet projektu
- ✅ Odstraněna závislost na `BudgetProjektu` (ponecháno pro kompatibilitu)
- ✅ Nové properties: `rozpocet_float`, `procento_vycerpano`
- ✅ Výdaje se počítají pouze do aktuálního data

#### 2. **Model VydajProjektu**
- ✅ Odstraněna povinnost kategorie (nyní volitelné, prázdné)
- ✅ Přidáno pole `poznamka` pro poznámky
- ✅ Zjednodušený model - jen výdaj k projektu

#### 3. **ProjectExecutor - Nové metody**
- ✅ `set_project_budget(projekt_id, rozpocet)` - nastavit rozpočet
- ✅ `update_project_budget(projekt_id, rozpocet)` - upravit rozpočet
- ✅ `get_project_budget(projekt_id)` - získat info o rozpočtu
- ✅ `add_expense(projekt_id, popis, castka, ...)` - přidat výdaj
- ✅ `update_expense(vydaj_id, ...)` - upravit výdaj
- ✅ `delete_expense(vydaj_id)` - smazat výdaj
- ✅ `get_expense_detail(vydaj_id)` - detail výdaje

#### 4. **Routes - Nové endpointy**
- ✅ `GET/POST /projekty/<id>/rozpocet` - nastavení rozpočtu
- ✅ `GET/POST /projekty/<id>/vydaje` - správa výdajů
- ✅ `GET/POST /projekty/<id>/vydaj/<id>/upravit` - úprava výdaje
- ✅ `POST /projekty/<id>/vydaj/<id>/smazat` - smazání výdaje

#### 5. **UI - Nové šablony**
- ✅ `templates/projekty/rozpocet.html` - nastavení rozpočtu s vizualizací
- ✅ `templates/projekty/vydaje.html` - správa výdajů s přehledem
- ✅ `templates/projekty/upravit_vydaj.html` - úprava výdaje
- ✅ Vylepšený `templates/projekty/detail.html` - přehled rozpočtu

#### 6. **AI Agent - Nové příkazy**
- ✅ `set_project_budget` - nastavit rozpočet
- ✅ `get_project_budget` - zobrazit rozpočet
- ✅ `add_project_expense` - přidat výdaj
- ✅ `update_project_expense` - upravit výdaj
- ✅ `delete_project_expense` - smazat výdaj
- ✅ Automatická detekce příkazů v textu

## 🎨 Uživatelský design

### Hlavní principy
1. **Jednoduchost** - jeden rozpočet, výdaje bez kategorií
2. **Přehlednost** - vizualizace pokroku, progress bary
3. **Editovatelnost** - vše lze upravit a smazat
4. **AI podpora** - všechny operace přes AI agenta

### Vizuální prvky
- **Progress bar** - zobrazení čerpání rozpočtu (zelená/žlutá/červená)
- **Karty s přehledem** - rozpočet, výdaje, zbytek, čerpání
- **Barevné kódování** - zelená (OK), žlutá (varování), červená (překročeno)
- **Tabulky výdajů** - přehledné zobrazení s akcemi
- **Formuláře** - jednoduché a intuitivní

## 🤖 AI Agent - Podporované příkazy

### Nastavení rozpočtu
- "Nastav rozpočet 100 000 Kč"
- "Rozpočet projektu je 50000 Kč"
- "Set budget 75000"

### Přidání výdaje
- "Přidej výdaj 5000 Kč za materiál"
- "Výdaj 2000 Kč pro tisk"
- "Zaplatil jsem 15000 Kč za služby"

### Úprava výdaje
- "Uprav výdaj ID 5 na 6000 Kč"
- "Změň výdaj 3, popis je 'Nový popis'"

### Smazání výdaje
- "Smaž výdaj ID 2"
- "Odstraň výdaj číslo 5"

### Zobrazení
- "Jaký je stav rozpočtu?"
- "Kolik zbývá?"
- "Ukaž všechny výdaje"

## 📊 Vizuální prvky

### Detail projektu
- Velká karta s přehledem rozpočtu
- 4 sloupce: Rozpočet, Vydaje, Zbývá, Čerpání
- Progress bar s barevným kódováním
- Rychlé odkazy na správu rozpočtu a výdajů

### Stránka rozpočtu
- Formulář pro nastavení rozpočtu
- Přehled s progress barem
- Zobrazení aktuálního stavu

### Stránka výdajů
- Přehled rozpočtu nahoře
- Formulář pro přidání výdaje vlevo
- Tabulka výdajů vpravo
- Možnost editace a mazání každého výdaje

## 🔧 Technické detaily

### Databázové změny
- Přidáno pole `rozpocet` do tabulky `projekt`
- Pole `kategorie` v `vydaj_projektu` je nyní volitelné (prázdné)
- Přidáno pole `poznamka` do `vydaj_projektu`

### Kompatibilita
- Starý model `BudgetProjektu` ponechán (pro kompatibilitu)
- Staré metody `add_budget_item` vrací chybu (zastaralé)
- Nové projekty používají novou logiku

## 🚀 Použití

### Nastavení rozpočtu projektu
1. Otevřít projekt
2. Kliknout na "Správa rozpočtu"
3. Zadat celkový rozpočet
4. Uložit

### Přidání výdaje
1. Otevřít projekt
2. Kliknout na "Správa výdajů"
3. Vyplnit formulář (popis, částka, datum, faktura, dodavatel)
4. Uložit

### Úprava výdaje
1. V seznamu výdajů kliknout na "Upravit"
2. Změnit potřebné údaje
3. Uložit

### Přes AI agenta
- Všechny operace lze provést přes chat s AI
- AI automaticky detekuje příkazy a provede je
- Všechny zprávy se ukládají do databáze

## 📝 Poznámky

- Rozpočet projektu je jedno číslo (ne součet položek)
- Výdaje nemají kategorie - jen popis a částka
- Výdaje se počítají pouze do aktuálního data
- Všechny operace jsou editovatelné
- AI agent podporuje všechny operace

---
**Vytvořeno:** 10.12.2025  
**Verze:** 0.73.1  
**Status:** ✅ Kompletní přepracování
