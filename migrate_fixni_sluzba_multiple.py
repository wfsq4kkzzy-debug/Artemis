#!/usr/bin/env python
"""
Migrace: Odstranění UniqueConstraint z tabulky sluzba
Umožňuje více služeb na jeden den/oddělení (různí zaměstnanci, různé časy)
"""
import sqlite3
import os
import re

DB_PATH = 'library_budget.db'

def migrate():
    """Odstraní UniqueConstraint z tabulky sluzba"""
    if not os.path.exists(DB_PATH):
        print(f"Databáze {DB_PATH} neexistuje!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Zkontroluj, zda UniqueConstraint existuje
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='sluzba'")
        create_sql = cursor.fetchone()
        
        if not create_sql:
            print("Tabulka 'sluzba' neexistuje!")
            return
        
        sql = create_sql[0]
        
        # Pokud UniqueConstraint neexistuje, není potřeba migrace
        if 'unique_sluzba_datum_oddeleni' not in sql:
            print("UniqueConstraint 'unique_sluzba_datum_oddeleni' již neexistuje. Migrace není nutná.")
            return
        
        print("Odstraňuji UniqueConstraint z tabulky sluzba...")
        print(f"Původní SQL má {len(sql)} znaků")
        
        # Zkontroluj, zda už neexistuje sluzba_new (z předchozího pokusu)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sluzba_new'")
        if cursor.fetchone():
            print("Odstraňuji starou tabulku sluzba_new...")
            cursor.execute("DROP TABLE sluzba_new")
        
        # Odstraň CONSTRAINT unique_sluzba_datum_oddeleni
        # Najdi a odstraň řádek s tímto constraintem
        lines = sql.split('\n')
        new_lines = []
        for line in lines:
            stripped = line.strip()
            # Přeskoč řádky s unique_sluzba_datum_oddeleni
            if 'unique_sluzba_datum_oddeleni' in stripped.lower():
                # Odstraň čárku z předchozího řádku, pokud existuje
                if new_lines and new_lines[-1].rstrip().endswith(','):
                    new_lines[-1] = new_lines[-1].rstrip().rstrip(',')
                continue
            new_lines.append(line)
        
        new_sql = '\n'.join(new_lines)
        
        # Také odstraň pomocí regexu pro jistotu
        new_sql = re.sub(r',?\s*CONSTRAINT\s+unique_sluzba_datum_oddeleni\s+UNIQUE\s*\([^)]+\)', '', new_sql, flags=re.IGNORECASE | re.MULTILINE)
        new_sql = re.sub(r',?\s*CONSTRAINT\s+unique_sluzba_datum_oddeleni\s+', '', new_sql, flags=re.IGNORECASE | re.MULTILINE)
        
        # Změň název tabulky
        new_sql = re.sub(r'CREATE\s+TABLE\s+"?sluzba"?\s*\(', 'CREATE TABLE sluzba_new (', new_sql, flags=re.IGNORECASE)
        
        print(f"Nový SQL má {len(new_sql)} znaků")
        print("Vytvářím novou tabulku...")
        
        # Vytvoř novou tabulku
        cursor.execute(new_sql)
        print("✓ Nová tabulka vytvořena")
        
        # 2. Zkopíruj data
        print("Kopíruji data...")
        cursor.execute("""
            INSERT INTO sluzba_new 
            SELECT * FROM sluzba
        """)
        print(f"✓ Zkopírováno {cursor.rowcount} záznamů")
        
        # 3. Smaž starou tabulku
        print("Mažu starou tabulku...")
        cursor.execute("DROP TABLE sluzba")
        
        # 4. Přejmenuj novou tabulku
        print("Přejmenovávám tabulku...")
        cursor.execute("ALTER TABLE sluzba_new RENAME TO sluzba")
        
        conn.commit()
        print("✓ UniqueConstraint byl úspěšně odstraněn. Nyní je možné mít více služeb na jeden den/oddělení.")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Chyba při migraci: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    print("Spouštím migraci: Odstranění UniqueConstraint z tabulky sluzba...")
    migrate()
    print("Migrace dokončena.")
