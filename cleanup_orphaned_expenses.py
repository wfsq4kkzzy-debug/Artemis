#!/usr/bin/env python3
"""
Vyčištění sirotčích Expense záznamů - výdaje bez existujícího projektu
"""

from app import app
from core import db
from modules.budget.models import Expense
from modules.projects.models import Projekt

def cleanup_orphaned_expenses():
    """Smaže všechny Expense záznamy, které odkazují na neexistující projekt"""
    with app.app_context():
        # Najdi všechny Expense s projekt_id
        all_expenses = Expense.query.filter(Expense.projekt_id.isnot(None)).all()
        
        print(f"🔍 Kontroluji {len(all_expenses)} Expense záznamů s projekt_id...")
        
        sirotci = []
        for exp in all_expenses:
            # Zkontroluj, zda projekt existuje
            projekt = db.session.get(Projekt, exp.projekt_id)
            if not projekt:
                sirotci.append(exp)
                print(f"  ⚠️  Sirotčí Expense ID {exp.id}:")
                print(f"     projekt_id={exp.projekt_id}")
                print(f"     popis={exp.popis[:60]}")
                print(f"     částka={float(exp.castka):,.2f} Kč")
        
        if not sirotci:
            print("\n✅ Žádné sirotčí Expense záznamy nebyly nalezeny!")
            return
        
        print(f"\n🗑️  Nalezeno {len(sirotci)} sirotčích Expense záznamů")
        celkem_castka = sum(float(e.castka) for e in sirotci)
        print(f"   Celková částka: {celkem_castka:,.2f} Kč")
        
        # Smazat
        for exp in sirotci:
            db.session.delete(exp)
            print(f"  ✓ Smazán Expense ID {exp.id}: {exp.popis[:50]}")
        
        try:
            db.session.commit()
            print(f"\n✅ Úspěšně smazáno {len(sirotci)} sirotčích Expense záznamů")
            print(f"   Celkem: {celkem_castka:,.2f} Kč")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Chyba při mazání: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == '__main__':
    print("=" * 60)
    print("Vyčištění sirotčích Expense záznamů")
    print("=" * 60)
    cleanup_orphaned_expenses()
