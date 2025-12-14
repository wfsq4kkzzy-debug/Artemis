"""
Migrační skript pro odstranění vztahů mezi projekty a obecným rozpočtem
Odstraní sloupce projekt_id a vydaj_projektu_id z tabulky expense
"""
import sqlite3
from pathlib import Path

def migrate():
    """Odstraní sloupce projekt_id a vydaj_projektu_id z tabulky expense"""
    db_path = Path(__file__).parent / 'library_budget.db'
    
    if not db_path.exists():
        print(f"Databáze {db_path} neexistuje!")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # SQLite nepodporuje DROP COLUMN přímo, musíme tabulku převytvořit
        print("🔧 Odstraňuji vztahy mezi projekty a rozpočtem...")
        
        # 1. Vytvoř novou tabulku bez projekt_id a vydaj_projektu_id
        cursor.execute("""
            CREATE TABLE expense_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_id INTEGER NOT NULL,
                budget_item_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                subcategory_id INTEGER,
                personnel_id INTEGER,
                user_id INTEGER,
                castka NUMERIC(12, 2) NOT NULL,
                datum DATETIME NOT NULL,
                popis VARCHAR(300) NOT NULL,
                cis_faktury VARCHAR(50),
                dodavatel VARCHAR(200),
                poznamka TEXT,
                typ VARCHAR(20) NOT NULL DEFAULT 'bezny',
                mesic INTEGER NOT NULL,
                rok INTEGER NOT NULL,
                datum_vytvoreni DATETIME NOT NULL,
                FOREIGN KEY (budget_id) REFERENCES budget(id),
                FOREIGN KEY (budget_item_id) REFERENCES budget_item(id),
                FOREIGN KEY (category_id) REFERENCES budget_category(id),
                FOREIGN KEY (subcategory_id) REFERENCES budget_subcategory(id),
                FOREIGN KEY (personnel_id) REFERENCES zamestnanec_oon(id),
                FOREIGN KEY (user_id) REFERENCES user(id)
            )
        """)
        
        # 2. Zkopíruj data (bez projekt_id a vydaj_projektu_id)
        cursor.execute("""
            INSERT INTO expense_new 
            (id, budget_id, budget_item_id, category_id, subcategory_id, personnel_id, user_id,
             castka, datum, popis, cis_faktury, dodavatel, poznamka, typ, mesic, rok, datum_vytvoreni)
            SELECT 
                id, budget_id, budget_item_id, category_id, subcategory_id, personnel_id, user_id,
                castka, datum, popis, cis_faktury, dodavatel, poznamka, typ, mesic, rok, datum_vytvoreni
            FROM expense
        """)
        
        # 3. Smaž starou tabulku
        cursor.execute("DROP TABLE expense")
        
        # 4. Přejmenuj novou tabulku
        cursor.execute("ALTER TABLE expense_new RENAME TO expense")
        
        # 5. Vytvoř indexy
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expense_budget_id ON expense(budget_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expense_budget_item_id ON expense(budget_item_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expense_category_id ON expense(category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expense_datum ON expense(datum)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expense_rok_mesic ON expense(rok, mesic)")
        
        conn.commit()
        print("✓ Sloupce projekt_id a vydaj_projektu_id byly odstraněny z tabulky expense")
        print("✓ Vztahy mezi projekty a obecným rozpočtem byly zrušeny")
        
    except Exception as e:
        conn.rollback()
        print(f"Chyba při migraci: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
