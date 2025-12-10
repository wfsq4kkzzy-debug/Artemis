"""
AI Executor - Bezpečné provádění akcí pro AI asistenta
- Přidávání/úpravy/mazání rozpočtových položek
- Správa výdajů
- Správa zaměstnanců
- Dotazy do databáze
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import json

from models import db, UctovaSkupina, RozpoctovaPolozka, Vydaj, ZamestnanecAOON


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
    
    @staticmethod
    def execute_command(command: str, params: Dict = None) -> Dict:
        """
        Provede příkaz z AI asistenta
        
        Příklady:
        - "list_budget_items" - vrátí všechny rozpočtové položky
        - "get_budget_summary" - vrátí souhrn
        - "create_budget_item" - vytvoří novou položku (params: nazev, rozpocet, uctova_skupina_id, ...)
        - "add_expense" - přidá výdaj (params: polozka_id, castka, popis, ...)
        - "get_employees" - vrátí zaměstnance
        - "add_project_budget" - přidá položku do rozpočtu projektu (params: projekt_id, kategorie, popis, castka, ...)
        - "add_project_expense" - přidá výdaj k projektu (params: projekt_id, popis, castka, ...)
        """
        params = params or {}
        
        # Import ProjectExecutor pro práci s projekty
        from project_executor import ProjectExecutor
        
        commands = {
            "list_budget_items": lambda: AIExecutor.get_all_budget_items(**params),
            "get_budget_summary": lambda: AIExecutor.get_budget_summary(**params),
            "create_budget_item": lambda: AIExecutor.create_budget_item(**params),
            "update_budget_item": lambda: AIExecutor.update_budget_item(**params),
            "delete_budget_item": lambda: AIExecutor.delete_budget_item(**params),
            "get_expenses": lambda: AIExecutor.get_expenses_for_item(**params),
            "add_expense": lambda: AIExecutor.add_expense(**params),
            "delete_expense": lambda: AIExecutor.delete_expense(**params),
            "get_employees": lambda: AIExecutor.get_all_employees(),
            "add_employee": lambda: AIExecutor.add_employee(**params),
            "update_employee": lambda: AIExecutor.update_employee(**params),
            "get_budget_status": lambda: AIExecutor.get_budget_status_by_category(),
            # Nové příkazy pro projekty
            "add_project_budget": lambda: ProjectExecutor.add_budget_item(**params),
            "add_project_expense": lambda: ProjectExecutor.add_expense(**params),
            "get_project_budgets": lambda: ProjectExecutor.get_project_budgets(**params),
            "get_project_expenses": lambda: ProjectExecutor.get_project_expenses(**params),
        }
        
        if command not in commands:
            return {"success": False, "error": f"Neznámý příkaz: {command}"}
        
        try:
            result = commands[command]()
            return {"success": True, "command": command, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
