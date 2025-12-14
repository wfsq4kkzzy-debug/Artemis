"""
Migrační skript pro vytvoření tabulek pro modul služeb
"""
import sqlite3
from pathlib import Path

def migrate():
    """Vytvoří tabulky pro služby"""
    db_path = Path(__file__).parent / 'library_budget.db'
    
    if not db_path.exists():
        print(f"Databáze {db_path} neexistuje!")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Vytvoř tabulku sluzba_template
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sluzba_template (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nazev VARCHAR(200) NOT NULL,
                typ VARCHAR(20) NOT NULL,
                oddeleni VARCHAR(100) NOT NULL,
                den_v_tydnu INTEGER,
                zamestnanec_id INTEGER,
                aktivni BOOLEAN DEFAULT 1,
                datum_vytvoreni DATETIME NOT NULL,
                poznamka TEXT,
                rotujici_seznam TEXT,
                FOREIGN KEY (zamestnanec_id) REFERENCES zamestnanec_oon(id)
            )
        """)
        
        # Vytvoř tabulku sluzba
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sluzba (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER,
                datum DATE NOT NULL,
                den_v_tydnu INTEGER NOT NULL,
                oddeleni VARCHAR(100) NOT NULL,
                zamestnanec_id INTEGER NOT NULL,
                typ VARCHAR(20) NOT NULL,
                poznamka TEXT,
                datum_vytvoreni DATETIME NOT NULL,
                FOREIGN KEY (template_id) REFERENCES sluzba_template(id),
                FOREIGN KEY (zamestnanec_id) REFERENCES zamestnanec_oon(id),
                UNIQUE(datum, oddeleni)
            )
        """)
        
        # Vytvoř indexy
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sluzba_datum ON sluzba(datum)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sluzba_template ON sluzba(template_id)")
        
        conn.commit()
        print("✓ Tabulky pro služby byly vytvořeny")
        
    except Exception as e:
        conn.rollback()
        print(f"Chyba při migraci: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
