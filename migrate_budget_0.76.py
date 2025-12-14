#!/usr/bin/env python3
"""
Migrace databáze pro verzi 0.76 - nová struktura rozpočtu
"""

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / 'library_budget.db'

if not db_path.exists():
    print("Databáze neexistuje, vytvoří se při prvním spuštění aplikace.")
    exit(0)

print(f"Migrace databáze: {db_path}")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

try:
    # Zkontroluj, zda tabulka budget_category existuje a má sloupec budget_id
    cursor.execute("PRAGMA table_info(budget_category)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'budget_id' not in columns:
        print("Přidávám sloupec budget_id do budget_category...")
        cursor.execute("ALTER TABLE budget_category ADD COLUMN budget_id INTEGER")
        
        # Pokud existuje hlavní rozpočet, přiřaď ho ke kategoriím
        cursor.execute("SELECT id FROM budget WHERE hlavni = 1 LIMIT 1")
        hlavni = cursor.fetchone()
        if hlavni:
            hlavni_id = hlavni[0]
            cursor.execute("UPDATE budget_category SET budget_id = ? WHERE budget_id IS NULL", (hlavni_id,))
            print(f"Kategorie přiřazeny k hlavnímu rozpočtu (ID: {hlavni_id})")
        else:
            # Vytvoř hlavní rozpočet
            cursor.execute("""
                INSERT INTO budget (nazev, typ, rok, castka_celkem, aktivni, hlavni, datum_vytvoreni)
                VALUES ('Rozpočet 2026', 'hlavni', 2026, 0, 1, 1, datetime('now'))
            """)
            hlavni_id = cursor.lastrowid
            cursor.execute("UPDATE budget_category SET budget_id = ?", (hlavni_id,))
            print(f"Vytvořen hlavní rozpočet (ID: {hlavni_id}) a kategorie přiřazeny")
    
    # Zkontroluj, zda tabulka budget_subcategory existuje
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='budget_subcategory'")
    if not cursor.fetchone():
        print("Vytvářím tabulku budget_subcategory...")
        cursor.execute("""
            CREATE TABLE budget_subcategory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                nazev VARCHAR(100) NOT NULL,
                kod VARCHAR(20),
                popis TEXT,
                poradi INTEGER NOT NULL DEFAULT 0,
                aktivni BOOLEAN DEFAULT 1,
                datum_vytvoreni DATETIME NOT NULL,
                FOREIGN KEY (category_id) REFERENCES budget_category(id)
            )
        """)
    
    # Zkontroluj, zda tabulka budget_item má subcategory_id
    cursor.execute("PRAGMA table_info(budget_item)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'subcategory_id' not in columns:
        print("Přidávám sloupec subcategory_id do budget_item...")
        cursor.execute("ALTER TABLE budget_item ADD COLUMN subcategory_id INTEGER")
    
    # Zkontroluj, zda tabulka expense má všechny potřebné sloupce
    cursor.execute("PRAGMA table_info(expense)")
    columns = [col[1] for col in cursor.fetchall()]
    
    required_columns = {
        'subcategory_id': 'INTEGER',
        'personnel_id': 'INTEGER',
        'user_id': 'INTEGER'
    }
    
    for col_name, col_type in required_columns.items():
        if col_name not in columns:
            print(f"Přidávám sloupec {col_name} do expense...")
            cursor.execute(f"ALTER TABLE expense ADD COLUMN {col_name} {col_type}")
    
    conn.commit()
    print("✅ Migrace dokončena!")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Chyba při migraci: {e}")
    raise
finally:
    conn.close()




