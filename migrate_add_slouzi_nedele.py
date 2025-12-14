#!/usr/bin/env python
"""
Migrace: Přidání sloupce slouzi_nedele do tabulky user
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = 'library_budget.db'

def migrate():
    """Přidá sloupec slouzi_nedele do tabulky user"""
    if not os.path.exists(DB_PATH):
        print(f"Databáze {DB_PATH} neexistuje!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Zkontroluj, zda sloupec už existuje
        cursor.execute("PRAGMA table_info(user)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'slouzi_nedele' in columns:
            print("Sloupec 'slouzi_nedele' již existuje. Migrace není nutná.")
            return
        
        # SQLite nepodporuje ALTER TABLE ADD COLUMN s DEFAULT přímo, ale můžeme použít:
        cursor.execute("ALTER TABLE user ADD COLUMN slouzi_nedele BOOLEAN DEFAULT 0")
        
        conn.commit()
        print("✓ Sloupec 'slouzi_nedele' byl úspěšně přidán do tabulky 'user'")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Chyba při migraci: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    print("Spouštím migraci: Přidání sloupce slouzi_nedele...")
    migrate()
    print("Migrace dokončena.")
