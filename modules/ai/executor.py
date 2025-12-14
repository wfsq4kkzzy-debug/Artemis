"""
AI Executor - Bezpečné provádění akcí pro AI asistenta
- Přidávání/úpravy/mazání rozpočtových položek
- Správa výdajů
- Správa zaměstnanců
- Dotazy do databáze

DŮLEŽITÉ - PŘIDÁVÁNÍ NOVÝCH MODELŮ:
===================================
Když vytváříš nový databázový model, MUSÍŠ:
1. Importovat model v sekci importů nahoře
2. Vytvořit metodu get_all_<model_name>() pro čtení všech záznamů
3. Přidat metodu do execute_command() v sekci commands
4. Aktualizovat dokumentaci v routes.py (build_system_prompt)

Aktuálně podporované modely:
- Budget: Budget, BudgetCategory, BudgetSubCategory, BudgetItem, Expense, Revenue, MonthlyBudgetItem
- Projects: Projekt, VydajProjektu, Termin, Zprava, Znalost, ProjectShare
- Services: SluzbaTemplate, Sluzba, SluzbaVynimka, SluzbaVymena
- Users: User, UserProject, UserConnection, SharedChat, UserMessage, UserNotification
- Personnel: ZamestnanecAOON
- Docs: ChangeLog
- AI: Employee, AISession, Message, KnowledgeEntry, ServiceRecord, AssistantMemory
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import json

from core import db
from ..budget.models import UctovaSkupina, RozpoctovaPolozka, Vydaj
from ..budget.models import Budget, BudgetCategory, BudgetSubCategory, BudgetItem, Expense, Revenue, MonthlyBudgetItem
from ..budget.executor import BudgetExecutor
from ..personnel.models import ZamestnanecAOON
from ..projects.models import Projekt, BudgetProjektu, VydajProjektu, Termin, Zprava, Znalost, ProjectShare
from ..services.models import SluzbaTemplate, Sluzba, SluzbaVynimka, SluzbaVymena
from ..users.models import User, UserProject, UserConnection, SharedChat, UserMessage, UserNotification
from ..docs.models import ChangeLog


class AIExecutor:
    """Třída pro bezpečné provádění akcí v aplikaci"""
    
    # ========================================================================
    # ROZPOČTOVÉ POLOŽKY
    # ========================================================================
    
    @staticmethod
    def get_all_budget_items(rok: int = 2026, typ: Optional[str] = None) -> List[Dict]:
        """Vrátí všechny rozpočtové položky jako JSON"""
        query = RozpoctovaPolozka.query.filter_by(rok=rok)
        
        if typ:
            query = query.join(UctovaSkupina).filter(UctovaSkupina.typ == typ)
        
        items = query.all()
        return [
            {
                "id": item.id,
                "nazev": item.nazev,
                "rozpocet": float(item.rozpocet),
                "uctova_skupina": item.uctova_skupina.nazev if item.uctova_skupina else None,
                "analyticky_ucet": item.analyticky_ucet,
                "poznamka": item.poznamka,
            }
            for item in items
        ]
    
    @staticmethod
    def get_budget_summary(rok: int = 2026) -> Dict:
        """Vrátí souhrn rozpočtu"""
        naklady = db.session.query(db.func.sum(RozpoctovaPolozka.rozpocet)).join(
            UctovaSkupina
        ).filter(
            (UctovaSkupina.typ == 'naklad') & (RozpoctovaPolozka.rok == rok)
        ).scalar() or 0
        
        vynos = db.session.query(db.func.sum(RozpoctovaPolozka.rozpocet)).join(
            UctovaSkupina
        ).filter(
            (UctovaSkupina.typ == 'vynos') & (RozpoctovaPolozka.rok == rok)
        ).scalar() or 0
        
        return {
            "rok": rok,
            "naklady_celkem": float(naklady),
            "vynos_celkem": float(vynos),
            "bilance": float(vynos - naklady),
        }
    
    @staticmethod
    def create_budget_item(
        nazev: str,
        rozpocet: float,
        uctova_skupina_id: int,
        analyticky_ucet: str = "",
        poznamka: str = None,
        rok: int = 2026
    ) -> Dict:
        """Vytvoří novou rozpočtovou položku"""
        try:
            # Validace
            if not nazev or rozpocet < 0:
                return {"success": False, "error": "Neplatný název nebo rozpočet"}
            
            if not UctovaSkupina.query.get(uctova_skupina_id):
                return {"success": False, "error": f"Účtová skupina ID {uctova_skupina_id} neexistuje"}
            
            polozka = RozpoctovaPolozka(
                nazev=nazev,
                rozpocet=Decimal(str(rozpocet)),
                uctova_skupina_id=uctova_skupina_id,
                analyticky_ucet=analyticky_ucet or "00",
                poznamka=poznamka,
                rok=rok
            )
            
            db.session.add(polozka)
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Položka '{nazev}' byla vytvořena s ID {polozka.id}",
                "item_id": polozka.id,
                "item": {
                    "id": polozka.id,
                    "nazev": polozka.nazev,
                    "rozpocet": float(polozka.rozpocet),
                }
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def update_budget_item(polozka_id: int, **kwargs) -> Dict:
        """Upraví rozpočtovou položku"""
        try:
            polozka = RozpoctovaPolozka.query.get(polozka_id)
            if not polozka:
                return {"success": False, "error": f"Položka ID {polozka_id} neexistuje"}
            
            # Povolené pole
            allowed_fields = ['nazev', 'rozpocet', 'poznamka', 'analyticky_ucet']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    if field == 'rozpocet':
                        value = Decimal(str(value))
                    setattr(polozka, field, value)
            
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Položka '{polozka.nazev}' byla aktualizována",
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def delete_budget_item(polozka_id: int) -> Dict:
        """Smaže rozpočtovou položku"""
        try:
            polozka = RozpoctovaPolozka.query.get(polozka_id)
            if not polozka:
                return {"success": False, "error": f"Položka ID {polozka_id} neexistuje"}
            
            nazev = polozka.nazev
            
            # Smazat výdaje
            Vydaj.query.filter_by(rozpoctova_polozka_id=polozka_id).delete()
            db.session.delete(polozka)
            db.session.commit()
            
            return {"success": True, "message": f"Položka '{nazev}' a její výdaje byly smazány"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    # ========================================================================
    # VÝDAJE
    # ========================================================================
    
    @staticmethod
    def get_expenses_for_item(polozka_id: int) -> List[Dict]:
        """Vrátí všechny výdaje pro danou rozpočtovou položku"""
        polozka = RozpoctovaPolozka.query.get(polozka_id)
        if not polozka:
            return []
        
        vydaje = Vydaj.query.filter_by(rozpoctova_polozka_id=polozka_id).all()
        return [
            {
                "id": v.id,
                "castka": float(v.castka),
                "popis": v.popis,
                "datum": v.datum.isoformat() if v.datum else None,
                "cis_faktury": v.cis_faktury,
                "dodavatel": v.dodavatel,
            }
            for v in vydaje
        ]
    
    @staticmethod
    def add_expense(
        polozka_id: int,
        castka: float,
        popis: str = None,
        cis_faktury: str = None,
        dodavatel: str = None,
    ) -> Dict:
        """Přidá nový výdaj"""
        try:
            polozka = RozpoctovaPolozka.query.get(polozka_id)
            if not polozka:
                return {"success": False, "error": f"Položka ID {polozka_id} neexistuje"}
            
            if castka <= 0:
                return {"success": False, "error": "Částka musí být větší než 0"}
            
            vydaj = Vydaj(
                rozpoctova_polozka_id=polozka_id,
                castka=Decimal(str(castka)),
                popis=popis,
                cis_faktury=cis_faktury,
                dodavatel=dodavatel,
                datum=datetime.utcnow()
            )
            
            db.session.add(vydaj)
            db.session.commit()
            
            # Kontrola, jestli nepřekročil rozpočet
            total_expenses = sum(
                float(v.castka) for v in Vydaj.query.filter_by(rozpoctova_polozka_id=polozka_id).all()
            )
            budget_remaining = float(polozka.rozpocet) - total_expenses
            
            return {
                "success": True,
                "message": f"Výdaj {castka} Kč byl přidán",
                "expense_id": vydaj.id,
                "budget_remaining": budget_remaining,
                "warning": "Rozpočet překročen!" if budget_remaining < 0 else None,
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def delete_expense(vydaj_id: int) -> Dict:
        """Smaže výdaj"""
        try:
            vydaj = Vydaj.query.get(vydaj_id)
            if not vydaj:
                return {"success": False, "error": f"Výdaj ID {vydaj_id} neexistuje"}
            
            db.session.delete(vydaj)
            db.session.commit()
            
            return {"success": True, "message": "Výdaj byl smazán"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    # ========================================================================
    # ZAMĚSTNANCI
    # ========================================================================
    
    @staticmethod
    def get_all_employees() -> List[Dict]:
        """Vrátí všechny zaměstnance a OON"""
        lide = ZamestnanecAOON.query.filter_by(aktivni=True).all()
        return [
            {
                "id": osoba.id,
                "jmeno": osoba.jmeno_plne,
                "typ": osoba.typ,
                "pozice": osoba.pozice,
                "uvazek": float(osoba.uvazek) if osoba.uvazek else 100,
                "hodinova_sazba": float(osoba.hodinova_sazba) if osoba.hodinova_sazba else None,
                "mesicni_plat": float(osoba.mesicni_plat) if osoba.mesicni_plat else None,
            }
            for osoba in lide
        ]
    
    @staticmethod
    def add_employee(
        jmeno: str,
        prijmeni: str,
        typ: str,
        pozice: str = None,
        uvazek: float = 100,
        hodinova_sazba: float = None,
        mesicni_plat: float = None,
    ) -> Dict:
        """Přidá nového zaměstnance/OON"""
        try:
            if typ not in ['zamestnanec', 'brigadnik', 'oon']:
                return {"success": False, "error": f"Neznámý typ: {typ}"}
            
            if not jmeno or not prijmeni:
                return {"success": False, "error": "Jméno a příjmení jsou povinné"}
            
            osoba = ZamestnanecAOON(
                jmeno=jmeno,
                prijmeni=prijmeni,
                typ=typ,
                pozice=pozice,
                uvazek=Decimal(str(uvazek)) if uvazek else Decimal('100'),
                hodinova_sazba=Decimal(str(hodinova_sazba)) if hodinova_sazba else None,
                mesicni_plat=Decimal(str(mesicni_plat)) if mesicni_plat else None,
                datum_zapojeni=datetime.utcnow(),
                aktivni=True
            )
            
            db.session.add(osoba)
            db.session.commit()
            
            return {
                "success": True,
                "message": f"{jmeno} {prijmeni} byl(a) přidán(a) jako {typ}",
                "person_id": osoba.id,
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def update_employee(osoba_id: int, **kwargs) -> Dict:
        """Upraví zaměstnance"""
        try:
            osoba = ZamestnanecAOON.query.get(osoba_id)
            if not osoba:
                return {"success": False, "error": f"Osoba ID {osoba_id} neexistuje"}
            
            allowed_fields = ['pozice', 'uvazek', 'hodinova_sazba', 'mesicni_plat']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    if field in ['uvazek', 'hodinova_sazba', 'mesicni_plat'] and value is not None:
                        value = Decimal(str(value))
                    setattr(osoba, field, value)
            
            db.session.commit()
            
            return {
                "success": True,
                "message": f"{osoba.jmeno_plne} byl(a) aktualizován(a)",
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    # ========================================================================
    # DOTAZY A ANALÝZY
    # ========================================================================
    
    @staticmethod
    def get_budget_status_by_category() -> Dict:
        """Vrátí stav rozpočtu podle kategorií"""
        categories = {}
        
        skupiny = UctovaSkupina.query.all()
        for skupina in skupiny:
            items = RozpoctovaPolozka.query.filter_by(uctova_skupina_id=skupina.id).all()
            budget_total = sum(float(p.rozpocet) for p in items)
            
            expenses_total = sum(
                float(v.castka)
                for item in items
                for v in Vydaj.query.filter_by(rozpoctova_polozka_id=item.id).all()
            )
            
            categories[skupina.nazev] = {
                "typ": skupina.typ,
                "rozpocet": budget_total,
                "vydaje": expenses_total,
                "zbytek": budget_total - expenses_total,
                "procento_vycerpano": round((expenses_total / budget_total * 100) if budget_total > 0 else 0, 2),
            }
        
        return categories
    
    # ========================================================================
    # NOVÝ MODUL ROZPOČTU - metody pro AI
    # ========================================================================
    
    @staticmethod
    def add_budget_category(typ: str, nazev: str, **kwargs) -> Dict:
        """Přidá kategorii do rozpočtu"""
        try:
            hlavni = BudgetExecutor.get_or_create_main_budget()
            return BudgetExecutor.create_category(
                budget_id=hlavni.id,
                typ=typ,
                nazev=nazev,
                **kwargs
            )
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def add_budget_subcategory(category_id: int, nazev: str, **kwargs) -> Dict:
        """Přidá podkategorii"""
        try:
            return BudgetExecutor.create_subcategory(
                category_id=category_id,
                nazev=nazev,
                **kwargs
            )
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def add_new_budget_item(category_id: int, nazev: str, castka: float, **kwargs) -> Dict:
        """Přidá rozpočtovou položku (řádek)"""
        try:
            hlavni = BudgetExecutor.get_or_create_main_budget()
            return BudgetExecutor.add_budget_item(
                budget_id=hlavni.id,
                category_id=category_id,
                nazev=nazev,
                castka=castka,
                **kwargs
            )
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def add_budget_expense(category_id: int, popis: str, castka: float, **kwargs) -> Dict:
        """Přidá výdaj do rozpočtu"""
        try:
            hlavni = BudgetExecutor.get_or_create_main_budget()
            return BudgetExecutor.add_expense(
                budget_id=hlavni.id,
                category_id=category_id,
                popis=popis,
                castka=castka,
                **kwargs
            )
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_budget_overview_new() -> Dict:
        """Vrátí přehled nového rozpočtu"""
        try:
            hlavni = BudgetExecutor.get_or_create_main_budget()
            overview = BudgetExecutor.get_budget_overview(hlavni.id)
            return {
                "success": True,
                "budget": {
                    "nazev": hlavni.nazev,
                    "rok": hlavni.rok,
                    "castka_celkem": float(hlavni.castka_celkem),
                    "celkove_vydaje": hlavni.celkove_vydaje,
                    "celkove_vynosy": hlavni.celkove_vynosy,
                    "bilance": hlavni.bilance,
                    "zbytek": hlavni.zbytek,
                    "procento_vycerpano": hlavni.procento_vycerpano
                },
                "kategorie": [
                    {
                        "nazev": kat_data['kategorie'].nazev,
                        "typ": kat_data['kategorie'].typ,
                        "vydaje": kat_data['vydaje']
                    }
                    for kat_data in overview['kategorie']
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ========================================================================
    # ČTENÍ DAT Z DATABÁZE - pro AI asistenta
    # ========================================================================
    
    @staticmethod
    def get_all_budget_items_new(typ: Optional[str] = None) -> List[Dict]:
        """Vrátí všechny položky rozpočtu (účty) z nového systému"""
        try:
            hlavni = BudgetExecutor.get_or_create_main_budget()
            query = BudgetItem.query.filter_by(budget_id=hlavni.id, aktivni=True)
            
            if typ:
                query = query.filter_by(typ=typ)
            
            polozky = query.order_by(BudgetItem.typ, BudgetItem.ucet, BudgetItem.poducet).all()
            
            return [
                {
                    "id": p.id,
                    "ucet": p.ucet,
                    "poducet": p.poducet,
                    "popis": p.popis,
                    "typ": p.typ,
                    "castka": float(p.castka),
                    "aktualni_plneni": p.aktualni_plneni,
                    "zbytek": p.zbytek,
                    "procento_vycerpano": p.procenta_vycerpani,
                    "kategorie": p.category.nazev if p.category else None,
                    "podkategorie": p.subcategory.nazev if p.subcategory else None
                }
                for p in polozky
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_budget_categories() -> List[Dict]:
        """Vrátí všechny kategorie rozpočtu"""
        try:
            hlavni = BudgetExecutor.get_or_create_main_budget()
            kategorie = BudgetCategory.query.filter_by(
                budget_id=hlavni.id,
                aktivni=True
            ).order_by(BudgetCategory.poradi).all()
            
            return [
                {
                    "id": k.id,
                    "nazev": k.nazev,
                    "typ": k.typ,
                    "kod": k.kod,
                    "barva": k.barva,
                    "celkove_vydaje": k.celkove_vydaje,
                    "podkategorie": [
                        {
                            "id": sub.id,
                            "nazev": sub.nazev,
                            "kod": sub.kod,
                            "celkove_vydaje": sub.celkove_vydaje
                        }
                        for sub in BudgetSubCategory.query.filter_by(
                            category_id=k.id,
                            aktivni=True
                        ).order_by(BudgetSubCategory.poradi).all()
                    ]
                }
                for k in kategorie
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_expenses(limit: int = 100) -> List[Dict]:
        """Vrátí všechny výdaje z rozpočtu"""
        try:
            hlavni = BudgetExecutor.get_or_create_main_budget()
            expenses = Expense.query.filter_by(
                budget_id=hlavni.id
            ).order_by(Expense.datum.desc()).limit(limit).all()
            
            return [
                {
                    "id": e.id,
                    "popis": e.popis,
                    "castka": float(e.castka),
                    "datum": e.datum.isoformat() if e.datum else None,
                    "mesic": e.mesic,
                    "rok": e.rok,
                    "typ": e.typ,
                    "kategorie": e.category.nazev if e.category else None,
                    "projekt": e.projekt.nazev if e.projekt else None,
                    "cis_faktury": e.cis_faktury,
                    "dodavatel": e.dodavatel
                }
                for e in expenses
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_revenues() -> List[Dict]:
        """Vrátí všechny výnosy z rozpočtu"""
        try:
            hlavni = BudgetExecutor.get_or_create_main_budget()
            revenues = Revenue.query.filter_by(budget_id=hlavni.id).all()
            
            return [
                {
                    "id": r.id,
                    "nazev": r.nazev,
                    "popis": r.popis,
                    "castka": float(r.castka),
                    "typ": r.typ,
                    "datum": r.datum.isoformat() if r.datum else None,
                    "mesic": r.mesic,
                    "rok": r.rok,
                    "naplanovano": r.naplanovano,
                    "skutecne_prijato": r.skutecne_prijato,
                    "frekvence": r.frekvence,
                    "mesice": r.mesice,
                    "odberatel": r.odberatel
                }
                for r in revenues
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_project_expenses(projekt_id: int = None) -> List[Dict]:
        """Vrátí všechny výdaje projektů"""
        try:
            query = VydajProjektu.query
            if projekt_id:
                query = query.filter_by(projekt_id=projekt_id)
            
            expenses = query.order_by(VydajProjektu.datum.desc()).all()
            
            return [
                {
                    "id": e.id,
                    "projekt_id": e.projekt_id,
                    "projekt_nazev": e.projekt.nazev if e.projekt else None,
                    "popis": e.popis,
                    "castka": float(e.castka),
                    "datum": e.datum.isoformat() if e.datum else None,
                    "cis_faktury": e.cis_faktury,
                    "dodavatel": e.dodavatel,
                    "poznamka": e.poznamka,
                    "created_by_initials": e.created_by_initials
                }
                for e in expenses
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_project_milestones(projekt_id: int = None) -> List[Dict]:
        """Vrátí všechny termíny/milestones projektů"""
        try:
            query = Termin.query
            if projekt_id:
                query = query.filter_by(projekt_id=projekt_id)
            
            milestones = query.order_by(Termin.datum_planovane).all()
            
            return [
                {
                    "id": m.id,
                    "projekt_id": m.projekt_id,
                    "projekt_nazev": m.projekt.nazev if m.projekt else None,
                    "nazev": m.nazev,
                    "datum_planovane": m.datum_planovane.isoformat() if m.datum_planovane else None,
                    "datum_skutecne": m.datum_skutecne.isoformat() if m.datum_skutecne else None,
                    "status": m.status,
                    "zodpovedny": m.zodpovedny,
                    "popis": m.popis,
                    "created_by_initials": m.created_by_initials
                }
                for m in milestones
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_project_messages(projekt_id: int = None) -> List[Dict]:
        """Vrátí všechny zprávy v projektech"""
        try:
            query = Zprava.query
            if projekt_id:
                query = query.filter_by(projekt_id=projekt_id)
            
            messages = query.order_by(Zprava.datum.desc()).all()
            
            return [
                {
                    "id": m.id,
                    "projekt_id": m.projekt_id,
                    "projekt_nazev": m.projekt.nazev if m.projekt else None,
                    "autor": m.autor,
                    "obsah": m.obsah,
                    "datum": m.datum.isoformat() if m.datum else None,
                    "typ": m.typ,
                    "created_by_initials": m.created_by_initials,
                    "to_user_id": m.to_user_id
                }
                for m in messages
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_project_knowledge(projekt_id: int = None) -> List[Dict]:
        """Vrátí všechny znalosti v projektech"""
        try:
            query = Znalost.query
            if projekt_id:
                query = query.filter_by(projekt_id=projekt_id)
            
            knowledge = query.order_by(Znalost.datum_vytvoreni.desc()).all()
            
            return [
                {
                    "id": k.id,
                    "projekt_id": k.projekt_id,
                    "projekt_nazev": k.projekt.nazev if k.projekt else None,
                    "nazev": k.nazev,
                    "obsah": k.obsah,
                    "kategorie": k.kategorie,
                    "datum_vytvoreni": k.datum_vytvoreni.isoformat() if k.datum_vytvoreni else None,
                    "autor": k.autor,
                    "created_by_initials": k.created_by_initials
                }
                for k in knowledge
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_services() -> List[Dict]:
        """Vrátí všechny služby"""
        try:
            services = Sluzba.query.order_by(Sluzba.datum.desc()).all()
            
            return [
                {
                    "id": s.id,
                    "template_id": s.template_id,
                    "template_nazev": s.template.nazev if s.template else None,
                    "datum": s.datum.isoformat() if s.datum else None,
                    "zamestnanec_id": s.zamestnanec_id,
                    "zamestnanec_jmeno": s.zamestnanec.jmeno_plne if s.zamestnanec else None,
                    "hodina_od": s.hodina_od,
                    "hodina_do": s.hodina_do,
                    "je_vynimka": s.je_vynimka,
                    "je_vymena": s.je_vymena
                }
                for s in services
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_service_templates() -> List[Dict]:
        """Vrátí všechny šablony služeb"""
        try:
            templates = SluzbaTemplate.query.filter_by(aktivni=True).all()
            
            return [
                {
                    "id": t.id,
                    "nazev": t.nazev,
                    "typ": t.typ,
                    "oddeleni": t.oddeleni,
                    "den_v_tydnu": t.den_v_tydnu,
                    "hodina_od": t.hodina_od,
                    "hodina_do": t.hodina_do,
                    "zamestnanec_id": t.zamestnanec_id,
                    "zamestnanec_jmeno": t.zamestnanec.jmeno_plne if t.zamestnanec else None,
                    "rotujici_seznam": t.rotujici_seznam_ids
                }
                for t in templates
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_service_exceptions() -> List[Dict]:
        """Vrátí všechny výjimky služeb"""
        try:
            exceptions = SluzbaVynimka.query.filter_by(aktivni=True).all()
            
            return [
                {
                    "id": e.id,
                    "sluzba_id": e.sluzba_id,
                    "datum": e.datum.isoformat() if e.datum else None,
                    "novy_zamestnanec_id": e.novy_zamestnanec_id,
                    "novy_zamestnanec_jmeno": e.novy_zamestnanec.jmeno_plne if e.novy_zamestnanec else None,
                    "nova_hodina_od": e.nova_hodina_od,
                    "nova_hodina_do": e.nova_hodina_do,
                    "duvod": e.duvod,
                    "aktivni": e.aktivni
                }
                for e in exceptions
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_service_exchanges() -> List[Dict]:
        """Vrátí všechny výměny služeb"""
        try:
            exchanges = SluzbaVymena.query.all()
            
            return [
                {
                    "id": e.id,
                    "sluzba1_id": e.sluzba1_id,
                    "sluzba2_id": e.sluzba2_id,
                    "zamestnanec1_id": e.zamestnanec1_id,
                    "zamestnanec1_jmeno": e.zamestnanec1.jmeno_plne if e.zamestnanec1 else None,
                    "zamestnanec2_id": e.zamestnanec2_id,
                    "zamestnanec2_jmeno": e.zamestnanec2.jmeno_plne if e.zamestnanec2 else None,
                    "schvaleno": e.schvaleno,
                    "schvalil_id": e.schvalil_id,
                    "datum_vytvoreni": e.datum_vytvoreni.isoformat() if e.datum_vytvoreni else None
                }
                for e in exchanges
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_users() -> List[Dict]:
        """Vrátí všechny uživatele"""
        try:
            users = User.query.filter_by(aktivni=True).all()
            
            return [
                {
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "role": u.role,
                    "personnel_id": u.personnel_id,
                    "personnel_jmeno": u.jmeno_prijmeni,
                    "datum_vytvoreni": u.datum_vytvoreni.isoformat() if u.datum_vytvoreni else None,
                    "posledni_prihlaseni": u.posledni_prihlaseni.isoformat() if u.posledni_prihlaseni else None
                }
                for u in users
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_user_projects() -> List[Dict]:
        """Vrátí všechna propojení uživatelů s projekty"""
        try:
            user_projects = UserProject.query.filter_by(aktivni=True).all()
            
            return [
                {
                    "id": up.id,
                    "user_id": up.user_id,
                    "user_username": up.user.username if up.user else None,
                    "projekt_id": up.projekt_id,
                    "projekt_nazev": up.projekt.nazev if up.projekt else None,
                    "role": up.role,
                    "datum_pridani": up.datum_pridani.isoformat() if up.datum_pridani else None
                }
                for up in user_projects
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_user_messages() -> List[Dict]:
        """Vrátí všechny zprávy mezi uživateli"""
        try:
            messages = UserMessage.query.order_by(UserMessage.datum_odeslani.desc()).all()
            
            return [
                {
                    "id": m.id,
                    "from_user_id": m.from_user_id,
                    "from_user_username": m.from_user.username if m.from_user else None,
                    "to_user_id": m.to_user_id,
                    "to_user_username": m.to_user.username if m.to_user else None,
                    "subject": m.subject,
                    "content": m.content,
                    "typ": m.typ,
                    "precteno": m.precteno,
                    "datum_odeslani": m.datum_odeslani.isoformat() if m.datum_odeslani else None,
                    "datum_precteni": m.datum_precteni.isoformat() if m.datum_precteni else None
                }
                for m in messages
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_user_notifications() -> List[Dict]:
        """Vrátí všechny notifikace uživatelů"""
        try:
            notifications = UserNotification.query.order_by(UserNotification.datum_vytvoreni.desc()).all()
            
            return [
                {
                    "id": n.id,
                    "user_id": n.user_id,
                    "user_username": n.user.username if n.user else None,
                    "typ": n.typ,
                    "title": n.title,
                    "content": n.content,
                    "precteno": n.precteno,
                    "related_id": n.related_id,
                    "related_type": n.related_type,
                    "datum_vytvoreni": n.datum_vytvoreni.isoformat() if n.datum_vytvoreni else None
                }
                for n in notifications
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_changelogs() -> List[Dict]:
        """Vrátí všechny záznamy changelogu"""
        try:
            changelogs = ChangeLog.query.filter_by(aktivni=True).order_by(ChangeLog.datum.desc()).all()
            
            return [
                {
                    "id": c.id,
                    "datum": c.datum.isoformat() if c.datum else None,
                    "verze": c.verze,
                    "typ": c.typ,
                    "modul": c.modul,
                    "nadpis": c.nadpis,
                    "popis": c.popis,
                    "autor": c.autor,
                    "aktivni": c.aktivni
                }
                for c in changelogs
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_monthly_budget_items() -> List[Dict]:
        """Vrátí všechny měsíční stavy položek rozpočtu"""
        try:
            monthly_items = MonthlyBudgetItem.query.order_by(MonthlyBudgetItem.rok.desc(), MonthlyBudgetItem.mesic.desc()).all()
            
            return [
                {
                    "id": m.id,
                    "budget_item_id": m.budget_item_id,
                    "budget_item_popis": m.budget_item.popis if m.budget_item else None,
                    "mesic": m.mesic,
                    "rok": m.rok,
                    "souhrnne_vydaje": float(m.souhrnne_vydaje),
                    "poznamka": m.poznamka,
                    "aktualizoval": m.aktualizoval,
                    "datum_aktualizace": m.datum_aktualizace.isoformat() if m.datum_aktualizace else None
                }
                for m in monthly_items
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_projects() -> List[Dict]:
        """Vrátí všechny projekty"""
        try:
            from ..projects.models import Projekt
            projekty = Projekt.query.order_by(Projekt.datum_vytvoreni.desc()).all()
            
            return [
                {
                    "id": p.id,
                    "nazev": p.nazev,
                    "popis": p.popis,
                    "status": p.status,
                    "vedouci": p.vedouci,
                    "rozpocet": float(p.rozpocet),
                    "celkove_vydaje": p.celkove_vydaje,
                    "zbytek": p.zbytek,
                    "procento_vycerpano": p.procento_vycerpano,
                    "datum_vytvoreni": p.datum_vytvoreni.isoformat() if p.datum_vytvoreni else None
                }
                for p in projekty
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_all_budgets() -> List[Dict]:
        """Vrátí všechny rozpočty (pro různé roky)"""
        try:
            rozpocty = Budget.query.filter_by(aktivni=True).order_by(Budget.rok.desc()).all()
            
            return [
                {
                    "id": r.id,
                    "nazev": r.nazev,
                    "rok": r.rok,
                    "hlavni": r.hlavni,
                    "castka_celkem": float(r.castka_celkem),
                    "celkove_vydaje": r.celkove_vydaje,
                    "celkove_vynosy": r.celkove_vynosy,
                    "bilance": r.bilance
                }
                for r in rozpocty
            ]
        except Exception as e:
            return []
    
    @staticmethod
    def get_monthly_overview() -> List[Dict]:
        """Vrátí měsíční přehled výdajů a výnosů"""
        try:
            hlavni = BudgetExecutor.get_or_create_main_budget()
            return BudgetExecutor.get_monthly_overview(hlavni.id, hlavni.rok)
        except Exception as e:
            return []
    
    @staticmethod
    def execute_command(command: str, params: Dict = None) -> Dict:
        """
        Provede příkaz z AI asistenta
        
        Nové příkazy pro rozpočet:
        - "add_budget_category" - přidá kategorii (params: typ, nazev, ...)
        - "add_budget_subcategory" - přidá podkategorii (params: category_id, nazev, ...)
        - "add_new_budget_item" - přidá rozpočtovou položku (params: category_id, nazev, castka, ...)
        - "add_budget_expense" - přidá výdaj (params: category_id, popis, castka, ...)
        - "get_budget_overview_new" - vrátí přehled nového rozpočtu
        """
        params = params or {}
        
        # Import ProjectExecutor pro práci s projekty
        from ..projects.executor import ProjectExecutor
        
        commands = {
            # Starý systém (kompatibilita)
            "list_budget_items": lambda: AIExecutor.get_all_budget_items(**params),
            "get_budget_summary": lambda: AIExecutor.get_budget_summary(**params),
            "create_budget_item": lambda: AIExecutor.create_budget_item(**params),
            "update_budget_item": lambda: AIExecutor.update_budget_item(**params),
            "delete_budget_item": lambda: AIExecutor.delete_budget_item(**params),
            "get_expenses": lambda: AIExecutor.get_expenses_for_item(**params),
            "add_expense": lambda: AIExecutor.add_expense(**params),
            "delete_expense": lambda: AIExecutor.delete_expense(**params),
            # Nový systém rozpočtu
            "add_budget_category": lambda: AIExecutor.add_budget_category(**params),
            "add_budget_subcategory": lambda: AIExecutor.add_budget_subcategory(**params),
            "add_new_budget_item": lambda: AIExecutor.add_new_budget_item(**params),
            "add_budget_expense": lambda: AIExecutor.add_budget_expense(**params),
            "get_budget_overview_new": lambda: AIExecutor.get_budget_overview_new(),
            # Čtení dat z databáze
            "get_all_budget_items_new": lambda: AIExecutor.get_all_budget_items_new(**params),
            "get_all_budget_categories": lambda: AIExecutor.get_all_budget_categories(),
            "get_all_expenses": lambda: AIExecutor.get_all_expenses(**params),
            "get_all_revenues": lambda: AIExecutor.get_all_revenues(),
            "get_all_projects": lambda: AIExecutor.get_all_projects(),
            "get_all_budgets": lambda: AIExecutor.get_all_budgets(),
            "get_monthly_overview": lambda: AIExecutor.get_monthly_overview(),
            # Projekty - detailní data
            "get_all_project_expenses": lambda: AIExecutor.get_all_project_expenses(**params),
            "get_all_project_milestones": lambda: AIExecutor.get_all_project_milestones(**params),
            "get_all_project_messages": lambda: AIExecutor.get_all_project_messages(**params),
            "get_all_project_knowledge": lambda: AIExecutor.get_all_project_knowledge(**params),
            # Služby
            "get_all_services": lambda: AIExecutor.get_all_services(),
            "get_all_service_templates": lambda: AIExecutor.get_all_service_templates(),
            "get_all_service_exceptions": lambda: AIExecutor.get_all_service_exceptions(),
            "get_all_service_exchanges": lambda: AIExecutor.get_all_service_exchanges(),
            # Uživatelé
            "get_all_users": lambda: AIExecutor.get_all_users(),
            "get_all_user_projects": lambda: AIExecutor.get_all_user_projects(),
            "get_all_user_messages": lambda: AIExecutor.get_all_user_messages(),
            "get_all_user_notifications": lambda: AIExecutor.get_all_user_notifications(),
            # Dokumentace
            "get_all_changelogs": lambda: AIExecutor.get_all_changelogs(),
            # Měsíční stavy
            "get_all_monthly_budget_items": lambda: AIExecutor.get_all_monthly_budget_items(),
            # Zaměstnanci
            "get_employees": lambda: AIExecutor.get_all_employees(),
            "add_employee": lambda: AIExecutor.add_employee(**params),
            "update_employee": lambda: AIExecutor.update_employee(**params),
            "get_budget_status": lambda: AIExecutor.get_budget_status_by_category(),
            # Projekty
            "set_project_budget": lambda: ProjectExecutor.set_project_budget(**params),
            "update_project_budget": lambda: ProjectExecutor.update_project_budget(**params),
            "get_project_budget": lambda: ProjectExecutor.get_project_budget(**params),
            "add_project_expense": lambda: ProjectExecutor.add_expense(**params),
            "update_project_expense": lambda: ProjectExecutor.update_expense(**params),
            "delete_project_expense": lambda: ProjectExecutor.delete_expense(**params),
            "get_project_expenses": lambda: ProjectExecutor.get_project_expenses(**params),
            "get_expense_detail": lambda: ProjectExecutor.get_expense_detail(**params),
            # Zastaralé - pro kompatibilitu
            "add_project_budget": lambda: ProjectExecutor.add_budget_item(**params),
            "get_project_budgets": lambda: ProjectExecutor.get_project_budgets(**params),
        }
        
        if command not in commands:
            return {"success": False, "error": f"Neznámý příkaz: {command}"}
        
        try:
            result = commands[command]()
            return {"success": True, "command": command, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
