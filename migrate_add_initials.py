#!/usr/bin/env python3
"""
Migrační script pro přidání logování změn s iniciálami
- Přidá sloupec created_by_initials do vydaj_projektu, termin, zprava, znalost
"""

import sqlite3
from pathlib import Path

def migrate_add_initials():
    """Přidá sloupce pro iniciály"""
    basedir = Path(__file__).parent
    db_path = basedir / 'library_budget.db'
    
    if not db_path.exists():
        print(f"Databáze {db_path} neexistuje.")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        tables = [
            ('vydaj_projektu', 'VydajProjektu'),
            ('termin', 'Termin'),
            ('zprava', 'Zprava'),
            ('znalost', 'Znalost')
        ]
        
        for table_name, model_name in tables:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'created_by_initials' not in columns:
                print(f"Přidávám sloupec created_by_initials do {table_name}...")
                cursor.execute(f"""
                    ALTER TABLE {table_name} 
                    ADD COLUMN created_by_initials VARCHAR(10)
                """)
                print(f"✓ Sloupec created_by_initials přidán do {table_name}")
            else:
                print(f"✓ Sloupec created_by_initials již existuje v {table_name}")
        
        conn.commit()
        print("\n✅ Migrace dokončena!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Chyba: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Migrace: Přidání logování změn s iniciálami")
    print("=" * 60)
    migrate_add_initials()
