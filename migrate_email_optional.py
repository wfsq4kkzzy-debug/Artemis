#!/usr/bin/env python
"""
Migrace: Změna emailu z povinného na volitelný
SQLite vyžaduje přestavbu tabulky pro změnu NOT NULL constraint
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = 'library_budget.db'

def migrate():
    """Změní email z povinného na volitelný přestavbou tabulky"""
    if not os.path.exists(DB_PATH):
        print(f"Databáze {DB_PATH} neexistuje!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Zkontroluj, zda email má NOT NULL
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='user'")
        create_sql = cursor.fetchone()
        
        if not create_sql:
            print("Tabulka 'user' neexistuje!")
            return
        
        sql = create_sql[0]
        
        # Pokud email už nemá NOT NULL, není potřeba migrace
        if 'email VARCHAR(120) NOT NULL' not in sql and 'email VARCHAR(120)NOT NULL' not in sql:
            print("Email již nemá NOT NULL constraint. Migrace není nutná.")
            return
        
        print("Přestavuji tabulku user pro volitelný email...")
        
        # 1. Vytvoř novou tabulku s volitelným emailem
        new_sql = sql.replace('email VARCHAR(120) NOT NULL', 'email VARCHAR(120)')
        new_sql = new_sql.replace('email VARCHAR(120)NOT NULL', 'email VARCHAR(120)')
        
        # Odstraň UNIQUE constraint z emailu (nebo ho ponecháme, ale povolíme NULL)
        # SQLite podporuje UNIQUE s NULL hodnotami
        new_sql = new_sql.replace('CREATE TABLE user', 'CREATE TABLE user_new')
        
        # Vytvoř novou tabulku
        cursor.execute(new_sql)
        
        # 2. Zkopíruj data (email zůstane stejný, ale constraint je volitelný)
        cursor.execute("""
            INSERT INTO user_new 
            SELECT * FROM user
        """)
        
        # 3. Smaž starou tabulku
        cursor.execute("DROP TABLE user")
        
        # 4. Přejmenuj novou tabulku
        cursor.execute("ALTER TABLE user_new RENAME TO user")
        
        # 5. Obnov indexy a constrainty
        # UNIQUE constraint na email už je v CREATE TABLE
        # UNIQUE constraint na personnel_id už je v CREATE TABLE
        
        conn.commit()
        print("✓ Tabulka byla úspěšně přestavěna. Email je nyní volitelný.")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Chyba při migraci: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    print("Spouštím migraci: Změna emailu z povinného na volitelný...")
    migrate()
    print("Migrace dokončena.")
