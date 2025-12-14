# Návrh struktury modulu rozpočtu

## Základní struktura

### Typ rozpočtu
- **Náklady** (expenses)
- **Výnosy** (revenue)

### Náklady - struktura
1. **Mzdové náklady**
   - Zaměstnanci (z personálního modulu)
   - Brigádníci (z personálního modulu)
   
2. **Ostatní náklady**
   - Flexibilní struktura kategorií a podkategorií
   - Uživatel může vytvářet vlastní kategorie

### Výnosy
- Flexibilní struktura kategorií a podkategorií

## Databázová struktura

### Budget (Rozpočet)
- Hlavní rozpočet nebo podrozpočet
- Typ: 'hlavni', 'podrozpocet'
- Rok

### BudgetCategory (Kategorie)
- Typ: 'naklad_mzdovy', 'naklad_ostatni', 'vynos'
- Název, kód, popis
- Barva pro vizualizaci
- Pořadí

### BudgetSubCategory (Podkategorie)
- Nadřazená kategorie
- Název, kód, popis
- Pořadí

### BudgetItem (Rozpočtová položka - řádek)
- Kategorie nebo podkategorie
- Název
- Plánovaná částka
- Poznámka

### Expense (Výdaj)
- Rozpočtová položka (volitelné)
- Kategorie
- Podkategorie (volitelné)
- Projekt (volitelné - propojení s projekty)
- Personální záznam (volitelné - pro mzdy)
- Částka, datum, popis
- Číslo faktury, dodavatel

## Propojení s moduly

### Personální modul
- Mzdy se automaticky zapisují do rozpočtu
- Propojení přes `personnel_id` v Expense
- Automatické kategorizování (zaměstnanec/brigádník)

### Projekty
- Výdaje projektů se zapisují do rozpočtu
- Propojení přes `projekt_id` v Expense
- Zobrazení v dashboardu

### Uživatelé
- Kdo přidal výdaj
- Notifikace o překročení rozpočtu

## Dashboard

### Hlavní přehled
- Celkový rozpočet (náklady vs. výnosy)
- Celkové výdaje
- Zbývá
- Procento čerpání

### Rozpis podle kategorií
- Mzdové náklady (zaměstnanci, brigádníci)
- Ostatní náklady (podle kategorií)
- Výnosy (podle kategorií)

### Projekty v rozpočtu
- Výdaje projektů
- Zbývající rozpočet projektů

### Měsíční přehled
- Čerpání po měsících
- Plán vs. skutečnost

### Top výdaje
- Největší výdaje
- Nejčastější kategorie

## UI

### Správa rozpočtu
- Vytvoření/úprava kategorie
- Vytvoření/úprava podkategorie
- Přidání rozpočtové položky
- Úprava částky

### Přidání výdaje
- Výběr kategorie/podkategorie
- Výběr projektu (volitelné)
- Výběr personálního záznamu (pro mzdy)
- Částka, datum, popis
- Číslo faktury, dodavatel

### Podrozpočty
- Vytvoření podrozpočtu
- Přiřazení položek k podrozpočtu
- Zobrazení v dashboardu




