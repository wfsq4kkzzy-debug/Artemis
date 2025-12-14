# Návrh nového modulu rozpočtu

## Požadavky

1. **Více rozpočtů** - možnost vytvářet různé rozpočty (roční, projektové, atd.)
2. **Hlavní rozpočet** - jeden hlavní rozpočet, který se hlídá
3. **Jednoduché přidávání řádků** - snadné přidávání rozpočtových položek
4. **Kategorie** - editovatelné kategorie pro organizaci
5. **Propojení s projekty** - rozpočet hlídá projekty
6. **Běžné výdaje** - mzdy, provozní výdaje, atd.
7. **Měsíční hlídání** - sledování čerpání po měsících
8. **Reporty** - generování reportů
9. **Dashboard** - přehledný dashboard s více informacemi

## Návrh databázové struktury

### Rozpočet (Budget)
- `id` - primární klíč
- `nazev` - název rozpočtu (např. "Rozpočet 2026", "Projekt X")
- `typ` - typ rozpočtu ('hlavni', 'projektovy', 'rocni', 'mesicni')
- `rok` - rok rozpočtu
- `mesic` - měsíc (pro měsíční rozpočty, null pro roční)
- `castka_celkem` - celková částka rozpočtu
- `aktivni` - je rozpočet aktivní
- `hlavni` - je to hlavní rozpočet (pouze jeden může být hlavní)
- `datum_vytvoreni`, `datum_aktualizace`

### Kategorie rozpočtu (BudgetCategory)
- `id` - primární klíč
- `nazev` - název kategorie (např. "Mzdy", "Materiál", "Služby")
- `kod` - kód kategorie (např. "MZD", "MAT", "SLU")
- `popis` - popis kategorie
- `barva` - barva pro vizualizaci
- `poradi` - pořadí zobrazení
- `aktivni` - je kategorie aktivní

### Rozpočtová položka (BudgetItem)
- `id` - primární klíč
- `budget_id` - FK na Rozpočet
- `category_id` - FK na Kategorii
- `nazev` - název položky
- `popis` - popis položky
- `castka` - plánovaná částka
- `poradi` - pořadí v rámci kategorie
- `aktivni` - je položka aktivní

### Výdaj (Expense)
- `id` - primární klíč
- `budget_id` - FK na Rozpočet (hlavní rozpočet)
- `budget_item_id` - FK na Rozpočtovou položku (volitelné)
- `category_id` - FK na Kategorii
- `projekt_id` - FK na Projekt (volitelné - pokud je výdaj k projektu)
- `castka` - částka výdaje
- `datum` - datum výdaje
- `popis` - popis výdaje
- `cis_faktury` - číslo faktury
- `dodavatel` - dodavatel
- `typ` - typ výdaje ('bezny', 'mzda', 'projektovy', 'provozni')
- `mesic` - měsíc výdaje (pro měsíční hlídání)
- `rok` - rok výdaje

### Měsíční přehled (MonthlyBudget)
- `id` - primární klíč
- `budget_id` - FK na Rozpočet
- `rok` - rok
- `mesic` - měsíc (1-12)
- `planovano` - plánovaná částka pro měsíc
- `skutecne` - skutečné výdaje v měsíci
- `odchylka` - odchylka od plánu

## Propojení s projekty

- Projekty mohou mít vlastní rozpočet (typ='projektovy')
- Výdaje projektů se zapisují do hlavního rozpočtu s `projekt_id`
- Dashboard zobrazuje projekty jako součást hlavního rozpočtu

## Dashboard

### Sekce:
1. **Přehled hlavního rozpočtu**
   - Celkový rozpočet
   - Celkové výdaje
   - Zbývá
   - Procento čerpání
   - Progress bar

2. **Měsíční přehled**
   - Graf měsíčního čerpání
   - Tabulka měsíců s plánem vs. skutečnost
   - Odchylky

3. **Přehled podle kategorií**
   - Rozpis podle kategorií
   - Grafy (koláč, sloupcový)
   - Top kategorie

4. **Projekty v rozpočtu**
   - Seznam projektů s jejich rozpočtem
   - Čerpání projektů
   - Varování při překročení

5. **Poslední výdaje**
   - Tabulka posledních výdajů
   - Filtrování

6. **Reporty**
   - Rychlé odkazy na reporty

## Reporty

1. **Měsíční report** - čerpání za měsíc
2. **Kategorický report** - čerpání podle kategorií
3. **Projektový report** - čerpání projektů
4. **Roční report** - přehled za rok
5. **Srovnávací report** - plán vs. skutečnost

## UI/UX

### Rozpočet
- Jednoduchý formulář pro přidání řádku
- Drag & drop pro změnu pořadí
- Rychlá editace přímo v tabulce
- Filtrování podle kategorií
- Hledání

### Dashboard
- Karty s klíčovými metrikami
- Grafy (Chart.js)
- Interaktivní prvky
- Export do PDF/Excel

## Implementace

### Fáze 1: Databázové modely
- Vytvořit nové modely
- Migrace z starých modelů

### Fáze 2: Routes a UI
- Nové routes pro rozpočet
- Formuláře pro přidání/úpravu
- Dashboard

### Fáze 3: Propojení s projekty
- Automatické zapisování výdajů projektů
- Zobrazení v dashboardu

### Fáze 4: Reporty
- Generování reportů
- Export

### Fáze 5: Měsíční hlídání
- Automatické počítání měsíčních přehledů
- Upozornění při překročení
