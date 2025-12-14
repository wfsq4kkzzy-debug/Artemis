"""
Budget Executor - Business logika pro modul rozpočtu
PŘEPRACOVÁVÁ SE - nová flexibilní struktura
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from core import db
from .models import Budget, BudgetCategory, BudgetItem, Expense, MonthlyBudget


class BudgetExecutor:
    """Třída pro správu rozpočtů"""
    
    # ========================================================================
    # ROZPOČTY
    # ========================================================================
    
    @staticmethod
    def create_budget(nazev: str, typ: str = 'hlavni', rok: int = 2026, castka: float = 0, **kwargs) -> Dict:
        """Vytvoří nový rozpočet"""
        try:
            # Pokud je to hlavní rozpočet, zruš hlavní u ostatních
            if typ == 'hlavni':
                Budget.query.filter_by(hlavni=True).update({'hlavni': False})
            
            budget = Budget(
                nazev=nazev,
                popis=kwargs.get('popis'),
                typ=typ,
                rok=rok,
                mesic=kwargs.get('mesic'),
                castka_celkem=Decimal(str(castka)),
                hlavni=(typ == 'hlavni')
            )
            
            db.session.add(budget)
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Rozpočet '{nazev}' byl vytvořen",
                "budget_id": budget.id
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_main_budget() -> Optional[Budget]:
        """Vrátí hlavní rozpočet"""
        return Budget.query.filter_by(hlavni=True, aktivni=True).first()
    
    @staticmethod
    def get_all_budgets(aktivni_only: bool = True) -> List[Budget]:
        """Vrátí všechny rozpočty"""
        query = Budget.query
        if aktivni_only:
            query = query.filter_by(aktivni=True)
        return query.order_by(Budget.datum_vytvoreni.desc()).all()
    
    # ========================================================================
    # KATEGORIE
    # ========================================================================
    
    @staticmethod
    def create_category(nazev: str, kod: str = None, barva: str = '#007bff', **kwargs) -> Dict:
        """Vytvoří novou kategorii"""
        try:
            category = BudgetCategory(
                nazev=nazev,
                kod=kod or nazev.upper()[:3],
                popis=kwargs.get('popis'),
                barva=barva,
                poradi=kwargs.get('poradi', 0)
            )
            
            db.session.add(category)
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Kategorie '{nazev}' byla vytvořena",
                "category_id": category.id
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_all_categories(aktivni_only: bool = True) -> List[BudgetCategory]:
        """Vrátí všechny kategorie"""
        query = BudgetCategory.query
        if aktivni_only:
            query = query.filter_by(aktivni=True)
        return query.order_by(BudgetCategory.poradi, BudgetCategory.nazev).all()
    
    # ========================================================================
    # ROZPOČTOVÉ POLOŽKY
    # ========================================================================
    
    @staticmethod
    def add_budget_item(budget_id: int, category_id: int, nazev: str, castka: float, **kwargs) -> Dict:
        """Přidá rozpočtovou položku"""
        try:
            budget = Budget.query.get(budget_id)
            if not budget:
                return {"success": False, "error": f"Rozpočet ID {budget_id} neexistuje"}
            
            category = BudgetCategory.query.get(category_id)
            if not category:
                return {"success": False, "error": f"Kategorie ID {category_id} neexistuje"}
            
            # Najdi nejvyšší pořadí v kategorii
            max_poradi = db.session.query(db.func.max(BudgetItem.poradi)).filter_by(
                budget_id=budget_id,
                category_id=category_id
            ).scalar() or 0
            
            item = BudgetItem(
                budget_id=budget_id,
                category_id=category_id,
                nazev=nazev,
                popis=kwargs.get('popis'),
                castka=Decimal(str(castka)),
                poradi=max_poradi + 1
            )
            
            db.session.add(item)
            # Aktualizuj celkovou částku rozpočtu
            budget.castka_celkem += Decimal(str(castka))
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Položka '{nazev}' byla přidána",
                "item_id": item.id
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    # ========================================================================
    # VÝDAJE
    # ========================================================================
    
    @staticmethod
    def add_expense(budget_id: int, category_id: int, popis: str, castka: float, **kwargs) -> Dict:
        """Přidá výdaj"""
        try:
            budget = Budget.query.get(budget_id)
            if not budget:
                return {"success": False, "error": f"Rozpočet ID {budget_id} neexistuje"}
            
            datum = kwargs.get('datum') or datetime.utcnow()
            if isinstance(datum, str):
                from datetime import datetime as dt
                datum = dt.fromisoformat(datum.replace('Z', '+00:00'))
            
            expense = Expense(
                budget_id=budget_id,
                budget_item_id=kwargs.get('budget_item_id'),
                category_id=category_id,
                projekt_id=kwargs.get('projekt_id'),
                castka=Decimal(str(castka)),
                datum=datum,
                popis=popis,
                cis_faktury=kwargs.get('cis_faktury'),
                dodavatel=kwargs.get('dodavatel'),
                poznamka=kwargs.get('poznamka'),
                typ=kwargs.get('typ', 'bezny'),
                mesic=datum.month,
                rok=datum.year
            )
            
            db.session.add(expense)
            db.session.commit()
            
            # Aktualizuj měsíční přehled
            BudgetExecutor._update_monthly_budget(budget_id, datum.year, datum.month)
            
            return {
                "success": True,
                "message": f"Výdaj '{popis}' byl přidán",
                "expense_id": expense.id
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _update_monthly_budget(budget_id: int, rok: int, mesic: int):
        """Aktualizuje měsíční přehled rozpočtu"""
        try:
            monthly = MonthlyBudget.query.filter_by(
                budget_id=budget_id,
                rok=rok,
                mesic=mesic
            ).first()
            
            if not monthly:
                monthly = MonthlyBudget(
                    budget_id=budget_id,
                    rok=rok,
                    mesic=mesic,
                    planovano=Decimal('0'),  # TODO: vypočítat z plánu
                    skutecne=Decimal('0')
                )
                db.session.add(monthly)
            
            # Vypočti skutečné výdaje za měsíc
            skutecne = db.session.query(db.func.sum(Expense.castka)).filter(
                Expense.budget_id == budget_id,
                Expense.rok == rok,
                Expense.mesic == mesic
            ).scalar() or Decimal('0')
            
            monthly.skutecne = skutecne
            monthly.odchylka = skutecne - monthly.planovano
            monthly.datum_aktualizace = datetime.utcnow()
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Necháme projít, není kritické
    
    # ========================================================================
    # MĚSÍČNÍ PŘEHLEDY
    # ========================================================================
    
    @staticmethod
    def get_monthly_overview(budget_id: int, rok: int) -> List[Dict]:
        """Vrátí měsíční přehled pro rok"""
        monthly_list = MonthlyBudget.query.filter_by(
            budget_id=budget_id,
            rok=rok
        ).order_by(MonthlyBudget.mesic).all()
        
        return [
            {
                "mesic": m.mesic,
                "planovano": float(m.planovano),
                "skutecne": float(m.skutecne),
                "odchylka": float(m.odchylka),
                "procento": float(m.procento_vycerpano)
            }
            for m in monthly_list
        ]
