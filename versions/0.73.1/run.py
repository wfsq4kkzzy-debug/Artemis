#!/usr/bin/env python
"""
Spustit aplikaci pro vývoj

Příklady:
    python run.py                 # Spustit na http://localhost:5001
    python run.py --host 0.0.0.0  # Přístupné ze sítě
"""

from app import app

if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║  Správa rozpočtu Městské knihovny Polička                ║
    ║  http://localhost:5001                                    ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    app.run(debug=True, host='127.0.0.1', port=5001)
