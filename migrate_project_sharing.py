#!/usr/bin/env python3
"""
Migrační script pro přidání sdílení projektů
- Přidá sloupce created_by_user_id a created_by_personnel_id do projekt
- Vytvoří tabulku project_share pro sdílení projektů
"""

import sqlite3
from pathlib import Path

def migrate_project_sharing():
    """Přidá podporu pro sdílení projektů"""
    basedir = Path(__file__).parent
    db_path = basedir / 'library_budget.db'
    
    if not db_path.exists():
        print(f"Databáze {db_path} neexistuje.")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Zkontroluj, zda už sloupce existují
        cursor.execute("PRAGMA table_info(projekt)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Přidej created_by_user_id pokud neexistuje
        if 'created_by_user_id' not in columns:
            print("Přidávám sloupec created_by_user_id...")
            cursor.execute("""
                ALTER TABLE projekt 
                ADD COLUMN created_by_user_id INTEGER 
                REFERENCES user(id)
            """)
            print("✓ Sloupec created_by_user_id přidán")
        else:
            print("✓ Sloupec created_by_user_id již existuje")
        
        # Přidej created_by_personnel_id pokud neexistuje
        if 'created_by_personnel_id' not in columns:
            print("Přidávám sloupec created_by_personnel_id...")
            cursor.execute("""
                ALTER TABLE projekt 
                ADD COLUMN created_by_personnel_id INTEGER 
                REFERENCES zamestnanec_oon(id)
            """)
            print("✓ Sloupec created_by_personnel_id přidán")
        else:
            print("✓ Sloupec created_by_personnel_id již existuje")
        
        # Vytvoř tabulku project_share pokud neexistuje
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='project_share'
        """)
        if not cursor.fetchone():
            print("Vytvářím tabulku project_share...")
            cursor.execute("""
                CREATE TABLE project_share (
                    id INTEGER NOT NULL PRIMARY KEY,
                    projekt_id INTEGER NOT NULL,
                    shared_with_user_id INTEGER NOT NULL,
                    shared_by_user_id INTEGER NOT NULL,
                    permission VARCHAR(20) NOT NULL DEFAULT 'read',
                    datum_sdileni DATETIME NOT NULL,
                    poznamka TEXT,
                    aktivni BOOLEAN DEFAULT 1,
                    FOREIGN KEY(projekt_id) REFERENCES projekt (id),
                    FOREIGN KEY(shared_with_user_id) REFERENCES user (id),
                    FOREIGN KEY(shared_by_user_id) REFERENCES user (id),
                    UNIQUE(projekt_id, shared_with_user_id)
                )
            """)
            print("✓ Tabulka project_share vytvořena")
        else:
            print("✓ Tabulka project_share již existuje")
        
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
    print("Migrace: Sdílení projektů")
    print("=" * 60)
    migrate_project_sharing()
