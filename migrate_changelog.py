"""
Migrační skript pro vytvoření tabulky changelog
"""
import sqlite3
from pathlib import Path

def migrate():
    """Vytvoří tabulku changelog"""
    db_path = Path(__file__).parent / 'library_budget.db'
    
    if not db_path.exists():
        print(f"Databáze {db_path} neexistuje!")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Vytvoř tabulku changelog
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS changelog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datum DATETIME NOT NULL,
                verze VARCHAR(20),
                typ VARCHAR(20) NOT NULL DEFAULT 'zmena',
                modul VARCHAR(50),
                nadpis VARCHAR(200) NOT NULL,
                popis TEXT NOT NULL,
                autor VARCHAR(100),
                aktivni BOOLEAN DEFAULT 1
            )
        """)
        
        # Vytvoř index
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_changelog_datum ON changelog(datum DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_changelog_verze ON changelog(verze)")
        
        conn.commit()
        print("✓ Tabulka changelog byla vytvořena")
        
    except Exception as e:
        conn.rollback()
        print(f"Chyba při migraci: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
