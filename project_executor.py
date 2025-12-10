"""
Project Executor - Správa projektů a jejich složek
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from models import db, Projekt, BudgetProjektu, VydajProjektu, Termin, Zprava, Znalost


class ProjectExecutor:
    """Třída pro správu projektů"""
    
    # ========================================================================
    # PROJEKTY
    # ========================================================================
    
    @staticmethod
    def get_all_projects(status: Optional[str] = None) -> List[Dict]:
        """Vrátí všechny projekty"""
        query = Projekt.query
        
        if status:
            query = query.filter_by(status=status)
        
        projects = query.order_by(Projekt.datum_vytvoreni.desc()).all()
        
        return [
            {
                "id": p.id,
                "nazev": p.nazev,
                "popis": p.popis,
                "status": p.status,
                "vedouci": p.vedouci,
                "datum_vytvoreni": p.datum_vytvoreni.isoformat() if p.datum_vytvoreni else None,
                "datum_zahajeni": p.datum_zahajeni.isoformat() if p.datum_zahajeni else None,
                "datum_ukonceni_planovane": p.datum_ukonceni_planovane.isoformat() if p.datum_ukonceni_planovane else None,
                "celkovy_rozpocet": float(p.celkovy_rozpocet),
                "celkove_vydaje": float(p.celkove_vydaje),
                "zbytek": float(p.zbytek),
            }
            for p in projects
        ]
    
    @staticmethod
    def create_project(nazev: str, popis: str = None, vedouci: str = None, **kwargs) -> Dict:
        """Vytvoří nový projekt"""
        try:
            if not nazev:
                return {"success": False, "error": "Název projektu je povinný"}
            
            projekt = Projekt(
                nazev=nazev,
                popis=popis,
                vedouci=vedouci,
                status='planovani'
            )
            
            db.session.add(projekt)
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Projekt '{nazev}' byl vytvořen",
                "project_id": projekt.id,
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def update_project(projekt_id: int, **kwargs) -> Dict:
        """Upraví projekt"""
        try:
            projekt = Projekt.query.get(projekt_id)
            if not projekt:
                return {"success": False, "error": f"Projekt ID {projekt_id} neexistuje"}
            
            allowed_fields = ['nazev', 'popis', 'status', 'vedouci', 'datum_zahajeni', 'datum_ukonceni_planovane', 'poznamka']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(projekt, field, value)
            
            db.session.commit()
            return {"success": True, "message": f"Projekt '{projekt.nazev}' byl aktualizován"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def delete_project(projekt_id: int) -> Dict:
        """Smaže projekt a všechny související záznamy"""
        try:
            projekt = Projekt.query.get(projekt_id)
            if not projekt:
                return {"success": False, "error": f"Projekt ID {projekt_id} neexistuje"}
            
            nazev = projekt.nazev
            
            # Díky cascade='all, delete-orphan' v modelu se automaticky smažou:
            # - budgets (BudgetProjektu)
            # - vydaje (VydajProjektu)
            # - terminy (Termin)
            # - zpravy (Zprava)
            # - znalosti (Znalost)
            
            db.session.delete(projekt)
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Projekt '{nazev}' byl úspěšně smazán včetně všech souvisejících záznamů"
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Chyba při mazání projektu: {str(e)}"}
    
    @staticmethod
    def get_project_detail(projekt_id: int) -> Dict:
        """Vrátí detailní informace o projektu"""
        projekt = Projekt.query.get(projekt_id)
        if not projekt:
            return {"success": False, "error": f"Projekt ID {projekt_id} neexistuje"}
        
        return {
            "success": True,
            "id": projekt.id,
            "nazev": projekt.nazev,
            "popis": projekt.popis,
            "status": projekt.status,
            "vedouci": projekt.vedouci,
            "datum_vytvoreni": projekt.datum_vytvoreni.isoformat() if projekt.datum_vytvoreni else None,
            "datum_zahajeni": projekt.datum_zahajeni.isoformat() if projekt.datum_zahajeni else None,
            "datum_ukonceni_planovane": projekt.datum_ukonceni_planovane.isoformat() if projekt.datum_ukonceni_planovane else None,
            "celkovy_rozpocet": float(projekt.celkovy_rozpocet),
            "celkove_vydaje": float(projekt.celkove_vydaje),
            "zbytek": float(projekt.zbytek),
            "budgets": len(projekt.budgets),
            "vydaje": len(projekt.vydaje),
            "terminy": len(projekt.terminy),
            "zpravy": len(projekt.zpravy),
            "znalosti": len(projekt.znalosti),
        }
    
    # ========================================================================
    # ROZPOČET PROJEKTU - NOVÁ LOGIKA
    # ========================================================================
    
    @staticmethod
    def set_project_budget(projekt_id: int, rozpocet: float) -> Dict:
        """Nastaví celkový rozpočet projektu"""
        try:
            projekt = Projekt.query.get(projekt_id)
            if not projekt:
                return {"success": False, "error": f"Projekt ID {projekt_id} neexistuje"}
            
            if rozpocet < 0:
                return {"success": False, "error": "Rozpočet nemůže být záporný"}
            
            projekt.rozpocet = Decimal(str(rozpocet))
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Rozpočet projektu nastaven na {rozpocet:.2f} Kč",
                "rozpocet": float(projekt.rozpocet)
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def update_project_budget(projekt_id: int, rozpocet: float) -> Dict:
        """Upraví celkový rozpočet projektu (alias pro set_project_budget)"""
        return ProjectExecutor.set_project_budget(projekt_id, rozpocet)
    
    @staticmethod
    def get_project_budget(projekt_id: int) -> Dict:
        """Vrátí informace o rozpočtu projektu"""
        projekt = Projekt.query.get(projekt_id)
        if not projekt:
            return {"success": False, "error": f"Projekt ID {projekt_id} neexistuje"}
        
        try:
            return {
                "success": True,
                "rozpocet": float(projekt.rozpocet) if projekt.rozpocet is not None else 0.0,
                "vydaje": float(projekt.celkove_vydaje),
                "zbytek": float(projekt.zbytek),
                "procento_vycerpano": float(projekt.procento_vycerpano)
            }
        except (TypeError, ValueError, AttributeError) as e:
            # Fallback pro staré projekty bez rozpočtu
            return {
                "success": True,
                "rozpocet": 0.0,
                "vydaje": 0.0,
                "zbytek": 0.0,
                "procento_vycerpano": 0.0
            }
    
    # Zastaralé metody - ponechány pro kompatibilitu
    @staticmethod
    def add_budget_item(projekt_id: int, kategorie: str, popis: str, castka: float, **kwargs) -> Dict:
        """ZASTARALÉ: Přidá položku do rozpočtu projektu (používá se starý systém)"""
        # Tato metoda už se nepoužívá, ale ponechána pro kompatibilitu
        return {"success": False, "error": "Tato metoda je zastaralá. Použijte set_project_budget()"}
    
    @staticmethod
    def get_project_budgets(projekt_id: int) -> List[Dict]:
        """ZASTARALÉ: Vrátí rozpočtové položky projektu (používá se starý systém)"""
        # Vrátí prázdný seznam, protože už nepoužíváme BudgetProjektu
        return []
    
    # ========================================================================
    # VÝDAJE PROJEKTU
    # ========================================================================
    
    @staticmethod
    def add_expense(projekt_id: int, popis: str, castka: float, **kwargs) -> Dict:
        """Přidá výdaj k projektu"""
        try:
            projekt = Projekt.query.get(projekt_id)
            if not projekt:
                return {"success": False, "error": f"Projekt ID {projekt_id} neexistuje"}
            
            if castka <= 0:
                return {"success": False, "error": "Částka musí být větší než 0"}
            
            if not popis or not popis.strip():
                return {"success": False, "error": "Popis výdaje je povinný"}
            
            # Kontrola rozpočtu - pouze varování, ne blokování
            budget_available = float(projekt.celkovy_rozpocet) - float(projekt.celkove_vydaje)
            warning = None
            if budget_available < 0:
                warning = f"Varování: Rozpočet již byl překročen o {abs(budget_available):.2f} Kč"
            elif castka > budget_available:
                warning = f"Varování: Překročení rozpočtu! Zbývá jen {budget_available:.2f} Kč, přidáváte {castka:.2f} Kč"
            
            # Parsuj datum pokud je zadán
            datum = kwargs.get('datum')
            if datum:
                from datetime import datetime as dt
                try:
                    if isinstance(datum, str):
                        datum = dt.fromisoformat(datum.replace('Z', '+00:00'))
                except:
                    datum = datetime.utcnow()
            else:
                datum = datetime.utcnow()
            
            vydaj = VydajProjektu(
                projekt_id=projekt_id,
                popis=popis.strip(),
                castka=Decimal(str(castka)),
                datum=datum,
                cis_faktury=kwargs.get('cis_faktury'),
                dodavatel=kwargs.get('dodavatel'),
                poznamka=kwargs.get('poznamka'),
                kategorie=""  # Prázdné - zrušeno
            )
            
            db.session.add(vydaj)
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Výdaj '{popis.strip()}' ({castka:.2f} Kč) byl přidán",
                "expense_id": vydaj.id,
                "warning": warning,
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def update_expense(vydaj_id: int, **kwargs) -> Dict:
        """Upraví výdaj projektu"""
        try:
            vydaj = VydajProjektu.query.get(vydaj_id)
            if not vydaj:
                return {"success": False, "error": f"Výdaj ID {vydaj_id} neexistuje"}
            
            allowed_fields = ['popis', 'castka', 'datum', 'cis_faktury', 'dodavatel', 'poznamka']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    if field == 'castka' and value is not None:
                        if value <= 0:
                            return {"success": False, "error": "Částka musí být větší než 0"}
                        setattr(vydaj, field, Decimal(str(value)))
                    elif field == 'datum' and value:
                        from datetime import datetime as dt
                        if isinstance(value, str):
                            value = dt.fromisoformat(value.replace('Z', '+00:00'))
                        setattr(vydaj, field, value)
                    elif field == 'popis' and value:
                        setattr(vydaj, field, value.strip())
                    else:
                        setattr(vydaj, field, value)
            
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Výdaj byl upraven",
                "expense_id": vydaj.id
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def delete_expense(vydaj_id: int) -> Dict:
        """Smaže výdaj projektu"""
        try:
            vydaj = VydajProjektu.query.get(vydaj_id)
            if not vydaj:
                return {"success": False, "error": f"Výdaj ID {vydaj_id} neexistuje"}
            
            popis = vydaj.popis
            db.session.delete(vydaj)
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Výdaj '{popis}' byl smazán"
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_project_expenses(projekt_id: int, k_datu: datetime = None) -> List[Dict]:
        """Vrátí výdaje projektu (pouze do zadaného data, pokud je zadáno)"""
        query = VydajProjektu.query.filter_by(projekt_id=projekt_id)
        
        if k_datu:
            query = query.filter(VydajProjektu.datum <= k_datu)
        
        expenses = query.order_by(VydajProjektu.datum.desc()).all()
        
        return [
            {
                "id": e.id,
                "popis": e.popis,
                "castka": float(e.castka),
                "datum": e.datum.isoformat() if e.datum else None,
                "cis_faktury": e.cis_faktury,
                "dodavatel": e.dodavatel,
                "poznamka": e.poznamka,
            }
            for e in expenses
        ]
    
    @staticmethod
    def get_expense_detail(vydaj_id: int) -> Dict:
        """Vrátí detail výdaje"""
        vydaj = VydajProjektu.query.get(vydaj_id)
        if not vydaj:
            return {"success": False, "error": f"Výdaj ID {vydaj_id} neexistuje"}
        
        return {
            "success": True,
            "id": vydaj.id,
            "projekt_id": vydaj.projekt_id,
            "popis": vydaj.popis,
            "castka": float(vydaj.castka),
            "datum": vydaj.datum.isoformat() if vydaj.datum else None,
            "cis_faktury": vydaj.cis_faktury,
            "dodavatel": vydaj.dodavatel,
            "poznamka": vydaj.poznamka,
        }
    
    # ========================================================================
    # TERMÍNY
    # ========================================================================
    
    @staticmethod
    def add_milestone(projekt_id: int, nazev: str, datum_planovane: str, **kwargs) -> Dict:
        """Přidá termín/milestone do projektu"""
        try:
            projekt = Projekt.query.get(projekt_id)
            if not projekt:
                return {"success": False, "error": f"Projekt ID {projekt_id} neexistuje"}
            
            if not nazev:
                return {"success": False, "error": "Název termínu je povinný"}
            
            # Parsuj datum
            from datetime import datetime as dt
            try:
                dt_parsed = dt.fromisoformat(datum_planovane.replace('Z', '+00:00'))
            except:
                try:
                    dt_parsed = dt.strptime(datum_planovane, "%d.%m.%Y")
                except:
                    return {"success": False, "error": "Neplatný formát data"}
            
            termin = Termin(
                projekt_id=projekt_id,
                nazev=nazev,
                datum_planovane=dt_parsed,
                popis=kwargs.get('popis'),
                zodpovedny=kwargs.get('zodpovedny'),
                status='planovano'
            )
            
            db.session.add(termin)
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Termín '{nazev}' byl přidán",
                "milestone_id": termin.id,
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_project_milestones(projekt_id: int) -> List[Dict]:
        """Vrátí termíny projektu"""
        terminy = Termin.query.filter_by(projekt_id=projekt_id).order_by(Termin.datum_planovane).all()
        
        return [
            {
                "id": t.id,
                "nazev": t.nazev,
                "datum_planovane": t.datum_planovane.isoformat() if t.datum_planovane else None,
                "datum_skutecne": t.datum_skutecne.isoformat() if t.datum_skutecne else None,
                "popis": t.popis,
                "status": t.status,
                "zodpovedny": t.zodpovedny,
            }
            for t in terminy
        ]
    
    # ========================================================================
    # ZPRÁVY
    # ========================================================================
    
    @staticmethod
    def add_message(projekt_id: int, obsah: str, autor: str = "AI", typ: str = "poznamka", **kwargs) -> Dict:
        """Přidá zprávu do projektu"""
        try:
            projekt = Projekt.query.get(projekt_id)
            if not projekt:
                return {"success": False, "error": f"Projekt ID {projekt_id} neexistuje"}
            
            zprava = Zprava(
                projekt_id=projekt_id,
                obsah=obsah,
                autor=autor,
                typ=typ,
            )
            
            db.session.add(zprava)
            db.session.commit()
            
            return {"success": True, "message": "Zpráva byla přidána"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_project_messages(projekt_id: int, limit: int = 50) -> List[Dict]:
        """Vrátí zprávy projektu"""
        zpravy = Zprava.query.filter_by(projekt_id=projekt_id).order_by(Zprava.datum.desc()).limit(limit).all()
        
        return [
            {
                "id": z.id,
                "obsah": z.obsah,
                "autor": z.autor,
                "datum": z.datum.isoformat() if z.datum else None,
                "typ": z.typ,
            }
            for z in reversed(zpravy)
        ]
    
    # ========================================================================
    # ZNALOSTI
    # ========================================================================
    
    @staticmethod
    def add_knowledge(projekt_id: int, nazev: str, obsah: str, **kwargs) -> Dict:
        """Přidá znalostní položku do projektu"""
        try:
            projekt = Projekt.query.get(projekt_id)
            if not projekt:
                return {"success": False, "error": f"Projekt ID {projekt_id} neexistuje"}
            
            znalost = Znalost(
                projekt_id=projekt_id,
                nazev=nazev,
                obsah=obsah,
                kategorie=kwargs.get('kategorie'),
                autor=kwargs.get('autor', 'AI'),
            )
            
            db.session.add(znalost)
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Znalost '{nazev}' byla přidána",
                "knowledge_id": znalost.id,
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_project_knowledge(projekt_id: int) -> List[Dict]:
        """Vrátí znalosti projektu"""
        znalosti = Znalost.query.filter_by(projekt_id=projekt_id).order_by(Znalost.datum_vytvoreni.desc()).all()
        
        return [
            {
                "id": z.id,
                "nazev": z.nazev,
                "obsah": z.obsah,
                "kategorie": z.kategorie,
                "autor": z.autor,
                "datum_vytvoreni": z.datum_vytvoreni.isoformat() if z.datum_vytvoreni else None,
            }
            for z in znalosti
        ]
    
    # ========================================================================
    # UNIVERZÁLNÍ PŘÍKAZY
    # ========================================================================
    
    @staticmethod
    def execute_command(command: str, params: Dict = None, projekt_id: int = None) -> Dict:
        """Provede příkaz"""
        params = params or {}
        
        commands = {
            "list_projects": lambda: ProjectExecutor.get_all_projects(**params),
            "create_project": lambda: ProjectExecutor.create_project(**params),
            "get_project": lambda: ProjectExecutor.get_project_detail(projekt_id) if projekt_id else {"error": "projekt_id required"},
            "add_budget": lambda: ProjectExecutor.add_budget_item(projekt_id, **params) if projekt_id else {"error": "projekt_id required"},
            "get_budgets": lambda: ProjectExecutor.get_project_budgets(projekt_id) if projekt_id else {"error": "projekt_id required"},
            "add_expense": lambda: ProjectExecutor.add_expense(projekt_id, **params) if projekt_id else {"error": "projekt_id required"},
            "get_expenses": lambda: ProjectExecutor.get_project_expenses(projekt_id) if projekt_id else {"error": "projekt_id required"},
            "add_milestone": lambda: ProjectExecutor.add_milestone(projekt_id, **params) if projekt_id else {"error": "projekt_id required"},
            "get_milestones": lambda: ProjectExecutor.get_project_milestones(projekt_id) if projekt_id else {"error": "projekt_id required"},
            "add_message": lambda: ProjectExecutor.add_message(projekt_id, **params) if projekt_id else {"error": "projekt_id required"},
            "get_messages": lambda: ProjectExecutor.get_project_messages(projekt_id, **params) if projekt_id else {"error": "projekt_id required"},
            "add_knowledge": lambda: ProjectExecutor.add_knowledge(projekt_id, **params) if projekt_id else {"error": "projekt_id required"},
            "get_knowledge": lambda: ProjectExecutor.get_project_knowledge(projekt_id) if projekt_id else {"error": "projekt_id required"},
        }
        
        if command not in commands:
            return {"success": False, "error": f"Neznámý příkaz: {command}"}
        
        try:
            result = commands[command]()
            return {"success": True, "command": command, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
