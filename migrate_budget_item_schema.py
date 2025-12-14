#!/usr/bin/env python3
"""
Migrace databáze - přidání chybějících sloupců do budget_item
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
    # Zkontroluj aktuální sloupce
    cursor.execute("PRAGMA table_info(budget_item)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Aktuální sloupce: {columns}")
    
    # Sloupce, které potřebujeme přidat
    required_columns = {
        'ucet': 'VARCHAR(20) NOT NULL DEFAULT ""',
        'poducet': 'VARCHAR(20)',
        'typ': 'VARCHAR(20) NOT NULL DEFAULT "naklad"',
        'popis_old': 'TEXT'
    }
    
    # Přidej chybějící sloupce
    for col_name, col_def in required_columns.items():
        if col_name not in columns:
            print(f"Přidávám sloupec {col_name} do budget_item...")
            try:
                cursor.execute(f"ALTER TABLE budget_item ADD COLUMN {col_name} {col_def}")
                print(f"✅ Sloupec {col_name} přidán")
            except Exception as e:
                print(f"⚠️  Chyba při přidávání {col_name}: {e}")
    
    # Migrace existujících dat
    cursor.execute("PRAGMA table_info(budget_item)")
    columns_after = [col[1] for col in cursor.fetchall()]
    
    # Pokud máme stará data s nazev, zkopíruj je do popis (pokud popis je prázdný)
    if 'nazev' in columns_after and 'popis' in columns_after:
        cursor.execute("SELECT COUNT(*) FROM budget_item WHERE (popis IS NULL OR popis = '') AND nazev IS NOT NULL AND nazev != ''")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"Kopíruji {count} záznamů z nazev do popis...")
            cursor.execute("UPDATE budget_item SET popis = nazev WHERE (popis IS NULL OR popis = '') AND nazev IS NOT NULL AND nazev != ''")
    
    # Pokud máme stará data s popis, zkopíruj je do popis_old pro zálohu
    if 'popis' in columns_after and 'popis_old' in columns_after:
        cursor.execute("SELECT COUNT(*) FROM budget_item WHERE popis_old IS NULL AND popis IS NOT NULL AND popis != ''")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"Kopíruji {count} záznamů z popis do popis_old pro zálohu...")
            cursor.execute("UPDATE budget_item SET popis_old = popis WHERE popis_old IS NULL AND popis IS NOT NULL AND popis != ''")
    
    # Pokud nemáme typ, nastav výchozí hodnotu
    if 'typ' in columns_after:
        cursor.execute("SELECT COUNT(*) FROM budget_item WHERE typ IS NULL OR typ = ''")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"Nastavuji výchozí typ 'naklad' pro {count} záznamů...")
            cursor.execute("UPDATE budget_item SET typ = 'naklad' WHERE typ IS NULL OR typ = ''")
    
    # Pokud nemáme ucet, nastav výchozí hodnotu (prázdný string je OK, protože nullable=False s default="")
    if 'ucet' in columns_after:
        cursor.execute("SELECT COUNT(*) FROM budget_item WHERE ucet IS NULL")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"Nastavuji výchozí ucet '' pro {count} záznamů...")
            cursor.execute("UPDATE budget_item SET ucet = '' WHERE ucet IS NULL")
    
    conn.commit()
    print("✅ Migrace dokončena!")
    
    # Zobraz finální schéma
    cursor.execute("PRAGMA table_info(budget_item)")
    final_columns = [col[1] for col in cursor.fetchall()]
    print(f"Finální sloupce: {final_columns}")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Chyba při migraci: {e}")
    raise
finally:
    conn.close()
