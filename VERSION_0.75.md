# Verze 0.75 - Nový modul rozpočtu (ve vývoji)

**Datum:** 10. prosince 2025

## ✅ Status: Ve vývoji

Začátek přepracování modulu rozpočtu na flexibilní systém s více rozpočty, kategoriemi a měsíčním hlídáním.

## 🎯 Nový modul rozpočtu - koncept

### Hlavní změny
- ✅ **Více rozpočtů** - možnost vytvářet různé rozpočty (hlavní, projektové, roční, měsíční)
- ✅ **Editovatelné kategorie** - flexibilní kategorie pro organizaci
- ✅ **Jednoduché přidávání řádků** - snadné přidávání rozpočtových položek
- ✅ **Propojení s projekty** - výdaje projektů se zapisují do hlavního rozpočtu
- ✅ **Měsíční hlídání** - automatické sledování čerpání po měsících
- ✅ **Nový dashboard** - přehledný dashboard s více informacemi
- ✅ **Samostatná databáze** - každá verze má svou vlastní databázi

## 🏗️ Nová databázová struktura

### Budget (Rozpočet)
- Hlavní rozpočet, projektové rozpočty, roční, měsíční
- Jeden hlavní rozpočet (`hlavni=True`)

### BudgetCategory (Kategorie)
- Editovatelné kategorie (Mzdy, Materiál, Služby, atd.)
- Barvy pro vizualizaci
- Pořadí zobrazení

### BudgetItem (Rozpočtová položka)
- Řádky v rozpočtu
- Přiřazení ke kategorii
- Plánovaná částka

### Expense (Výdaj)
- Univerzální výdaje (běžné, mzdy, projektové)
- Propojení s projektem (volitelné)
- Měsíc a rok pro měsíční hlídání

### MonthlyBudget (Měsíční přehled)
- Automatické počítání měsíčních přehledů
- Plán vs. skutečnost
- Odchylky

## 📊 Dashboard

### Sekce:
1. **Přehled hlavního rozpočtu** - celkový rozpočet, výdaje, zbytek, čerpání
2. **Měsíční přehled** - tabulka měsíců s plánem vs. skutečnost
3. **Přehled podle kategorií** - výdaje podle kategorií
4. **Projekty v rozpočtu** - projekty s jejich výdaji
5. **Poslední výdaje** - tabulka posledních výdajů

## 🔧 Technické změny

### Databáze
- Každá verze má svou vlastní databázi (`library_budget.db`)
- Při vytvoření verze se zkopíruje aktuální databáze
- Config upraven pro správnou cestu k databázi

### Modely
- Nové modely: `Budget`, `BudgetCategory`, `BudgetItem`, `Expense`, `MonthlyBudget`
- Zastaralé modely ponechány pro kompatibilitu
- Propojení s projekty přes `projekt_id` v `Expense`

### Routes
- Dočasně placeholder stránka "Ve vývoji"
- Staré routes zálohovány v `routes_old.py`

## 📝 Poznámky

- Modul rozpočtu je ve vývoji
- Starý systém stále funguje pro kompatibilitu
- Nový systém bude postupně implementován
- Databáze je nyní součástí každé verze

---
**Vytvořeno:** 10.12.2025  
**Verze:** 0.75  
**Status:** 🚧 Ve vývoji




