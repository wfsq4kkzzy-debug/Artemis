"""
Migrační skript pro přidání pole to_user_id do tabulky zprava
"""
import sqlite3
import os
from pathlib import Path

def migrate():
    """Přidá pole to_user_id do tabulky zprava"""
    db_path = Path(__file__).parent / 'library_budget.db'
    
    if not db_path.exists():
        print(f"Databáze {db_path} neexistuje!")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Zkontroluj, zda sloupec už existuje
        cursor.execute("PRAGMA table_info(zprava)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'to_user_id' in columns:
            print("Sloupec to_user_id již existuje v tabulce zprava")
            return
        
        # Přidej sloupec
        cursor.execute("ALTER TABLE zprava ADD COLUMN to_user_id INTEGER")
        
        # Přidej foreign key constraint (SQLite to podporuje od verze 3.37.0)
        # Pokud verze nepodporuje, přeskočíme
        try:
            cursor.execute("""
                CREATE TABLE zprava_new (
                    id INTEGER PRIMARY KEY,
                    projekt_id INTEGER NOT NULL,
                    autor VARCHAR(200) NOT NULL,
                    obsah TEXT NOT NULL,
                    datum DATETIME NOT NULL,
                    typ VARCHAR(20) NOT NULL DEFAULT 'poznamka',
                    created_by_initials VARCHAR(10),
                    to_user_id INTEGER,
                    FOREIGN KEY (projekt_id) REFERENCES projekt(id),
                    FOREIGN KEY (to_user_id) REFERENCES user(id)
                )
            """)
            cursor.execute("""
                INSERT INTO zprava_new 
                SELECT id, projekt_id, autor, obsah, datum, typ, created_by_initials, to_user_id 
                FROM zprava
            """)
            cursor.execute("DROP TABLE zprava")
            cursor.execute("ALTER TABLE zprava_new RENAME TO zprava")
        except sqlite3.OperationalError as e:
            # Pokud foreign key constraint nefunguje, necháme to tak
            print(f"Poznámka: Foreign key constraint nelze přidat: {e}")
        
        conn.commit()
        print("✓ Sloupec to_user_id byl přidán do tabulky zprava")
        
    except Exception as e:
        conn.rollback()
        print(f"Chyba při migraci: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
