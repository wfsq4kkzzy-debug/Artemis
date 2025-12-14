"""
Migrační skript pro přejmenování sloupců hodiny_od/do na hodina_od/do
"""
import sqlite3
from pathlib import Path

def migrate():
    """Přejmenuje sloupce hodiny_od/do na hodina_od/do"""
    db_path = Path(__file__).parent / 'library_budget.db'
    
    if not db_path.exists():
        print(f"Databáze {db_path} neexistuje!")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Zkontroluj, zda sloupce hodiny_od existují
        cursor.execute("PRAGMA table_info(sluzba_template)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'hodiny_od' in columns and 'hodina_od' not in columns:
            # SQLite nepodporuje RENAME COLUMN přímo, musíme vytvořit novou tabulku
            print("Přejmenovávám sloupce v sluzba_template...")
            cursor.execute("""
                CREATE TABLE sluzba_template_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nazev VARCHAR(200) NOT NULL,
                    typ VARCHAR(20) NOT NULL,
                    oddeleni VARCHAR(20) NOT NULL,
                    den_v_tydnu INTEGER,
                    hodina_od VARCHAR(10) NOT NULL DEFAULT '08:00',
                    hodina_do VARCHAR(10) NOT NULL DEFAULT '16:00',
                    zamestnanec_id INTEGER,
                    aktivni BOOLEAN DEFAULT 1,
                    datum_vytvoreni DATETIME NOT NULL,
                    poznamka TEXT,
                    rotujici_seznam TEXT,
                    FOREIGN KEY (zamestnanec_id) REFERENCES zamestnanec_oon(id)
                )
            """)
            cursor.execute("""
                INSERT INTO sluzba_template_new 
                SELECT id, nazev, typ, oddeleni, den_v_tydnu, 
                       COALESCE(hodiny_od, '08:00'), COALESCE(hodiny_do, '16:00'),
                       zamestnanec_id, aktivni, datum_vytvoreni, poznamka, rotujici_seznam
                FROM sluzba_template
            """)
            cursor.execute("DROP TABLE sluzba_template")
            cursor.execute("ALTER TABLE sluzba_template_new RENAME TO sluzba_template")
            print("✓ Sloupce přejmenovány v sluzba_template")
        else:
            print("Sloupce již mají správné názvy v sluzba_template")
        
        # Pro tabulku sluzba
        cursor.execute("PRAGMA table_info(sluzba)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'hodiny_od' in columns and 'hodina_od' not in columns:
            print("Přejmenovávám sloupce v sluzba...")
            cursor.execute("""
                CREATE TABLE sluzba_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_id INTEGER,
                    datum DATE NOT NULL,
                    den_v_tydnu INTEGER NOT NULL,
                    oddeleni VARCHAR(20) NOT NULL,
                    hodina_od VARCHAR(10) NOT NULL DEFAULT '08:00',
                    hodina_do VARCHAR(10) NOT NULL DEFAULT '16:00',
                    zamestnanec_id INTEGER NOT NULL,
                    typ VARCHAR(20) NOT NULL,
                    poznamka TEXT,
                    datum_vytvoreni DATETIME NOT NULL,
                    FOREIGN KEY (template_id) REFERENCES sluzba_template(id),
                    FOREIGN KEY (zamestnanec_id) REFERENCES zamestnanec_oon(id),
                    UNIQUE(datum, oddeleni)
                )
            """)
            cursor.execute("""
                INSERT INTO sluzba_new 
                SELECT id, template_id, datum, den_v_tydnu, oddeleni,
                       COALESCE(hodiny_od, '08:00'), COALESCE(hodiny_do, '16:00'),
                       zamestnanec_id, typ, poznamka, datum_vytvoreni
                FROM sluzba
            """)
            cursor.execute("DROP TABLE sluzba")
            cursor.execute("ALTER TABLE sluzba_new RENAME TO sluzba")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sluzba_datum ON sluzba(datum)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sluzba_template ON sluzba(template_id)")
            print("✓ Sloupce přejmenovány v sluzba")
        else:
            print("Sloupce již mají správné názvy v sluzba")
        
        conn.commit()
        print("✓ Migrace dokončena")
        
    except Exception as e:
        conn.rollback()
        print(f"Chyba při migraci: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
