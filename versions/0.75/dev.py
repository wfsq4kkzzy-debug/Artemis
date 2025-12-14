"""
Skript pro rychlé spuštění aplikace ve vývojovém režimu

Příklady:
    $ python dev.py              # Normální start
    $ python dev.py --host 0.0.0.0  # Dostupné na síti
"""

import os
import sys
from app import app, db
from models import UctovaSkupina, RozpoctovaPolozka, Vydaj, ZamestnanecAOON

def create_app():
    """Vytvoří a nastaví aplikaci"""
    with app.app_context():
        # Vytvoří tabulky, pokud neexistují
        db.create_all()
        
        # Zkontroluje, zda je databáze prázdná
        if UctovaSkupina.query.count() == 0:
            print("⚠️  Databáze je prázdná. Spusťte: python init_db.py")
        
        return app

if __name__ == '__main__':
    app = create_app()
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║   📚 Správa rozpočtu Městské knihovny Polička                  ║
    ║                                                                ║
    ║   🌐 http://127.0.0.1:5000                                    ║
    ║   🐍 Python 3.8+                                              ║
    ║   💾 SQLite                                                   ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    app.run(
        debug=True,
        host='127.0.0.1',
        port=5000,
        use_reloader=True
    )
