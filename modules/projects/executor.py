"""
Project Executor - Správa projektů a jejich složek
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from core import db
from .models import Projekt, BudgetProjektu, VydajProjektu, Termin, Zprava, ProjectShare


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
                "created_by_user": {
                    "id": p.created_by_user.id,
                    "jmeno_prijmeni": p.created_by_user.jmeno_prijmeni
                } if p.created_by_user else None,
                "created_by_personnel": {
                    "id": p.created_by_personnel.id,
                    "jmeno_plne": p.created_by_personnel.jmeno_plne
                } if p.created_by_personnel else None,
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
    def create_project(nazev: str, popis: str = None, created_by_user_id: int = None, created_by_personnel_id: int = None, **kwargs) -> Dict:
        """Vytvoří nový projekt"""
        try:
            if not nazev:
                return {"success": False, "error": "Název projektu je povinný"}
            
            projekt = Projekt(
                nazev=nazev,
                popis=popis,
                status='planovani',
                created_by_user_id=created_by_user_id,
                created_by_personnel_id=created_by_personnel_id
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
            
            allowed_fields = ['nazev', 'popis', 'status', 'datum_zahajeni', 'datum_ukonceni_planovane', 'poznamka']
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
        """Smaže projekt a všechny související záznamy včetně výdajů v rozpočtu"""
        try:
            projekt = Projekt.query.get(projekt_id)
            if not projekt:
                return {"success": False, "error": f"Projekt ID {projekt_id} neexistuje"}
            
            nazev = projekt.nazev
            
            # Počítadla pro upozornění
            pocet_vydaju_projektu = len(projekt.vydaje) if projekt.vydaje else 0
            
            
            # Díky cascade='all, delete-orphan' v modelu se automaticky smažou:
            # - budgets (BudgetProjektu)
            # - vydaje (VydajProjektu)
            # - terminy (Termin)
            # - zpravy (Zprava)
            
            db.session.delete(projekt)
            db.session.commit()
            
            message = f"Projekt '{nazev}' byl úspěšně smazán včetně všech souvisejících záznamů"
            if pocet_vydaju_rozpoctu > 0:
                message += f" ({pocet_vydaju_rozpoctu} výdajů v rozpočtu, {pocet_vydaju_projektu} výdajů projektu)"
            
            return {
                "success": True,
                "message": message
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
            "created_by_user": {
                "id": projekt.created_by_user.id,
                "jmeno_prijmeni": projekt.created_by_user.jmeno_prijmeni
            } if projekt.created_by_user else None,
            "created_by_personnel": {
                "id": projekt.created_by_personnel.id,
                "jmeno_plne": projekt.created_by_personnel.jmeno_plne
            } if projekt.created_by_personnel else None,
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
            
            # Získej iniciály z kwargs nebo použij prázdné
            created_by_initials = kwargs.get('created_by_initials', '').strip()[:10] if kwargs.get('created_by_initials') else None
            
            vydaj = VydajProjektu(
                projekt_id=projekt_id,
                popis=popis.strip(),
                castka=Decimal(str(castka)),
                datum=datum,
                cis_faktury=kwargs.get('cis_faktury'),
                dodavatel=kwargs.get('dodavatel'),
                poznamka=kwargs.get('poznamka'),
                kategorie="",  # Prázdné - zrušeno
                created_by_initials=created_by_initials
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
                "created_by_initials": e.created_by_initials,
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
    def add_milestone(projekt_id: int, nazev: str, datum_planovane: str, created_by_initials: str = None, **kwargs) -> Dict:
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
                "created_by_initials": t.created_by_initials,
            }
            for t in terminy
        ]
    
    # ========================================================================
    # ZPRÁVY
    # ========================================================================
    
    @staticmethod
    def add_message(projekt_id: int, obsah: str, autor: str = "AI", typ: str = "poznamka", created_by_initials: str = None, to_user_id: int = None, **kwargs) -> Dict:
        """Přidá zprávu do projektu"""
        try:
            projekt = Projekt.query.get(projekt_id)
            if not projekt:
                return {"success": False, "error": f"Projekt ID {projekt_id} neexistuje"}
            
            # Získej iniciály z kwargs nebo použij prázdné
            initials = created_by_initials.strip()[:10] if created_by_initials else None
            
            zprava = Zprava(
                projekt_id=projekt_id,
                obsah=obsah,
                autor=autor,
                typ=typ,
                created_by_initials=initials,
                to_user_id=to_user_id  # null = všem, jinak ID uživatele
            )
            
            db.session.add(zprava)
            db.session.commit()
            
            return {"success": True, "message": "Zpráva byla přidána"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_project_messages(projekt_id: int, limit: int = 50, current_user_id: int = None) -> List[Dict]:
        """Vrátí zprávy projektu (pouze ty, které jsou určeny všem nebo aktuálnímu uživateli)"""
        query = Zprava.query.filter_by(projekt_id=projekt_id)
        
        # Pokud je zadán current_user_id, zobraz zprávy určené všem (to_user_id IS NULL) nebo tomuto uživateli
        if current_user_id:
            from sqlalchemy import or_
            query = query.filter(or_(Zprava.to_user_id.is_(None), Zprava.to_user_id == current_user_id))
        
        zpravy = query.order_by(Zprava.datum.desc()).limit(limit).all()
        
        return [
            {
                "id": z.id,
                "obsah": z.obsah,
                "autor": z.autor,
                "datum": z.datum.isoformat() if z.datum else None,
                "typ": z.typ,
                "created_by_initials": z.created_by_initials,
                "to_user_id": z.to_user_id,
                "to_user": {
                    "id": z.to_user.id,
                    "jmeno_prijmeni": z.to_user.jmeno_prijmeni
                } if z.to_user else None,
            }
            for z in reversed(zpravy)
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
        }
        
        if command not in commands:
            return {"success": False, "error": f"Neznámý příkaz: {command}"}
        
        try:
            result = commands[command]()
            return {"success": True, "command": command, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ========================================================================
    # SDÍLENÍ PROJEKTŮ
    # ========================================================================
    
    @staticmethod
    def share_project(projekt_id: int, shared_with_user_id: int, shared_by_user_id: int, permission: str = 'read', poznamka: str = None) -> Dict:
        """Sdílí projekt s jiným uživatelem"""
        try:
            projekt = Projekt.query.get(projekt_id)
            if not projekt:
                return {"success": False, "error": f"Projekt ID {projekt_id} neexistuje"}
            
            # Zkontroluj, zda uživatel existuje
            from ..users.models import User
            shared_with_user = User.query.get(shared_with_user_id)
            if not shared_with_user:
                return {"success": False, "error": f"Uživatel ID {shared_with_user_id} neexistuje"}
            
            # Zkontroluj, zda shared_by_user existuje
            shared_by_user = User.query.get(shared_by_user_id)
            if not shared_by_user:
                return {"success": False, "error": f"Uživatel, který pozývá (ID {shared_by_user_id}) neexistuje"}
            
            # Nemůžete pozvat sami sebe
            if shared_with_user_id == shared_by_user_id:
                return {"success": False, "error": "Nemůžete pozvat sami sebe"}
            
            if permission not in ['read', 'write']:
                return {"success": False, "error": "Neplatné oprávnění (povoleno: 'read', 'write')"}
            
            # Zkontroluj, zda už není sdíleno
            existing = ProjectShare.query.filter_by(
                projekt_id=projekt_id,
                shared_with_user_id=shared_with_user_id,
                aktivni=True
            ).first()
            
            if existing:
                # Aktualizuj existující sdílení
                existing.permission = permission
                existing.poznamka = poznamka
                existing.datum_sdileni = datetime.utcnow()
            else:
                # Vytvoř nové sdílení
                share = ProjectShare(
                    projekt_id=projekt_id,
                    shared_with_user_id=shared_with_user_id,
                    shared_by_user_id=shared_by_user_id,
                    permission=permission,
                    poznamka=poznamka
                )
                db.session.add(share)
            
            db.session.commit()
            
            # Bezpečně získej jméno uživatele
            try:
                user_name = shared_with_user.jmeno_prijmeni
            except (AttributeError, Exception):
                user_name = shared_with_user.username
            
            return {
                "success": True,
                "message": f"Uživatel {user_name} byl pozván do projektu"
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def unshare_project(projekt_id: int, shared_with_user_id: int) -> Dict:
        """Zruší sdílení projektu s uživatelem"""
        try:
            share = ProjectShare.query.filter_by(
                projekt_id=projekt_id,
                shared_with_user_id=shared_with_user_id,
                aktivni=True
            ).first()
            
            if not share:
                return {"success": False, "error": "Sdílení neexistuje"}
            
            share.aktivni = False
            db.session.commit()
            
            return {
                "success": True,
                "message": "Sdílení bylo zrušeno"
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _safe_get_user_name(user) -> str:
        """Bezpečně získá jméno uživatele"""
        try:
            return user.jmeno_prijmeni
        except (AttributeError, Exception):
            try:
                return user.username
            except:
                return "Neznámý uživatel"
    
    @staticmethod
    def get_project_shares(projekt_id: int) -> List[Dict]:
        """Vrátí seznam všech aktivních sdílení projektu"""
        shares = ProjectShare.query.filter_by(
            projekt_id=projekt_id,
            aktivni=True
        ).all()
        
        return [
            {
                "id": s.id,
                "shared_with_user_id": s.shared_with_user_id,
                "shared_by_user_id": s.shared_by_user_id,
                "permission": s.permission,
                "datum_sdileni": s.datum_sdileni.isoformat() if s.datum_sdileni else None,
                "poznamka": s.poznamka,
                "shared_with_user": {
                    "id": s.shared_with_user.id,
                    "username": s.shared_with_user.username,
                    "jmeno_prijmeni": ProjectExecutor._safe_get_user_name(s.shared_with_user)
                } if s.shared_with_user else None,
                "shared_by_user": {
                    "id": s.shared_by_user.id,
                    "username": s.shared_by_user.username,
                    "jmeno_prijmeni": ProjectExecutor._safe_get_user_name(s.shared_by_user)
                } if s.shared_by_user else None
            }
            for s in shares
        ]
    
    @staticmethod
    def can_user_access_project(user_id: int, projekt_id: int) -> Dict:
        """Zkontroluje, zda má uživatel přístup k projektu"""
        projekt = Projekt.query.get(projekt_id)
        if not projekt:
            return {"can_access": False, "permission": None, "reason": "Projekt neexistuje"}
        
        # Vlastník projektu má vždy plný přístup
        if projekt.created_by_user_id == user_id:
            return {"can_access": True, "permission": "owner", "reason": "Vlastník projektu"}
        
        # Zkontroluj sdílení
        share = ProjectShare.query.filter_by(
            projekt_id=projekt_id,
            shared_with_user_id=user_id,
            aktivni=True
        ).first()
        
        if share:
            return {
                "can_access": True,
                "permission": share.permission,
                "reason": "Sdílený projekt"
            }
        
        return {"can_access": False, "permission": None, "reason": "Nemáte přístup k tomuto projektu"}
