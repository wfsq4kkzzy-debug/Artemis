#!/usr/bin/env python
"""
Migrace: Přidání sloupce aktualni_stav do tabulky monthly_budget_item
"""
import sqlite3
import os

DB_PATH = 'library_budget.db'

def migrate():
    """Přidá sloupec aktualni_stav do tabulky monthly_budget_item"""
    if not os.path.exists(DB_PATH):
        print(f"Databáze {DB_PATH} neexistuje!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Zkontroluj, zda sloupec už existuje
        cursor.execute("PRAGMA table_info(monthly_budget_item)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'aktualni_stav' in columns:
            print("Sloupec 'aktualni_stav' již existuje. Migrace není nutná.")
            return
        
        # Přidej sloupec
        cursor.execute("ALTER TABLE monthly_budget_item ADD COLUMN aktualni_stav NUMERIC(12, 2)")
        
        conn.commit()
        print("✓ Sloupec 'aktualni_stav' byl úspěšně přidán do tabulky 'monthly_budget_item'")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Chyba při migraci: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    print("Spouštím migraci: Přidání sloupce aktualni_stav...")
    migrate()
    print("Migrace dokončena.")
