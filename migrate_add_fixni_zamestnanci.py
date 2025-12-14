#!/usr/bin/env python
"""
Migrace: Přidání sloupce fixni_zamestnanci do tabulky sluzba_template
"""
import sqlite3
import os

DB_PATH = 'library_budget.db'

def migrate():
    """Přidá sloupec fixni_zamestnanci do tabulky sluzba_template"""
    if not os.path.exists(DB_PATH):
        print(f"Databáze {DB_PATH} neexistuje!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Zkontroluj, zda sloupec už existuje
        cursor.execute("PRAGMA table_info(sluzba_template)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'fixni_zamestnanci' in columns:
            print("Sloupec 'fixni_zamestnanci' již existuje. Migrace není nutná.")
            return
        
        # Přidej sloupec
        cursor.execute("ALTER TABLE sluzba_template ADD COLUMN fixni_zamestnanci TEXT")
        
        conn.commit()
        print("✓ Sloupec 'fixni_zamestnanci' byl úspěšně přidán do tabulky 'sluzba_template'")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Chyba při migraci: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    print("Spouštím migraci: Přidání sloupce fixni_zamestnanci...")
    migrate()
    print("Migrace dokončena.")
