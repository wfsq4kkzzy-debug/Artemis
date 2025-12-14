"""
Migrační skript pro vytvoření tabulek pro výjimky a výměny služeb
"""
import sqlite3
from pathlib import Path

def migrate():
    """Vytvoří tabulky pro výjimky a výměny služeb"""
    db_path = Path(__file__).parent / 'library_budget.db'
    
    if not db_path.exists():
        print(f"Databáze {db_path} neexistuje!")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Přidej sloupce do tabulky sluzba
        try:
            cursor.execute("ALTER TABLE sluzba ADD COLUMN je_vynimka BOOLEAN DEFAULT 0")
            print("✓ Přidán sloupec je_vynimka do tabulky sluzba")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
            print("  Sloupec je_vynimka již existuje")
        
        try:
            cursor.execute("ALTER TABLE sluzba ADD COLUMN je_vymena BOOLEAN DEFAULT 0")
            print("✓ Přidán sloupec je_vymena do tabulky sluzba")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise
            print("  Sloupec je_vymena již existuje")
        
        # Vytvoř tabulku sluzba_vynimka
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sluzba_vynimka (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sluzba_id INTEGER NOT NULL,
                datum DATE NOT NULL,
                oddeleni VARCHAR(20) NOT NULL,
                hodina_od VARCHAR(10) NOT NULL,
                hodina_do VARCHAR(10) NOT NULL,
                zamestnanec_id INTEGER NOT NULL,
                poznamka TEXT,
                vytvoril_user_id INTEGER,
                datum_vytvoreni DATETIME NOT NULL,
                aktivni BOOLEAN DEFAULT 1,
                FOREIGN KEY (sluzba_id) REFERENCES sluzba(id),
                FOREIGN KEY (zamestnanec_id) REFERENCES zamestnanec_oon(id),
                FOREIGN KEY (vytvoril_user_id) REFERENCES user(id)
            )
        """)
        print("✓ Tabulka sluzba_vynimka byla vytvořena")
        
        # Vytvoř indexy
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vynimka_datum ON sluzba_vynimka(datum DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vynimka_sluzba ON sluzba_vynimka(sluzba_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vynimka_zamestnanec ON sluzba_vynimka(zamestnanec_id)")
        
        # Vytvoř tabulku sluzba_vymena
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sluzba_vymena (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sluzba1_id INTEGER NOT NULL,
                sluzba2_id INTEGER NOT NULL,
                zamestnanec1_id INTEGER NOT NULL,
                zamestnanec2_id INTEGER NOT NULL,
                poznamka TEXT,
                vytvoril_user_id INTEGER,
                schvaleno BOOLEAN DEFAULT 0,
                datum_vytvoreni DATETIME NOT NULL,
                aktivni BOOLEAN DEFAULT 1,
                FOREIGN KEY (sluzba1_id) REFERENCES sluzba(id),
                FOREIGN KEY (sluzba2_id) REFERENCES sluzba(id),
                FOREIGN KEY (zamestnanec1_id) REFERENCES zamestnanec_oon(id),
                FOREIGN KEY (zamestnanec2_id) REFERENCES zamestnanec_oon(id),
                FOREIGN KEY (vytvoril_user_id) REFERENCES user(id)
            )
        """)
        print("✓ Tabulka sluzba_vymena byla vytvořena")
        
        # Vytvoř indexy
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vymena_sluzba1 ON sluzba_vymena(sluzba1_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vymena_sluzba2 ON sluzba_vymena(sluzba2_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vymena_schvaleno ON sluzba_vymena(schvaleno)")
        
        conn.commit()
        print("✓ Migrace dokončena úspěšně")
        
    except Exception as e:
        conn.rollback()
        print(f"Chyba při migraci: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
