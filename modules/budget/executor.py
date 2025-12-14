"""
Budget Executor - Business logika pro modul rozpočtu
Kompletní implementace s propojením na všechny moduly
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from collections import defaultdict
from core import db
from .models import Budget, BudgetCategory, BudgetSubCategory, BudgetItem, Expense, Revenue, MonthlyBudgetItem


class BudgetExecutor:
    """Třída pro správu rozpočtů"""
    
    # ========================================================================
    # ROZPOČTY
    # ========================================================================
    
    @staticmethod
    def get_or_create_main_budget(rok: int = None) -> Budget:
        """Vrátí hlavní rozpočet nebo ho vytvoří"""
        import json
        from datetime import datetime as dt
        
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"budget/executor.py:22","message":"get_or_create_main_budget called","data":{"rok":rok},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        
        if rok is None:
            rok = datetime.utcnow().year
        
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"budget/executor.py:28","message":"Before Budget.query","data":{"rok":rok},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        
        hlavni = Budget.query.filter_by(hlavni=True, aktivni=True).first()
        
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"budget/executor.py:30","message":"After Budget.query","data":{"found":hlavni is not None,"id":hlavni.id if hlavni else None},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        
        if not hlavni:
            # #region agent log
            with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"budget/executor.py:33","message":"Creating new budget","data":{"rok":rok},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
            # #endregion
            
            hlavni = Budget(
                nazev=f"Rozpočet {rok}",
                typ='hlavni',
                rok=rok,
                hlavni=True
            )
            db.session.add(hlavni)
            
            # #region agent log
            with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"budget/executor.py:43","message":"Before db.commit","data":{},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
            # #endregion
            
            db.session.commit()
            
            # #region agent log
            with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"budget/executor.py:46","message":"After db.commit, before _create_default_categories","data":{"budget_id":hlavni.id},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
            # #endregion
            
            # Vytvoř základní kategorie
            try:
                BudgetExecutor._create_default_categories(hlavni.id)
                # #region agent log
                with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"budget/executor.py:51","message":"_create_default_categories completed","data":{},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
                # #endregion
            except Exception as e:
                # #region agent log
                with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"budget/executor.py:54","message":"_create_default_categories failed","data":{"error":str(e)},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
                # #endregion
                raise
        
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"budget/executor.py:58","message":"get_or_create_main_budget returning","data":{"budget_id":hlavni.id,"nazev":hlavni.nazev},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        
        return hlavni
    
    @staticmethod
    def _create_default_categories(budget_id: int):
        """Vytvoří základní kategorie rozpočtu"""
        kategorie = [
            {'typ': 'naklad_mzdovy', 'nazev': 'Mzdové náklady', 'kod': 'MZD', 'barva': '#dc3545', 'poradi': 1},
            {'typ': 'naklad_ostatni', 'nazev': 'Ostatní náklady', 'kod': 'OST', 'barva': '#fd7e14', 'poradi': 2},
            {'typ': 'vynos', 'nazev': 'Výnosy', 'kod': 'VYN', 'barva': '#28a745', 'poradi': 3},
        ]
        
        for kat_data in kategorie:
            kat = BudgetCategory(
                budget_id=budget_id,
                **kat_data
            )
            db.session.add(kat)
        
        db.session.commit()
    
    # ========================================================================
    # KATEGORIE
    # ========================================================================
    
    @staticmethod
    def create_category(budget_id: int, typ: str, nazev: str, **kwargs) -> Dict:
        """Vytvoří novou kategorii"""
        try:
            max_poradi = db.session.query(db.func.max(BudgetCategory.poradi)).filter_by(
                budget_id=budget_id
            ).scalar() or 0
            
            category = BudgetCategory(
                budget_id=budget_id,
                typ=typ,
                nazev=nazev,
                kod=kwargs.get('kod'),
                popis=kwargs.get('popis'),
                barva=kwargs.get('barva', '#007bff'),
                poradi=max_poradi + 1
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
    def create_subcategory(category_id: int, nazev: str, **kwargs) -> Dict:
        """Vytvoří novou podkategorii"""
        try:
            category = BudgetCategory.query.get(category_id)
            if not category:
                return {"success": False, "error": "Kategorie neexistuje"}
            
            max_poradi = db.session.query(db.func.max(BudgetSubCategory.poradi)).filter_by(
                category_id=category_id
            ).scalar() or 0
            
            subcategory = BudgetSubCategory(
                category_id=category_id,
                nazev=nazev,
                kod=kwargs.get('kod'),
                popis=kwargs.get('popis'),
                poradi=max_poradi + 1
            )
            
            db.session.add(subcategory)
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Podkategorie '{nazev}' byla vytvořena",
                "subcategory_id": subcategory.id
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_categories_by_type(budget_id: int, typ: str = None) -> List[BudgetCategory]:
        """Vrátí kategorie podle typu"""
        query = BudgetCategory.query.filter_by(budget_id=budget_id, aktivni=True)
        if typ:
            query = query.filter_by(typ=typ)
        return query.order_by(BudgetCategory.poradi).all()
    
    # ========================================================================
    # ROZPOČTOVÉ POLOŽKY
    # ========================================================================
    
    @staticmethod
    def add_budget_item(budget_id: int, category_id: int, nazev: str, castka: float, subcategory_id: int = None, **kwargs) -> Dict:
        """Přidá rozpočtovou položku"""
        try:
            budget = Budget.query.get(budget_id)
            if not budget:
                return {"success": False, "error": f"Rozpočet ID {budget_id} neexistuje"}
            
            max_poradi = db.session.query(db.func.max(BudgetItem.poradi)).filter_by(
                budget_id=budget_id,
                category_id=category_id
            ).scalar() or 0
            
            item = BudgetItem(
                budget_id=budget_id,
                category_id=category_id,
                subcategory_id=subcategory_id,
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
    def add_expense(budget_id: int, budget_item_id: int, category_id: int, popis: str, castka: float, **kwargs) -> Dict:
        """Přidá výdaj s propojením na ostatní moduly - budget_item_id je povinné"""
        try:
            budget = Budget.query.get(budget_id)
            if not budget:
                return {"success": False, "error": f"Rozpočet ID {budget_id} neexistuje"}
            
            budget_item = BudgetItem.query.get(budget_item_id)
            if not budget_item:
                return {"success": False, "error": f"Položka rozpočtu ID {budget_item_id} neexistuje"}
            
            datum = kwargs.get('datum') or datetime.utcnow()
            if isinstance(datum, str):
                datum = datetime.fromisoformat(datum.replace('Z', '+00:00'))
            
            # Urči typ výdaje
            typ = kwargs.get('typ', 'bezny')
            if kwargs.get('personnel_id'):
                typ = 'mzda'
            
            expense = Expense(
                budget_id=budget_id,
                budget_item_id=budget_item_id,
                category_id=category_id,
                subcategory_id=kwargs.get('subcategory_id'),
                personnel_id=kwargs.get('personnel_id'),
                user_id=kwargs.get('user_id'),
                castka=Decimal(str(castka)),
                datum=datum,
                popis=popis,
                cis_faktury=kwargs.get('cis_faktury'),
                dodavatel=kwargs.get('dodavatel'),
                poznamka=kwargs.get('poznamka'),
                typ=typ,
                mesic=datum.month,
                rok=datum.year
            )
            
            db.session.add(expense)
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Výdaj '{popis}' byl přidán k položce rozpočtu '{budget_item.popis}'",
                "expense_id": expense.id
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    # ========================================================================
    # STATISTIKY A PŘEHLEDY
    # ========================================================================
    
    @staticmethod
    def get_budget_overview(budget_id: int) -> Dict:
        """Vrátí přehled rozpočtu"""
        import json
        from datetime import datetime as dt
        
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"budget/executor.py:235","message":"get_budget_overview called","data":{"budget_id":budget_id},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        
        budget = Budget.query.get(budget_id)
        if not budget:
            # #region agent log
            with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"budget/executor.py:240","message":"Budget not found","data":{"budget_id":budget_id},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
            # #endregion
            return None
        
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"budget/executor.py:245","message":"Before BudgetCategory.query","data":{"budget_id":budget_id},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        
        # Kategorie s výdaji
        kategorie = BudgetCategory.query.filter_by(budget_id=budget_id, aktivni=True).order_by(
            BudgetCategory.poradi
        ).all()
        
        # #region agent log
        with open('/Users/jendouch/library_budget/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"budget/executor.py:250","message":"After BudgetCategory.query","data":{"kategorie_count":len(kategorie)},"timestamp":int(dt.now().timestamp()*1000)})+'\n')
        # #endregion
        
        kategorie_data = []
        for kat in kategorie:
            kategorie_data.append({
                'kategorie': kat,
                'vydaje': kat.celkove_vydaje,
                'podkategorie': [
                    {
                        'podkategorie': sub,
                        'vydaje': sub.celkove_vydaje
                    }
                    for sub in BudgetSubCategory.query.filter_by(
                        category_id=kat.id, aktivni=True
                    ).order_by(BudgetSubCategory.poradi).all()
                ]
            })
        
        # Mzdové náklady
        mzdove_kategorie = BudgetCategory.query.filter_by(
            budget_id=budget_id,
            typ='naklad_mzdovy',
            aktivni=True
        ).all()
        
        mzdove_vydaje = []
        for kat in mzdove_kategorie:
            vydaje = Expense.query.filter_by(
                budget_id=budget_id,
                category_id=kat.id,
                typ='mzda'
            ).all()
            
            # Seskupit podle personálního záznamu
            from collections import defaultdict
            by_personnel = defaultdict(float)
            for v in vydaje:
                if v.personnel_id:
                    by_personnel[v.personnel_id] += float(v.castka)
            
            mzdove_vydaje.append({
                'kategorie': kat,
                'celkem': sum(float(e.castka) for e in vydaje),
                'by_personnel': dict(by_personnel)
            })
        
        return {
            'budget': budget,
            'kategorie': kategorie_data,
            'mzdove_vydaje': mzdove_vydaje
        }
    
    @staticmethod
    def get_monthly_expenses(budget_id: int, rok: int = None) -> List[Dict]:
        """Vrátí měsíční přehled výdajů"""
        if rok is None:
            rok = datetime.utcnow().year
        
        expenses = Expense.query.filter_by(
            budget_id=budget_id,
            rok=rok
        ).all()
        
        monthly = defaultdict(float)
        for e in expenses:
            monthly[e.mesic] += float(e.castka)
        
        # Vytvoř seznam pro všech 12 měsíců
        result = []
        for m in range(1, 13):
            result.append({
                'mesic': m,
                'castka': monthly.get(m, 0.0)
            })
        
        return result
    
    @staticmethod
    def get_all_budgets(aktivni_only: bool = True):
        """Vrátí všechny rozpočty - pro kompatibilitu"""
        query = Budget.query
        if aktivni_only:
            query = query.filter_by(aktivni=True)
        return query.order_by(Budget.datum_vytvoreni.desc()).all()
    
    @staticmethod
    def get_all_categories():
        """Vrátí všechny kategorie - pro kompatibilitu"""
        return BudgetCategory.query.filter_by(aktivni=True).order_by(BudgetCategory.poradi).all()
    
    # ========================================================================
    # SPRÁVA VÍCE ROZPOČTŮ (ROKY)
    # ========================================================================
    
    @staticmethod
    def get_all_budgets_by_year() -> List[Dict]:
        """Vrátí všechny rozpočty seřazené podle roku"""
        rozpocty = Budget.query.filter_by(aktivni=True).order_by(Budget.rok.desc()).all()
        return [
            {
                'id': r.id,
                'nazev': r.nazev,
                'rok': r.rok,
                'hlavni': r.hlavni,
                'castka_celkem': float(r.castka_celkem),
                'celkove_vydaje': r.celkove_vydaje,
                'celkove_vynosy': r.celkove_vynosy,
                'bilance': r.bilance,
                'datum_vytvoreni': r.datum_vytvoreni
            }
            for r in rozpocty
        ]
    
    @staticmethod
    def create_budget_for_year(rok: int, nazev: str = None) -> Dict:
        """Vytvoří nový rozpočet pro daný rok"""
        try:
            # Zkontroluj, zda už existuje rozpočet pro tento rok
            existujici = Budget.query.filter_by(rok=rok, aktivni=True).first()
            if existujici:
                return {
                    "success": False,
                    "error": f"Rozpočet pro rok {rok} již existuje"
                }
            
            if nazev is None:
                nazev = f"Rozpočet {rok}"
            
            novy_rozpocet = Budget(
                nazev=nazev,
                typ='hlavni',
                rok=rok,
                hlavni=False,  # Nový rozpočet není automaticky hlavní
                aktivni=True
            )
            
            db.session.add(novy_rozpocet)
            db.session.commit()
            
            # Vytvoř základní kategorie
            BudgetExecutor._create_default_categories(novy_rozpocet.id)
            
            return {
                "success": True,
                "message": f"Rozpočet pro rok {rok} byl vytvořen",
                "budget_id": novy_rozpocet.id
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def set_main_budget(budget_id: int) -> Dict:
        """Nastaví rozpočet jako hlavní (odstraní hlavní z ostatních)"""
        try:
            budget = Budget.query.get(budget_id)
            if not budget:
                return {"success": False, "error": f"Rozpočet ID {budget_id} neexistuje"}
            
            # Odstraň hlavní z ostatních rozpočtů
            Budget.query.filter_by(hlavni=True).update({'hlavni': False})
            
            # Nastav tento jako hlavní
            budget.hlavni = True
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Rozpočet '{budget.nazev}' byl nastaven jako hlavní"
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_budget_by_year(rok: int) -> Optional[Budget]:
        """Vrátí rozpočet pro daný rok"""
        return Budget.query.filter_by(rok=rok, aktivni=True).first()
    
    # ========================================================================
    # VÝNOSY
    # ========================================================================
    
    @staticmethod
    def add_revenue(budget_id: int, category_id: int, nazev: str, castka: float, typ: str = 'jednorazovy', **kwargs) -> Dict:
        """Přidá výnos (jednorázový nebo pravidelný)"""
        try:
            budget = Budget.query.get(budget_id)
            if not budget:
                return {"success": False, "error": f"Rozpočet ID {budget_id} neexistuje"}
            
            if typ == 'jednorazovy':
                datum = kwargs.get('datum') or datetime.utcnow()
                if isinstance(datum, str):
                    datum = datetime.fromisoformat(datum.replace('Z', '+00:00'))
                
                revenue = Revenue(
                    budget_id=budget_id,
                    category_id=category_id,
                    subcategory_id=kwargs.get('subcategory_id'),
                    nazev=nazev,
                    popis=kwargs.get('popis'),
                    castka=Decimal(str(castka)),
                    typ='jednorazovy',
                    datum=datum,
                    mesic=datum.month,
                    rok=datum.year,
                    naplanovano=kwargs.get('naplanovano', False),
                    skutecne_prijato=kwargs.get('skutecne_prijato', False),
                    cis_faktury=kwargs.get('cis_faktury'),
                    odberatel=kwargs.get('odberatel'),
                    poznamka=kwargs.get('poznamka')
                )
            else:  # pravidelny
                datum_zacatku = kwargs.get('datum_zacatku')
                if isinstance(datum_zacatku, str):
                    datum_zacatku = datetime.fromisoformat(datum_zacatku.replace('Z', '+00:00'))
                
                datum_konce = kwargs.get('datum_konce')
                if datum_konce and isinstance(datum_konce, str):
                    datum_konce = datetime.fromisoformat(datum_konce.replace('Z', '+00:00'))
                
                revenue = Revenue(
                    budget_id=budget_id,
                    category_id=category_id,
                    subcategory_id=kwargs.get('subcategory_id'),
                    nazev=nazev,
                    popis=kwargs.get('popis'),
                    castka=Decimal(str(castka)),
                    typ='pravidelny',
                    rok=kwargs.get('rok', datetime.utcnow().year),
                    datum_zacatku=datum_zacatku,
                    datum_konce=datum_konce,
                    frekvence=kwargs.get('frekvence', 'mesicne'),
                    mesice=kwargs.get('mesice', 'vse'),
                    naplanovano=kwargs.get('naplanovano', True),
                    skutecne_prijato=kwargs.get('skutecne_prijato', False),
                    cis_faktury=kwargs.get('cis_faktury'),
                    odberatel=kwargs.get('odberatel'),
                    poznamka=kwargs.get('poznamka')
                )
            
            db.session.add(revenue)
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Výnos '{nazev}' byl přidán",
                "revenue_id": revenue.id
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_monthly_revenues(budget_id: int, rok: int = None) -> List[Dict]:
        """Vrátí měsíční přehled výnosů (naplánovaných i skutečných)"""
        if rok is None:
            rok = datetime.utcnow().year
        
        revenues = Revenue.query.filter_by(budget_id=budget_id, rok=rok).all()
        
        monthly_planned = defaultdict(float)
        monthly_actual = defaultdict(float)
        
        for r in revenues:
            if r.typ == 'jednorazovy':
                if r.mesic:
                    if r.naplanovano:
                        monthly_planned[r.mesic] += float(r.castka)
                    if r.skutecne_prijato:
                        monthly_actual[r.mesic] += float(r.castka)
            else:  # pravidelny
                months = r.get_planned_months()
                for m in months:
                    if r.naplanovano:
                        monthly_planned[m] += float(r.castka)
                    if r.skutecne_prijato:
                        monthly_actual[m] += float(r.castka)
        
        # Vytvoř seznam pro všech 12 měsíců
        result = []
        for m in range(1, 13):
            result.append({
                'mesic': m,
                'planovano': monthly_planned.get(m, 0.0),
                'skutecne': monthly_actual.get(m, 0.0)
            })
        
        return result
    
    @staticmethod
    def get_monthly_overview(budget_id: int, rok: int = None) -> List[Dict]:
        """Vrátí měsíční přehled výdajů i výnosů"""
        if rok is None:
            rok = datetime.utcnow().year
        
        # Výdaje
        expenses = Expense.query.filter_by(budget_id=budget_id, rok=rok).all()
        monthly_expenses = defaultdict(float)
        for e in expenses:
            monthly_expenses[e.mesic] += float(e.castka)
        
        # Výnosy
        revenues = Revenue.query.filter_by(budget_id=budget_id, rok=rok).all()
        monthly_revenues_planned = defaultdict(float)
        monthly_revenues_actual = defaultdict(float)
        
        for r in revenues:
            if r.typ == 'jednorazovy':
                if r.mesic:
                    if r.naplanovano:
                        monthly_revenues_planned[r.mesic] += float(r.castka)
                    if r.skutecne_prijato:
                        monthly_revenues_actual[r.mesic] += float(r.castka)
            else:  # pravidelny
                months = r.get_planned_months()
                for m in months:
                    if r.naplanovano:
                        monthly_revenues_planned[m] += float(r.castka)
                    if r.skutecne_prijato:
                        monthly_revenues_actual[m] += float(r.castka)
        
        # Vytvoř seznam pro všech 12 měsíců
        result = []
        for m in range(1, 13):
            vydaje = monthly_expenses.get(m, 0.0)
            vynosy_plan = monthly_revenues_planned.get(m, 0.0)
            vynosy_skut = monthly_revenues_actual.get(m, 0.0)
            bilance = vynosy_skut - vydaje
            
            result.append({
                'mesic': m,
                'vydaje': vydaje,
                'vynosy_planovane': vynosy_plan,
                'vynosy_skutecne': vynosy_skut,
                'bilance': bilance
            })
        
        return result
    
    # ========================================================================
    # MĚSÍČNÍ STATISTIKY
    # ========================================================================
    
    @staticmethod
    def get_mesicni_statistiky(budget_id: int, mesic: int, rok: int) -> Dict:
        """Vrátí statistiky rozpočtu pro konkrétní měsíc"""
        polozky = BudgetItem.query.filter_by(budget_id=budget_id, aktivni=True).all()
        
        # Výdaje (náklady)
        naklady_rozpocet = 0.0
        naklady_skutecne = 0.0
        
        # Výnosy
        vynosy_rozpocet = 0.0
        vynosy_skutecne = 0.0
        
        for polozka in polozky:
            if polozka.typ == 'naklad':
                naklady_rozpocet += polozka.castka_float
                
                # Skutečné výdaje v měsíci
                # 1. Ručně zadané výdaje
                from sqlalchemy import extract
                vydaje_mesic = Expense.query.filter(
                    Expense.budget_item_id == polozka.id,
                    extract('month', Expense.datum) == mesic,
                    extract('year', Expense.datum) == rok
                ).all()
                naklady_skutecne += sum(float(e.castka) if e.castka else 0.0 for e in vydaje_mesic)
                
                # 2. Aktuální stav z měsíčních aktualizací (pokud je zadán)
                mesicni_stav = MonthlyBudgetItem.query.filter_by(
                    budget_item_id=polozka.id,
                    mesic=mesic,
                    rok=rok
                ).first()
                if mesicni_stav and mesicni_stav.aktualni_stav is not None:
                    # Použij aktuální stav, pokud je zadán (přepíše ruční výdaje)
                    naklady_skutecne = mesicni_stav.aktualni_stav_float
                elif mesicni_stav:
                    # Jinak použij souhrnné výdaje (zpětná kompatibilita)
                    naklady_skutecne += mesicni_stav.souhrnne_vydaje_float
            else:
                # Výnosy
                vynosy_rozpocet += polozka.castka_float
                
                # Skutečné výnosy v měsíci
                vynosy_mesic = Revenue.query.filter(
                    Revenue.budget_item_id == polozka.id,
                    Revenue.rok == rok,
                    Revenue.skutecne_prijato == True
                ).all()
                
                # Zkontroluj, zda výnos spadá do tohoto měsíce
                for vynos in vynosy_mesic:
                    if vynos.typ == 'jednorazovy' and vynos.mesic == mesic:
                        vynosy_skutecne += vynos.castka_float
                    elif vynos.typ == 'pravidelny':
                        planned_months = vynos.get_planned_months()
                        if mesic in planned_months:
                            vynosy_skutecne += vynos.castka_float
        
        bilance = vynosy_skutecne - naklady_skutecne
        
        return {
            'naklady_rozpocet': naklady_rozpocet,
            'naklady_skutecne': naklady_skutecne,
            'naklady_procento': (naklady_skutecne / naklady_rozpocet * 100) if naklady_rozpocet > 0 else 0,
            'vynosy_rozpocet': vynosy_rozpocet,
            'vynosy_skutecne': vynosy_skutecne,
            'vynosy_procento': (vynosy_skutecne / vynosy_rozpocet * 100) if vynosy_rozpocet > 0 else 0,
            'bilance': bilance
        }
    
    @staticmethod
    def get_rocni_statistiky(budget_id: int, rok: int) -> Dict:
        """Vrátí celkové statistiky rozpočtu za rok"""
        polozky = BudgetItem.query.filter_by(budget_id=budget_id, aktivni=True).all()
        
        naklady_rozpocet = 0.0
        naklady_skutecne = 0.0
        vynosy_rozpocet = 0.0
        vynosy_skutecne = 0.0
        
        for polozka in polozky:
            if polozka.typ == 'naklad':
                naklady_rozpocet += polozka.castka_float
                
                # Výdaje za celý rok
                from sqlalchemy import extract
                vydaje_rok = Expense.query.filter(
                    Expense.budget_item_id == polozka.id,
                    extract('year', Expense.datum) == rok
                ).all()
                naklady_skutecne += sum(float(e.castka) if e.castka else 0.0 for e in vydaje_rok)
                
                # Aktuální stavy za celý rok - použij nejnovější měsíční stav
                mesicni_stavy = MonthlyBudgetItem.query.filter_by(
                    budget_item_id=polozka.id,
                    rok=rok
                ).order_by(MonthlyBudgetItem.mesic.desc()).all()
                
                if mesicni_stavy:
                    # Najdi nejnovější stav s aktuálním stavem
                    nejnovejsi_s_aktualnim = None
                    for s in mesicni_stavy:
                        if s.aktualni_stav is not None:
                            nejnovejsi_s_aktualnim = s
                            break
                    
                    if nejnovejsi_s_aktualnim:
                        # Použij aktuální stav z nejnovějšího měsíce
                        naklady_skutecne = nejnovejsi_s_aktualnim.aktualni_stav_float
                    else:
                        # Jinak použij souhrnné výdaje (zpětná kompatibilita)
                        for s in mesicni_stavy:
                            if s.souhrnne_vydaje:
                                naklady_skutecne += float(s.souhrnne_vydaje)
            else:
                vynosy_rozpocet += polozka.castka_float
                
                # Výnosy za celý rok
                vynosy_rok = Revenue.query.filter(
                    Revenue.budget_item_id == polozka.id,
                    Revenue.rok == rok,
                    Revenue.skutecne_prijato == True
                ).all()
                vynosy_skutecne += sum(float(v.castka) if v.castka else 0.0 for v in vynosy_rok)
        
        bilance = vynosy_skutecne - naklady_skutecne
        
        return {
            'naklady_rozpocet': naklady_rozpocet,
            'naklady_skutecne': naklady_skutecne,
            'naklady_procento': (naklady_skutecne / naklady_rozpocet * 100) if naklady_rozpocet > 0 else 0,
            'vynosy_rozpocet': vynosy_rozpocet,
            'vynosy_skutecne': vynosy_skutecne,
            'vynosy_procento': (vynosy_skutecne / vynosy_rozpocet * 100) if vynosy_rozpocet > 0 else 0,
            'bilance': bilance
        }




