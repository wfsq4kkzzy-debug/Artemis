#!/usr/bin/env python3
"""
Synchronizace výdajů projektů do rozpočtu
Přidá všechny existující výdaje projektů jako Expense do hlavního rozpočtu
"""

from app import app
from core import db
from modules.projects.models import Projekt, VydajProjektu
from modules.budget.models import Budget, BudgetCategory, Expense
from decimal import Decimal
from datetime import datetime

def sync_project_expenses():
    """Synchronizuje všechny výdaje projektů do rozpočtu"""
    with app.app_context():
        # Najdi hlavní rozpočet
        hlavni_rozpocet = Budget.query.filter_by(hlavni=True, aktivni=True).first()
        
        if not hlavni_rozpocet:
            print("❌ Hlavní rozpočet neexistuje!")
            return
        
        print(f"📊 Hlavní rozpočet: {hlavni_rozpocet.nazev} (ID: {hlavni_rozpocet.id})")
        
        # Najdi nebo vytvoř kategorii "Projekty"
        kategorie_projekty = BudgetCategory.query.filter_by(
            budget_id=hlavni_rozpocet.id,
            nazev='Projekty'
        ).first()
        
        if not kategorie_projekty:
            print("📁 Vytvářím kategorii 'Projekty'...")
            kategorie_projekty = BudgetCategory(
                budget_id=hlavni_rozpocet.id,
                typ='naklad_ostatni',
                nazev='Projekty',
                kod='PROJ',
                barva='#ffc107',
                poradi=100
            )
            db.session.add(kategorie_projekty)
            db.session.flush()
            print(f"✓ Kategorie vytvořena (ID: {kategorie_projekty.id})")
        else:
            print(f"✓ Kategorie 'Projekty' existuje (ID: {kategorie_projekty.id})")
        
        # Projdi všechny projekty
        projekty = Projekt.query.all()
        print(f"\n📋 Nalezeno {len(projekty)} projektů")
        
        celkem_sync = 0
        celkem_skip = 0
        
        for projekt in projekty:
            print(f"\n🔹 Projekt: {projekt.nazev} (ID: {projekt.id})")
            
            # Najdi všechny výdaje projektu
            vydaje = VydajProjektu.query.filter_by(projekt_id=projekt.id).all()
            print(f"   Výdajů: {len(vydaje)}")
            
            for vydaj in vydaje:
                # Zkontroluj, zda už není v rozpočtu
                existing = Expense.query.filter_by(
                    budget_id=hlavni_rozpocet.id,
                    vydaj_projektu_id=vydaj.id
                ).first()
                
                if existing:
                    print(f"   ⏭️  Výdaj '{vydaj.popis}' už je v rozpočtu (skip)")
                    celkem_skip += 1
                    continue
                
                # Vytvoř Expense
                datum = vydaj.datum or datetime.utcnow()
                expense = Expense(
                    budget_id=hlavni_rozpocet.id,
                    category_id=kategorie_projekty.id,
                    projekt_id=projekt.id,
                    vydaj_projektu_id=vydaj.id,
                    castka=vydaj.castka,
                    datum=datum,
                    popis=f"{vydaj.popis} (Projekt: {projekt.nazev})",
                    cis_faktury=vydaj.cis_faktury,
                    dodavatel=vydaj.dodavatel,
                    poznamka=vydaj.poznamka,
                    typ='projektovy',
                    mesic=datum.month,
                    rok=datum.year
                )
                
                db.session.add(expense)
                print(f"   ✓ Přidán: '{vydaj.popis}' - {float(vydaj.castka):,.2f} Kč")
                celkem_sync += 1
        
        # Commit
        try:
            db.session.commit()
            print(f"\n✅ Synchronizace dokončena!")
            print(f"   ✓ Přidáno: {celkem_sync} výdajů")
            print(f"   ⏭️  Přeskočeno: {celkem_skip} výdajů (už v rozpočtu)")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Chyba při synchronizaci: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == '__main__':
    print("=" * 60)
    print("Synchronizace výdajů projektů do rozpočtu")
    print("=" * 60)
    sync_project_expenses()

