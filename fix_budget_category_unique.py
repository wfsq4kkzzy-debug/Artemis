#!/usr/bin/env python3
"""
Oprava UNIQUE constraint na budget_category - odstranění globálního UNIQUE na kod a nazev
Kódy a názvy by měly být unikátní pouze v rámci jednoho rozpočtu, ne globálně
"""

import sqlite3
from pathlib import Path

def fix_budget_category_constraints():
    """Odstraní UNIQUE constraint na kod a nazev v budget_category"""
    basedir = Path(__file__).parent
    db_path = basedir / 'library_budget.db'
    
    if not db_path.exists():
        print(f"Databáze {db_path} neexistuje.")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Zkontroluj existující indexy
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='budget_category'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        print(f"Nalezené indexy: {indexes}")
        
        # Odstraň UNIQUE indexy na kod a nazev (pokud existují)
        indexes_to_drop = []
        for idx_name in indexes:
            if 'kod' in idx_name.lower() or 'nazev' in idx_name.lower():
                if 'unique' in idx_name.lower() or 'autoindex' in idx_name.lower():
                    indexes_to_drop.append(idx_name)
        
        for idx_name in indexes_to_drop:
            print(f"Odstraňuji index: {idx_name}")
            cursor.execute(f"DROP INDEX IF EXISTS {idx_name}")
        
        # Vytvoř novou tabulku bez UNIQUE constraint (pokud je to potřeba)
        # SQLite neumožňuje jednoduše odstranit UNIQUE constraint, takže musíme:
        # 1. Vytvořit novou tabulku bez constraint
        # 2. Zkopírovat data
        # 3. Smazat starou tabulku
        # 4. Přejmenovat novou tabulku
        
        # Zkontroluj, zda má tabulka UNIQUE constraint v definici
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='budget_category'")
        table_sql = cursor.fetchone()
        
        if table_sql and table_sql[0]:
            sql = table_sql[0]
            if 'UNIQUE' in sql.upper() and ('kod' in sql.lower() or 'nazev' in sql.lower()):
                print("\n⚠️  Tabulka má UNIQUE constraint v definici. Musím ji přecreovat...")
                
                # Vytvoř novou tabulku bez UNIQUE
                cursor.execute("""
                    CREATE TABLE budget_category_new (
                        id INTEGER NOT NULL PRIMARY KEY,
                        budget_id INTEGER NOT NULL,
                        typ VARCHAR(30) NOT NULL,
                        nazev VARCHAR(100) NOT NULL,
                        kod VARCHAR(20),
                        popis TEXT,
                        barva VARCHAR(7),
                        poradi INTEGER NOT NULL DEFAULT 0,
                        aktivni BOOLEAN DEFAULT 1,
                        datum_vytvoreni DATETIME NOT NULL,
                        FOREIGN KEY(budget_id) REFERENCES budget (id)
                    )
                """)
                
                # Zkopíruj data
                cursor.execute("""
                    INSERT INTO budget_category_new 
                    SELECT id, budget_id, typ, nazev, kod, popis, barva, poradi, aktivni, datum_vytvoreni
                    FROM budget_category
                """)
                
                # Smazat starou tabulku
                cursor.execute("DROP TABLE budget_category")
                
                # Přejmenovat novou tabulku
                cursor.execute("ALTER TABLE budget_category_new RENAME TO budget_category")
                
                print("✓ Tabulka přecreována bez UNIQUE constraint")
            else:
                print("✓ Tabulka nemá UNIQUE constraint v definici")
        
        conn.commit()
        print("\n✅ Oprava dokončena!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Chyba: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Oprava UNIQUE constraint na budget_category")
    print("=" * 60)
    fix_budget_category_constraints()
