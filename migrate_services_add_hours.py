"""
Migrační skript pro přidání polí hodiny_od a hodiny_do do tabulek služeb
"""
import sqlite3
from pathlib import Path

def migrate():
    """Přidá pole hodiny_od a hodiny_do do tabulek"""
    db_path = Path(__file__).parent / 'library_budget.db'
    
    if not db_path.exists():
        print(f"Databáze {db_path} neexistuje!")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Zkontroluj, zda sloupce už existují
        cursor.execute("PRAGMA table_info(sluzba_template)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'hodiny_od' not in columns:
            cursor.execute("ALTER TABLE sluzba_template ADD COLUMN hodiny_od VARCHAR(5) DEFAULT '09:00'")
            print("✓ Přidán sloupec hodiny_od do sluzba_template")
        else:
            print("Sloupec hodiny_od již existuje v sluzba_template")
        
        if 'hodiny_do' not in columns:
            cursor.execute("ALTER TABLE sluzba_template ADD COLUMN hodiny_do VARCHAR(5) DEFAULT '17:00'")
            print("✓ Přidán sloupec hodiny_do do sluzba_template")
        else:
            print("Sloupec hodiny_do již existuje v sluzba_template")
        
        # Pro tabulku sluzba
        cursor.execute("PRAGMA table_info(sluzba)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'hodiny_od' not in columns:
            cursor.execute("ALTER TABLE sluzba ADD COLUMN hodiny_od VARCHAR(5) DEFAULT '09:00'")
            print("✓ Přidán sloupec hodiny_od do sluzba")
        else:
            print("Sloupec hodiny_od již existuje v sluzba")
        
        if 'hodiny_do' not in columns:
            cursor.execute("ALTER TABLE sluzba ADD COLUMN hodiny_do VARCHAR(5) DEFAULT '17:00'")
            print("✓ Přidán sloupec hodiny_do do sluzba")
        else:
            print("Sloupec hodiny_do již existuje v sluzba")
        
        conn.commit()
        print("✓ Migrace dokončena")
        
    except Exception as e:
        conn.rollback()
        print(f"Chyba při migraci: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
