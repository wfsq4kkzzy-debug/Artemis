"""
Migrace databáze pro verzi 0.73.1
Přidá sloupec rozpocet do tabulky projekt
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """Přidá sloupec rozpocet do tabulky projekt"""
    # Databáze je v kořenovém adresáři projektu
    db_path = Path(__file__).parent / 'library_budget.db'
    
    if not db_path.exists():
        print(f"❌ Databáze nenalezena: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Zkontroluj, jestli sloupec už existuje
        cursor.execute("PRAGMA table_info(projekt)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'rozpocet' in columns:
            print("✅ Sloupec 'rozpocet' již existuje v tabulce 'projekt'")
            conn.close()
            return True
        
        # Přidej sloupec rozpocet do tabulky projekt
        if 'rozpocet' not in columns:
            print("🔄 Přidávám sloupec 'rozpocet' do tabulky 'projekt'...")
            cursor.execute("ALTER TABLE projekt ADD COLUMN rozpocet NUMERIC(12, 2) DEFAULT 0 NOT NULL")
            # Aktualizuj existující projekty - nastav rozpočet na 0
            cursor.execute("UPDATE projekt SET rozpocet = 0 WHERE rozpocet IS NULL")
        
        # Zkontroluj tabulku vydaj_projektu
        cursor.execute("PRAGMA table_info(vydaj_projektu)")
        vydaj_columns = [col[1] for col in cursor.fetchall()]
        
        # Přidej sloupec poznamka do tabulky vydaj_projektu
        if 'poznamka' not in vydaj_columns:
            print("🔄 Přidávám sloupec 'poznamka' do tabulky 'vydaj_projektu'...")
            try:
                cursor.execute("ALTER TABLE vydaj_projektu ADD COLUMN poznamka TEXT")
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e).lower():
                    raise
        
        # Kategorie by měla být nullable, ale pokud neexistuje, přidáme ji
        if 'kategorie' not in vydaj_columns:
            print("🔄 Přidávám sloupec 'kategorie' do tabulky 'vydaj_projektu'...")
            try:
                cursor.execute("ALTER TABLE vydaj_projektu ADD COLUMN kategorie VARCHAR(100) DEFAULT ''")
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e).lower():
                    raise
        
        conn.commit()
        conn.close()
        
        print("✅ Migrace dokončena úspěšně!")
        return True
        
    except Exception as e:
        print(f"❌ Chyba při migraci: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Migrace databáze pro verzi 0.73.1")
    print("=" * 60)
    migrate_database()
