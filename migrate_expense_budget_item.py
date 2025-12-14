#!/usr/bin/env python3
"""
Migrace databáze - změna budget_item_id na NOT NULL a vytvoření tabulky monthly_budget_item
"""

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / 'library_budget.db'

if not db_path.exists():
    print("Databáze neexistuje.")
    exit(1)

print(f"Migrace databáze: {db_path}")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

try:
    # 1. Zkontroluj, zda existují výdaje bez budget_item_id
    cursor.execute("SELECT COUNT(*) FROM expense WHERE budget_item_id IS NULL")
    count_without = cursor.fetchone()[0]
    
    if count_without > 0:
        print(f"⚠️  Nalezeno {count_without} výdajů bez budget_item_id")
        print("Vytvářím dočasnou položku rozpočtu pro tyto výdaje...")
        
        # Najdi hlavní rozpočet
        cursor.execute("SELECT id FROM budget WHERE hlavni = 1 AND aktivni = 1 LIMIT 1")
        hlavni = cursor.fetchone()
        
        if hlavni:
            hlavni_id = hlavni[0]
            
            # Najdi nebo vytvoř položku "Nepřiřazené výdaje"
            cursor.execute("""
                SELECT id FROM budget_item 
                WHERE budget_id = ? AND ucet = 'UNASSIGNED' AND aktivni = 1
            """, (hlavni_id,))
            unassigned = cursor.fetchone()
            
            if not unassigned:
                # Vytvoř položku
                cursor.execute("""
                    INSERT INTO budget_item 
                    (budget_id, ucet, popis, typ, castka, aktivni, datum_vytvoreni, poradi)
                    VALUES (?, 'UNASSIGNED', 'Nepřiřazené výdaje', 'naklad', 0, 1, datetime('now'), 0)
                """, (hlavni_id,))
                unassigned_id = cursor.lastrowid
                print(f"✅ Vytvořena položka rozpočtu ID {unassigned_id} pro nepřiřazené výdaje")
            else:
                unassigned_id = unassigned[0]
            
            # Přiřaď všechny výdaje bez budget_item_id
            cursor.execute("""
                UPDATE expense SET budget_item_id = ? WHERE budget_item_id IS NULL
            """, (unassigned_id,))
            print(f"✅ Přiřazeno {count_without} výdajů k položce rozpočtu")
    
    # 2. Vytvoř novou tabulku expense_new s NOT NULL budget_item_id
    print("\nVytvářím novou tabulku expense s NOT NULL budget_item_id...")
    cursor.execute("DROP TABLE IF EXISTS expense_new")
    cursor.execute("""
        CREATE TABLE expense_new (
            id INTEGER NOT NULL,
            budget_id INTEGER NOT NULL,
            budget_item_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            subcategory_id INTEGER,
            projekt_id INTEGER,
            vydaj_projektu_id INTEGER,
            personnel_id INTEGER,
            user_id INTEGER,
            castka NUMERIC(12, 2) NOT NULL,
            datum DATETIME NOT NULL,
            popis VARCHAR(300) NOT NULL,
            cis_faktury VARCHAR(50),
            dodavatel VARCHAR(200),
            poznamka TEXT,
            typ VARCHAR(20) NOT NULL,
            mesic INTEGER NOT NULL,
            rok INTEGER NOT NULL,
            datum_vytvoreni DATETIME NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(budget_id) REFERENCES budget (id),
            FOREIGN KEY(budget_item_id) REFERENCES budget_item (id),
            FOREIGN KEY(category_id) REFERENCES budget_category (id),
            FOREIGN KEY(projekt_id) REFERENCES projekt (id),
            FOREIGN KEY(personnel_id) REFERENCES zamestnanec_oon (id),
            FOREIGN KEY(user_id) REFERENCES user (id)
        )
    """)
    
    # Zkopíruj data - explicitně vyber sloupce a nahraď NULL hodnoty
    cursor.execute("SELECT COUNT(*) FROM expense")
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"Kopíruji {count} záznamů...")
        cursor.execute("""
            INSERT INTO expense_new (
                id, budget_id, budget_item_id, category_id, subcategory_id,
                projekt_id, vydaj_projektu_id, personnel_id, user_id,
                castka, datum, popis, cis_faktury, dodavatel, poznamka,
                typ, mesic, rok, datum_vytvoreni
            )
            SELECT 
                id, budget_id, budget_item_id, category_id, subcategory_id,
                projekt_id, vydaj_projektu_id, personnel_id, user_id,
                castka, 
                COALESCE(datum, datetime('now')) as datum,
                popis, cis_faktury, dodavatel, poznamka,
                COALESCE(typ, 'bezny') as typ,
                COALESCE(mesic, CAST(strftime('%m', COALESCE(datum, datetime('now'))) AS INTEGER)) as mesic,
                COALESCE(rok, CAST(strftime('%Y', COALESCE(datum, datetime('now'))) AS INTEGER)) as rok,
                COALESCE(datum_vytvoreni, datetime('now')) as datum_vytvoreni
            FROM expense
        """)
        print(f"✅ Zkopírováno {count} záznamů")
    
    # Smazat starou tabulku
    print("Mažu starou tabulku expense...")
    cursor.execute("DROP TABLE expense")
    
    # Přejmenovat novou tabulku
    print("Přejmenovávám tabulku...")
    cursor.execute("ALTER TABLE expense_new RENAME TO expense")
    
    # 3. Vytvoř tabulku monthly_budget_item
    print("\nVytvářím tabulku monthly_budget_item...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monthly_budget_item (
            id INTEGER NOT NULL,
            budget_item_id INTEGER NOT NULL,
            mesic INTEGER NOT NULL,
            rok INTEGER NOT NULL,
            souhrnne_vydaje NUMERIC(12, 2) NOT NULL DEFAULT 0,
            poznamka TEXT,
            aktualizoval VARCHAR(200),
            datum_aktualizace DATETIME NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(budget_item_id) REFERENCES budget_item (id),
            UNIQUE(budget_item_id, mesic, rok)
        )
    """)
    print("✅ Tabulka monthly_budget_item vytvořena")
    
    conn.commit()
    print("\n✅ Migrace dokončena!")
    
except Exception as e:
    conn.rollback()
    print(f"❌ Chyba při migraci: {e}")
    import traceback
    traceback.print_exc()
    raise
finally:
    conn.close()
