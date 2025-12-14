"""
Migrační skript pro přidání hodin od-do do služeb
"""
import sqlite3
from pathlib import Path

def migrate():
    """Přidá sloupce hodina_od a hodina_do do tabulek"""
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
        
        if 'hodina_od' not in columns:
            cursor.execute("ALTER TABLE sluzba_template ADD COLUMN hodina_od VARCHAR(10) DEFAULT '08:00'")
            print("✓ Přidán sloupec hodina_od do sluzba_template")
        else:
            print("Sloupec hodina_od již existuje v sluzba_template")
        
        if 'hodina_do' not in columns:
            cursor.execute("ALTER TABLE sluzba_template ADD COLUMN hodina_do VARCHAR(10) DEFAULT '16:00'")
            print("✓ Přidán sloupec hodina_do do sluzba_template")
        else:
            print("Sloupec hodina_do již existuje v sluzba_template")
        
        # Pro tabulku sluzba
        cursor.execute("PRAGMA table_info(sluzba)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'hodina_od' not in columns:
            cursor.execute("ALTER TABLE sluzba ADD COLUMN hodina_od VARCHAR(10) DEFAULT '08:00'")
            print("✓ Přidán sloupec hodina_od do sluzba")
        else:
            print("Sloupec hodina_od již existuje v sluzba")
        
        if 'hodina_do' not in columns:
            cursor.execute("ALTER TABLE sluzba ADD COLUMN hodina_do VARCHAR(10) DEFAULT '16:00'")
            print("✓ Přidán sloupec hodina_do do sluzba")
        else:
            print("Sloupec hodina_do již existuje v sluzba")
        
        # Aktualizuj existující záznamy s výchozími hodnotami
        cursor.execute("UPDATE sluzba_template SET hodina_od = '08:00' WHERE hodina_od IS NULL")
        cursor.execute("UPDATE sluzba_template SET hodina_do = '16:00' WHERE hodina_do IS NULL")
        cursor.execute("UPDATE sluzba SET hodina_od = '08:00' WHERE hodina_od IS NULL")
        cursor.execute("UPDATE sluzba SET hodina_do = '16:00' WHERE hodina_do IS NULL")
        
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
