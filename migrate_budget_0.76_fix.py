#!/usr/bin/env python3
"""
Migrace databáze pro verzi 0.76 - přidání výnosů a propojení projektů
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """Přidá chybějící sloupce a tabulky"""
    basedir = Path(__file__).parent
    db_path = basedir / 'library_budget.db'
    
    if not db_path.exists():
        print(f"Databáze {db_path} neexistuje. Bude vytvořena při prvním spuštění.")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # 1. Zkontroluj, zda sloupec vydaj_projektu_id existuje v expense
        cursor.execute("PRAGMA table_info(expense)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'vydaj_projektu_id' not in columns:
            print("Přidávám sloupec vydaj_projektu_id do tabulky expense...")
            cursor.execute("ALTER TABLE expense ADD COLUMN vydaj_projektu_id INTEGER")
            print("✓ Sloupec vydaj_projektu_id přidán")
        else:
            print("✓ Sloupec vydaj_projektu_id již existuje")
        
        # 2. Zkontroluj, zda tabulka revenue existuje
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='revenue'")
        if not cursor.fetchone():
            print("Vytvářím tabulku revenue...")
            cursor.execute("""
                CREATE TABLE revenue (
                    id INTEGER NOT NULL PRIMARY KEY,
                    budget_id INTEGER NOT NULL,
                    budget_item_id INTEGER,
                    category_id INTEGER NOT NULL,
                    subcategory_id INTEGER,
                    nazev VARCHAR(300) NOT NULL,
                    popis TEXT,
                    castka NUMERIC(12, 2) NOT NULL,
                    typ VARCHAR(20) NOT NULL DEFAULT 'jednorazovy',
                    datum DATETIME,
                    mesic INTEGER,
                    rok INTEGER NOT NULL,
                    datum_zacatku DATETIME,
                    datum_konce DATETIME,
                    frekvence VARCHAR(20),
                    mesice VARCHAR(50),
                    naplanovano BOOLEAN DEFAULT 0,
                    skutecne_prijato BOOLEAN DEFAULT 0,
                    cis_faktury VARCHAR(50),
                    odberatel VARCHAR(200),
                    poznamka TEXT,
                    datum_vytvoreni DATETIME NOT NULL,
                    datum_aktualizace DATETIME,
                    FOREIGN KEY(budget_id) REFERENCES budget (id),
                    FOREIGN KEY(budget_item_id) REFERENCES budget_item (id),
                    FOREIGN KEY(category_id) REFERENCES budget_category (id),
                    FOREIGN KEY(subcategory_id) REFERENCES budget_subcategory (id)
                )
            """)
            print("✓ Tabulka revenue vytvořena")
        else:
            print("✓ Tabulka revenue již existuje")
            # Zkontroluj, zda má sloupec budget_item_id
            cursor.execute("PRAGMA table_info(revenue)")
            revenue_columns = [col[1] for col in cursor.fetchall()]
            if 'budget_item_id' not in revenue_columns:
                print("Přidávám sloupec budget_item_id do tabulky revenue...")
                cursor.execute("ALTER TABLE revenue ADD COLUMN budget_item_id INTEGER")
                print("✓ Sloupec budget_item_id přidán do revenue")
            else:
                print("✓ Sloupec budget_item_id již existuje v revenue")
        
        # 3. Zkontroluj, zda budget_item má potřebné sloupce
        cursor.execute("PRAGMA table_info(budget_item)")
        budget_item_columns = [col[1] for col in cursor.fetchall()]
        
        needed_columns = {
            'ucet': 'VARCHAR(20)',
            'poducet': 'VARCHAR(20)',
            'typ': 'VARCHAR(20)',
            'popis_old': 'TEXT'
        }
        
        for col_name, col_type in needed_columns.items():
            if col_name not in budget_item_columns:
                print(f"Přidávám sloupec {col_name} do tabulky budget_item...")
                cursor.execute(f"ALTER TABLE budget_item ADD COLUMN {col_name} {col_type}")
                print(f"✓ Sloupec {col_name} přidán do budget_item")
            else:
                print(f"✓ Sloupec {col_name} již existuje v budget_item")
        
        # 4. Zkontroluj, zda expense má budget_item_id jako NOT NULL (mělo by být nullable=False podle modelu)
        # Ale v databázi to může být NULL, takže to necháme být
        
        conn.commit()
        print("\n✅ Migrace dokončena úspěšně!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Chyba při migraci: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Migrace databáze pro verzi 0.76")
    print("=" * 60)
    migrate_database()

