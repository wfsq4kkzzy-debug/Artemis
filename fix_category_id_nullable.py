#!/usr/bin/env python3
"""
Oprava - změna category_id na nullable v budget_item
"""

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / 'library_budget.db'

if not db_path.exists():
    print("Databáze neexistuje.")
    exit(1)

print(f"Oprava databáze: {db_path}")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

try:
    # Zkontroluj, zda jsou nějaká data
    cursor.execute("SELECT COUNT(*) FROM budget_item")
    count = cursor.fetchone()[0]
    print(f"Počet záznamů v budget_item: {count}")
    
    if count > 0:
        print("⚠️  Tabulka obsahuje data. Vytvářím zálohu...")
        # Vytvoř zálohu
        cursor.execute("""
            CREATE TABLE budget_item_backup AS 
            SELECT * FROM budget_item
        """)
        print("✅ Záloha vytvořena")
    
    # Vytvoř novou tabulku s nullable category_id
    print("Vytvářím novou tabulku s nullable category_id...")
    cursor.execute("DROP TABLE IF EXISTS budget_item_new")
    cursor.execute("""
        CREATE TABLE budget_item_new (
            id INTEGER NOT NULL,
            budget_id INTEGER NOT NULL,
            category_id INTEGER,
            subcategory_id INTEGER,
            nazev VARCHAR(300),
            popis TEXT,
            castka NUMERIC(12, 2) NOT NULL,
            poradi INTEGER NOT NULL,
            aktivni BOOLEAN,
            datum_vytvoreni DATETIME NOT NULL,
            ucet VARCHAR(20) NOT NULL DEFAULT "",
            poducet VARCHAR(20),
            typ VARCHAR(20) NOT NULL DEFAULT "naklad",
            popis_old TEXT,
            PRIMARY KEY (id),
            FOREIGN KEY(budget_id) REFERENCES budget (id),
            FOREIGN KEY(category_id) REFERENCES budget_category (id)
        )
    """)
    
    # Zkopíruj data pokud existují
    if count > 0:
        print("Kopíruji data...")
        cursor.execute("""
            INSERT INTO budget_item_new 
            SELECT * FROM budget_item
        """)
        print(f"✅ Zkopírováno {count} záznamů")
    
    # Smazat starou tabulku
    print("Mažu starou tabulku...")
    cursor.execute("DROP TABLE budget_item")
    
    # Přejmenovat novou tabulku
    print("Přejmenovávám tabulku...")
    cursor.execute("ALTER TABLE budget_item_new RENAME TO budget_item")
    
    conn.commit()
    print("✅ Oprava dokončena!")
    
    # Zobraz finální schéma
    cursor.execute("PRAGMA table_info(budget_item)")
    columns = cursor.fetchall()
    print("\nFinální schéma budget_item:")
    for col in columns:
        nullable = "NULL" if not col[3] else "NOT NULL"
        print(f"  {col[1]}: {col[2]} {nullable}")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Chyba při opravě: {e}")
    raise
finally:
    conn.close()
